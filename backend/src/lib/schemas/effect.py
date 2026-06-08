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
