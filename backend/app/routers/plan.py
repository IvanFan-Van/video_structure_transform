from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.models import User
from app.repositories import get_asset_by_id
from app.schemas import FillSlotRequest, PlanRequest
from app.schemas.plan import FillMethod, SlotStatus, VideoTemplate
from app.services import start_plan_generation
from app.tasks import task_registry

router = APIRouter(tags=["plan"])


def _find_slot_in_template(template: VideoTemplate, slot_id: str):
    if template.bgm_spec.slot.slot_id == slot_id:
        return template.bgm_spec.slot
    for seg in template.segments:
        for slot in seg.slots:
            if slot.slot_id == slot_id:
                return slot
    return None


@router.post("/plan")
async def create_plan(
    body: PlanRequest,
    current_user: User = Depends(get_current_user),
):
    for tid in [
        body.script_task_id,
        body.visual_task_id,
        body.audio_task_id,
        body.effect_task_id,
    ]:
        if tid is None:
            continue
        task = task_registry.get(tid)
        if task is None:
            raise HTTPException(404, f"任务 {tid} 不存在")
        if task.user_id != current_user.user_id:
            raise HTTPException(403, f"无权访问任务 {tid}")
        if task.status != "completed":
            raise HTTPException(
                400,
                f"任务 {tid} 尚未完成，当前状态：{task.status}",
            )

    task_id = start_plan_generation(body, current_user.user_id)
    return JSONResponse(
        status_code=202,
        content={"status": "success", "data": {"task_id": task_id}},
    )


@router.patch("/plan/{plan_id}/slot/{slot_id}")
def fill_slot(
    plan_id: str,
    slot_id: str,
    body: FillSlotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    task_info = task_registry.get(plan_id)
    if task_info is None or task_info.type != "plan":
        raise HTTPException(404, "计划不存在")
    if task_info.user_id != current_user.user_id:
        raise HTTPException(403, "无权访问该计划")
    if task_info.status != "completed":
        raise HTTPException(400, "计划尚未生成完成")

    template = VideoTemplate.model_validate(task_info.result)

    target_slot = _find_slot_in_template(template, slot_id)
    if target_slot is None:
        raise HTTPException(404, f"Slot {slot_id} 不存在")

    if body.fill_method == FillMethod.manual_input:
        target_slot.value = body.value
        target_slot.status = SlotStatus.filled

    elif body.fill_method == FillMethod.user_upload:
        asset = get_asset_by_id(db, body.value)
        if asset is None:
            raise HTTPException(404, f"素材 {body.value} 不存在")
        if asset.user_id != current_user.user_id:
            raise HTTPException(403, "无权使用该素材")
        target_slot.value = body.value
        target_slot.status = SlotStatus.filled

    elif body.fill_method == FillMethod.ai_generate:
        target_slot.status = SlotStatus.pending

    target_slot.fill_method = body.fill_method

    task_info.result = template.model_dump()

    return {"status": "success", "data": target_slot.model_dump()}
