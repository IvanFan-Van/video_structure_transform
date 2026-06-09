"""本地预处理管线 — Phase 0 全部纯本地操作

本模块是分析管线的第一阶段，所有操作都在本地完成，不涉及任何LLM调用。

处理流程 (6步):
  1. 视频元数据提取 — ffprobe获取时长、分辨率、帧率、编码信息
  2. 音频提取+人声分离 — ffmpeg提取WAV → UVR-MDX-NET分离vocals/BGM
  3. ASR语音转写 — faster-whisper(small)对vocals进行词级时间戳转写
  4. 镜头切分检测 — OpenCV直方图差异法检测镜头切换点
  5. 关键帧抽取 — 在每个镜头中点 + 首帧末帧抽取JPEG
  6. BGM分析 — librosa检测BPM、节拍时间点、能量曲线、情绪推断

产出: PreprocessResult 数据对象，包含后续Phase 1/2/3所需的所有本地数据。

核心数据类:
  PreprocessResult — 数据容器，26个字段覆盖视频/音频/ASR/镜头/BGM全部预处理结果
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import librosa
import numpy as np

from analysis.video_utils import (
    extract_audio,
    extract_frame_at_time,
    frame_to_base64,
    get_video_metadata,
)
from analysis.audio_separator import separate_vocals_and_bgm


@dataclass
class PreprocessResult:
    """预处理结果容器 — 汇总Phase 0所有本地分析数据

    该对象在分析管线中全局传递，被Phase 1/2/3/4所有阶段引用。
    包含4大类数据: 视频元数据、ASR语音转写、镜头分析、BGM分析。
    """

    # ── 视频基础信息 ──
    filename: str = ""  # 视频文件名（如 "1.mp4"）
    duration: float = 0  # 总时长(秒)
    resolution: str = "unknown"  # 分辨率如 "1080x1920"
    fps: float = 0  # 帧率
    codec: str = "unknown"  # 视频编码如 "h264"
    has_audio: bool = False  # 是否有音轨

    # ── ASR 语音转写 ──
    asr_segments: list[dict] = field(
        default_factory=list
    )  # faster-whisper输出的片段列表
    asr_full_text: str = ""  # 全部转写文本（空格分隔）
    language: str = "zh"  # 语种

    # ── 镜头检测 ──
    shot_count: int = 0  # 镜头总数
    shot_boundaries: list[float] = field(default_factory=list)  # 镜头边界时间点(秒)
    avg_shot_duration: float = 0  # 平均镜头时长(秒)

    # ── 关键帧 ──
    keyframe_times: list[float] = field(default_factory=list)  # 关键帧时间点(秒)
    keyframe_paths: list[str] = field(default_factory=list)  # 关键帧文件路径
    keyframe_base64_list: list[str] = field(default_factory=list)  # 关键帧base64编码

    # ── BGM 分析 ──
    bpm: float = 0  # 每分钟节拍数
    beat_timings: list[float] = field(default_factory=list)  # 重拍时间点列表(秒)
    energy_curve: list[float] = field(default_factory=list)  # 能量曲线(RMS值)
    bgm_mood_hint: str = ""  # BGM情绪推断: energetic/uplifting/moderate/calm/none

    # ── 人声分离 ──
    vocals_path: str = ""  # 分离出的人声WAV路径
    bgm_path: str = ""  # 分离出的伴奏WAV路径
    original_audio_path: str = ""  # 原始音频WAV路径
    has_vocals: bool = False  # 是否真的分离出了人声（vs 纯BGM视频）

    # ── 卡点同步 ──
    beat_sync_ratio: float = 0  # 卡点匹配率(0-1)
    beat_sync_matched_count: int = 0  # 匹配的切点数
    beat_sync_total_cuts: int = 0  # 总切点数
    beat_sync_typical_offset: float = 0  # 典型偏移量(秒)

    # ── 派生统计 ──
    subtitle_density: float = 0  # 字幕密度(条/分钟)


def run_asr(audio_path: str, has_audio: bool = True) -> tuple[list[dict], str, str]:
    """运行 ASR 语音转写（faster-whisper）

    使用 faster-whisper-small 模型对 vocals 轨道进行词级时间戳转写。
    这个模型是 Whisper 的 CTranslate2 实现，比原始 openai-whisper 快约4倍。

    Args:
        audio_path: 音频WAV文件路径（应是分离后的人声轨道）
        has_audio:  如果为False则跳过ASR

    Returns:
        (segments, full_text, language) 三元组
        - segments: 片段列表，每个包含 start/end/text/words(词级时间戳)
        - full_text: 完整转写文本
        - language: 语种代码如 "zh"/"en"
    """
    if not has_audio:
        print("  [ASR] 视频无音轨, 跳过语音转写")
        return [], "", "zh"

    if not audio_path or not Path(audio_path).exists():
        print("  [ASR] 音频文件不存在, 跳过语音转写")
        return [], "", "zh"

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  [ASR] faster-whisper 未安装, 使用 openai-whisper 替代...")
        return _run_whisper_openai_file(audio_path)

    print(f"  [ASR] 加载模型 faster-whisper-small, 转写: {Path(audio_path).name}...")

    # 创建 WhisperModel 实例
    # model_size="small": 244M参数，平衡速度和准确率
    # device="cpu": 本地CPU推理（不需要GPU）
    # compute_type="int8": 8位整数量化（减少内存占用）
    model = WhisperModel("small", device="cpu", compute_type="int8")

    # 调用转录
    # beam_size=5: beam search宽度，越大准确率越高但越慢
    # word_timestamps=True: 开启词级时间戳
    segments_result, info = model.transcribe(
        audio_path, beam_size=5, word_timestamps=True
    )

    language = info.language  # 检测到的语种
    segments = []  # 片段列表
    full_text_parts = []  # 用于拼接完整文本

    for seg in segments_result:
        # 提取词级时间戳
        words_data = []
        if seg.words:
            for w in seg.words:
                words_data.append(
                    {
                        "start": round(w.start, 2),  # 词开始时间(秒)
                        "end": round(w.end, 2),  # 词结束时间(秒)
                        "word": w.word,  # 词文本
                    }
                )

        segments.append(
            {
                "start": round(seg.start, 2),  # 片段开始时间
                "end": round(seg.end, 2),  # 片段结束时间
                "text": seg.text.strip(),  # 片段文本
                "words": words_data if words_data else None,  # 词级时间戳
            }
        )
        full_text_parts.append(seg.text.strip())

    full_text = " ".join(full_text_parts)

    print(f"  [ASR] 完成: {len(segments)} 个片段, 语种: {language}")
    return segments, full_text, language


def _run_whisper_openai_file(audio_path: str) -> tuple[list[dict], str, str]:
    """回退方案：使用 openai-whisper 进行转写

    当 faster-whisper 不可用时（如安装失败），回退到原始 whisper。
    速度较慢但兼容性更好。
    """
    try:
        import whisper
    except ImportError:
        print("  [ASR] openai-whisper 也未安装, 跳过语音转写")
        return [], "", "zh"

    model = whisper.load_model("small")
    result = model.transcribe(audio_path, word_timestamps=True)

    segments = []
    for seg in result.get("segments", []):
        segments.append(
            {
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
                "words": None,  # openai-whisper的词级时间戳格式不同，暂不处理
            }
        )

    return segments, result.get("text", ""), result.get("language", "zh")


def detect_shots(
    video_path: str, duration: float, fps: float, threshold: float = 15.0
) -> list[float]:
    """使用直方图差异法检测镜头切换点

    算法原理:
      1. 每0.5秒采样一帧，计算HSV颜色直方图
      2. 比较相邻帧的直方图相似度（卡方距离）
      3. 差异超过阈值 → 标记为镜头切换点
      4. 最少间隔0.5秒（防止同一镜头内因运动误检测）

    Args:
        video_path: 视频文件路径
        duration:   视频时长(秒)
        fps:        帧率
        threshold:  卡方距离阈值(默认15.0)，值越小越敏感

    Returns:
        镜头边界时间点列表(秒)，如 [0.0, 2.5, 5.0, 10.0, 16.6]
    """
    print("  [Shot] 检测镜头切分...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("  [Shot] 无法打开视频, 使用默认均匀切分")
        return _fallback_shots(duration)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧数
    if total_frames <= 0:
        cap.release()
        return _fallback_shots(duration)

    sample_interval = max(1, int(fps * 0.5))  # 采样间隔 = 0.5秒
    boundaries = [0.0]  # 镜头边界列表（始终从0开始）
    prev_hist = None  # 上一帧的直方图

    frame_idx = 0  # 当前帧号
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_interval == 0:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # 计算H-S二维直方图（50×60 = 3000 bins）
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)  # 归一化到[0,1]

            if prev_hist is not None:
                # 卡方距离：数值越大差异越大
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR)
                if diff > threshold:
                    timestamp = frame_idx / fps
                    # 确保新切点距离上一个至少0.5秒
                    if timestamp > boundaries[-1] + 0.5:
                        boundaries.append(timestamp)

            prev_hist = hist

        frame_idx += 1

    cap.release()

    # 如果最后一个边界离视频结尾较远，追加终点
    if boundaries[-1] < duration - 0.5:
        boundaries.append(duration)

    print(f"  [Shot] 检测到 {len(boundaries) - 1} 个镜头切换点")
    return boundaries


def _fallback_shots(duration: float) -> list[float]:
    """回退方案：无法打开视频时，按每3秒均匀划分"""
    step = 3.0
    boundaries = [0.0]
    t = step
    while t < duration:
        boundaries.append(t)
        t += step
    boundaries.append(duration)
    return boundaries


def extract_keyframes(
    video_path: str,
    shot_boundaries: list[float],
    output_dir: str | Path,
    max_keyframes: int = 20,
) -> tuple[list[float], list[str], list[str]]:
    """从每个镜头的中点 + 首尾帧抽取关键帧

    策略:
      - 每个shot区间取中点帧（最具代表性）
      - 强制包含首帧(t=0)和尾帧(t≈duration)
      - 总数超过max_keyframes时，均匀降采样（保留首尾）

    Args:
        video_path:      视频文件路径
        shot_boundaries: 镜头边界时间点列表
        output_dir:      关键帧输出目录
        max_keyframes:   最大关键帧数量(默认20)

    Returns:
        (keyframe_times, keyframe_paths, keyframe_base64_list) 三元组
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 确定关键帧时间点——每个镜头区间的中点
    keyframe_times = []
    for i in range(len(shot_boundaries) - 1):
        mid = (shot_boundaries[i] + shot_boundaries[i + 1]) / 2
        keyframe_times.append(round(mid, 2))

    # 强制包含首帧 (t=0)
    if keyframe_times and keyframe_times[0] > 0.1:
        keyframe_times.insert(0, 0.0)

    # 强制包含尾帧 (t≈duration-0.1，避免seek到文件末尾报错)
    last_boundary = shot_boundaries[-1] if shot_boundaries else duration
    actual_last = last_boundary - 0.1 if last_boundary > 0.1 else last_boundary
    if not keyframe_times or keyframe_times[-1] < actual_last - 0.5:
        keyframe_times.append(round(actual_last, 2))

    # 数量限制：均匀降采样
    if len(keyframe_times) > max_keyframes:
        if len(keyframe_times) > 2:
            first, last = keyframe_times[0], keyframe_times[-1]
            middle = keyframe_times[1:-1]  # 去掉首尾的中间部分
            step = max(1, len(middle) / (max_keyframes - 2))
            keyframe_times = (
                [first]
                + [middle[int(i * step)] for i in range(max_keyframes - 2)]
                + [last]
            )
        else:
            keyframe_times = keyframe_times[:max_keyframes]

    print(f"  [Keyframe] 抽取 {len(keyframe_times)} 个关键帧...")

    paths = []  # 关键帧文件路径列表
    base64_list = []  # 关键帧base64编码列表

    for i, t in enumerate(keyframe_times):
        filename = f"keyframe_{i + 1:03d}_{t:.1f}s.jpg"
        out_path = output_dir / filename

        success = extract_frame_at_time(video_path, t, str(out_path))
        if success:
            paths.append(str(out_path))
            b64 = frame_to_base64(out_path)  # 转为base64供LLM使用
            base64_list.append(b64)
        else:
            print(f"  [Keyframe] 警告: 无法提取 t={t:.1f}s 的帧")

    print(f"  [Keyframe] 成功抽取 {len(paths)}/{len(keyframe_times)} 帧")
    return keyframe_times, paths, base64_list


def analyze_bgm(audio_path: str, has_audio: bool = True) -> dict:
    """分析BGM特征：BPM、节拍时间点、能量曲线、情绪推断

    对分离后的伴奏轨道（无vocals）进行分析，因为人声会干扰BPM检测。

    Args:
        audio_path: 音频WAV文件路径（应是分离后的伴奏轨道）
        has_audio:  如果为False则跳过分析

    Returns:
        {"bpm": float, "beat_timings": list[float], "energy_curve": list[float], "bgm_mood_hint": str}
    """
    result = {
        "bpm": 0,
        "beat_timings": [],  # 重拍/强拍时间点(秒)
        "energy_curve": [],  # RMS能量曲线
        "bgm_mood_hint": "",  # 情绪推断: energetic/uplifting/moderate/calm/none
    }

    if not has_audio:
        print("  [BGM] 视频无音轨, 跳过BGM分析")
        return result

    if not audio_path or not Path(audio_path).exists():
        print("  [BGM] 音频文件不存在, 跳过BGM分析")
        return result

    print(f"  [BGM] 分析音频特征: {Path(audio_path).name}...")

    try:
        # 加载音频为单声道（BGM分析不需要立体声）
        y, sr = librosa.load(audio_path, sr=None)  # y: 波形数据, sr: 原始采样率

        # ── BPM 检测 ──
        # librosa.beat.beat_track 返回 (tempo, beat_frames)
        # tempo 是动态BPM估计值
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if hasattr(tempo, "__iter__") else float(tempo)
        result["bpm"] = round(bpm, 1)

        # ── 节拍时间点 ──
        # beat_frames 是节拍对应的帧索引，转为秒
        _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        result["beat_timings"] = [round(float(t), 2) for t in beat_times]

        # ── 能量曲线(RMS) ──
        # RMS = Root Mean Square，衡量信号的幅值/响度
        rms = librosa.feature.rms(y=y)[0]
        result["energy_curve"] = [round(float(e), 4) for e in rms]

        # ── 情绪推断 ──
        # 简单规则：BPM + 平均能量 → 情绪标签
        avg_energy = float(np.mean(rms))  # 平均能量
        if bpm > 120 and avg_energy > 0.1:
            result["bgm_mood_hint"] = "energetic"  # 高BPM + 高能量 → 充满活力
        elif bpm > 100:
            result["bgm_mood_hint"] = "uplifting"  # 中高BPM → 振奋
        elif bpm > 70:
            result["bgm_mood_hint"] = "moderate"  # 中等BPM → 平和
        elif bpm > 0:
            result["bgm_mood_hint"] = "calm"  # 低BPM → 舒缓
        else:
            result["bgm_mood_hint"] = "none"  # 无节拍 → 纯音效/静音

        print(
            f"  [BGM] BPM={bpm:.0f}, 重拍数={len(beat_times)}, 情绪={result['bgm_mood_hint']}"
        )

    except Exception as e:
        print(f"  [BGM] 分析失败: {e}")

    return result


# ═══════════════════════════════════════════════════════════════════
# 卡点同步率计算 — 衡量视频切点与BGM重拍的对齐程度
# ═══════════════════════════════════════════════════════════════════


def compute_beat_sync_ratio(
    cut_timestamps: list[float],
    beat_timings: list[float],
    sync_threshold: float = 0.05,
) -> dict:
    """计算视频切点与BGM重拍的匹配率

    判断标准: 切点与最近重拍的时间差 < sync_threshold(50ms) → 算"卡点"。
    这是判断视频是否"踩着BGM节奏剪辑"的核心指标。

    Args:
        cut_timestamps: 镜头切点时间列表(秒)
        beat_timings:   BGM重拍时间列表(秒)
        sync_threshold: 匹配阈值(秒)，默认50ms

    Returns:
        {"ratio": 匹配率(0-1), "matched_count": 匹配切点数,
         "total_cuts": 总切点数, "typical_offset": 平均偏移(秒)}
    """
    if not cut_timestamps or not beat_timings:
        return {
            "ratio": 0,
            "matched_count": 0,
            "total_cuts": len(cut_timestamps),
            "typical_offset": 0,
        }

    cuts = sorted(set(cut_timestamps))  # 去重排序的切点列表
    beats = sorted(set(beat_timings))  # 去重排序的重拍列表

    matched = 0  # 匹配的切点数
    offsets = []  # 所有切点的偏移量（用于计算典型偏移）

    for cut in cuts:
        # 找到距离这个切点最近的重拍
        nearest_beat = min(beats, key=lambda b: abs(cut - b))
        offset = abs(cut - nearest_beat)
        offsets.append(offset)
        if offset <= sync_threshold:
            matched += 1

    ratio = matched / len(cuts) if cuts else 0
    typical_offset = float(np.mean(offsets)) if offsets else 0

    print(
        f"  [Sync] 卡点匹配率: {ratio:.1%} ({matched}/{len(cuts)}切点, "
        f"阈值{sync_threshold * 1000:.0f}ms, 平均偏移{typical_offset * 1000:.0f}ms)"
    )

    return {
        "ratio": round(ratio, 3),
        "matched_count": matched,
        "total_cuts": len(cuts),
        "typical_offset": round(typical_offset, 3),
    }


# ═══════════════════════════════════════════════════════════════════
# 逐beat密集关键帧抽取 — 供Phase 2使用
# ═══════════════════════════════════════════════════════════════════


def extract_beat_keyframes(
    video_path: str,
    start_s: float,
    end_s: float,
    output_dir: str | Path,
    num_keyframes: int = 8,
) -> tuple[list[str], list[str]]:
    """在单个beat的时间范围内均匀抽取密集关键帧

    与全局关键帧抽取不同，每个beat独立抽取8帧，让LLM能看到
    该beat内的细微变化（文字出现过程、特效动画、人物表情变化）。

    Args:
        video_path:    源视频路径
        start_s:       beat开始时间(秒)
        end_s:         beat结束时间(秒)
        output_dir:    输出目录
        num_keyframes: 抽取帧数(默认8)

    Returns:
        (file_paths, base64_list) 二元组
    """
    output_dir = Path(output_dir) / "beat_keyframes"
    output_dir.mkdir(parents=True, exist_ok=True)

    duration = end_s - start_s
    if duration <= 0 or num_keyframes <= 0:
        return [], []

    # 均匀采样时间点
    times = []
    if num_keyframes == 1:
        times = [start_s + duration / 2]
    else:
        times = [
            start_s + i * duration / (num_keyframes - 1) for i in range(num_keyframes)
        ]
    times = [round(t, 2) for t in times]

    paths = []
    base64_list = []

    for i, t in enumerate(times):
        filename = f"beat_kf_{i + 1:03d}_{t:.1f}s.jpg"
        out_path = output_dir / filename

        success = extract_frame_at_time(video_path, t, str(out_path))
        if success:
            paths.append(str(out_path))
            b64 = frame_to_base64(out_path)
            base64_list.append(b64)

    return paths, base64_list


def compute_derived_stats(result: PreprocessResult) -> None:
    """从原始预处理数据计算派生统计量

    修改 result 对象的以下字段（in-place）:
      - shot_count: 镜头数
      - avg_shot_duration: 平均镜头时长
      - subtitle_density: 字幕密度(条/分钟)
    """
    if result.duration > 0:
        # 镜头统计
        result.shot_count = max(1, len(result.shot_boundaries) - 1)
        result.avg_shot_duration = (
            result.duration / result.shot_count
            if result.shot_count > 0
            else result.duration
        )

        # 字幕密度 — 每分钟多少条ASR片段
        if result.duration >= 60:
            result.subtitle_density = round(
                len(result.asr_segments) / (result.duration / 60), 1
            )
        elif result.duration > 0:
            result.subtitle_density = round(
                len(result.asr_segments) * (60 / result.duration), 1
            )


# ═══════════════════════════════════════════════════════════════════
# 主入口 — 完整预处理管线
# ═══════════════════════════════════════════════════════════════════


def preprocess(
    video_path: str, output_dir: str | Path, max_keyframes: int = 20
) -> PreprocessResult:
    """运行完整预处理管线（Phase 0）

    这是整个分析管线的入口，完成6个本地预处理步骤后，
    返回 PreprocessResult 对象，供 Phase 1/2/3/4 使用。

    Args:
        video_path:    输入视频的绝对路径
        output_dir:    输出目录（按时间戳命名的run_dir）
        max_keyframes: 最大关键帧数量

    Returns:
        PreprocessResult 对象，包含所有预处理数据
    """
    print("=" * 60)
    print("阶段0: 本地预处理")
    print("=" * 60)

    result = PreprocessResult()
    run_dir = Path(output_dir)

    # ── 步骤1: 视频元数据提取 ──
    print("\n[1/6] 提取视频元数据...")
    meta = get_video_metadata(video_path)
    result.filename = meta["filename"]
    result.duration = meta["duration"]
    result.resolution = meta["resolution"]
    result.fps = meta["fps"]
    result.codec = meta["codec"]
    result.has_audio = meta["has_audio"]
    print(f"  文件名: {result.filename}")
    print(
        f"  时长: {result.duration:.1f}s | 分辨率: {result.resolution} | 帧率: {result.fps}fps"
    )
    print(f"  编码: {result.codec} | 音轨: {'有' if result.has_audio else '无'}")

    # ── 步骤2: 音频提取 + 人声分离 ──
    vocals_path = ""
    bgm_path = ""
    original_audio_path = ""

    if result.has_audio:
        print("\n[2/6] 提取音频并分离人声/背景音乐...")
        audio_dir = run_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # 提取高质量音频（44.1kHz立体声——适合音乐质量）
        original_audio_path = str(audio_dir / "original.wav")
        print(f"  提取音频到: {original_audio_path}")
        extract_audio(video_path, original_audio_path, sample_rate=44100, channels=2)
        result.original_audio_path = original_audio_path

        # 分离人声和BGM
        sep_result = separate_vocals_and_bgm(original_audio_path, audio_dir)
        if sep_result["success"]:
            vocals_path = sep_result["vocals_path"]
            bgm_path = sep_result["bgm_path"]
            result.vocals_path = vocals_path
            result.bgm_path = bgm_path
            result.has_vocals = sep_result.get("has_vocals", True)
        else:
            print(f"  [分离] 失败, 使用原始音频: {sep_result['error']}")
            vocals_path = original_audio_path
            bgm_path = original_audio_path
            result.has_vocals = True  # 分离失败时保守假设有语音
    else:
        print("\n[2/6] 音轨处理: 视频无音轨, 跳过")

    # ── 步骤3: ASR语音转写 ──
    print("\n[3/6] 语音转写 (ASR)...")
    if result.has_vocals:
        segments, full_text, lang = run_asr(vocals_path, result.has_audio)
    else:
        print("  分离检测: 未发现人声, 跳过ASR转写 (纯BGM视频)")
        segments, full_text, lang = [], "", "zh"
    result.asr_segments = segments
    result.asr_full_text = full_text
    result.language = lang

    # ── 步骤4: 镜头切分检测 ──
    print("\n[4/6] 镜头切分检测...")
    result.shot_boundaries = detect_shots(video_path, result.duration, result.fps)

    # ── 步骤5: 关键帧抽取 ──
    print("\n[5/6] 关键帧抽取...")
    keyframe_dir = run_dir / "keyframes"
    times, paths, b64_list = extract_keyframes(
        video_path, result.shot_boundaries, keyframe_dir, max_keyframes
    )
    result.keyframe_times = times
    result.keyframe_paths = paths
    result.keyframe_base64_list = b64_list

    # ── 步骤6: BGM分析 ──
    print("\n[6/6] BGM分析...")
    bgm = analyze_bgm(bgm_path, result.has_audio)
    result.bpm = bgm["bpm"]
    result.beat_timings = bgm["beat_timings"]
    result.energy_curve = bgm["energy_curve"]
    result.bgm_mood_hint = bgm["bgm_mood_hint"]

    # ── 计算卡点同步率 ──
    if result.shot_boundaries and result.beat_timings:
        sync = compute_beat_sync_ratio(result.shot_boundaries, result.beat_timings)
        result.beat_sync_ratio = sync["ratio"]
        result.beat_sync_matched_count = sync["matched_count"]
        result.beat_sync_total_cuts = sync["total_cuts"]
        result.beat_sync_typical_offset = sync["typical_offset"]

    # ── 计算派生统计 ──
    compute_derived_stats(result)

    # ── 保存中间数据 ──
    _save_preprocess_result(result, run_dir)

    print(
        f"\n预处理完成: {result.shot_count}个镜头, {len(result.keyframe_base64_list)}个关键帧, "
        f"BPM={result.bpm:.0f}, ASR片段={len(result.asr_segments)}"
    )
    return result


def _save_preprocess_result(result: PreprocessResult, output_dir: str | Path) -> None:
    """保存预处理数据为JSON文件（供调试和追踪）"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    preprocess_data = {
        "filename": result.filename,
        "duration": result.duration,
        "resolution": result.resolution,
        "fps": result.fps,
        "has_audio": result.has_audio,
        "shot_count": result.shot_count,
        "shot_boundaries": result.shot_boundaries,
        "avg_shot_duration": result.avg_shot_duration,
        "keyframe_count": len(result.keyframe_paths),
        "keyframe_times": result.keyframe_times,
        "bpm": result.bpm,
        "beat_timings": result.beat_timings[:50]
        if len(result.beat_timings) > 50
        else result.beat_timings,
        "bgm_mood_hint": result.bgm_mood_hint,
        "language": result.language,
        "beat_sync": {
            "ratio": result.beat_sync_ratio,
            "matched_count": result.beat_sync_matched_count,
            "total_cuts": result.beat_sync_total_cuts,
            "typical_offset": result.beat_sync_typical_offset,
        },
        "audio_separation": {
            "original": result.original_audio_path,
            "vocals": result.vocals_path,
            "bgm": result.bgm_path,
        }
        if result.has_audio
        else None,
    }

    intermediates_dir = output_dir / "intermediates"
    intermediates_dir.mkdir(parents=True, exist_ok=True)

    # 单独保存转录文本（避免JSON文件过大）
    transcript_path = intermediates_dir / "transcript.json"
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "language": result.language,
                "full_text": result.asr_full_text,
                "segments": result.asr_segments,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    preprocess_path = intermediates_dir / "preprocess_result.json"
    with open(preprocess_path, "w", encoding="utf-8") as f:
        json.dump(preprocess_data, f, ensure_ascii=False, indent=2)

    print(f"  中间结果已保存: {preprocess_path}")
    print(f"  转写文本已保存: {transcript_path}")
