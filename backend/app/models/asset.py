from datetime import datetime

from sqlmodel import Field, SQLModel


class Asset(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, unique=True)
    user_id: str = Field(index=True, foreign_key="user.user_id")
    source_asset_id: str | None = Field(default=None, index=True)
    path: str = Field()
    type: str = Field()
    created_at: datetime = Field(default_factory=datetime.now)
