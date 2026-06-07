import asyncio
import base64
from pathlib import Path

import cv2
import ffmpeg
import numpy as np
from PIL import Image

from .schemas import VideoMeta


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
            .output(str(output_path))
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        output_paths.append(output_path)

    return output_paths


def extract_cover_image(video_path: str) -> Image.Image:
    probe = ffmpeg.probe(str(video_path))
    video_stream = next(v for v in probe["streams"] if v["codec_type"] == "video")
    width = int(video_stream["width"])
    height = int(video_stream["height"])

    out, _ = (
        ffmpeg.input(str(video_path), skip_frame="nokey")
        .output("pipe:", vsync="vfr", format="rawvideo", pix_fmt="bgr24")
        .run(capture_stdout=True, capture_stderr=True)
    )

    if not out:
        raise RuntimeError(
            f"Failed to extract frames from an empty video: {video_path}"
        )

    frames_array = np.frombuffer(out, dtype=np.uint8)
    frames = frames_array.reshape((-1, height, width, 3))

    # blur detection
    def get_blur_score(image: np.ndarray) -> float:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    # brightness detection
    def get_brightness_score(image: np.ndarray) -> float:
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb[:, :, 0]
        return cv2.mean(y_channel)[0]

    def is_valid_frame(frame: np.ndarray) -> bool:
        blur_score = get_blur_score(frame)
        brightness_score = get_brightness_score(frame)
        # print(
        #     f"Frame blur score: {blur_score:.2f}, brightness score: {brightness_score:.2f}"
        # )
        return blur_score > 50.0 and (
            brightness_score > 40.0 and brightness_score < 220.0
        )

    valid_frame = None
    for frame in frames:
        if is_valid_frame(frame):
            valid_frame = frame
            break

    if valid_frame is None:
        valid_frame = frames[-1]

    return Image.fromarray(cv2.cvtColor(valid_frame, cv2.COLOR_BGR2RGB))


if __name__ == "__main__":
    from PIL import Image

    # video_path = Path.cwd() / "tests" / "videos" / "6.mp4"
    video_path = Path.cwd() / "notebooks" / "output" / "clips" / "hook_0.0s-4.0s.mp4"
    print(video_path)
    frame = extract_cover_image(str(video_path))
    img = Image.fromarray(frame)  # type: ignore
    img.save("cover.jpg")
