from pydantic import BaseModel


class RenderRequest(BaseModel):
    plan_id: str
