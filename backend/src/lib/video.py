import asyncio
import base64
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import ffmpeg
import numpy as np
from PIL import Image


@dataclass
class VideoMeta:
    filepath: str
    codec: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    v_bitrate: int | None = None
    total_bitrate: int | None = None
    audio_sample_rate: int | None = None
    audio_channels: int | None = None
    a_bitrate: int | None = None
    size: int | None = None
    duration: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def probe_video(video_path: str | Path) -> VideoMeta:
    """Probe video file metadata and return a `VideoMeta`."""
    filepath = str(Path(video_path).resolve())
    meta = VideoMeta(filepath=filepath)

    try:
        probe = ffmpeg.probe(filepath)
        meta.size = probe.get("format", {}).get("size")
        dur = probe.get("format", {}).get("duration")
        if dur:
            meta.duration = float(dur)

        video_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "video"),
            None,
        )
        audio_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "audio"),
            None,
        )
        format_info = probe.get("format", {})

        if video_stream:
            meta.codec = video_stream.get("codec_name", "unknown")
            meta.width = video_stream.get("width")
            meta.height = video_stream.get("height")

            fps_string = video_stream.get("r_frame_rate", "0/0")
            if "/" in fps_string:
                num, den = map(int, fps_string.split("/"))
                meta.fps = num / den if den != 0 else 0
            else:
                meta.fps = float(fps_string)

            v_bitrate = video_stream.get("bit_rate")
            meta.v_bitrate = int(v_bitrate) // 1000 if v_bitrate else None
            total_bitrate = format_info.get("bit_rate")
            meta.total_bitrate = int(total_bitrate) // 1000 if total_bitrate else None

        if audio_stream:
            sr = audio_stream.get("sample_rate")
            if sr:
                meta.audio_sample_rate = int(sr)
            ch = audio_stream.get("channels")
            if ch:
                meta.audio_channels = int(ch)
            a_bitrate = audio_stream.get("bit_rate")
            meta.a_bitrate = int(a_bitrate) // 1000 if a_bitrate else None

    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to probe video file: {filepath}") from e

    return meta


def compress_video(
    input_path: str | Path,
    output_path: str | Path,
    vcodec: str = "libx264",
    crf: int | None = 32,
    target_v_bitrate: str | None = None,
    scale_width: int | None = None,
    max_fps: int | None = 30,
    acodec: str = "aac",
    target_a_bitrate: str = "96k",
) -> Path:
    """Compress a video and return the output path."""
    input_path = str(Path(input_path).resolve())
    output_path = Path(output_path).resolve()

    stream = ffmpeg.input(input_path)
    v_stream = stream.video
    a_stream = stream.audio

    if scale_width:
        v_stream = v_stream.filter("scale", scale_width, -2)
    if max_fps:
        v_stream = v_stream.filter("fps", fps=max_fps)

    output_kwargs: dict = {
        "vcodec": vcodec,
        "acodec": acodec,
        "audio_bitrate": target_a_bitrate,
    }

    if target_v_bitrate:
        output_kwargs["video_bitrate"] = target_v_bitrate
    elif crf is not None:
        output_kwargs["crf"] = crf

    if vcodec == "libx265":
        output_kwargs["preset"] = "medium"

    try:
        process = ffmpeg.output(v_stream, a_stream, str(output_path), **output_kwargs)
        process.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        print("FFmpeg error during compression!")
        if e.stderr:
            print(e.stderr.decode("utf-8"))
        raise e

    return output_path


async def compress_video_async(
    input_path: str | Path,
    output_path: str | Path,
    vcodec: str = "libx264",
    crf: int | None = 32,
    target_v_bitrate: str | None = None,
    scale_width: int | None = None,
    max_fps: int | None = 30,
    acodec: str = "aac",
    target_a_bitrate: str = "96k",
) -> Path:
    """异步压缩视频，可通过 asyncio.CancelledError 中途取消。"""
    input_path = str(Path(input_path).resolve())
    output_path = Path(output_path).resolve()

    stream = ffmpeg.input(input_path)
    v_stream = stream.video
    a_stream = stream.audio

    if scale_width:
        v_stream = v_stream.filter("scale", scale_width, -2)
    if max_fps:
        v_stream = v_stream.filter("fps", fps=max_fps)

    output_kwargs: dict = {
        "vcodec": vcodec,
        "acodec": acodec,
        "audio_bitrate": target_a_bitrate,
    }

    if target_v_bitrate:
        output_kwargs["video_bitrate"] = target_v_bitrate
    elif crf is not None:
        output_kwargs["crf"] = crf

    if vcodec == "libx265":
        output_kwargs["preset"] = "medium"

    output = ffmpeg.output(v_stream, a_stream, str(output_path), **output_kwargs)
    args = output.compile()
    if "-y" not in args:
        args = args[:1] + ["-y"] + args[1:]

    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        await process.wait()
    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        raise

    if process.returncode != 0:
        if process.stderr:
            stderr = await process.stderr.read()
        else:
            stderr = b""
        raise RuntimeError(
            f"ffmpeg exited with code {process.returncode}: {stderr.decode()}"
        )

    return output_path


def video_to_base64(video_path: str | Path) -> str:
    """Return the base64-encoded string of the video file."""
    with open(video_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def format_video_meta(meta: VideoMeta) -> str:
    """Format `VideoMeta` as a human-readable string."""
    return (
        f"Video Path: {meta.filepath}\n"
        f"Codec: {meta.codec}\n"
        f"Resolution: {meta.width}x{meta.height}\n"
        f"FPS: {meta.fps}\n"
        f"Video Bitrate: {meta.v_bitrate} kbps\n"
        f"Total Bitrate: {meta.total_bitrate} kbps\n"
        f"Audio Sample Rate: {meta.audio_sample_rate} Hz\n"
        f"Audio Channels: {meta.audio_channels}\n"
        f"Audio Bitrate: {meta.a_bitrate} kbps\n"
        f"Size: {meta.size} bytes\n"
        f"Duration: {meta.duration}s"
    )


def get_video_duration(video_path: str | Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return frame_count / fps if fps > 0 else 0.0


def detect_scenes_scenedetect(
    video_path: str | Path,
    threshold: float = 25.0,
    min_scene_len: int = 15,
) -> list[dict]:
    from scenedetect import SceneManager, StatsManager, open_video
    from scenedetect.detectors import ContentDetector

    video = open_video(str(video_path))
    stats_manager = StatsManager()
    scene_manager = SceneManager(stats_manager=stats_manager)
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len)
    )
    scene_manager.detect_scenes(video)

    scene_list = scene_manager.get_scene_list()

    frame_scores = {}
    if stats_manager is not None:
        for frame_num, metrics in stats_manager._frame_metrics.items():
            frame_scores[frame_num] = metrics.get("content_val", 0)

    segments = []
    for i, (start, end) in enumerate(scene_list):
        end_frame = end.frame_num
        nearby_scores = [
            frame_scores.get(end_frame + offset, 0) for offset in range(-2, 3)
        ]
        cut_score = max(nearby_scores) if nearby_scores else 0

        segments.append(
            {
                "index": i,
                "start_sec": start.seconds,
                "end_sec": end.seconds,
                "duration": end.seconds - start.seconds,
                "cut_score": round(cut_score, 4),
            }
        )

    return segments


def split_video_by_segments(
    video_path: str | Path,
    segments: list[dict],
    output_dir: Path,
    clip_prefix: str = "clip",
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths = []
    for seg in segments:
        output_path = output_dir / f"{clip_prefix}_{seg['index']:03d}.mp4"
        (
            ffmpeg.input(str(video_path), ss=seg["start_sec"], t=seg["duration"])
            .output(str(output_path), c="copy")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        output_paths.append(output_path)

    return output_paths


def extract_cover_image(video_path: str) -> Image.Image:
    """
    从视频中提取第一个有效关键帧作为封面图。
    跳过亮度过低的静默帧（黑屏、带水印黑屏等），返回 PIL Image 对象。

    Args:
        video_path: 视频文件路径

    Returns:
        PIL.Image.Image: 封面图像
    """
    PIXEL_BRIGHTNESS_THRESHOLD = 15  # 单个像素亮度阈值 (0-255)
    CONTENT_RATIO_THRESHOLD = 0.1  # 至少 10% 的像素有内容才算有效帧
    MAX_KEYFRAMES = 10  # 最多检查前 N 个关键帧

    # 获取视频元信息（宽高）
    probe = ffmpeg.probe(video_path)
    video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    width = int(video_stream["width"])
    height = int(video_stream["height"])

    # 抽取前 MAX_KEYFRAMES 个 I 帧，输出原始 RGB 字节流
    out, _ = (
        ffmpeg.input(video_path)
        .video.filter("select", f"lte(n,{MAX_KEYFRAMES})*eq(pict_type,I)")
        .output("pipe:", format="rawvideo", pix_fmt="rgb24", vsync="vfr")
        .run(capture_stdout=True, capture_stderr=True, quiet=True)
    )

    frame_size = width * height * 3  # bytes per frame (RGB24)

    if len(out) < frame_size:
        raise ValueError(f"未能从视频中抽取到任何关键帧: {video_path}")

    def is_valid_frame(frame: np.ndarray) -> bool:
        """判断帧是否为有效内容帧（非静默帧、非纯水印黑屏）"""
        gray = frame.mean(axis=2)  # (H, W) 灰度
        content_ratio = (gray > PIXEL_BRIGHTNESS_THRESHOLD).sum() / gray.size
        return content_ratio >= CONTENT_RATIO_THRESHOLD

    # 逐帧检查，返回第一个有效帧
    num_frames = min(MAX_KEYFRAMES, len(out) // frame_size)
    for i in range(num_frames):
        raw = out[i * frame_size : (i + 1) * frame_size]
        frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
        if is_valid_frame(frame):
            return Image.fromarray(frame)

    # 所有关键帧均为静默帧，退而返回最后一个关键帧
    raw = out[(num_frames - 1) * frame_size : num_frames * frame_size]
    frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
    return Image.fromarray(frame)


if __name__ == "__main__":
    input_path = Path("tests/videos/抖音2026529-207530.mp4")
    output_path = Path("tests/videos/compressed_output.mp4")

    meta = probe_video(input_path)
    print("原视频信息：")
    print(format_video_meta(meta))

    compressed_path = compress_video(input_path, output_path)
    compressed_meta = probe_video(compressed_path)

    print("\n压缩后视频信息：")
    print(format_video_meta(compressed_meta))

    compressed_path.unlink()
