import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlmodel import Session

from models import User
from repositories import create_user, get_user_by_email
from utils import create_access_token, hash_password, verify_password


def register_user(session: Session, email: str, password: str) -> User:
    if get_user_by_email(session, email):
        raise HTTPException(status_code=400, detail=f"邮箱 {email} 已经注册")

    user = User(
        user_id=str(uuid.uuid4()), email=email, password_hash=hash_password(password)
    )

    return create_user(session, user)


def login_user(session: Session, email: str, password: str) -> dict:
    user = get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=404, detail=f"邮箱 {email} 未注册")

    if user.password_hash is None:
        raise HTTPException(
            status_code=400,
            detail="该账号通过 Google 登录注册，请使用 Google 登录",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="密码错误")

    expires_delta = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)))
    token = create_access_token(
        data={"user_id": user.user_id, "email": user.email},
        expires_delta=expires_delta,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": (datetime.now(UTC) + expires_delta).strftime("%Y-%m-%d %H:%M:%S"),
        "user": {
            "user_id": user.user_id,
            "email": user.email,
        },
    }
