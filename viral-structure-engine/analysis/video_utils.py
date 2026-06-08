"""FFmpeg 工具函数 — 视频元数据、帧提取、音频处理、base64 编码

本文件封装了一系列通过 subprocess 调用 ffmpeg/ffprobe 的工具函数，
是 Phase 0 预处理阶段与视频文件交互的底层IO层。

所有函数都是纯本地操作，不涉及LLM调用。

核心函数:
  ffprobe()              — 调用ffprobe获取原始JSON元数据
  get_video_metadata()   — 简化后的视频元数据（时长、分辨率、帧率等）
  extract_audio()        — 从视频中提取WAV音频（用于ASR/BGM分析）
  extract_frame_at_time()— 在指定时间点截取单帧JPEG
  extract_video_clip()   — 提取视频片段（用于Phase 2逐beat分析）
  frame_to_base64()      — 图片文件→base64字符串
  video_to_base64()      — 视频文件→base64字符串（用于LLM Vision API）
"""

import base64
import json
import subprocess
import tempfile
from pathlib import Path


def ffprobe(video_path: str | Path) -> dict:
    """调用 ffprobe 提取视频原始元数据（JSON格式）

    Args:
        video_path: 视频文件路径

    Returns:
        ffprobe 的完整 JSON 输出，包含 format 和 streams 两大块
    """
    video_path = str(video_path)
    cmd = [
        "ffprobe",
        "-v", "quiet",               # 减少日志输出
        "-print_format", "json",     # JSON格式输出
        "-show_format",              # 显示封装格式信息（时长、码率等）
        "-show_streams",             # 显示流信息（视频流、音频流）
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    result.check_returncode()
    return json.loads(result.stdout)


def get_video_metadata(video_path: str | Path) -> dict:
    """获取简化后的视频元数据

    从 ffprobe 的原始输出中提取最常用的字段，供后续分析使用。

    返回:
        filename:   文件名
        duration:   总时长(秒)
        resolution: 分辨率如 "1080x1920"
        fps:        帧率
        codec:      视频编码如 "h264"
        has_audio:  是否有音轨
        bitrate:    码率(bps)
        size:       文件大小(字节)
    """
    info = ffprobe(video_path)
    video_stream = None   # 第一个视频流
    audio_stream = None   # 第一个音频流

    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0))

    return {
        "filename": str(Path(video_path).name),
        "duration": duration,
        "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}" if video_stream else "unknown",
        "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0,
        "codec": video_stream.get("codec_name", "unknown") if video_stream else "unknown",
        "has_audio": audio_stream is not None,
        "bitrate": int(fmt.get("bit_rate", 0)) if fmt.get("bit_rate") else 0,
        "size": int(fmt.get("size", 0)) if fmt.get("size") else 0,
    }


def extract_audio(video_path: str | Path, output_path: str | Path | None = None,
                  sample_rate: int = 16000, channels: int = 1) -> str:
    """从视频中提取音频为WAV文件

    Args:
        video_path:  视频文件路径
        output_path: 输出WAV路径，None则存到临时目录
        sample_rate: 采样率(Hz) — 16000用于ASR，44100用于音乐质量
        channels:    声道数 — 1=单声道(ASR)，2=立体声(音乐)

    Returns:
        输出WAV文件的路径
    """
    video_path = str(video_path)
    if output_path is None:
        # 默认存到系统临时目录
        output_path = str(Path(tempfile.gettempdir()) / f"_vse_audio_{Path(video_path).stem}.wav")
    else:
        output_path = str(output_path)

    cmd = [
        "ffmpeg",
        "-y",                        # 覆盖已有文件
        "-i", video_path,            # 输入
        "-vn",                       # 丢弃视频流
        "-acodec", "pcm_s16le",      # 16-bit PCM编码(WAV标准)
        "-ar", str(sample_rate),     # 采样率
        "-ac", str(channels),        # 声道数
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120).check_returncode()
    return output_path


def extract_frame_at_time(video_path: str | Path, time_sec: float, output_path: str | Path) -> bool:
    """在指定时间点截取单帧JPEG图片

    使用 ffmpeg 的 -ss 快速定位 + -vframes 1 截取单帧。

    Args:
        video_path:  视频文件路径
        time_sec:    目标时间点(秒)，支持小数
        output_path: 输出JPEG图片路径

    Returns:
        是否成功截取（文件存在为True）
    """
    video_path = str(video_path)
    output_path = str(output_path)
    cmd = [
        "ffmpeg",
        "-y",                  # 覆盖已有文件
        "-ss", str(time_sec),  # 跳转到目标时间点
        "-i", video_path,      # 输入文件
        "-vframes", "1",       # 只截取1帧
        "-q:v", "2",           # 图片质量(2=高质量, 1-31范围)
        output_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30).check_returncode()
        return Path(output_path).exists()
    except subprocess.CalledProcessError:
        return False


def frame_to_base64(image_path: str | Path) -> str:
    """将JPEG图片文件编码为 base64 字符串

    用于将关键帧图片发送给LLM Vision API（作为 image_url content block）。

    Args:
        image_path: 图片文件路径

    Returns:
        base64编码的字符串，不含 data URI 前缀
    """
    image_path = Path(image_path)
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def video_to_base64(video_path: str | Path) -> str:
    """将整个视频文件编码为 base64 字符串

    用于 Phase 1 将完整视频发送给LLM Vision API。
    注意：大视频编码后体积膨胀约33%，建议视频≤20MB。

    Args:
        video_path: 视频文件路径

    Returns:
        base64编码的字符串
    """
    video_path = Path(video_path)
    with open(video_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ═══════════════════════════════════════════════════════════════════
# 视频片段提取 — Phase 2 逐beat分析专用
# ═══════════════════════════════════════════════════════════════════


def extract_video_clip(
    video_path: str | Path,
    start_s: float,
    end_s: float,
    overlap_before: float = 0.5,
    overlap_after: float = 0.0,
) -> dict:
    """提取视频片段（用于Phase 2逐beat分析）

    向前扩展 overlap_before 秒，让LLM能看到跨beat的转场/动画入场效果。
    使用 ultrafast 预设 + 低码率，优先速度而非画质（LLM只需要看个大概）。

    Args:
        video_path:      源视频路径
        start_s:         beat开始时间(秒)
        end_s:           beat结束时间(秒)
        overlap_before:  向前多取的时间(秒)，默认0.5s
        overlap_after:   向后多取的时间(秒)，默认0

    Returns:
        {"clip_b64":      片段base64编码,
         "actual_start_s": 实际起始时间(秒),
         "duration":       片段时长(秒)}
    """
    video_path = str(video_path)
    actual_start = max(0.0, start_s - overlap_before)  # 片段实际起始时间
    actual_end = end_s + overlap_after                  # 片段实际结束时间
    clip_duration = actual_end - actual_start           # 片段时长

    if clip_duration <= 0:
        return {"clip_b64": "", "actual_start_s": start_s, "duration": 0}

    # 写到系统临时目录，用完即删
    tmp_path = str(Path(tempfile.gettempdir()) / f"_vse_clip_{Path(video_path).stem}_{int(start_s)}s.mp4")

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(actual_start),      # 起始时间
        "-i", video_path,              # 输入
        "-t", str(clip_duration),      # 持续时长
        "-c:v", "libx264",             # H.264编码
        "-preset", "ultrafast",        # 最快编码速度（画质较低但LLM够用）
        "-crf", "28",                  # 恒定质量因子(28=较低画质，减小体积)
        "-c:a", "aac",                 # AAC音频编码
        "-b:a", "96k",                 # 96kbps音频（节省带宽）
        "-movflags", "+faststart",     # 将moov atom移到文件头（便于流式传输）
        tmp_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120).check_returncode()

        if Path(tmp_path).exists() and Path(tmp_path).stat().st_size > 0:
            clip_b64 = video_to_base64(tmp_path)  # 编码为base64
            # 清理临时文件
            try:
                Path(tmp_path).unlink()
            except OSError:
                pass
            return {"clip_b64": clip_b64, "actual_start_s": round(actual_start, 2), "duration": round(clip_duration, 2)}
        else:
            return {"clip_b64": "", "actual_start_s": start_s, "duration": 0}

    except subprocess.CalledProcessError:
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass
        return {"clip_b64": "", "actual_start_s": start_s, "duration": 0}
