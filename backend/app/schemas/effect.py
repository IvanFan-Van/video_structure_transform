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
