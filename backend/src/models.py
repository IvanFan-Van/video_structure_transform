from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator
from sqlmodel import Field, SQLModel, create_engine


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
    emotional_tone: str | None = Field(
        default=None,
        description="情绪基调：positive / negative / neutral / suspenseful",
    )
    hook_type: str | None = Field(
        default=None,
        description="钩子类型（仅 hook）：pain_point/suspense/result_first"
        "/counter_intuitive/number_shock/identity_lock/scene_immersion/contrast_flip",
    )
    cta_type: str | None = Field(
        default=None,
        description="行动号召类型（仅 cta）：follow/like_collect/comment/"
        "purchase/discount_hook/dm_funnel/share_spread/challenge",
    )


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

    @model_validator(mode="after")
    def coerce_null_narrator_perspective_note(self):
        if self.narrator_perspective_note == "null":
            object.__setattr__(self, "narrator_perspective_note", None)
        return self


engine = create_engine("sqlite:///database.db", echo=False)
SQLModel.metadata.create_all(engine)
