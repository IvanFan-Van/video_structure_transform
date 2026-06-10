"""Audio feature extraction for music-driven video generation.

Features extracted:
    - BPM (tempo, via librosa)
    - Beat timings (rhythmic pulse points)
    - RMS energy curve (loudness envelope)
    - Spectral centroid (brightness)
    - Dynamic range (loudness variation)

Utilities:
    - BGM extraction (ffmpeg + UVR-MDX-NET vocal separation)
    - Music genre classification (HuggingFace transformer)
"""

import logging
import threading
from pathlib import Path

import ffmpeg
import librosa
from audio_separator.separator import Separator

from app.config import MODELS_DIR, TMP_DIR

_separator: Separator | None = None
_separator_lock = threading.Lock()

_classifier = None
_classifier_lock = threading.Lock()


def _get_separator() -> Separator:
    global _separator
    if _separator is None:
        with _separator_lock:
            if _separator is None:
                TMP_DIR.mkdir(parents=True, exist_ok=True)
                _separator = Separator(
                    output_dir=str(TMP_DIR),
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

                MODELS_DIR.mkdir(parents=True, exist_ok=True)
                _classifier = pipeline(
                    "audio-classification",
                    model="dima806/music_genres_classification",
                    trust_remote_code=True,
                    cache_dir=str(MODELS_DIR),
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
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    audio_wav = TMP_DIR / f"{audio_asset_id}_audio.wav"
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

    bgm_src = TMP_DIR / Path(output_files[0])
    bgm_dst = dst_dir / f"{audio_asset_id}_bgm.wav"
    bgm_src.rename(bgm_dst)

    audio_wav.unlink(missing_ok=True)
    bgm_src.unlink(missing_ok=True)

    return bgm_dst


def analyze_audio_features(audio_path: str | Path) -> dict:
    """Extract global audio features from a BGM WAV file using librosa.

    Replaces the old aubio-based ``stream_audio_features``.
    All features are computed in one pass — no streaming, no
    frame-by-frame yielding.

    Parameters
    ----------
    audio_path : str or Path
        Path to the extracted BGM WAV file.

    Returns
    -------
    dict with keys:
        duration               — total audio duration (seconds)
        genre                  — music genre (HuggingFace classification)
        bpm                    — BPM via librosa beat tracking
        beat_timings           — all heavy-beat time positions (seconds)
        energy_curve           — per-frame RMS energy values
        spectral_centroid      — per-frame spectral centroid (Hz)
        spectral_centroid_mean — global mean spectral centroid (Hz)
        spectral_flux          — per-frame spectral flux
        onset_envelope         — per-frame onset strength envelope
        dynamic_range          — max – min RMS
    """
    import numpy as np

    audio_path = Path(audio_path)

    y, sr = librosa.load(str(audio_path), sr=None)
    duration = float(librosa.get_duration(y=y, sr=sr))

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(tempo[0]) if hasattr(tempo, "__iter__") else float(tempo)  # type: ignore
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    rms = librosa.feature.rms(y=y)[0]
    rms_arr = np.asarray(rms)
    dynamic_range = float(rms_arr.max() - rms_arr.min())

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_arr = np.asarray(centroid)

    S = np.abs(librosa.stft(y, hop_length=512))
    flux_diff = np.diff(S, axis=1)
    flux = np.sqrt(np.sum(flux_diff**2, axis=0))
    flux = np.concatenate(([0.0], flux))

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    classifier = _get_classifier()
    with _classifier_lock:
        genres = classifier(str(audio_path))
    genre = max(genres, key=lambda x: x["score"])["label"]

    return {
        "duration": round(duration, 1),
        "genre": genre,
        "bpm": round(bpm, 1),
        "beat_timings": [round(float(t), 2) for t in beat_times],
        "energy_curve": [round(float(e), 4) for e in rms],
        "spectral_centroid": [round(float(c), 1) for c in centroid_arr],
        "spectral_centroid_mean": round(float(centroid_arr.mean()), 1),
        "spectral_flux": [round(float(f), 4) for f in flux],
        "onset_envelope": [round(float(o), 4) for o in onset_env],
        "dynamic_range": round(dynamic_range, 4),
    }
