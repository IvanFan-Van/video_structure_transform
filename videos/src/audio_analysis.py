"""
BGM 音频特征提取 — 用 librosa 分析音轨的节奏、能量分布

    提取 BPM、beat 时间点、onset 瞬态点、分段 RMS energy，
    并格式化为 LLM prompt 可用的文本描述。

用法:
    from audio_analysis import analyze_bgm, format_bgm_features
    features = analyze_bgm("audio.wav")
    text = format_bgm_features(features)
"""

from __future__ import annotations

import numpy as np


def analyze_bgm(audio_path: str, segment_seconds: float = 2.0) -> dict:
    """提取 BGM 音频特征。

    Returns:
        {
            "bpm": 128.0,
            "beat_times": [0.47, 0.94, 1.41, ...],
            "onset_times": [0.23, 0.47, 1.18, ...],
            "energy_segments": [
                {"start": 0.0, "end": 2.0, "level": "low", "rms": 0.03},
                ...
            ],
            "duration": 20.0,
        }
    """
    import librosa

    y, sr = librosa.load(audio_path, sr=None)
    duration = len(y) / sr

    # ── tempo + beats ──────────────────────────────────────────────
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # ── onsets (瞬态事件，如鼓点、音效) ──────────────────────────
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="frames")
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # ── 分段 RMS energy ───────────────────────────────────────────
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    energy_segments = _segment_energy(rms_times, rms, duration, segment_seconds)

    return {
        "bpm": float(tempo),
        "beat_times": beat_times.tolist(),
        "onset_times": onset_times.tolist(),
        "energy_segments": energy_segments,
        "duration": duration,
    }


def _segment_energy(
    times: np.ndarray,
    rms: np.ndarray,
    total_duration: float,
    segment_seconds: float = 2.0,
) -> list[dict]:
    """将 RMS energy 按时间切片，归类为 low / medium / high。"""
    if len(times) == 0 or total_duration <= 0:
        return []

    # 全局 RMS 百分位阈值
    p33, p66 = np.percentile(rms, [33, 66])

    segments = []
    t = 0.0
    while t < total_duration:
        end = min(t + segment_seconds, total_duration)
        mask = (times >= t) & (times < end)
        if mask.any():
            mean_rms = float(np.mean(rms[mask]))
            if mean_rms > p66:
                level = "high"
            elif mean_rms > p33:
                level = "medium"
            else:
                level = "low"
        else:
            mean_rms = 0.0
            level = "low"

        segments.append({
            "start": round(t, 1),
            "end": round(end, 1),
            "level": level,
            "rms": round(mean_rms, 4),
        })
        t = end

    return segments


def _describe_energy_level(level: str) -> str:
    return {"low": "低（安静/前奏）", "medium": "中（平稳/铺垫）", "high": "高（高潮/强节奏）"}.get(level, level)


def format_bgm_features(f: dict, fps: float | None = None) -> str:
    """将特征 dict → LLM 可读的 prompt 文本片段。"""

    bpm = f.get("bpm", 0)
    duration = f.get("duration", 0)
    beat_times = f.get("beat_times", [])
    onset_times = f.get("onset_times", [])
    energy_segments = f.get("energy_segments", [])

    beat_interval = 60.0 / bpm if bpm > 0 else 0

    lines = [
        "【BGM 音频特征 — 可用于卡点同步特效】",
        "",
        f"- 整体 BPM: {bpm:.0f}（{'快节奏' if bpm > 120 else '中节奏' if bpm > 80 else '慢节奏'}，每拍约 {beat_interval:.2f}s）",
        f"- 音频总时长: {duration:.1f}s",
        "",
        "- 能量分段:",
    ]

    for seg in energy_segments:
        lines.append(
            f"  {seg['start']:5.1f}s → {seg['end']:5.1f}s : {seg['level']:6s}  "
            f"({_describe_energy_level(seg['level'])})"
        )

    lines.append("")
    lines.append("- Beat 时间点（重拍，适合触发转场/高亮/弹出）:")

    # 只列出前 20 个和后 5 个 beat，避免 prompt 过长
    max_show = 20
    if len(beat_times) > max_show + 5:
        shown = beat_times[:max_show]
        tail = beat_times[-5:]
        beat_str = ", ".join(f"{t:.2f}" for t in shown)
        beat_str += f", ... (共 {len(beat_times)} 个 beat), "
        beat_str += ", ".join(f"{t:.2f}" for t in tail)
    else:
        beat_str = ", ".join(f"{t:.2f}" for t in beat_times)

    lines.append(f"  [{beat_str}]")

    if onset_times and len(onset_times) > 0:
        lines.append("")
        lines.append("- Onset 时间点（瞬态/鼓点/音效，适合弹出动画）:")
        onset_str = ", ".join(f"{t:.2f}" for t in onset_times[:15])
        if len(onset_times) > 15:
            onset_str += f", ... (共 {len(onset_times)} 个)"
        lines.append(f"  [{onset_str}]")

    # 如果提供了 fps，给出帧号参考
    if fps:
        lines.append("")
        lines.append(f"- 帧率参考: {fps}fps")
        lines.append("  前 10 个 beat 对应的帧号:")
        for i, bt in enumerate(beat_times[:10]):
            frame = int(bt * fps)
            lines.append(f"    beat {i+1:2d}: {bt:.2f}s → frame {frame}")

    return "\n".join(lines)
