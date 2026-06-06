from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from deps import get_current_user
from models import Asset, User, engine

router = APIRouter(tags=["files"])


@router.get("/files/{asset_id}")
async def serve_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_id == asset_id)
        asset = session.exec(statement).first()
        if not asset:
            raise StarletteHTTPException(status_code=404, detail="文件不存在")
        if asset.user_id != current_user.user_id:
            raise StarletteHTTPException(status_code=403, detail="无权访问该文件")

        file_path = Path(asset.path)
        if not file_path.exists():
            raise StarletteHTTPException(status_code=500, detail="文件丢失")

        return FileResponse(file_path)
