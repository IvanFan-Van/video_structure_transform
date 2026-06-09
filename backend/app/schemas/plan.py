from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, model_validator

from app.schemas.visual import (
    CameraMovement,
    TextEmphasis,
    TextPosition,
    TransitionType,
)


class SlotType(str, Enum):
    visual_text = "visual_text"
    narration = "narration"
    background_video = "background_video"
    background_image = "background_image"
    bgm = "bgm"


class FillMethod(str, Enum):
    user_upload = "user_upload"
    ai_generate = "ai_generate"


class SlotStatus(str, Enum):
    empty = "empty"
    pending = "pending"
    filled = "filled"


class SlotConstraints(BaseModel):
    max_chars: int | None = None
    position: TextPosition | None = None
    appear_style: str | None = None
    emphasis: TextEmphasis | None = None
    max_duration_sec: float | None = None
    duration_sec: float | None = None
    camera_movement: CameraMovement | None = None


class Slot(BaseModel):
    slot_id: str
    slot_type: SlotType
    description: str
    constraints: SlotConstraints
    status: SlotStatus = SlotStatus.empty
    fill_method: FillMethod | None = None
    value: str | None = None


class TransitionSpec(BaseModel):
    type: TransitionType
    duration: float


class Segment(BaseModel):
    index: int
    stage: str
    start_time: float
    end_time: float
    narrative_intent: str
    hook_type: str | None = None
    cta_type: str | None = None
    emotional_tone: str | None = None
    is_text_frame: bool = False
    camera_movement: CameraMovement | None = None
    effects: list[str] = []
    transition_out: TransitionSpec | None = None
    slots: list[Slot] = []


class BgmSpec(BaseModel):
    genre: str | None = None
    bpm: float | None = None
    mood: str | None = None
    reference_audio_asset_id: str | None = None
    slot: Slot


class VideoTemplate(BaseModel):
    plan_id: str
    created_at: str
    user_id: str
    user_brief: str
    reference_asset_id: str | None = None
    estimated_duration: float
    narrator_perspective: str | None = None
    bgm_spec: BgmSpec
    segments: list[Segment]


class PlanRequest(BaseModel):
    script_task_id: str | None = None
    visual_task_id: str | None = None
    audio_task_id: str | None = None
    effect_task_id: str | None = None
    user_brief: str
    target_duration: float | None = None

    @model_validator(mode="after")
    def check_at_least_one_analysis(self):
        if not self.script_task_id and not self.visual_task_id:
            raise ValueError("script_task_id 和 visual_task_id 至少提供一个")
        return self


class FillSlotRequest(BaseModel):
    fill_method: FillMethod
    value: str | None = None

    @model_validator(mode="after")
    def validate_value(self):
        if self.fill_method == FillMethod.user_upload and not self.value:
            raise ValueError("fill_method 为 user_upload 时必须提供 value（asset_id）")
        return self


# ── LLM 结构化输出模型（instructor response_model）─────────

class RawSlotConstraints(BaseModel):
    max_chars: int | None = None
    position: str | None = None
    appear_style: str | None = None
    emphasis: str | None = None
    max_duration_sec: float | None = None
    duration_sec: float | None = None
    camera_movement: str | None = None


class RawSlot(BaseModel):
    slot_type: str
    description: str
    constraints: RawSlotConstraints | None = None


class RawSegment(BaseModel):
    index: int
    stage: str
    start_time: float
    end_time: float
    narrative_intent: str
    hook_type: str | None = None
    cta_type: str | None = None
    emotional_tone: str | None = None
    is_text_frame: bool = False
    slots: list[RawSlot]


class PlanOutput(BaseModel):
    bgm_mood: str | None = None
    segments: list[RawSegment]
