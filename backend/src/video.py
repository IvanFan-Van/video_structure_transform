import base64
from dataclasses import asdict, dataclass
from pathlib import Path

import ffmpeg


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
