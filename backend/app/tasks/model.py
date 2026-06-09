import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

TaskStatus = Literal["running", "completed", "failed", "cancelled"]
STREAM_EOF = object()


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
    _event: asyncio.Event = field(default_factory=asyncio.Event)
    _stream_queue: asyncio.Queue | None = None

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
