from contextlib import asynccontextmanager

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session, SQLModel

from app.database import engine
from app.repositories import seed_effects
from app.routers import (
    auth_router,
    effect_router,
    files_router,
    pipeline_router,
    plan_router,
    render_router,
    task_router,
)

load_dotenv(find_dotenv())


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_effects(session)
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """全局 HTTP 异常处理器，根据状态码区分客户端错误和服务器错误"""
    status = "fail" if 400 <= exc.status_code < 500 else "error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": status,
            "message": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """全局请求验证异常处理器，当请求数据不符合预期时返回详细的错误信息"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "fail",
            "message": "请求数据验证失败",
            "data": exc.errors(),
        },
    )


app.include_router(auth_router)
app.include_router(effect_router)
app.include_router(task_router)
app.include_router(pipeline_router)
app.include_router(plan_router)
app.include_router(render_router)
app.include_router(files_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
