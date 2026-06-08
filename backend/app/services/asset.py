from pathlib import Path

from fastapi import HTTPException
from sqlmodel import Session

from app.models import User
from app.repositories import get_asset_by_id


def serve_asset_file(session: Session, asset_id: str, current_user: User) -> Path:
    asset = get_asset_by_id(session, asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail="文件不存在")
    if asset.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问该文件")

    file_path = Path(asset.path)
    if not file_path.exists():
        raise HTTPException(status_code=500, detail="文件丢失")

    return file_path
