from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from app.deps import get_current_user
from app.models import User
from app.services.task import build_event_stream, cancel_task, get_task_for_user

HEARTBEAT_INTERVAL = 15.0

router = APIRouter(tags=["tasks"])


SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.get("/task/{task_id}/stream")
async def stream_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_info = get_task_for_user(task_id, current_user)

    return StreamingResponse(
        build_event_stream(task_id, task_info),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/task/{task_id}/cancel")
async def cancel_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": cancel_task(task_id, current_user),
        },
    )
