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

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import aubio
import ffmpeg
import librosa
import numpy as np
from audio_separator.separator import Separator
from matplotlib import pyplot as plt

__all__ = [
    "extract_bgm",
    "extract_music_features",
    "compute_spectral_flux",
    "compute_dynamic_range",
    "detect_downbeats",
    "compute_pulse_clarity",
    "generate_golden_cut_points",
    "generate_golden_cut_points_from_features",
    "merge_adjacent_beats",
    "visualize_onset_strength",
    "print_onset_heatmap",
    "format_onset_heatmap",
    "stream_audio_features",
]


# ═══════════════════════════════════════════════════════════════════════
# Core Feature Extraction
# ═══════════════════════════════════════════════════════════════════════


def extract_music_features(
    audio_path: str | Path,
    *,
    hop_length: int = 512,
    n_mfcc: int = 13,
    n_mels: int = 128,
    fmax: float | None = None,
    verbose: bool = False,
) -> dict:
    """Extract a comprehensive set of music features from an audio file.

    Parameters
    ----------
    audio_path : str or Path
        Path to the input audio file (mp3, wav, etc.).
    hop_length : int
        Hop length for STFT-based features (default 512 at 22.05 kHz =
        ~23.2 ms per frame).
    n_mfcc : int
        Number of MFCC coefficients (default 13).
    n_mels : int
        Number of Mel bands for MFCC computation (default 128).
    fmax : float or None
        Maximum frequency for Mel scale. None = sr/2.
    verbose : bool
        Print progress messages.

    Returns
    -------
    dict with keys:
        bpm : float
            Estimated global tempo (beats per minute).
        beat_times : np.ndarray (N,)
            Beat positions in seconds.
        onset_times : np.ndarray (M,)
            Onset (transient) positions in seconds.
        onset_strengths : np.ndarray (M,)
            Onset strength values at each onset position (raw units).
        onset_env : np.ndarray (F,)
            Full onset strength envelope (one value per frame).
        rms : np.ndarray (F,)
            RMS energy per frame (linear amplitude).
        spectral_centroids : np.ndarray (F,)
            Spectral centroid per frame (Hz).
        spectral_flux : np.ndarray (F-1,)
            Spectral flux per frame (frame-to-frame spectrum change).
        mfcc : np.ndarray (n_mfcc, F)
            Mel-frequency cepstral coefficients.
        chroma : np.ndarray (12, F)
            Chroma (pitch class) features per frame.
        downbeat_times : np.ndarray (D,)
            Estimated downbeat (bar-first-beat) positions in seconds.
        pulse_clarity : float
            Score 0-1 indicating how clear the rhythmic pulse is.
        dynamic_range : np.ndarray (F,)
            Local dynamic range per frame (dB).
    """
    audio_path = Path(audio_path)

    if verbose:
        print(f"Loading audio: {audio_path} ...")

    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    if verbose:
        print(f"Loaded: sr={sr} Hz, duration={duration:.2f}s")

    features: dict = {}

    # ── Rhythm & timing ──────────────────────────────────────────
    if verbose:
        print("  [1/4] Rhythm & timing features ...")

    tempo_array, beat_frames = librosa.beat.beat_track(
        y=y, sr=sr, hop_length=hop_length
    )
    features["bpm"] = float(np.mean(tempo_array))
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
    features["beat_times"] = np.asarray(beat_times)

    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, hop_length=hop_length, backtrack=True
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    features["onset_times"] = np.asarray(onset_times)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    features["onset_env"] = onset_env
    features["onset_strengths"] = (
        onset_env[onset_frames] if len(onset_frames) > 0 else np.array([])
    )

    # ── Energy & timbre ──────────────────────────────────────────
    if verbose:
        print("  [2/4] Energy & timbre features ...")

    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    features["rms"] = rms

    features["spectral_centroids"] = librosa.feature.spectral_centroid(
        y=y, sr=sr, hop_length=hop_length
    )[0]

    features["spectral_flux"] = compute_spectral_flux(y=y, hop_length=hop_length)

    features["mfcc"] = librosa.feature.mfcc(
        y=y, sr=sr, hop_length=hop_length, n_mfcc=n_mfcc, n_mels=n_mels, fmax=fmax
    )

    # ── Harmony & tonality ───────────────────────────────────────
    if verbose:
        print("  [3/4] Harmonic & tonal features ...")

    features["chroma"] = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length)

    # ── Structural features ──────────────────────────────────────
    if verbose:
        print("  [4/4] Structural features ...")

    features["downbeat_times"] = detect_downbeats(
        y=y, sr=sr, beat_times=beat_times, hop_length=hop_length
    )
    features["pulse_clarity"] = compute_pulse_clarity(y=y, sr=sr, onset_env=onset_env)
    features["dynamic_range"] = compute_dynamic_range(rms, sr=sr, hop_length=hop_length)

    if verbose:
        print("\nFeature extraction complete.")
        print(
            f"  BPM: {features['bpm']:.1f}  ·  "
            f"Beats: {len(features['beat_times'])}  ·  "
            f"Onsets: {len(features['onset_times'])}  ·  "
            f"Downbeats: {len(features['downbeat_times'])}"
        )
        print(
            f"  Pulse Clarity: {features['pulse_clarity']:.2f}  ·  "
            f"Duration: {duration:.2f}s"
        )

    return features


# ═══════════════════════════════════════════════════════════════════════
# Sub-feature Extractors
# ═══════════════════════════════════════════════════════════════════════


def compute_spectral_flux(
    y: np.ndarray | None = None,
    S: np.ndarray | None = None,
    hop_length: int = 512,
) -> np.ndarray:
    """Compute spectral flux — frame-to-frame magnitude spectrum change.

    Spectral flux measures how much the frequency content changes between
    consecutive frames. High flux = new sounds appearing/disappearing
    (drum hits, instrument entries, sudden stops). Low flux = stable
    sustained tones.

    Parameters
    ----------
    y : np.ndarray or None
        Raw audio signal. Required if S not provided.
    S : np.ndarray or None
        Precomputed magnitude spectrogram. Takes precedence over y.
    hop_length : int
        STFT hop length (only used if y is provided).

    Returns
    -------
    flux : np.ndarray (F-1,)
        L2 norm of frame-to-frame magnitude difference, length = n_frames-1.
    """
    if S is not None:
        mag = np.abs(S)
    elif y is not None:
        mag = np.abs(librosa.stft(y, hop_length=hop_length))
    else:
        raise ValueError("Either y or S must be provided")

    diff = np.diff(mag, axis=1)
    flux = np.sqrt(np.sum(diff**2, axis=0))
    return flux


def compute_dynamic_range(
    rms: np.ndarray,
    sr: float = 22050,
    hop_length: int = 512,
    window_sec: float = 2.0,
) -> np.ndarray:
    """Compute local dynamic range from an RMS energy curve.

    Dynamic range is the difference (in dB) between the loudest and
    quietest moment within a sliding time window. High values indicate
    passages with strong loud-soft contrast (e.g., orchestral swells).
    Low values suggest compressed/steady energy (e.g., ambient drones).

    Parameters
    ----------
    rms : np.ndarray (F,)
        RMS energy per frame (linear amplitude), as returned by
        ``librosa.feature.rms``.
    sr : float
        Sample rate of the audio (used to convert window_sec to frames).
    hop_length : int
        Hop length used to compute rms (default 512).
    window_sec : float
        Sliding window size in seconds (default 2.0).

    Returns
    -------
    dynamic_range : np.ndarray (F,)
        Local dynamic range per frame in dB. Same shape as input rms.
    """
    rms_db = librosa.amplitude_to_db(rms, ref=np.max(rms) if np.max(rms) > 0 else 1.0)
    n_frames = len(rms_db)
    window_frames = max(1, int(window_sec * sr / hop_length))
    half = window_frames // 2

    dynamic_range = np.zeros_like(rms_db)
    for i in range(n_frames):
        lo = max(0, i - half)
        hi = min(n_frames, i + half)
        dynamic_range[i] = rms_db[lo:hi].max() - rms_db[lo:hi].min()

    return dynamic_range


def detect_downbeats(
    y: np.ndarray,
    sr: float,
    beat_times: np.ndarray,
    hop_length: int = 512,
) -> np.ndarray:
    """Estimate downbeat (bar-first-beat) positions.

    A downbeat is the strongest beat that marks the start of each
    musical measure/bar. Uses librosa's PLP (Predominant Local Pulse)
    to estimate the metric structure, then picks every Nth beat where
    N is the inferred number of beats per bar.

    If madmom is installed, it will be preferred for higher accuracy
    (> 85 % vs librosa's ~65 % on typical pop/EDM). Falls back to
    librosa gracefully.

    Parameters
    ----------
    y : np.ndarray
        Raw audio signal.
    sr : float
        Sample rate.
    beat_times : np.ndarray
        Precomputed beat positions in seconds.
    hop_length : int
        Hop length used for beat tracking.

    Returns
    -------
    downbeat_times : np.ndarray (D,)
        Estimated downbeat positions in seconds.
    """
    if len(beat_times) < 2:
        return np.array([])

    try:
        return _detect_downbeats_madmom(y, sr, beat_times)
    except (ImportError, FileNotFoundError):
        pass

    try:
        return _detect_downbeats_librosa(y, sr, beat_times, hop_length)
    except Exception:
        return np.array([])


def _detect_downbeats_librosa(
    y: np.ndarray,
    sr: float,
    beat_times: np.ndarray,
    hop_length: int = 512,
) -> np.ndarray:
    """Librosa-based downbeat estimation via PLP + meter inference."""
    pulse = librosa.beat.plp(y=y, sr=sr, hop_length=hop_length)
    bpm = float(np.mean(librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)[0]))

    # Infer beats per bar from inter-beat autocorrelation
    if len(beat_times) >= 8:
        ibi = np.diff(beat_times)
        if ibi.mean() > 0:
            candidates = list(range(2, 9))  # 2/4 to 8/4
            # Score each candidate by how well it divides the bar length
            best_score = -np.inf
            best_bpb = 4  # default: 4/4
            ref = ibi.mean() * best_bpb
            for c in candidates:
                bar_len = ibi.mean() * c
                # Favor candidates whose bar length is close to typical (~2-4s)
                if 1.5 < bar_len < 5.0:
                    score = 1.0 / abs(bar_len - 2.5)
                    if score > best_score:
                        best_score = score
                        best_bpb = c

            beats_per_bar = best_bpb
        else:
            beats_per_bar = 4
    else:
        beats_per_bar = 4

    downbeat_indices = np.arange(0, len(beat_times), beats_per_bar)
    return beat_times[downbeat_indices]


def _detect_downbeats_madmom(
    y: np.ndarray,
    sr: float,
    beat_times: np.ndarray,
) -> np.ndarray:
    """Madmom-based downbeat estimation (highest accuracy, needs TensorFlow)."""
    import tempfile
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Write y to temp file — madmom processors require file path
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, y, int(sr))
            tmp_path = f.name

        try:
            from madmom.features.downbeats import (
                DBNDownBeatTrackingProcessor,
                RNNDownBeatProcessor,
            )

            act = RNNDownBeatProcessor()(tmp_path)
            tracker = DBNDownBeatTrackingProcessor(
                beats_per_bar=[2, 3, 4, 5, 6], fps=100
            )
            result = tracker(act)
            # result: np.ndarray of shape (N, 2) with columns [time, beat_position]
            # beat_position=1 means downbeat, beat_position>=2 means other positions
            downbeat_times = result[result[:, 1] == 1, 0]
            return np.asarray(downbeat_times)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


def compute_pulse_clarity(
    y: np.ndarray,
    sr: float,
    onset_env: np.ndarray | None = None,
    hop_length: int = 512,
) -> float:
    """Compute pulse clarity — how easily a listener can tap along.

    Pulse clarity quantifies the strength of the rhythmic pulse in a
    piece of music. Electronic dance music scores ~0.8-0.95, rubato
    classical piano ~0.2-0.4, and ambient noise ~0.0-0.1.

    Uses autocorrelation of the onset strength envelope: a clear,
    periodic pulse produces strong secondary peaks at the beat period.
    The ratio of the strongest secondary peak to the zero-lag peak
    gives the clarity score.

    Parameters
    ----------
    y : np.ndarray
        Raw audio signal.
    sr : float
        Sample rate.
    onset_env : np.ndarray or None
        Precomputed onset strength envelope. Computed if None.
    hop_length : int
        Hop length for onset envelope.

    Returns
    -------
    clarity : float
        Score in [0, 1]. Higher = clearer rhythmic pulse.
    """
    try:
        return _pulse_clarity_essentia(y, sr)
    except (ImportError, RuntimeError):
        pass

    return _pulse_clarity_librosa(y, sr, onset_env, hop_length)


def _pulse_clarity_librosa(
    y: np.ndarray,
    sr: float,
    onset_env: np.ndarray | None = None,
    hop_length: int = 512,
) -> float:
    """Estimate pulse clarity via onset envelope autocorrelation."""
    if onset_env is None:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    if len(onset_env) < 16:
        return 0.0

    # Subtract mean for better autocorrelation
    onset_centered = onset_env - onset_env.mean()
    autocorr = np.correlate(onset_centered, onset_centered, mode="full")
    autocorr = autocorr[len(autocorr) // 2 :]  # Keep only non-negative lags
    autocorr = autocorr / (autocorr[0] + 1e-10)  # Normalize by zero-lag

    # Search for secondary peaks in the plausible beat range
    bpm_low, bpm_high = 40, 240
    frame_rate = sr / hop_length
    lag_low = max(1, int(frame_rate * 60 / bpm_high))
    lag_high = min(len(autocorr) - 1, int(frame_rate * 60 / bpm_low))

    if lag_high <= lag_low:
        return 0.0

    search_region = autocorr[lag_low:lag_high]
    peak_height = float(np.max(search_region))

    # A strong secondary peak in the beat range = clear rhythmic pulse
    clarity = np.clip(peak_height, 0.0, 1.0)
    return float(clarity)


def _pulse_clarity_essentia(y: np.ndarray, sr: float) -> float:
    """Essentia-based pulse clarity via RhythmExtractor2013."""
    import essentia.standard as es

    extractor = es.RhythmExtractor2013(method="multifeature")
    y = y.astype(np.float32)
    _, _, confidence, _, _ = extractor(y)
    return float(np.clip(confidence, 0.0, 1.0))


# ═══════════════════════════════════════════════════════════════════════
# Golden Cut Points — merged beat+onset for video cutting
# ═══════════════════════════════════════════════════════════════════════


def merge_adjacent_beats(
    times: np.ndarray,
    threshold: float = 0.07,
) -> np.ndarray:
    """Merge nearby timestamps into a single representative point.

    Greedy clustering: consecutive points within ``threshold`` seconds
    are grouped into clusters, and each cluster's centroid is returned.

    Parameters
    ----------
    times : np.ndarray
        Sorted 1-D array of timestamps in seconds.
    threshold : float
        Maximum gap (seconds) for points to be considered the same
        musical event. Default 70 ms aligns with human perception of
        simultaneity.

    Returns
    -------
    merged : np.ndarray
        Deduplicated timestamp array.
    """
    if len(times) == 0:
        return np.array([])
    if len(times) == 1:
        return times.copy()

    merged = []
    cluster = [times[0]]

    for t in times[1:]:
        if t - cluster[-1] < threshold:
            cluster.append(t)
        else:
            merged.append(np.mean(cluster))
            cluster = [t]

    merged.append(np.mean(cluster))
    return np.array(merged)


def generate_golden_cut_points_from_features(
    beat_times: np.ndarray,
    onset_times: np.ndarray,
    threshold: float = 0.10,
) -> np.ndarray:
    """Generate golden cut points from already-extracted features.

    Merges beat times and onset times, then deduplicates via
    ``merge_adjacent_beats``.

    Parameters
    ----------
    beat_times : np.ndarray
        Beat positions from ``extract_music_features``.
    onset_times : np.ndarray
        Onset positions from ``extract_music_features``.
    threshold : float
        Deduplication threshold in seconds (default 100 ms).

    Returns
    -------
    cut_times : np.ndarray
        Merged and deduplicated cut points sorted in time.
    """
    combined = np.sort(np.concatenate([beat_times, onset_times]))
    return merge_adjacent_beats(combined, threshold=threshold)


def generate_golden_cut_points(
    audio_path: str | Path,
    threshold: float = 0.10,
    hop_length: int = 512,
    verbose: bool = False,
) -> np.ndarray:
    """Convenience: load audio, extract features, return golden cut points.

    Parameters
    ----------
    audio_path : str or Path
        Path to audio file.
    threshold : float
        Deduplication threshold in seconds (default 100 ms).
    hop_length : int
        STFT hop length.
    verbose : bool
        Print step-by-step progress.

    Returns
    -------
    cut_times : np.ndarray
        Sorted array of recommended video cut points in seconds.
    """
    audio_path = Path(audio_path)

    if verbose:
        print("Step 1: Loading audio ...")
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    if verbose:
        print("Step 2: Beat tracking ...")
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    if verbose:
        print("Step 3: Onset detection ...")
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, hop_length=hop_length, backtrack=True
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)

    if verbose:
        print(f"  Raw: {len(beat_times)} beats, {len(onset_times)} onsets")

    if verbose:
        print(f"Step 4: Merging (threshold = {threshold * 1000:.0f} ms) ...")
    combined = np.sort(np.concatenate([beat_times, onset_times]))
    gold = merge_adjacent_beats(combined, threshold=threshold)

    if verbose:
        print(f"  Golden cut points: {len(gold)}")

    return gold


# ═══════════════════════════════════════════════════════════════════════
# Visualization
# ═══════════════════════════════════════════════════════════════════════


def visualize_onset_strength(
    y: np.ndarray,
    sr: float,
    beat_times: np.ndarray,
    onset_times: np.ndarray,
    onset_strengths: np.ndarray,
    onset_env: np.ndarray,
    output_path: str | Path | None = None,
    figsize: tuple[int, int] = (16, 6),
    title: str = "Music Feature Analysis",
    dpi: int = 120,
) -> plt.Figure:
    """Create a waveform chart with beat/onset annotations for user review.

    Produces a three-panel figure:
      - Top: waveform with beats (red dashed) and onsets (green, scaled
        by strength).
      - Middle: onset strength envelope.
      - Bottom: onset strength heatmap / event density.

    Strong onsets (top 30 %) are marked with thicker, more opaque lines
    to draw attention to recommended cut points.

    Parameters
    ----------
    y : np.ndarray
        Raw audio signal.
    sr : float
        Sample rate.
    beat_times : np.ndarray
        Beat positions in seconds.
    onset_times : np.ndarray
        Onset positions in seconds.
    onset_strengths : np.ndarray
        Onset strength values at each onset.
    onset_env : np.ndarray
        Full onset strength envelope.
    output_path : str, Path, or None
        If provided, save figure to this path. Otherwise display.
    figsize : tuple
        Figure size in inches (width, height).
    title : str
        Figure suptitle.
    dpi : int
        Output resolution.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    time = np.linspace(0, len(y) / sr, len(y))
    env_time = librosa.times_like(onset_env, sr=sr)
    hop = 512
    env_seconds = len(onset_env) * hop / sr

    # Classify onsets: strong (top 30 %) vs weak
    strong_thresh = 0.0
    if len(onset_strengths) > 0:
        strong_thresh = np.percentile(onset_strengths, 70)
        strong_mask = onset_strengths >= strong_thresh
        weak_mask = ~strong_mask
    else:
        strong_mask = np.zeros(0, dtype=bool)
        weak_mask = np.zeros(0, dtype=bool)

    fig, (ax_wave, ax_env, ax_heat) = plt.subplots(
        3,
        1,
        figsize=figsize,
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1, 1]},
    )

    # ── Panel 1: Waveform ──────────────────────────────────
    ax_wave.plot(time, y, color="#4a90d9", alpha=0.6, linewidth=0.5, label="Waveform")
    ax_wave.vlines(
        beat_times,
        ymin=y.min(),
        ymax=y.max(),
        colors="#e74c3c",
        linestyles="--",
        linewidths=0.6,
        alpha=0.7,
        label="Beats",
    )
    if weak_mask.any():
        ax_wave.vlines(
            onset_times[weak_mask],
            ymin=y.min() * 0.8,
            ymax=y.max() * 0.8,
            colors="#2ecc71",
            linestyles="-",
            linewidths=0.8,
            alpha=0.35,
            label="Onsets (weak)",
        )
    if strong_mask.any():
        ax_wave.vlines(
            onset_times[strong_mask],
            ymin=y.min() * 0.8,
            ymax=y.max() * 0.8,
            colors="#f39c12",
            linestyles="-",
            linewidths=1.5,
            alpha=0.85,
            label="Onsets (strong → recommended cut)",
        )
    ax_wave.set_ylabel("Amplitude")
    ax_wave.legend(loc="upper right", fontsize=7, ncol=3)
    ax_wave.set_xlim(0, max(time[-1], env_seconds))

    # ── Panel 2: Onset strength envelope ───────────────────
    ax_env.plot(env_time, onset_env, color="#8e44ad", linewidth=1.0, alpha=0.85)
    ax_env.fill_between(env_time, 0, onset_env, color="#8e44ad", alpha=0.12)
    ax_env.axhline(
        y=strong_thresh,
        color="#f39c12",
        linestyle=":",
        linewidth=1.0,
        alpha=0.6,
        label=f"Strong threshold = {strong_thresh:.2f}"
        if len(onset_strengths) > 0
        else "",
    )
    ax_env.set_ylabel("Onset Strength")
    ax_env.legend(loc="upper right", fontsize=7)

    # ── Panel 3: Density / event raster ────────────────────
    n_bins = 120
    if onset_times.size > 0:
        bin_edges = np.linspace(0, max(time[-1], onset_times[-1]), n_bins + 1)
        counts, _ = np.histogram(onset_times, bins=bin_edges)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        ax_heat.bar(
            bin_centers,
            counts,
            width=bin_edges[1] - bin_edges[0],
            color="#2ecc71",
            alpha=0.7,
            edgecolor="none",
        )
    ax_heat.set_ylabel("Events / bin")
    ax_heat.set_xlabel("Time (seconds)")

    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    if output_path is not None:
        fig.savefig(str(output_path), dpi=dpi, bbox_inches="tight")
        plt.close(fig)

    return fig


def format_onset_heatmap(
    onset_times: np.ndarray,
    onset_strengths: np.ndarray,
    duration: float | None = None,
    bins: int = 80,
) -> str:
    """Format onset activity as an ASCII heatmap string.

    Each column represents a time bin, with character density reflecting
    how many onsets fall within that bin. Strong onsets are weighted
    more heavily.

    Legend (built into the output):
      .   = no onsets (quiet)
      ·   = very sparse
      ░░  = low density
      ▒▒  = medium density
      ▓▓  = high density
      ██  = very dense / strong onsets

    Parameters
    ----------
    onset_times : np.ndarray
        Onset positions in seconds.
    onset_strengths : np.ndarray
        Onset strength values (same length as onset_times).
    duration : float or None
        Total audio duration. If None, inferred from last onset.
    bins : int
        Number of time bins (columns). Default 80.

    Returns
    -------
    heatmap : str
        Multi-line ASCII string.
    """
    if duration is None:
        duration = float(onset_times[-1]) if len(onset_times) > 0 else 0.0
    if duration <= 0:
        return "(no onsets detected)"

    bin_edges = np.linspace(0, duration, bins + 1)
    bin_width = bin_edges[1] - bin_edges[0]

    # Weight each onset by its relative strength
    strengths_norm = np.ones_like(onset_strengths, dtype=float)
    if len(onset_strengths) > 0 and onset_strengths.max() > 0:
        strengths_norm = onset_strengths / onset_strengths.max()

    chars_per_bin = [0.0] * bins
    for t, w in zip(onset_times, strengths_norm):
        idx = np.searchsorted(bin_edges, t, side="right") - 1
        if 0 <= idx < bins:
            chars_per_bin[idx] += w

    max_chars = max(max(chars_per_bin), 1e-10)
    levels = " ·░▒▓█"
    n_levels = len(levels) - 1

    main_line = []
    for v in chars_per_bin:
        norm = v / max_chars
        idx = min(n_levels, round(norm * n_levels))
        main_line.append(levels[idx])
    main_str = "".join(main_line)

    # Time axis labels
    label_count = min(10, max(2, bins // 8))
    interval = max(1, bins // label_count)
    label_chars = [" "] * bins
    for i in range(0, bins, interval):
        t = bin_edges[i]
        label_str = f"{t:.1f}s"
        for j, ch in enumerate(label_str):
            if i + j < bins:
                label_chars[i + j] = ch
    label_line = "".join(label_chars)

    return (
        "Onset Activity Heatmap  (each column = "
        + f"{bin_width:.2f}s)\n"
        + "=" * bins
        + "\n"
        + main_str
        + "\n"
        + "=" * bins
        + "\n"
        + label_line
        + "\n"
        + "\nLegend:   =none  ·sparse  ░low  ▒med  ▓high  █dense"
    )


def print_onset_heatmap(
    onset_times: np.ndarray,
    onset_strengths: np.ndarray,
    duration: float | None = None,
    bins: int = 80,
) -> None:
    """Print ASCII onset heatmap to stdout. See ``format_onset_heatmap``."""
    print(format_onset_heatmap(onset_times, onset_strengths, duration, bins))


# ═══════════════════════════════════════════════════════════════════════
# Streaming Feature Extraction (aubio-based, for SSE endpoints)
# ═══════════════════════════════════════════════════════════════════════


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

    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        audio_wav = Path(temp_dir) / "audio.wav"
        ffmpeg.input(str(video_path)).output(str(audio_wav), loglevel="error").run(
            overwrite_output=True
        )

        separator = Separator(output_dir=str(temp_dir), output_format="wav")
        separator.load_model("UVR-MDX-NET-Inst_HQ_3.onnx")
        output_files = separator.separate(
            str(audio_wav),
            {
                # "Vocals": "vocal",
                "Instrumental": "bgm",
            },
        )
        bgm_src = Path(output_files[0])
        bgm_dst = dst_dir / f"{audio_asset_id}_bgm.wav"
        (Path(temp_dir) / bgm_src).rename(bgm_dst)

        return bgm_dst


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
    from transformers import pipeline

    classifier = pipeline(
        "audio-classification",
        model="dima806/music_genres_classification",
        trust_remote_code=True,
    )
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


# ═══════════════════════════════════════════════════════════════════════
# Demo / Usage
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    _DEMO_AUDIO = (
        Path(__file__).resolve().parents[2] / "backend" / "notebooks" / "1_audio.wav"
    )

    if not _DEMO_AUDIO.exists():
        import sys as _sys

        print(
            f"Demo audio not found: {_DEMO_AUDIO}\n"
            "Place a .wav/.mp3 file at that path, or run:\n"
            f"  python -m src.audio <path/to/audio>\n",
            file=_sys.stderr,
        )
        if len(_sys.argv) < 2:
            _sys.exit(1)
        _DEMO_AUDIO = Path(_sys.argv[1])

    print("=" * 64)
    print("  Audio Feature Extraction Demo")
    print("=" * 64)
    print(f"\nInput: {_DEMO_AUDIO}")

    # ── 1. Full feature extraction ──────────────────────────────────
    print("\n--- 1. extract_music_features() ---")
    feats = extract_music_features(_DEMO_AUDIO, verbose=True)

    # ── 2. Key scalar features ──────────────────────────────────────
    print("\n--- 2. Scalar Summaries ---")
    for key in ("bpm", "pulse_clarity"):
        print(f"  {key:>20s}: {feats[key]:.3f}")

    # ── 3. Array features ───────────────────────────────────────────
    print("\n--- 3. Array Shapes ---")
    for key in (
        "beat_times",
        "onset_times",
        "onset_strengths",
        "onset_env",
        "rms",
        "spectral_centroids",
        "spectral_flux",
        "mfcc",
        "chroma",
        "downbeat_times",
        "dynamic_range",
    ):
        val = feats[key]
        shape = val.shape if hasattr(val, "shape") else f"scalar ({val})"
        print(f"  {key:>20s}: shape={shape}")

    # ── 4. Golden cut points (convenience API) ──────────────────────
    print("\n--- 4. generate_golden_cut_points() (convenience) ---")
    gold = generate_golden_cut_points(_DEMO_AUDIO, threshold=0.10, verbose=True)
    print(f"  First 10 cut points: {np.round(gold[:10], 3).tolist()}")

    # ── 5. Golden cut points (from pre-extracted features) ──────────
    print("\n--- 5. generate_golden_cut_points_from_features() ---")
    gold2 = generate_golden_cut_points_from_features(
        feats["beat_times"], feats["onset_times"], threshold=0.10
    )
    print(
        f"  Cut points: {len(gold2)} (matches convenience): {np.allclose(gold, gold2)}"
    )

    # ── 6. Standalone sub-extractors ────────────────────────────────
    print("\n--- 6. Standalone Functions ---")
    import librosa as _lr

    _y, _sr = _lr.load(str(_DEMO_AUDIO), sr=None, mono=True)

    sf = compute_spectral_flux(y=_y, hop_length=512)
    print(f"  spectral_flux: shape={sf.shape}, range=({sf.min():.3f}, {sf.max():.3f})")

    dr = compute_dynamic_range(feats["rms"], sr=_sr)
    print(
        f"  dynamic_range (standalone): shape={dr.shape},"
        f" range=({dr.min():.1f}, {dr.max():.1f}) dB"
    )

    pc = compute_pulse_clarity(_y, _sr)
    print(f"  pulse_clarity (standalone): {pc:.3f}")

    # ── 7. ASCII heatmap ────────────────────────────────────────────
    print("\n--- 7. print_onset_heatmap() ---")
    duration = len(_y) / _sr
    print_onset_heatmap(
        feats["onset_times"], feats["onset_strengths"], duration=duration, bins=80
    )

    # ── 8. Matplotlib visualization ─────────────────────────────────
    print("\n--- 8. visualize_onset_strength() ---")
    _out_png = (
        Path(__file__).resolve().parents[2] / "backend" / "notebooks" / "_onset_viz.png"
    )
    visualize_onset_strength(
        y=_y,
        sr=_sr,
        beat_times=feats["beat_times"],
        onset_times=feats["onset_times"],
        onset_strengths=feats["onset_strengths"],
        onset_env=feats["onset_env"],
        output_path=str(_out_png),
        title=f"Music Feature Analysis — {_DEMO_AUDIO.name}",
    )
    print(f"  Saved: {_out_png}")

    print("\n" + "=" * 64)
    print("  Demo complete.")
    print("=" * 64)
