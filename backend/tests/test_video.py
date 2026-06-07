from pathlib import Path

import pytest
from PIL import Image

from src.video import (
    VideoMeta,
    compress_video,
    detect_scenes_scenedetect,
    extract_cover_image,
    format_video_meta,
    get_video_duration,
    probe_video,
    split_video_by_segments,
    video_to_base64,
)


class TestVideoMeta:
    def test_to_dict_works(self):
        meta = VideoMeta(filepath="/a.mp4", width=1920, height=1080, fps=30.0)
        d = meta.to_dict()
        assert d["filepath"] == "/a.mp4"
        assert d["width"] == 1920
        assert d["height"] == 1080
        assert d["fps"] == 30.0

    def test_to_dict_handles_none_fields(self):
        meta = VideoMeta(filepath="/a.mp4")
        d = meta.to_dict()
        assert d["codec"] is None
        assert d["duration"] is None


class TestFormatVideoMeta:
    def test_format_video_meta_works(self):
        meta = VideoMeta(
            filepath="/v.mp4",
            codec="h264",
            width=1920,
            height=1080,
            fps=30.0,
            duration=15.5,
            size=1000000,
        )
        s = format_video_meta(meta)
        assert "h264" in s
        assert "1920x1080" in s
        assert "30.0" in s
        assert "15.5s" in s

    def test_format_video_meta_handles_none_fields(self):
        meta = VideoMeta(filepath="/v.mp4")
        s = format_video_meta(meta)
        assert "None" in s


class TestVideoToBase64:
    def test_video_to_base64_works(self, sample_video):
        result = video_to_base64(sample_video)
        assert len(result) > 0
        assert isinstance(result, str)

    def test_video_to_base64_fails_with_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            video_to_base64("nonexistent.mp4")


class TestProbeVideo:
    def test_probe_video_works(self, sample_video):
        meta = probe_video(sample_video)
        assert meta.width is not None
        assert meta.height is not None
        assert meta.fps is not None
        assert meta.duration is not None

    def test_probe_video_fails_with_nonexistent_file(self):
        with pytest.raises(RuntimeError, match="Failed to probe"):
            probe_video("nonexistent.mp4")

    def test_probe_video_accepts_path_object(self, sample_video):
        assert probe_video(Path(sample_video)).width is not None


class TestGetVideoDuration:
    def test_get_video_duration_works(self, sample_video):
        dur = get_video_duration(sample_video)
        assert dur > 0


class TestCompressVideo:
    def test_compress_video_works(self, sample_video, tmp_path):
        out = tmp_path / "out.mp4"
        result = compress_video(sample_video, out, target_v_bitrate="500k")
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_compress_video_with_scale_width(self, sample_video, tmp_path):
        out = tmp_path / "scaled.mp4"
        compress_video(sample_video, out, scale_width=640, target_v_bitrate="500k")
        meta = probe_video(out)
        assert meta.width <= 640

    def test_compress_video_fails_with_nonexistent_input(self, tmp_path):
        with pytest.raises(Exception):
            compress_video("nonexistent.mp4", tmp_path / "out.mp4")


class TestDetectScenes:
    def test_detect_scenes_works(self, sample_video):
        segments = detect_scenes_scenedetect(sample_video)
        assert isinstance(segments, list)
        assert len(segments) >= 1

    def test_detect_scenes_returns_expected_keys(self, sample_video):
        segments = detect_scenes_scenedetect(sample_video)
        for seg in segments:
            assert "index" in seg
            assert "start_sec" in seg
            assert "end_sec" in seg
            assert "duration" in seg
            assert "cut_score" in seg
            assert seg["duration"] > 0
            assert seg["end_sec"] > seg["start_sec"]

    def test_detect_scenes_respects_threshold(self, sample_video):
        low = detect_scenes_scenedetect(sample_video, threshold=10.0)
        high = detect_scenes_scenedetect(sample_video, threshold=80.0)
        assert len(low) >= len(high)


class TestSplitVideo:
    def test_split_video_works(self, sample_video, tmp_path):
        segs = detect_scenes_scenedetect(sample_video)
        clips = split_video_by_segments(sample_video, segs, tmp_path, "test")
        assert len(clips) == len(segs)
        for clip in clips:
            assert clip.exists()
            assert clip.stat().st_size > 0
            assert clip.suffix == ".mp4"

    def test_split_video_with_custom_prefix(self, sample_video, tmp_path):
        segs = detect_scenes_scenedetect(sample_video)
        clips = split_video_by_segments(sample_video, segs, tmp_path, "myclip")
        for clip in clips:
            assert "myclip_" in clip.name


class TestExtractCoverImage:
    def test_extract_cover_image_works(self, sample_video):
        img = extract_cover_image(str(sample_video))
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0

    def test_extract_cover_image_fails_with_nonexistent_file(self):
        with pytest.raises(Exception):
            extract_cover_image("nonexistent.mp4")
