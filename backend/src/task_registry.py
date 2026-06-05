import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

TaskStatus = Literal["running", "completed", "failed", "cancelled"]


@dataclass
class TaskInfo:
    task_id: str
    user_id: str
    type: str
    resource_id: str
    status: TaskStatus = "running"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    task: asyncio.Task | None = None
    result: Any = None
    error: str | None = None
    # TODO: SSE 替代轮询 — 添加 _event: asyncio.Event
    #       field(default_factory=asyncio.Event)
    #       状态变更为 completed/failed/cancelled 时 set event
    #       SSE 端点 (GET /task/{task_id}/stream) await 此 event 后推送

    def to_dict(self) -> dict:
        base: dict = {
            "task_id": self.task_id,
            "type": self.type,
            "resource_id": self.resource_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
        if self.status == "completed":
            base["result"] = self.result
        if self.status == "failed":
            base["error"] = self.error
        return base


class TaskRegistry:
    def __init__(self):
        self._tasks: dict[str, TaskInfo] = {}

    def register(
        self,
        task_id: str,
        user_id: str,
        type: str,
        resource_id: str,
        task: asyncio.Task | None = None,
    ) -> TaskInfo:
        info = TaskInfo(
            task_id=task_id,
            user_id=user_id,
            type=type,
            resource_id=resource_id,
            task=task,
        )
        self._tasks[task_id] = info
        return info

    def get(self, task_id: str) -> TaskInfo | None:
        return self._tasks.get(task_id)

    def set_result(self, task_id: str, result: Any) -> None:
        info = self._tasks.get(task_id)
        if info:
            info.status = "completed"
            info.result = result
            # TODO: SSE — info._event.set()

    def set_error(self, task_id: str, error: str) -> None:
        info = self._tasks.get(task_id)
        if info:
            info.status = "failed"
            info.error = error
            # TODO: SSE — info._event.set()

    def cancel(self, task_id: str) -> bool:
        info = self._tasks.get(task_id)
        if info is None or info.task is None or info.task.done():
            return False
        info.task.cancel()
        info.status = "cancelled"
        # TODO: SSE — info._event.set()
        return True

    def remove(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def list_by_user(self, user_id: str) -> list[TaskInfo]:
        return [info for info in self._tasks.values() if info.user_id == user_id]


task_registry = TaskRegistry()
