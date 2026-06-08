import os
from pathlib import Path

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.database import engine, get_session
from app.models import Asset, User
from app.repositories import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme), session: Session = Depends(get_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    try:
        payload = jwt.decode(
            token,
            os.environ["SECRET_KEY"],
            algorithms=[os.getenv("ALGORITHM", "HS256")],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="令牌已过期或无效")

    user_id: str | None = payload.get("user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="令牌格式无效")

    user = get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在或已注销")

    return user


def get_video_asset(asset_id: str, current_user: User) -> Asset:
    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_id == asset_id)
        asset = session.exec(statement).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"素材 {asset_id} 不存在")
        if asset.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权访问该素材")
        video_path = Path(asset.path)
        if not video_path.exists():
            raise HTTPException(status_code=500, detail="源文件丢失")
        return asset
