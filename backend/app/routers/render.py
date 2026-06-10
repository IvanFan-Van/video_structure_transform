from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from app.config.style_config import get_available_styles
from app.database import get_session
from app.deps import get_current_user
from app.models import User
from app.schemas.render import PreviewRequest, RenderRequest
from app.services.render_service import start_preview_task, start_render_task
from app.tasks import task_registry

router = APIRouter(tags=["render"])


@router.get("/styles")
def list_styles():
    return JSONResponse(
        content={"status": "success", "data": get_available_styles()},
    )


@router.post("/render/preview")
async def preview_versions(
    body: PreviewRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan_task = task_registry.get(body.plan_id)
    if plan_task is None:
        raise HTTPException(404, f"Plan {body.plan_id} not found")
    if plan_task.user_id != current_user.user_id:
        raise HTTPException(403, "Access denied")
    if plan_task.status != "completed":
        raise HTTPException(
            400,
            f"Plan not completed, current status: {plan_task.status}",
        )

    task_id = start_preview_task(session, current_user.user_id, body.plan_id)
    return JSONResponse(
        status_code=202,
        content={"status": "success", "data": {"task_id": task_id}},
    )


@router.post("/render")
async def start_render(
    body: RenderRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan_task = task_registry.get(body.plan_id)
    if plan_task is None:
        raise HTTPException(404, f"Plan {body.plan_id} not found")
    if plan_task.user_id != current_user.user_id:
        raise HTTPException(403, "Access denied")
    if plan_task.status != "completed":
        raise HTTPException(
            400,
            f"Plan not completed, current status: {plan_task.status}",
        )

    task_id = start_render_task(
        session, current_user.user_id, body.plan_id, body.style
    )
    return JSONResponse(
        status_code=202,
        content={"status": "success", "data": {"task_id": task_id}},
    )


@router.get("/render/still/{task_id}/{filename:path}")
async def serve_preview_still(
    task_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    still_path = Path("storage") / "preview" / task_id / filename
    if not still_path.exists():
        raise HTTPException(404, "Still not found")
    return FileResponse(str(still_path.resolve()), media_type="image/png")
