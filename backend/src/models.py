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

TransitionType = Literal["cut", "dissolve", "wipe", "fade_in", "fade_out"]
CameraMovement = Literal["static", "zoom_in", "zoom_out", "pan", "tilt", "handheld"]
AppearStyle = Literal["fade_in", "pop", "slide", "typewriter"]
TextEmphasis = Literal["zoom", "shake", "color_change", "stroke"]
TextPosition = Literal[
    "top_center",
    "center",
    "bottom_center",
    "overlay_left",
    "overlay_right",
    "full_screen",
]
PacingCategory = Literal["fast", "medium", "slow"]


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
    source_asset_id: str | None = Field(default=None, index=True)
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


class ShotInfo(BaseModel):
    shot_index: int = Field(description="镜头序号，从 1 开始，仅用于展示，非数组下标")
    start_time: float = Field(description="镜头开始时间（秒）")
    end_time: float = Field(description="镜头结束时间（秒）")
    camera_movement: CameraMovement | None = Field(
        default=None,
        description="镜头运动类型：static/zoom_in/zoom_out/pan/tilt/handheld",
    )
    is_text_frame: bool = Field(
        default=False,
        description="该镜头是否为纯文字帧（无视频素材，仅文字+纯色背景）",
    )
    description: str = Field(description="镜头画面简述，10-30字")

    _coerce_nulls = null_str_validator("camera_movement")


class Transition(BaseModel):
    after_shot_index: int = Field(
        description="转场发生在第 N 个镜头之后（对应 shot_index）"
    )
    type: TransitionType = Field(
        description="转场类型：cut/dissolve/wipe/fade_in/fade_out"
    )
    duration: float = Field(description="转场持续时长（秒），硬切为 0.0")


class TextElement(BaseModel):
    text: str = Field(description="文字内容")
    position: TextPosition | None = Field(
        default=None,
        description="屏幕位置：top_center/center/bottom_center/overlay_left/overlay_right/full_screen",
    )
    appear_style: AppearStyle | None = Field(
        default=None,
        description="出现动效：fade_in/pop/slide/typewriter",
    )
    appear_time: float = Field(description="文字出现时间（秒）")
    disappear_time: float = Field(description="文字消失时间（秒）")
    emphasis: TextEmphasis | None = Field(
        default=None,
        description="强调动效：zoom/shake/color_change/stroke",
    )

    _coerce_nulls = null_str_validator("position", "appear_style", "emphasis")


class TextDensityPoint(BaseModel):
    time: float
    text_count: int


class PacingSummary(BaseModel):
    avg_shot_duration: float = Field(description="平均镜头时长（秒）")
    pacing_category: PacingCategory = Field(
        description="节奏档位：fast(<2s) / medium(2-4s) / slow(>4s)"
    )
    acceleration_points: list[float] = Field(
        default_factory=list,
        description="节奏骤然加快的时间点列表（秒），通常对应高潮段入口",
    )


class VideoVisualAnalysis(BaseModel):
    total_duration: float = Field(description="视频总时长（秒）")
    pacing: PacingSummary = Field(description="全局节奏摘要")
    shots: list[ShotInfo] = Field(description="镜头列表，按时间顺序排列")
    transitions: list[Transition] = Field(
        default_factory=list,
        description="转场列表，长度应为 len(shots)-1",
    )
    text_elements: list[TextElement] = Field(
        default_factory=list,
        description="独立文字时间轴，元素可跨镜头，不嵌套在 ShotInfo 内",
    )
    text_density_curve: list[TextDensityPoint] = Field(
        default_factory=list,
        description="文字密度曲线，由后处理代码计算填充",
    )


def compute_text_density_curve(
    text_elements: list[TextElement],
) -> list[TextDensityPoint]:
    events: list[tuple[float, int]] = []
    for elem in text_elements:
        events.append((elem.appear_time, +1))
        events.append((elem.disappear_time, -1))
    events.sort(key=lambda x: x[0])

    points: list[TextDensityPoint] = []
    count = 0
    for time, delta in events:
        count += delta
        points.append(TextDensityPoint(time=time, text_count=max(count, 0)))
    return points


class CutPoint(BaseModel):
    timestamp: float = Field(description="切割时间点（秒）")
    reason: str = Field(description="切割原因")


class CutPointList(BaseModel):
    cut_points: list[CutPoint] = Field(description="所有切割时间点列表")


class SegmentInfo(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    duration: float
    cut_score: float | None = None
    reason: str | None = None


class ClipAssetInfo(BaseModel):
    asset_id: str
    index: int
    path: str
    metadata: dict
    cover_image_asset_id: str | None = None


class SplitResult(BaseModel):
    source_asset_id: str
    method: str
    total_segments: int
    segments: list[SegmentInfo]
    clip_assets: list[ClipAssetInfo]


engine = create_engine("sqlite:///database.db", echo=False)
SQLModel.metadata.create_all(engine)

try:
    with engine.connect() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE asset ADD COLUMN source_asset_id VARCHAR"
        )
        conn.commit()
except Exception:
    pass
