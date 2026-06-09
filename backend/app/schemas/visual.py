from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.utils import null_str_validator

TransitionType = Literal[
    "cut",
    "dissolve",
    "wipe",
    "fade_in",
    "fade_out",
    "slide",
    "zoom",
    "glitch",
    "rgb_split",
]
CameraMovement = Literal["static", "zoom_in", "zoom_out", "pan", "tilt", "handheld"]
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
    appear_time: float = Field(description="文字出现时间（秒）")
    disappear_time: float = Field(description="文字消失时间（秒）")

    _coerce_nulls = null_str_validator("position")


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
