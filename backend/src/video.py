from pathlib import Path

import ffmpeg


class VideoClip:
    """Video object that stores metadata and compresses itself."""

    def __init__(self, video_path: str | Path) -> None:
        self.filepath = str(Path(video_path).resolve())
        self.codec = None
        self.width = None
        self.height = None
        self.fps = None
        self.v_bitrate = None
        self.total_bitrate = None
        self.audio_sample_rate = None
        self.audio_channels = None
        self.a_bitrate = None
        self.__initialize()

    def __str__(self) -> str:
        return (
            f"Video Path: {self.filepath}\n"
            f"Codec: {self.codec}\n"
            f"Resolution: {self.width}x{self.height}\n"
            f"FPS: {self.fps}\n"
            f"Video Bitrate: {self.v_bitrate} kbps\n"
            f"Total Bitrate: {self.total_bitrate} kbps\n"
            f"Audio Sample Rate: {self.audio_sample_rate} Hz\n"
            f"Audio Channels: {self.audio_channels}\n"
            f"Audio Bitrate: {self.a_bitrate} kbps"
        )

    def __initialize(self) -> None:
        try:
            # 使用 ffprobe 探测文件元数据
            probe = ffmpeg.probe(self.filepath)

            # 分离视频流和音频流
            video_stream = next(
                (
                    stream
                    for stream in probe["streams"]
                    if stream["codec_type"] == "video"
                ),
                None,
            )
            audio_stream = next(
                (
                    stream
                    for stream in probe["streams"]
                    if stream["codec_type"] == "audio"
                ),
                None,
            )
            format_info = probe.get("format", {})

            if video_stream:
                # 1. 编码格式
                self.codec = video_stream.get("codec_name", "unknown")

                # 2. 分辨率
                width = video_stream.get("width")
                height = video_stream.get("height")
                self.width = width
                self.height = height

                # 3. 帧率 (FFmpeg 返回的是分数形式，如 "30000/1001" 或 "24/1")
                fps_string = video_stream.get("r_frame_rate", "0/0")
                if "/" in fps_string:
                    num, den = map(int, fps_string.split("/"))
                    fps = num / den if den != 0 else 0
                else:
                    fps = float(fps_string)

                self.fps = fps

                # 4. 码率 (比特率)
                # 优先获取视频流本身的码率，如果没有，再用文件总码率估算
                v_bitrate = video_stream.get("bit_rate")
                self.v_bitrate = int(v_bitrate) // 1000 if v_bitrate else None
                total_bitrate = format_info.get("bit_rate")
                self.total_bitrate = (
                    int(total_bitrate) // 1000 if total_bitrate else None
                )

            # 5. 音频属性
            if audio_stream:
                self.audio_sample_rate = int(audio_stream.get("sample_rate", 0))
                self.audio_channels = int(audio_stream.get("channels", 0))
                a_bitrate = audio_stream.get("bit_rate")
                self.a_bitrate = int(a_bitrate) // 1000 if a_bitrate else None

        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to probe video file: {self.filepath}") from e

    def compress(
        self,
        output_path: str | Path,
        vcodec: str = "libx264",
        crf: int | None = 32,
        target_v_bitrate: str | None = None,
        scale_width: int | None = None,
        max_fps: int | None = 30,
        acodec: str = "aac",
        target_a_bitrate: str = "96k",
    ) -> "VideoClip":
        """Compress the video and return a new `VideoClip`."""
        input_path = self.filepath
        output_path = Path(output_path)

        # 1. 构建输入流并分离音视频轨
        stream = ffmpeg.input(input_path)
        v_stream = stream.video
        a_stream = stream.audio

        # 2. 【核心修复】：通过清晰的链式调用（Chain）单独叠加滤镜
        if scale_width:
            # -2 确保等比例缩放后的高度也是 2 的倍数，防止 H.264/H.265 编码报错
            v_stream = v_stream.filter("scale", scale_width, -2)

        if max_fps:
            v_stream = v_stream.filter("fps", fps=max_fps)

        # 3. 组装输出参数字典
        output_kwargs = {
            "vcodec": vcodec,
            "acodec": acodec,
            "audio_bitrate": target_a_bitrate,
        }

        # 选择码率控制模式
        if target_v_bitrate:
            output_kwargs["video_bitrate"] = target_v_bitrate
        elif crf is not None:
            output_kwargs["crf"] = crf  # type: ignore

        if vcodec == "libx265":
            output_kwargs["preset"] = "medium"

        # 4. 执行转码与压缩
        try:
            process = ffmpeg.output(
                v_stream, a_stream, str(output_path), **output_kwargs
            )

            process.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            print("视频压缩成功！")

        except ffmpeg.Error as e:
            print("FFmpeg 压缩过程中出错！")
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            raise e

        # 5. 返回压缩后的新对象
        return VideoClip(str(output_path.resolve()))


if __name__ == "__main__":
    input_path = Path("tests/videos/抖音2026529-207530.mp4")
    output_path = Path("tests/videos/compressed_output.mp4")
    video = VideoClip(input_path)
    print("原视频信息：")
    print(video)

    compressed_video = video.compress(
        output_path=output_path,
        # vcodec="libx264",
        # crf=32,
        # max_fps=30,
        # target_a_bitrate="96k",
    )

    print("\n压缩后视频信息：")
    print(compressed_video)

    Path(compressed_video.filepath).unlink()  # 删除测试生成的压缩文件
