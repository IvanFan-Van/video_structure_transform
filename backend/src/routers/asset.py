from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session

from database import get_session
from deps import get_current_user
from models import User
from services import serve_asset_file

router = APIRouter(tags=["files"])


@router.get("/files/{asset_id}")
async def serve_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return FileResponse(
        serve_asset_file(session, asset_id, current_user),
    )
