from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CompressRequest(BaseModel):
    asset_id: str
    vcodec: str = "libx264"
    crf: int = 32
    target_v_bitrate: str | None = None
    scale_width: int | None = None
    max_fps: int = 30
    acodec: str = "aac"
    target_a_bitrate: str = "96k"


class AnalyzeRequest(BaseModel):
    asset_id: str
