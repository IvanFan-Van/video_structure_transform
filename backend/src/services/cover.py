import uuid
from pathlib import Path

import ffmpeg
from fastapi import HTTPException
from sqlmodel import Session

from database import engine
from lib.video import extract_cover_image
from models import Asset
from repositories import create_asset

STORAGE_IMAGES = Path("storage/images")


def extract_cover_for_video(
    video_path: str,
    user_id: str,
    source_asset_id: str | None = None,
) -> str | None:
    try:
        img = extract_cover_image(video_path)
    except ffmpeg.Error as e:
        if e.stderr:
            raise HTTPException(
                status_code=500,
                detail=f"封面提取失败: {e.stderr.decode('utf-8', errors='ignore')}",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"未捕捉到 ffmpeg stderr 信息. 封面提取失败: {str(e)}",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"封面提取失败: {str(e)}")

    STORAGE_IMAGES.mkdir(parents=True, exist_ok=True)
    cover_id = str(uuid.uuid4())
    cover_path = STORAGE_IMAGES / f"{cover_id}.jpg"
    img.save(str(cover_path), "JPEG", quality=85)

    with Session(engine) as session:
        asset = Asset(
            asset_id=cover_id,
            user_id=user_id,
            source_asset_id=source_asset_id,
            path=str(cover_path),
            type="image",
        )
        create_asset(session, asset)

    return cover_id
