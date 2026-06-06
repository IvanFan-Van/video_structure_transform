import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core import _STREAM_EOF
from deps import get_current_user
from models import User
from task_registry import task_registry

HEARTBEAT_INTERVAL = 15.0

router = APIRouter(tags=["tasks"])


@router.get("/task/{task_id}")
async def get_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise StarletteHTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    if task_info.user_id != current_user.user_id:
        raise StarletteHTTPException(status_code=403, detail="无权访问该任务")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": task_info.to_dict(),
        },
    )


@router.get("/task/{task_id}/stream")
async def stream_task_endpoint(  # noqa: C901
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise StarletteHTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    if task_info.user_id != current_user.user_id:
        raise StarletteHTTPException(status_code=403, detail="无权访问该任务")

    async def event_stream():
        if task_info.status != "running":
            payload = json.dumps(task_info.to_dict(), ensure_ascii=False)
            yield f"data: {payload}\n\n"
            return

        initial = json.dumps(
            {"task_id": task_id, "status": "running"}, ensure_ascii=False
        )
        yield f"data: {initial}\n\n"

        if task_info._stream_queue is not None:
            queue = task_info._stream_queue
            try:
                while not task_info._event.is_set():
                    try:
                        frame = await asyncio.wait_for(
                            queue.get(), timeout=HEARTBEAT_INTERVAL
                        )
                        if frame is _STREAM_EOF:
                            break
                        payload = json.dumps(frame, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
                    except TimeoutError:
                        yield ": keepalive\n\n"
            except asyncio.CancelledError:
                return

        try:
            while not task_info._event.is_set():
                try:
                    await asyncio.wait_for(
                        asyncio.shield(task_info._event.wait()),
                        timeout=HEARTBEAT_INTERVAL,
                    )
                except TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            return

        payload = json.dumps(task_info.to_dict(), ensure_ascii=False)
        yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/task/{task_id}/cancel")
async def cancel_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise StarletteHTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    if task_info.user_id != current_user.user_id:
        raise StarletteHTTPException(status_code=403, detail="无权操作该任务")

    if task_info.status != "running":
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": "任务已完成，无需取消",
            },
        )

    task_registry.cancel(task_id)
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": f"任务 {task_id} 已发起取消",
        },
    )
