from datetime import datetime

from pydantic import BaseModel
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


class ElementContent(BaseModel):
    """单个叙事阶段的内容与时间范围"""

    visual_text: str = Field(
        default="",
        description="该段落画面上的核心叙事文字（不含水印、UI等无关文字）",
    )
    audio_text: str = Field(
        default="",
        description="该段落的音频文本：旁白/台词/对话（纯BGM则返回空字符串）",
    )
    start_time: float = Field(
        default=0,
        description="该阶段在视频中的开始时间（秒）",
    )
    end_time: float = Field(
        default=0,
        description="该阶段在视频中的结束时间（秒）",
    )


class VideoStructure(BaseModel):
    """视频按叙事结构的完整拆解结果"""

    hook: ElementContent | None = Field(
        default=None,
        description="钩子：开头抛出问题/悬念/冲突，抓住观众注意力（通常在前 5-8 秒）",
    )
    setup: ElementContent | None = Field(
        default=None,
        description="铺垫：交代背景、设定情境、介绍前提",
    )
    story: ElementContent | None = Field(
        default=None,
        description="正文：故事主体/事件叙述/观点展开，通常占据视频最大篇幅",
    )
    insight: ElementContent | None = Field(
        default=None,
        description="金句：核心观点/感悟/反转，点睛之笔和传播核心",
    )
    cta: ElementContent | None = Field(
        default=None,
        description="行动号召：引导点赞/关注/转发/评论等互动",
    )
    outro: ElementContent | None = Field(
        default=None,
        description="结尾：收束/道别或落版文字",
    )


engine = create_engine("sqlite:///database.db", echo=False)
SQLModel.metadata.create_all(engine)
