from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


@dataclass
class ImageMeta:
    filepath: str
    width: int | None = None
    height: int | None = None
    size: int | None = None
    format: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def probe_image(image_path: str | Path) -> ImageMeta:
    filepath = str(Path(image_path).resolve())
    file_size = Path(image_path).stat().st_size
    with Image.open(image_path) as img:
        return ImageMeta(
            filepath=filepath,
            width=img.width,
            height=img.height,
            size=file_size,
            format=img.format,
        )
