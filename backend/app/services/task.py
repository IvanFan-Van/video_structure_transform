import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import HTTPException

from app.models import User
from app.tasks.model import STREAM_EOF
from app.tasks.registry import HEARTBEAT_INTERVAL, task_registry


def register_and_launch(
    task_id: str,
    user_id: str,
    task_type: str,
    resource_id: str,
    coro,
    stream_queue: asyncio.Queue | None = None,
) -> None:
    info = task_registry.register(
        task_id=task_id,
        user_id=user_id,
        type=task_type,
        resource_id=resource_id,
        task=None,
    )
    if stream_queue is not None:
        info._stream_queue = stream_queue
    asyncio_task = asyncio.create_task(coro)
    info.task = asyncio_task


def get_task_for_user(task_id: str, current_user: User):
    """查找任务并做权限校验，失败直接抛 HTTPException"""
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    if task_info.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问该任务")
    return task_info


async def build_event_stream(task_id: str, task_info) -> AsyncGenerator[str, None]:
    """生成 SSE 帧序列，供 StreamingResponse 消费"""

    # 任务已结束：直接返回最终状态
    if task_info.status != "running":
        yield f"data: {json.dumps(task_info.to_dict(), ensure_ascii=False)}\n\n"
        return

    # 任务运行中：先发一帧 running 状态
    yield f"data: {json.dumps({'task_id': task_id, 'status': 'running'}, ensure_ascii=False)}\n\n"

    # 阶段一：消费 stream_queue（有实时帧时）
    if task_info._stream_queue is not None:
        try:
            while not task_info._event.is_set():
                try:
                    frame = await asyncio.wait_for(
                        task_info._stream_queue.get(),
                        timeout=HEARTBEAT_INTERVAL,
                    )
                    if frame is STREAM_EOF:
                        break
                    yield f"data: {json.dumps(frame, ensure_ascii=False)}\n\n"
                except TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            return

    # 阶段二：等待任务完成事件
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

    # 发送最终结果帧
    yield f"data: {json.dumps(task_info.to_dict(), ensure_ascii=False)}\n\n"


def cancel_task(task_id: str, current_user: User) -> str:
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    if task_info.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权操作该任务")

    if task_info.status == "running":
        task_registry.cancel(task_id)
        return f"任务 {task_id} 已成功取消"
    else:
        return f"任务 {task_id} 已经 {task_info.status}，无需取消"
