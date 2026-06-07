from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from database import get_session
from deps import get_current_user, get_video_asset
from lib.video import probe_video
from models import User
from schemas import AnalyzeRequest, CompressRequest, SplitRequest
from services import (
    check_analysis_size_limit,
    start_audio_analysis,
    start_compress_task,
    start_script_analysis,
    start_split_task,
    start_visual_analysis,
    upload_video,
)

router = APIRouter(tags=["pipeline"])

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}


@router.get("/")
def index():
    return JSONResponse(status_code=200, content={"status": "success", "data": "ok"})


@router.post("/upload")
async def upload_video_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    result = await upload_video(session, current_user, file)
    return JSONResponse(status_code=201, content={"status": "success", "data": result})


@router.post("/compress")
async def compress_video_endpoint(
    req: CompressRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, source_path = get_video_asset(req.asset_id, current_user)
    task_id = start_compress_task(current_user, req.asset_id, str(source_path), req)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-script")
async def analyze_script_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    video_path_str = str(video_path)

    meta = probe_video(video_path)
    check_analysis_size_limit(meta)

    task_id = start_script_analysis(current_user, video_path_str, req.asset_id)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-visual")
async def analyze_visual_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    video_path_str = str(video_path)

    meta = probe_video(video_path)
    check_analysis_size_limit(meta)

    task_id = start_visual_analysis(current_user, video_path_str, req.asset_id)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-audio")
async def analyze_audio_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)

    ext = video_path.suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise StarletteHTTPException(status_code=400, detail=f"不支持的文件类型 {ext}")

    task_id, _ = start_audio_analysis(current_user, str(video_path), req.asset_id)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/split")
async def split_video_endpoint(
    req: SplitRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset, video_path = get_video_asset(req.asset_id, current_user)
    task_id = start_split_task(current_user, str(video_path), req.asset_id, req)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )
