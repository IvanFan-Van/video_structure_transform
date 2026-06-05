import asyncio
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from audio import extract_bgm, stream_audio_features
from core import analyze_video_script_async
from models import Asset, User, engine
from task_registry import task_registry
from utils import create_access_token, hash_password, verify_password
from video import compress_video_async, probe_video

load_dotenv(find_dotenv())

STORAGE_DIR = Path("storage")
VIDEO_STORAGE_DIR = STORAGE_DIR / "videos"
AUDIO_STORAGE_DIR = STORAGE_DIR / "audios"
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
    "video/x-flv",
    "video/x-ms-wmv",
}

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if 400 <= exc.status_code < 500:
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "fail", "message": exc.detail},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )


async def get_current_user(token: str | None = Depends(oauth2_scheme)):
    if token is None:
        raise StarletteHTTPException(status_code=401, detail="未提供认证令牌")

    try:
        payload = jwt.decode(
            token,
            os.environ["SECRET_KEY"],
            algorithms=[os.getenv("ALGORITHM", "HS256")],
        )
    except JWTError:
        raise StarletteHTTPException(status_code=401, detail="令牌已过期或无效")

    user_id: str | None = payload.get("user_id", None)
    if user_id is None:
        raise StarletteHTTPException(status_code=401, detail="令牌格式无效")

    with Session(engine) as session:
        statement = select(User).where(User.user_id == user_id)
        user = session.exec(statement).first()
        if user is None:
            raise StarletteHTTPException(status_code=401, detail="用户不存在或已注销")

        return user


@app.get("/")
def index():
    return JSONResponse(status_code=200, content={"status": "success", "data": "ok"})


@app.post("/register")
async def register(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email:
        raise StarletteHTTPException(status_code=400, detail="邮箱不能为空")
    if not password:
        raise StarletteHTTPException(status_code=400, detail="密码不能为空")

    with Session(engine) as session:
        statement = select(User).where(User.email == data["email"])
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


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email", None)
    password = data.get("password", None)

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


@app.post("/upload")
async def upload_video_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "upload.mp4").suffix.lower()
    if (
        ext not in ALLOWED_VIDEO_EXTENSIONS
        and file.content_type not in ALLOWED_VIDEO_MIME_TYPES
    ):
        raise StarletteHTTPException(status_code=400, detail="不支持的文件类型")

    VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    asset_id = str(uuid.uuid4())
    filename = f"{asset_id}{ext}"
    filepath = VIDEO_STORAGE_DIR / filename

    content = await file.read()
    filepath.write_bytes(content)

    try:
        meta = probe_video(filepath)
    except Exception as e:
        filepath.unlink(missing_ok=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "视频元数据探测失败",
                "data": {"code": "PROBE_FAILED", "details": str(e)},
            },
        )

    with Session(engine) as session:
        asset = Asset(
            asset_id=asset_id,
            user_id=current_user.user_id,
            path=str(filepath),
            type="video",
        )
        session.add(asset)
        session.commit()

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "data": {
                "asset_id": asset_id,
                "type": "video",
                "path": str(filepath),
                "metadata": meta.to_dict(),
            },
        },
    )


@app.post("/compress")
async def compress_video_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    data = await request.json()
    asset_id = data.get("asset_id")

    if not asset_id:
        raise StarletteHTTPException(status_code=400, detail="缺少 asset_id 参数")

    compressed_asset_id = str(uuid.uuid4())
    compressed_filename = f"{compressed_asset_id}_compressed.mp4"
    compressed_path = VIDEO_STORAGE_DIR / compressed_filename
    VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    vcodec = data.get("vcodec", "libx264")
    crf = data.get("crf", 32)
    target_v_bitrate = data.get("target_v_bitrate")
    scale_width = data.get("scale_width")
    max_fps = data.get("max_fps", 30)
    acodec = data.get("acodec", "aac")
    target_a_bitrate = data.get("target_a_bitrate", "96k")

    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_id == asset_id)
        source_asset = session.exec(statement).first()

        if not source_asset:
            raise StarletteHTTPException(
                status_code=404, detail=f"素材 {asset_id} 不存在"
            )

        source_path = Path(source_asset.path)
        if not source_path.exists():
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "源文件丢失",
                    "data": {
                        "code": "FILE_MISSING",
                        "details": f"素材记录存在但文件丢失：{source_asset.path}",
                    },
                },
            )

        source_path_str = str(source_path)

    task_id = str(uuid.uuid4())
    user_id = current_user.user_id

    async def _run_compress():
        try:
            output = await compress_video_async(
                source_path_str,
                compressed_path,
                vcodec=vcodec,
                crf=crf,
                target_v_bitrate=target_v_bitrate,
                scale_width=scale_width,
                max_fps=max_fps,
                acodec=acodec,
                target_a_bitrate=target_a_bitrate,
            )
            compressed_meta = probe_video(output)

            with Session(engine) as session:
                compressed_asset = Asset(
                    asset_id=compressed_asset_id,
                    user_id=user_id,
                    path=str(compressed_path),
                    type="video",
                )
                session.add(compressed_asset)
                session.commit()

            task_registry.set_result(
                task_id,
                {
                    "asset_id": compressed_asset_id,
                    "source_asset_id": asset_id,
                    "type": "video",
                    "path": str(compressed_path),
                    "metadata": compressed_meta.to_dict(),
                },
            )
        except asyncio.CancelledError:
            compressed_path.unlink(missing_ok=True)
        except Exception as e:
            compressed_path.unlink(missing_ok=True)
            task_registry.set_error(task_id, str(e))

    asyncio_task = asyncio.create_task(_run_compress())
    task_registry.register(
        task_id=task_id,
        user_id=user_id,
        type="compress",
        resource_id=asset_id,
        task=asyncio_task,
    )

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )


@app.post("/analyze-script")
async def analyze_script_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    data = await request.json()
    asset_id = data.get("asset_id")

    if not asset_id:
        raise StarletteHTTPException(status_code=400, detail="缺少 asset_id 参数")

    # 检查素材存在性和访问权限，并获取文件路径
    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_id == asset_id)
        asset = session.exec(statement).first()

        if not asset:
            raise StarletteHTTPException(
                status_code=404, detail=f"素材 {asset_id} 不存在"
            )

        if asset.user_id != current_user.user_id:
            raise StarletteHTTPException(status_code=403, detail="无权访问该素材")

        video_path = Path(asset.path)
        if not video_path.exists():
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "源文件丢失",
                    "data": {
                        "code": "FILE_MISSING",
                        "details": str(asset.path),
                    },
                },
            )

        video_path_str = str(video_path)

    task_id = str(uuid.uuid4())

    async def _run_analyze():
        try:
            structure = await analyze_video_script_async(video_path_str)
            task_registry.set_result(task_id, structure.model_dump())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            task_registry.set_error(task_id, str(e))

    asyncio_task = asyncio.create_task(_run_analyze())
    task_registry.register(
        task_id=task_id,
        user_id=current_user.user_id,
        type="analyze-script",
        resource_id=asset_id,
        task=asyncio_task,
    )

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )


# TODO: SSE 替代轮询 — 新增 GET /task/{task_id}/stream
#       await task_info._event.wait()
#       首次连接立即发送当前状态，状态变更后推送 finished 状态并关闭连接
#       保留 GET /task/{task_id} 作为一次性查询/降级回退


@app.get("/task/{task_id}")
async def get_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise StarletteHTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    if task_info.user_id != current_user.user_id:
        raise StarletteHTTPException(status_code=403, detail="无权访问该任务")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": task_info.to_dict(),
        },
    )


@app.post("/task/{task_id}/cancel")
async def cancel_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_info = task_registry.get(task_id)
    if task_info is None:
        raise StarletteHTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    if task_info.user_id != current_user.user_id:
        raise StarletteHTTPException(status_code=403, detail="无权操作该任务")

    if task_info.status != "running":
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": "任务已完成，无需取消",
            },
        )

    task_registry.cancel(task_id)
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": f"任务 {task_id} 已发起取消",
        },
    )


@app.get("/analyze-audio")
async def analyze_audio_endpoint(  # noqa: C901
    asset_id: str = Query(..., description="素材 ID"),
    current_user: User = Depends(get_current_user),
):
    if not asset_id:
        raise StarletteHTTPException(status_code=400, detail="缺少 asset_id 参数")

    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_id == asset_id)
        video_asset = session.exec(statement).first()
        if not video_asset:
            raise StarletteHTTPException(
                status_code=404, detail=f"素材 {asset_id} 不存在"
            )
        if video_asset.user_id != current_user.user_id:
            raise StarletteHTTPException(status_code=403, detail="无权访问该素材")
        video_path = Path(video_asset.path)
        if not video_path.exists():
            raise StarletteHTTPException(status_code=500, detail="源文件丢失")

    ext = video_path.suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise StarletteHTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}",
        )

    AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    audio_asset_id = str(uuid.uuid4())
    bgm_path = extract_bgm(str(video_path), AUDIO_STORAGE_DIR, audio_asset_id)

    with Session(engine) as session:
        bgm_asset = Asset(
            asset_id=audio_asset_id,
            user_id=current_user.user_id,
            path=str(bgm_path),
            type="audio",
        )
        session.add(bgm_asset)
        session.commit()

    async def event_stream():
        _sentinel = object()
        loop = asyncio.get_running_loop()
        gen = stream_audio_features(str(bgm_path), audio_asset_id=audio_asset_id)

        try:
            while True:
                frame = await loop.run_in_executor(None, next, gen, _sentinel)
                if frame is _sentinel:
                    break
                payload = json.dumps(frame, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except asyncio.CancelledError:
            return
        except Exception as exc:
            error_payload = json.dumps(
                {"error": True, "message": str(exc)}, ensure_ascii=False
            )
            yield f"event: error\ndata: {error_payload}\n\n"
        finally:
            gen.close()  # type: ignore[attr-defined]

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
