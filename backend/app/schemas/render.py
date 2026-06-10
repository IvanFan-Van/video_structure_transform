from pydantic import BaseModel


class RenderRequest(BaseModel):
    plan_id: str
    style: str = "standard"


class PreviewRequest(BaseModel):
    plan_id: str
