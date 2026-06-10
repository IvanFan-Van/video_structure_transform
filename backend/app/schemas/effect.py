from pydantic import BaseModel, Field


class EffectMatch(BaseModel):
    name: str = Field(
        description="Effect name, must exactly match a name from the effects library"
    )
    evidence: str = Field(
        description=(
            "Specific visual phenomenon observed in the video that "
            "supports this match, max 20 words"
        )
    )


class EffectAnalysisResult(BaseModel):
    observations: str = Field(
        description=(
            "Free-form description of all visual phenomena observed in the video, "
            "written before consulting the effects library"
        )
    )
    effects: list[EffectMatch] = Field(
        description="Matched effects, only include effects with clear visual evidence"
    )


class UpdateEffectRequest(BaseModel):
    task_id: str = Field(description="/analyze-effect 返回的 task_id")
    effects: list[EffectMatch] = Field(
        description="用户校正后的完整 effects 列表（替换原有列表）"
    )


class EffectParamDetail(BaseModel):
    effect_name: str = Field(
        description="效果名称，如 Typewriter、BlurReveal"
    )
    remocn_component: str = Field(
        description="kebab-case 组件 ID，如 typewriter、blur-reveal"
    )
    remocn_props: dict = Field(
        default_factory=dict,
        description="组件参数键值对，如 {'fontSize': 64, 'charsPerSecond': 15}",
    )
    timing_start: float = Field(description="效果开始时间（秒）")
    timing_duration: float = Field(description="效果持续时长（秒）")
    applies_to: str = Field(
        description="目标 stage（hook/story/cta/...）或 slot 类型"
    )
    evidence: str = Field(description="视觉证据，基于观察的现象")


class EffectParamAnalysisRequest(BaseModel):
    asset_id: str = Field(description="参考视频的 asset_id")
    effects: list[str] = Field(
        description="用户确认后的效果名称列表，如 ['Typewriter', 'BlurReveal']"
    )


class EffectParamAnalysisResult(BaseModel):
    observations: str = Field(
        description="Step 1 自由观察的所有视觉现象描述"
    )
    param_set: list[EffectParamDetail] = Field(
        description="每个选中效果的参数化匹配结果"
    )
