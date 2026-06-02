from datetime import datetime

from sqlmodel import Field, SQLModel, create_engine


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    password_hash: str | None = Field()
    created_at: datetime = Field(default_factory=datetime.now)


class UserOAuth(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, foreign_key="user.user_id")
    provider: str = Field(index=True)
    provider_id: str = Field(index=True)


class Asset(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, unique=True)
    user_id: str = Field(index=True, foreign_key="user.user_id")
    path: str = Field()
    type: str = Field()
    created_at: datetime = Field(default_factory=datetime.now)


engine = create_engine("sqlite:///database.db", echo=False)
SQLModel.metadata.create_all(engine)
