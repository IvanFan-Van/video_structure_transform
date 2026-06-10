from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.models import User
from app.schemas.render import RenderRequest
from app.services.render_service import start_render_task
from app.tasks import task_registry

router = APIRouter(tags=["render"])


@router.post("/render")
async def start_render(
    body: RenderRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan_task = task_registry.get(body.plan_id)
    if plan_task is None:
        raise HTTPException(404, f"计划 {body.plan_id} 不存在")
    if plan_task.user_id != current_user.user_id:
        raise HTTPException(403, "无权访问该计划")
    if plan_task.status != "completed":
        raise HTTPException(
            400,
            f"计划尚未生成完成，当前状态：{plan_task.status}",
        )

    task_id = start_render_task(session, current_user.user_id, body.plan_id)
    return JSONResponse(
        status_code=202,
        content={"status": "success", "data": {"task_id": task_id}},
    )
