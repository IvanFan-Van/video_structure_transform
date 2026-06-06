import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from models import User, engine
from schemas import LoginRequest, RegisterRequest
from utils import create_access_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(req: RegisterRequest):
    email = req.email
    password = req.password

    if not email:
        raise StarletteHTTPException(status_code=400, detail="邮箱不能为空")
    if not password:
        raise StarletteHTTPException(status_code=400, detail="密码不能为空")

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        result = session.exec(statement).first()
        if result:
            raise StarletteHTTPException(status_code=400, detail=f"邮箱 {email} 已注册")

        user = User(
            user_id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_password(password),
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "data": {
                    "user_id": user.user_id,
                    "email": user.email,
                },
            },
        )


@router.post("/login")
async def login(req: LoginRequest):
    email = req.email
    password = req.password

    if not email:
        raise StarletteHTTPException(status_code=400, detail="邮箱不能为空")
    if not password:
        raise StarletteHTTPException(status_code=400, detail="密码不能为空")

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()

        if not user:
            raise StarletteHTTPException(status_code=404, detail=f"邮箱 {email} 未注册")

        if user.password_hash is None:
            raise StarletteHTTPException(
                status_code=400,
                detail="该账号通过 Google 登录注册，请使用 Google 登录",
            )

        if not verify_password(password, user.password_hash):
            raise StarletteHTTPException(status_code=401, detail="密码错误")

        expires_delta = timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
        )
        token = create_access_token(
            data={"user_id": user.user_id, "email": user.email},
            expires_delta=expires_delta,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "access_token": token,
                    "token_type": "bearer",
                    "expires_at": (datetime.now(UTC) + expires_delta).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "user": {
                        "user_id": user.user_id,
                        "email": user.email,
                    },
                },
            },
        )
