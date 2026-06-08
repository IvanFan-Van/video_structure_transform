from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.database import get_session
from app.schemas import LoginRequest, RegisterRequest
from app.services import login_user, register_user

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(req: RegisterRequest, session: Session = Depends(get_session)):
    user = register_user(session, req.email, req.password)
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
async def login(req: LoginRequest, session: Session = Depends(get_session)):
    data = login_user(session, req.email, req.password)
    return JSONResponse(
        status_code=200,
        content={"status": "success", "data": data},
    )
