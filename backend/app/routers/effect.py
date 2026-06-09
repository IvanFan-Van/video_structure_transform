from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.models import User
from app.repositories import search_effects

router = APIRouter(tags=["effects"])


@router.get("/effects")
async def list_effects(
    q: str = Query(None, description="关键词模糊搜索 (name / category / description)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    effects = search_effects(session, q)
    return JSONResponse(status_code=200, content={
        "status": "success",
        "data": [
            {"name": e.name, "category": e.category, "description": e.description}
            for e in effects
        ],
    })
