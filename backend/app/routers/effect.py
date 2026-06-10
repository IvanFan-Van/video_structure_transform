from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.models import User
from app.repositories import search_effects
from app.schemas import UpdateEffectRequest
from app.services.task import get_task_for_user

router = APIRouter(tags=["effects"])

OUT_DIR = Path(__file__).parent.parent.parent.parent / "effects-renderer" / "out"


@router.get("/effects/demo/{filename}")
async def serve_effect_demo(filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = OUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Demo not found")
    return FileResponse(file_path, media_type="video/mp4")


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
            {
                "name": e.name,
                "category": e.category,
                "description": e.description,
                "demo_path": e.demo_path,
            }
            for e in effects
        ],
    })


@router.patch("/effects")
async def update_effects(
    req: UpdateEffectRequest,
    current_user: User = Depends(get_current_user),
):
    task_info = get_task_for_user(req.task_id, current_user)

    if task_info.type != "analyze-effect":
        raise HTTPException(
            status_code=400,
            detail=f"任务类型为 {task_info.type}，仅 analyze-effect 可修改 effects",
        )
    if task_info.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"任务状态为 {task_info.status}，仅 completed 可修改 effects",
        )

    task_info.result["effects"] = [ef.model_dump() for ef in req.effects]

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": task_info.result["effects"],
        },
    )
