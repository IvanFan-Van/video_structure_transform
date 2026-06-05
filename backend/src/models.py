from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel, create_engine

EmotionalTone = Literal["positive", "negative", "neutral", "suspenseful"]
HookType = Literal[
    "pain_point",
    "suspense",
    "result_first",
    "counter_intuitive",
    "number_shock",
    "identity_lock",
    "scene_immersion",
    "contrast_flip",
]
CtaType = Literal[
    "follow",
    "like_collect",
    "comment",
    "purchase",
    "discount_hook",
    "dm_funnel",
    "share_spread",
    "challenge",
]


def null_str_validator(*field_names: str):
    @field_validator(*field_names, mode="before")
    @classmethod
    def _coerce_null_strings(cls, v):
        if v == "null":
            return None
        return v

    return _coerce_null_strings


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    password_hash: str | None = Field()
    created_at: datetime = Field(default_factory=datetime.now)


class UserOAuth(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, foreign_key="user.user_id")
    provider: str = Field(index=True)
    provider_id: str = Field(index=True)


class Asset(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, unique=True)
    user_id: str = Field(index=True, foreign_key="user.user_id")
    path: str = Field()
    type: str = Field()
    created_at: datetime = Field(default_factory=datetime.now)


class ElementContent(BaseModel):
    """单个叙事阶段的内容与时间范围"""

    visual_text: str = Field(
        default="",
        description="该段落画面上的核心叙事文字（不含水印、UI等无关文字）",
    )
    audio_text: str = Field(
        default="",
        description="该段落的音频文本：旁白/台词/对话（纯BGM则返回空字符串）",
    )
    start_time: float = Field(
        default=0,
        description="该阶段在视频中的开始时间（秒）",
    )
    end_time: float = Field(
        default=0,
        description="该阶段在视频中的结束时间（秒）",
    )
    emotional_tone: EmotionalTone | None = Field(
        default=None,
        description="情绪基调：positive / negative / neutral / suspenseful",
    )
    hook_type: HookType | None = Field(
        default=None,
        description="钩子类型（仅 hook）：pain_point/suspense/result_first"
        "/counter_intuitive/number_shock/identity_lock/scene_immersion/contrast_flip",
    )
    cta_type: CtaType | None = Field(
        default=None,
        description="行动号召类型（仅 cta）：follow/like_collect/comment/"
        "purchase/discount_hook/dm_funnel/share_spread/challenge",
    )

    _coerce_nulls = null_str_validator("emotional_tone", "hook_type", "cta_type")


class StageContainer(BaseModel):
    """6 个叙事阶段的容器"""

    hook: ElementContent | None = Field(default=None)
    setup: ElementContent | None = Field(default=None)
    story: ElementContent | None = Field(default=None)
    insight: ElementContent | None = Field(default=None)
    cta: ElementContent | None = Field(default=None)
    outro: ElementContent | None = Field(default=None)


class VideoStructure(BaseModel):
    """视频按叙事结构的完整拆解结果"""

    narrator_perspective: (
        Literal["first_person", "second_person", "third_person", "mixed"] | None
    ) = Field(
        default=None,
        description="全局叙述视角：first_person / second_person / third_person / mixed",
    )
    narrator_perspective_note: str | None = Field(
        default=None,
        description="仅 mixed 时的视角切换说明，其余为 null",
    )
    stages: StageContainer = Field(
        default_factory=StageContainer,
        description="6 个叙事阶段的拆解内容",
    )

    _coerce_nulls = null_str_validator(
        "narrator_perspective_note", "narrator_perspective"
    )


engine = create_engine("sqlite:///database.db", echo=False)
SQLModel.metadata.create_all(engine)
