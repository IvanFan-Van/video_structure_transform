from dataclasses import asdict, dataclass


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
