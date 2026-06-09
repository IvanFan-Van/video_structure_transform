from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user, get_video_asset
from app.lib.video import probe_video
from app.models import User
from app.schemas import AnalyzeRequest, CompressRequest, SplitRequest
from app.services import (
    check_analysis_size_limit,
    start_audio_analysis,
    start_compress_task,
    start_effect_analysis,
    start_script_analysis,
    start_split_task,
    start_visual_analysis,
    upload,
)

router = APIRouter(tags=["pipeline"])

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}


@router.get("/")
def index():
    return JSONResponse(status_code=200, content={"status": "success", "data": "ok"})


@router.post("/upload")
async def upload_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    result = await upload(session, current_user, file)
    return JSONResponse(status_code=201, content={"status": "success", "data": result})


@router.post("/compress")
async def compress_video_endpoint(
    req: CompressRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    source_asset = get_video_asset(req.asset_id, current_user)
    task_id = start_compress_task(
        session, current_user, req.asset_id, str(source_asset.path), req
    )
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-script")
async def analyze_script_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset = get_video_asset(req.asset_id, current_user)
    meta = probe_video(source_asset.path)
    check_analysis_size_limit(meta)

    task_id = start_script_analysis(current_user, source_asset.path, req.asset_id)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-visual")
async def analyze_visual_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset = get_video_asset(req.asset_id, current_user)
    meta = probe_video(source_asset.path)
    check_analysis_size_limit(meta)

    task_id = start_visual_analysis(current_user, source_asset.path, req.asset_id)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-audio")
async def analyze_audio_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    source_asset = get_video_asset(req.asset_id, current_user)

    ext = Path(source_asset.path).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型 {ext}")

    task_id = start_audio_analysis(
        session, current_user, source_asset.path, req.asset_id
    )
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/split")
async def split_video_endpoint(
    req: SplitRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    source_asset = get_video_asset(req.asset_id, current_user)
    task_id = start_split_task(
        session, current_user, source_asset.path, req.asset_id, req
    )
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )


@router.post("/analyze-effect")
async def analyze_effect_endpoint(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    source_asset = get_video_asset(req.asset_id, current_user)
    meta = probe_video(source_asset.path)
    check_analysis_size_limit(meta)

    task_id = start_effect_analysis(current_user, source_asset.path, req.asset_id)
    return JSONResponse(
        status_code=202, content={"status": "success", "data": {"task_id": task_id}}
    )
