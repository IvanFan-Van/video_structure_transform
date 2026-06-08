from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    asset_id: str
