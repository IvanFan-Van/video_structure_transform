import asyncio
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from core import (
    run_audio_analysis,
    run_compress_task,
    run_script_analysis,
    run_split_task,
    run_visual_analysis,
    save_cover_for_video,
)
from deps import get_current_user, get_video_asset
from lib.video import probe_video
from models import Asset, User, engine
from schemas import AnalyzeRequest, CompressRequest, SplitRequest
from task_registry import task_registry

router = APIRouter(tags=["pipeline"])

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
MAX_ANALYZE_SIZE_MB = int(os.getenv("MAX_ANALYZE_SIZE_MB", "50"))


@router.get("/")
def index():
    return JSONResponse(status_code=200, content={"status": "success", "data": "ok"})


@router.post("/upload")
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

    loop = asyncio.get_running_loop()
    cover_id = await loop.run_in_executor(
        None,
        save_cover_for_video,
        str(filepath),
        current_user.user_id,
        asset_id,
    )

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "data": {
                "asset_id": asset_id,
                "type": "video",
                "path": str(filepath),
                "metadata": meta.to_dict(),
                "cover_image_asset_id": cover_id,
            },
        },
    )


@router.post("/compress")
async def compress_video_endpoint(
    req: CompressRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, source_path = get_video_asset(req.asset_id, current_user)
    source_path_str = str(source_path)

    compressed_asset_id = str(uuid.uuid4())
    compressed_filename = f"{compressed_asset_id}_compressed.mp4"
    compressed_path = VIDEO_STORAGE_DIR / compressed_filename
    VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    task_id = str(uuid.uuid4())
    user_id = current_user.user_id

    info = task_registry.register(
        task_id=task_id,
        user_id=user_id,
        type="compress",
        resource_id=req.asset_id,
        task=None,
    )

    asyncio_task = asyncio.create_task(
        run_compress_task(
            task_id=task_id,
            user_id=user_id,
            source_asset_id=req.asset_id,
            source_path_str=source_path_str,
            compressed_asset_id=compressed_asset_id,
            compressed_path=compressed_path,
            vcodec=req.vcodec,
            crf=req.crf,
            target_v_bitrate=req.target_v_bitrate,
            scale_width=req.scale_width,
            max_fps=req.max_fps,
            acodec=req.acodec,
            target_a_bitrate=req.target_a_bitrate,
        )
    )
    info.task = asyncio_task

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )


@router.post("/analyze-script")
async def analyze_script_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    video_path_str = str(video_path)

    meta = probe_video(video_path)
    file_size_mb = (int(meta.size) if meta.size else 0) / (1024 * 1024)
    if file_size_mb > MAX_ANALYZE_SIZE_MB:
        raise StarletteHTTPException(
            status_code=400,
            detail=(
                f"视频文件过大（{file_size_mb:.1f} MB），"
                f"超过分析上限 {MAX_ANALYZE_SIZE_MB} MB。"
                "请先调用 /compress 压缩后再分析。"
            ),
        )

    task_id = str(uuid.uuid4())

    info = task_registry.register(
        task_id=task_id,
        user_id=current_user.user_id,
        type="analyze-script",
        resource_id=req.asset_id,
        task=None,
    )

    asyncio_task = asyncio.create_task(run_script_analysis(task_id, video_path_str))
    info.task = asyncio_task

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )


@router.post("/analyze-visual")
async def analyze_visual_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    video_path_str = str(video_path)

    meta = probe_video(video_path)
    file_size_mb = (int(meta.size) if meta.size else 0) / (1024 * 1024)
    if file_size_mb > MAX_ANALYZE_SIZE_MB:
        raise StarletteHTTPException(
            status_code=400,
            detail=(
                f"视频文件过大（{file_size_mb:.1f} MB），"
                f"超过分析上限 {MAX_ANALYZE_SIZE_MB} MB。"
                "请先调用 /compress 压缩后再分析。"
            ),
        )

    task_id = str(uuid.uuid4())

    info = task_registry.register(
        task_id=task_id,
        user_id=current_user.user_id,
        type="analyze-visual",
        resource_id=req.asset_id,
        task=None,
    )
    asyncio_task = asyncio.create_task(run_visual_analysis(task_id, video_path_str))
    info.task = asyncio_task

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )


@router.post("/analyze-audio")
async def analyze_audio_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    video_path_str = str(video_path)

    ext = video_path.suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise StarletteHTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}",
        )

    AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    audio_asset_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    info = task_registry.register(
        task_id=task_id,
        user_id=current_user.user_id,
        type="analyze-audio",
        resource_id=req.asset_id,
        task=None,
    )
    info._stream_queue = asyncio.Queue(maxsize=256)

    asyncio_task = asyncio.create_task(
        run_audio_analysis(
            task_id=task_id,
            user_id=current_user.user_id,
            source_asset_id=req.asset_id,
            video_path_str=video_path_str,
            audio_asset_id=audio_asset_id,
            dst_dir=str(AUDIO_STORAGE_DIR),
        )
    )
    info.task = asyncio_task

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )


@router.post("/split")
async def split_video_endpoint(
    req: SplitRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    video_path_str = str(video_path)

    task_id = str(uuid.uuid4())

    info = task_registry.register(
        task_id=task_id,
        user_id=current_user.user_id,
        type="split",
        resource_id=req.asset_id,
        task=None,
    )

    asyncio_task = asyncio.create_task(
        run_split_task(
            task_id=task_id,
            user_id=current_user.user_id,
            source_asset_id=req.asset_id,
            video_path_str=video_path_str,
            use_ai=req.use_ai,
            threshold=req.threshold,
            min_scene_len=req.min_scene_len,
        )
    )
    info.task = asyncio_task

    return JSONResponse(
        status_code=202,
        content={
            "status": "success",
            "data": {"task_id": task_id},
        },
    )
