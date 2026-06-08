from pydantic import BaseModel, Field


class SplitRequest(BaseModel):
    asset_id: str
    use_ai: bool = False
    threshold: float = 25.0
    min_scene_len: int = 15


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
