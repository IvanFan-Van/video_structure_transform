import asyncio
from typing import Any

from .model import TaskInfo

STREAM_EOF = object()
HEARTBEAT_INTERVAL = 15.0


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
            info._event.set()

    def set_error(self, task_id: str, error: str) -> None:
        info = self._tasks.get(task_id)
        if info:
            info.status = "failed"
            info.error = error
            info._event.set()

    def cancel(self, task_id: str) -> bool:
        info = self._tasks.get(task_id)
        if info is None or info.task is None or info.task.done():
            return False
        info.task.cancel()
        info.status = "cancelled"
        info._event.set()
        return True

    def remove(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def list_by_user(self, user_id: str) -> list[TaskInfo]:
        return [info for info in self._tasks.values() if info.user_id == user_id]


task_registry = TaskRegistry()
