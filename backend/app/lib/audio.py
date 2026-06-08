"""Audio feature extraction for music-driven video generation.

Features extracted:
    - BPM (tempo)
    - Beat times (rhythmic pulse points)
    - Onset times and strengths (transient detection)
    - RMS energy (loudness envelope)
    - Spectral centroid (brightness)
    - Spectral flux (spectral change rate)
    - Dynamic range (loudness variation)
    - MFCCs (timbral features, 13 coefficients)
    - Chroma (harmonic/tonal features, 12 semitones)
    - Downbeats (first beat of each bar)
    - Pulse clarity (rhythm detectability)

Utilities:
    - Golden cut points (merged beat + onset for video cutting)
    - Onset strength visualization (ASCII heatmap + matplotlib chart)
    - Streaming feature extraction (aubio-based, generator for SSE endpoints)
"""

import logging
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import no_type_check

import aubio
import ffmpeg
from audio_separator.separator import Separator

STORAGE_TMP = Path("storage/tmp")
STREAM_EOF = object()

_separator: Separator | None = None
_separator_lock = threading.Lock()

_classifier = None
_classifier_lock = threading.Lock()


def _get_separator() -> Separator:
    global _separator
    if _separator is None:
        with _separator_lock:
            if _separator is None:
                STORAGE_TMP.mkdir(parents=True, exist_ok=True)
                _separator = Separator(
                    output_dir=str(STORAGE_TMP),
                    output_format="wav",
                    log_level=logging.ERROR,
                )
                _separator.load_model("UVR-MDX-NET-Inst_HQ_3.onnx")
    return _separator


def _get_classifier():
    global _classifier
    if _classifier is None:
        with _classifier_lock:
            if _classifier is None:
                from transformers import pipeline

                _classifier = pipeline(
                    "audio-classification",
                    model="dima806/music_genres_classification",
                    trust_remote_code=True,
                )
    return _classifier


def extract_bgm(
    video_path: str | Path,
    dst_dir: Path,
    audio_asset_id: str,
) -> Path:
    """从视频中分离背景音乐（伴奏），仅保留 instrumental 轨道。

    1. ffmpeg 提取音轨 → 临时 WAV
    2. audio_separator (UVR-MDX-NET-Inst_HQ_3.onnx) 人声/伴奏分离
    3. 保留伴奏 (instrumental) → dst_dir / {audio_asset_id}_bgm.mp3
    4. 丢弃人声 (vocal)，清理所有临时文件

    Parameters
    ----------
    video_path : str or Path
        源视频文件路径。
    dst_dir : Path
        目标存储目录。
    audio_asset_id : str
        用于生成输出文件名的 asset UUID。

    Returns
    -------
    bgm_path : Path
        分离后的背景音乐 mp3 文件路径。
    """
    video_path = Path(video_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    STORAGE_TMP.mkdir(parents=True, exist_ok=True)

    audio_wav = STORAGE_TMP / f"{audio_asset_id}_audio.wav"
    ffmpeg.input(str(video_path)).output(str(audio_wav), loglevel="error").run(
        overwrite_output=True
    )

    separator = _get_separator()
    with _separator_lock:
        output_files = separator.separate(
            str(audio_wav),
            {
                "Instrumental": "bgm",
            },
        )

    bgm_src = STORAGE_TMP / Path(output_files[0])
    bgm_dst = dst_dir / f"{audio_asset_id}_bgm.wav"
    bgm_src.rename(bgm_dst)

    audio_wav.unlink(missing_ok=True)
    bgm_src.unlink(missing_ok=True)

    return bgm_dst


@no_type_check
def stream_audio_features(
    audio_path: str | Path,
    *,
    audio_asset_id: str | None = None,
    win_size: int = 1024,
    hop_size: int = 512,
    sample_rate: int = 0,
) -> Iterator[dict]:
    """Stream frames of audio features in real time using aubio.

    Processes an audio file frame-by-frame via ``aubio.source`` and
    yields one dict per frame.  Each dict contains both **local**
    (frame-level) and **running global** (cumulative from the
    beginning) features.  Designed as a backend for SSE streaming
    endpoints — the consumer can read incrementally without waiting
    for the full file to be analysed.

    Before streaming begins, two fixed global attributes are
    extracted from the full file: ``duration`` (seconds) and
    ``genre`` (via HuggingFace audio classification).  These are
    attached to every frame's ``running_global`` dict.

    Parameters
    ----------
    audio_path : str or Path
        Path to an audio file (wav, mp3, etc.).
    audio_asset_id : str or None
        Optional UUID of the audio asset in the database.  When
        provided it is attached to every yielded frame as the
        top-level key ``asset_id`` so clients can reference
        the source without an extra round-trip.
    win_size : int
        FFT window size in samples. Default 1024.
    hop_size : int
        Hop size in samples. Default 512 tells how many samples
        advance between successive frames.
    sample_rate : int
        Target sample rate. 0 means use the file's native rate.

    Yields
    ------
    dict with keys:
        time : float
            Position in seconds since the start of the audio.
        asset_id : str or None
            The ``audio_asset_id`` passed in (same across all frames).
        frame_index : int
            Zero-based sequential frame number.
        is_last_frame : bool
            True only on the very last frame (read < hop_size).
        local : dict
            Frame-level features — ``rms``, ``spectral_centroid``,
            ``spectral_flux``, ``onset_envelope``.
        running_global : dict
            Cumulative features computed sequentially from frame 0
            up to and including the current frame —
            ``duration``, ``genre``,
            ``average_spectral_centroid``, ``overall_brightness_hz``,
            ``dynamic_range``, ``estimated_bpm``.
    """
    audio_path = Path(audio_path)
    source = aubio.source(str(audio_path), sample_rate, hop_size)
    sr = source.samplerate
    pv = aubio.pvoc(win_size, hop_size)

    # ── Pre-processing: duration ───────────────────────────────────
    duration_sec = source.duration / float(sr)

    # ── Pre-processing: genre (HuggingFace audio classification) ───
    classifier = _get_classifier()
    with _classifier_lock:
        genres = classifier(str(audio_path))
    genre = max(genres, key=lambda x: x["score"])["label"]

    # ── Streaming setup ────────────────────────────────────────────
    centroid_detector = aubio.specdesc("centroid", win_size)
    flux_detector = aubio.specdesc("specflux", win_size)
    onset_detector = aubio.specdesc("default", win_size)
    tempo_detector = aubio.tempo("default", win_size, hop_size, sr)

    frame_index = 0
    total_frames = 0

    running_avg_centroid = 0.0
    running_max_rms = -float("inf")
    running_min_rms = float("inf")

    try:
        while True:
            samples, read = source()
            current_time = total_frames / float(sr)

            rms_val = aubio.level_lin(samples)
            ffted = pv(samples)
            centroid_val = centroid_detector(ffted)[0]
            flux_val = flux_detector(ffted)[0]
            onset_env_val = onset_detector(ffted)[0]
            tempo_detector(samples)

            if frame_index == 0:
                running_avg_centroid = centroid_val
            else:
                running_avg_centroid += (centroid_val - running_avg_centroid) / (
                    frame_index + 1
                )

            if rms_val > 0.0001:
                if rms_val > running_max_rms:
                    running_max_rms = rms_val
                if rms_val < running_min_rms:
                    running_min_rms = rms_val

            running_dynamic_range = (
                running_max_rms - running_min_rms
                if running_max_rms != -float("inf") and running_min_rms != float("inf")
                else 0.0
            )
            running_bpm = tempo_detector.get_bpm()
            is_last = read < hop_size

            yield {
                "time": current_time,
                "asset_id": audio_asset_id,
                "frame_index": frame_index,
                "is_last_frame": is_last,
                "local": {
                    "rms": float(rms_val),
                    "spectral_centroid": float(centroid_val),
                    "spectral_flux": float(flux_val),
                    "onset_envelope": float(onset_env_val),
                },
                "running_global": {
                    "duration": float(duration_sec),
                    "genre": genre,
                    "average_spectral_centroid": float(running_avg_centroid),
                    "overall_brightness_hz": float(running_avg_centroid),
                    "dynamic_range": float(running_dynamic_range),
                    "estimated_bpm": float(running_bpm),
                },
            }

            frame_index += 1
            total_frames += read
            if is_last:
                break

    finally:
        del source, pv, centroid_detector, flux_detector, onset_detector, tempo_detector
