import asyncio
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlmodel import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from core import (
    run_audio_analysis,
    run_compress_task,
    run_effect_analysis,
    run_script_analysis,
    run_split_task,
    run_visual_analysis,
)
from lib.video import probe_video
from models import Asset, User
from repositories import create_asset
from schemas import CompressRequest, SplitRequest
from tasks import task_registry

from .cover import extract_cover_for_video

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
STORAGE_DIR = Path("storage")
VIDEO_STORAGE_DIR = STORAGE_DIR / "videos"
AUDIO_STORAGE_DIR = STORAGE_DIR / "audios"
MAX_ANALYZE_SIZE_MB = int(os.getenv("MAX_ANALYZE_SIZE_MB", "50"))


def check_analysis_size_limit(meta) -> None:
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


def _register_and_launch(
    task_id: str,
    user_id: str,
    task_type: str,
    resource_id: str,
    coro,
    stream_queue: asyncio.Queue | None = None,
) -> None:
    info = task_registry.register(
        task_id=task_id,
        user_id=user_id,
        type=task_type,
        resource_id=resource_id,
        task=None,
    )
    if stream_queue is not None:
        info._stream_queue = stream_queue
    asyncio_task = asyncio.create_task(coro)
    info.task = asyncio_task


async def upload_video(session: Session, user: User, file: UploadFile) -> dict:
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
        raise StarletteHTTPException(
            status_code=500,
            detail=f"视频元数据探测失败: {e}",
        )

    asset = Asset(
        asset_id=asset_id,
        user_id=user.user_id,
        path=str(filepath),
        type="video",
    )
    create_asset(session, asset)

    loop = asyncio.get_running_loop()
    cover_id = await loop.run_in_executor(
        None,
        extract_cover_for_video,
        str(filepath),
        user.user_id,
        asset_id,
    )

    return {
        "asset_id": asset_id,
        "type": "video",
        "path": str(filepath),
        "metadata": meta.to_dict(),
        "cover_image_asset_id": cover_id,
    }


def start_compress_task(
    user: User, source_asset_id: str, source_path_str: str, req: CompressRequest
) -> str:
    compressed_asset_id = str(uuid.uuid4())
    compressed_filename = f"{compressed_asset_id}_compressed.mp4"
    compressed_path = VIDEO_STORAGE_DIR / compressed_filename
    VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    task_id = str(uuid.uuid4())
    _register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="compress",
        resource_id=source_asset_id,
        coro=run_compress_task(
            task_id=task_id,
            user_id=user.user_id,
            source_asset_id=source_asset_id,
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
        ),
    )
    return task_id


def start_script_analysis(user: User, video_path_str: str, asset_id: str) -> str:
    task_id = str(uuid.uuid4())
    _register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-script",
        resource_id=asset_id,
        coro=run_script_analysis(task_id, video_path_str),
    )
    return task_id


def start_visual_analysis(user: User, video_path_str: str, asset_id: str) -> str:
    task_id = str(uuid.uuid4())
    _register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-visual",
        resource_id=asset_id,
        coro=run_visual_analysis(task_id, video_path_str),
    )
    return task_id


def start_audio_analysis(
    user: User, video_path_str: str, source_asset_id: str
) -> tuple[str, str]:
    AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    audio_asset_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    _register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-audio",
        resource_id=source_asset_id,
        coro=run_audio_analysis(
            task_id=task_id,
            user_id=user.user_id,
            source_asset_id=source_asset_id,
            video_path_str=video_path_str,
            audio_asset_id=audio_asset_id,
            dst_dir=str(AUDIO_STORAGE_DIR),
        ),
        stream_queue=asyncio.Queue(maxsize=256),
    )
    return task_id, audio_asset_id


def start_split_task(
    user: User,
    video_path_str: str,
    source_asset_id: str,
    req: SplitRequest,
) -> str:
    task_id = str(uuid.uuid4())
    _register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="split",
        resource_id=source_asset_id,
        coro=run_split_task(
            task_id=task_id,
            user_id=user.user_id,
            source_asset_id=source_asset_id,
            video_path_str=video_path_str,
            use_ai=req.use_ai,
            threshold=req.threshold,
            min_scene_len=req.min_scene_len,
        ),
    )
    return task_id


def start_effect_analysis(user: User, video_path_str: str, asset_id: str) -> str:
    task_id = str(uuid.uuid4())
    _register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-effect",
        resource_id=asset_id,
        coro=run_effect_analysis(task_id, video_path_str),
    )
    return task_id
