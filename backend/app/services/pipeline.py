import asyncio
import os
import uuid
from pathlib import Path

import ffmpeg
import instructor
from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from app.database import engine
from app.lib.audio import analyze_audio_features, extract_bgm
from app.lib.image import probe_image
from app.lib.video import (
    compress_video_async,
    detect_scenes_scenedetect,
    extract_cover_image,
    get_video_duration,
    probe_video,
    split_video_by_segments,
    video_to_base64,
)
from app.llm import async_client
from app.models import Asset, Effect, User
from app.prompts import (
    EFFECT_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
    EFFECT_ANALYSIS_USER_PROMPT,
    SPLIT_DETECTION_SYSTEM_PROMPT,
    SPLIT_DETECTION_USER_PROMPT,
    TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT,
    TRANSCRIPT_EXTRACTION_USER_PROMPT,
    VIDEO_VISUAL_ANALYSIS_SYSTEM_PROMPT,
    VIDEO_VISUAL_ANALYSIS_USER_PROMPT,
)
from app.repositories import create_asset
from app.schemas import (
    CompressRequest,
    CutPointList,
    EffectAnalysisResult,
    SplitRequest,
    VideoStructure,
    VideoVisualAnalysis,
)
from app.services.task import register_and_launch
from app.tasks import task_registry
from app.utils import compute_text_density_curve

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
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
}
STORAGE_DIR = Path("storage")
VIDEO_STORAGE_DIR = STORAGE_DIR / "videos"
AUDIO_STORAGE_DIR = STORAGE_DIR / "audios"
IMAGES_STORAGE_DIR = STORAGE_DIR / "images"
MAX_ANALYZE_SIZE_MB = int(os.getenv("MAX_ANALYZE_SIZE_MB", "50"))


def extract_cover_for_video(
    session: Session,
    video_path: str,
    user_id: str,
    source_asset_id: str | None = None,
) -> str | None:
    try:
        img = extract_cover_image(video_path)
    except ffmpeg.Error as e:
        if e.stderr:
            raise HTTPException(
                status_code=500,
                detail=f"封面提取失败: {e.stderr.decode('utf-8', errors='ignore')}",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"未捕捉到 ffmpeg stderr 信息. 封面提取失败: {str(e)}",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"封面提取失败: {str(e)}")

    IMAGES_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    cover_id = str(uuid.uuid4())
    cover_path = IMAGES_STORAGE_DIR / f"{cover_id}.jpg"
    img.save(str(cover_path), "JPEG", quality=85)

    asset = Asset(
        asset_id=cover_id,
        user_id=user_id,
        source_asset_id=source_asset_id,
        path=str(cover_path),
        type="image",
    )
    create_asset(session, asset)

    return cover_id


# COMPRESS
async def run_compress_task(
    session: Session,
    task_id: str,
    user_id: str,
    source_asset_id: str,
    source_path_str: str,
    compressed_asset_id: str,
    compressed_path: Path,
    vcodec: str,
    crf: int,
    target_v_bitrate: str | None,
    scale_width: int | None,
    max_fps: int,
    acodec: str,
    target_a_bitrate: str,
) -> None:
    try:
        output = await compress_video_async(
            source_path_str,
            str(compressed_path),
            vcodec=vcodec,
            crf=crf,
            target_v_bitrate=target_v_bitrate,
            scale_width=scale_width,
            max_fps=max_fps,
            acodec=acodec,
            target_a_bitrate=target_a_bitrate,
        )
        compressed_meta = probe_video(output)

        compressed_asset = Asset(
            asset_id=compressed_asset_id,
            user_id=user_id,
            path=str(compressed_path),
            type="video",
        )
        create_asset(session, compressed_asset)

        loop = asyncio.get_running_loop()
        cover_id = await loop.run_in_executor(
            None,
            extract_cover_for_video,
            session,
            str(compressed_path),
            user_id,
            compressed_asset_id,
        )

        task_registry.set_result(
            task_id,
            {
                "asset_id": compressed_asset_id,
                "source_asset_id": source_asset_id,
                "type": "video",
                "path": str(compressed_path),
                "metadata": compressed_meta.to_dict(),
                "cover_image_asset_id": cover_id,
            },
        )
    except asyncio.CancelledError:
        compressed_path.unlink(missing_ok=True)
    except Exception as e:
        compressed_path.unlink(missing_ok=True)
        task_registry.set_error(task_id, str(e))


def start_compress_task(
    session: Session,
    user: User,
    source_asset_id: str,
    source_path_str: str,
    req: CompressRequest,
) -> str:
    compressed_asset_id = str(uuid.uuid4())
    compressed_filename = f"{compressed_asset_id}_compressed.mp4"
    compressed_path = VIDEO_STORAGE_DIR / compressed_filename
    VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    task_id = str(uuid.uuid4())
    register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="compress",
        resource_id=source_asset_id,
        coro=run_compress_task(
            session=session,
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


# SCRIPT ANALYSIS
async def run_script_analysis(task_id: str, video_path: str) -> None:
    try:
        instructor_client = instructor.from_openai(async_client)

        video_b64 = video_to_base64(video_path)

        user_content: list[dict] = [
            {"type": "text", "text": TRANSCRIPT_EXTRACTION_USER_PROMPT},
            {
                "type": "video_url",
                "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
            },
        ]

        structure: VideoStructure = await instructor_client.chat.completions.create(
            model=os.getenv("MODEL"),  # type: ignore
            response_model=VideoStructure,
            messages=[
                {"role": "system", "content": TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},  # type: ignore
            ],
        )

        task_registry.set_result(task_id, structure.model_dump())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


# AUDIO ANALYSIS
async def run_audio_analysis(
    session: Session,
    task_id: str,
    user_id: str,
    source_asset_id: str,
    video_path_str: str,
    audio_asset_id: str,
    dst_dir: str,
) -> None:
    try:
        loop = asyncio.get_running_loop()

        bgm_path = await loop.run_in_executor(
            None, extract_bgm, video_path_str, Path(dst_dir), audio_asset_id
        )

        features = await loop.run_in_executor(
            None, analyze_audio_features, str(bgm_path)
        )

        asset = Asset(
            asset_id=audio_asset_id,
            user_id=user_id,
            path=str(bgm_path),
            type="audio",
        )
        create_asset(session, asset)

        task_registry.set_result(
            task_id,
            {
                "audio_asset_id": audio_asset_id,
                "bgm_path": str(bgm_path),
                **features,
            },
        )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


def start_audio_analysis(
    session: Session, user: User, video_path_str: str, source_asset_id: str
) -> str:
    AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    audio_asset_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-audio",
        resource_id=source_asset_id,
        coro=run_audio_analysis(
            session=session,
            task_id=task_id,
            user_id=user.user_id,
            source_asset_id=source_asset_id,
            video_path_str=video_path_str,
            audio_asset_id=audio_asset_id,
            dst_dir=str(AUDIO_STORAGE_DIR),
        ),
    )
    return task_id


def start_script_analysis(user: User, video_path_str: str, asset_id: str) -> str:
    task_id = str(uuid.uuid4())
    register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-script",
        resource_id=asset_id,
        coro=run_script_analysis(task_id, video_path_str),
    )
    return task_id


# EFFECT ANALYSIS
def format_effects_library(effects: list[dict]) -> str:
    """按 category 分组格式化特效库，减少模型扫描压力。"""
    grouped: dict[str, list[dict]] = {}
    for effect in effects:
        category = effect.get("category", "Other")
        grouped.setdefault(category, []).append(effect)

    lines = []
    for category, items in grouped.items():
        lines.append(f"### {category}")
        for item in items:
            lines.append(f"- **{item['name']}**: {item['description']}")
        lines.append("")

    return "\n".join(lines)


def load_effects() -> list[dict]:
    with Session(engine) as session:
        effects = session.exec(select(Effect)).all()
        return [
            {"name": e.name, "category": e.category, "description": e.description}
            for e in effects
        ]


async def analyze_video_effects_async(video_path: str | Path) -> EffectAnalysisResult:
    """使用多模态模型分析视频中包含哪些视觉特效。"""
    video_path = Path(video_path)

    effects = load_effects()
    effects_library_text = format_effects_library(effects)
    system_prompt = EFFECT_ANALYSIS_SYSTEM_PROMPT_TEMPLATE.format(
        effects_library=effects_library_text,
    )

    video_b64 = video_to_base64(video_path)

    user_content: list[dict] = [
        {"type": "text", "text": EFFECT_ANALYSIS_USER_PROMPT},
        {
            "type": "video_url",
            "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
        },
    ]

    instructor_client = instructor.from_openai(async_client)
    result: EffectAnalysisResult = await instructor_client.chat.completions.create(
        model=os.getenv("MODEL"),  # type: ignore
        response_model=EffectAnalysisResult,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},  # type: ignore
        ],
    )

    return result


async def run_effect_analysis(task_id: str, video_path_str: str) -> None:
    try:
        result = await analyze_video_effects_async(video_path_str)
        task_registry.set_result(task_id, result.model_dump())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


def start_effect_analysis(user: User, video_path_str: str, asset_id: str) -> str:
    task_id = str(uuid.uuid4())
    register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-effect",
        resource_id=asset_id,
        coro=run_effect_analysis(task_id, video_path_str),
    )
    return task_id


# SPLIT VIDEO


async def detect_cut_points_ai(video_path: str, duration: float) -> CutPointList:
    instructor_client = instructor.from_openai(async_client)
    video_b64 = video_to_base64(video_path)

    return await instructor_client.chat.completions.create(
        model=os.getenv("MODEL"),
        response_model=CutPointList,
        messages=[
            {"role": "system", "content": SPLIT_DETECTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": SPLIT_DETECTION_USER_PROMPT.format(duration=duration),
                    },
                    {
                        "type": "video_url",
                        "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
                    },
                ],
            },  # type: ignore
        ],
    )


def cut_points_to_segments(cut_points: CutPointList, duration: float) -> list[dict]:
    timestamps = sorted([cp.timestamp for cp in cut_points.cut_points])
    boundaries = [0.0] + timestamps + [duration]

    segments = []
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        segments.append(
            {
                "index": i,
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "duration": round(end - start, 2),
                "reason": next(
                    (
                        cp.reason
                        for cp in cut_points.cut_points
                        if abs(cp.timestamp - end) < 0.01
                    ),
                    None,
                ),
            }
        )

    return segments


async def run_split_task(
    session: Session,
    task_id: str,
    user_id: str,
    source_asset_id: str,
    video_path_str: str,
    use_ai: bool,
    threshold: float,
    min_scene_len: int,
) -> None:
    try:
        loop = asyncio.get_running_loop()

        if use_ai:
            duration = await loop.run_in_executor(
                None, get_video_duration, video_path_str
            )
            cut_points = await detect_cut_points_ai(video_path_str, duration)
            segments_raw = cut_points_to_segments(cut_points, duration)
            method = "ai"
        else:
            segments_raw = await loop.run_in_executor(
                None,
                detect_scenes_scenedetect,
                video_path_str,
                threshold,
                min_scene_len,
            )
            method = "scenedetect"

        output_dir = Path("storage/videos")
        clip_prefix = str(uuid.uuid4())
        clip_paths = await loop.run_in_executor(
            None,
            split_video_by_segments,
            video_path_str,
            segments_raw,
            output_dir,
            clip_prefix,
        )

        clip_assets = []
        for i, clip_path in enumerate(clip_paths):
            meta = probe_video(clip_path)
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                user_id=user_id,
                source_asset_id=source_asset_id,
                path=str(clip_path),
                type="video",
            )
            create_asset(session, asset)

            cover_id = await loop.run_in_executor(
                None,
                extract_cover_for_video,
                session,
                str(clip_path),
                user_id,
                asset.asset_id,
            )

            clip_assets.append(
                {
                    "asset_id": asset.asset_id,
                    "index": i,
                    "path": str(clip_path),
                    "metadata": meta.to_dict(),
                    "cover_image_asset_id": cover_id,
                }
            )

        segments = []
        for s in segments_raw:
            seg = {
                "index": s["index"],
                "start_sec": s["start_sec"],
                "end_sec": s["end_sec"],
                "duration": s["duration"],
            }
            if method == "scenedetect":
                seg["cut_score"] = s.get("cut_score")
            else:
                seg["reason"] = s.get("reason")
            segments.append(seg)

        task_registry.set_result(
            task_id,
            {
                "source_asset_id": source_asset_id,
                "method": method,
                "total_segments": len(segments),
                "segments": segments,
                "clip_assets": clip_assets,
            },
        )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


def start_split_task(
    session: Session,
    user: User,
    video_path_str: str,
    source_asset_id: str,
    req: SplitRequest,
) -> str:
    task_id = str(uuid.uuid4())
    register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="split",
        resource_id=source_asset_id,
        coro=run_split_task(
            session=session,
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


# VISUAL ANALYSIS
async def run_visual_analysis(task_id: str, video_path: str) -> None:
    try:
        video_b64 = video_to_base64(video_path)

        user_content: list[dict] = [
            {"type": "text", "text": VIDEO_VISUAL_ANALYSIS_USER_PROMPT},
            {
                "type": "video_url",
                "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
            },
        ]

        instructor_client = instructor.from_openai(async_client)
        result: VideoVisualAnalysis = await instructor_client.chat.completions.create(
            model=os.getenv("MODEL"),  # type: ignore
            response_model=VideoVisualAnalysis,
            messages=[
                {"role": "system", "content": VIDEO_VISUAL_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},  # type: ignore
            ],
        )

        result.text_density_curve = compute_text_density_curve(result.text_elements)
        task_registry.set_result(task_id, result.model_dump())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


def start_visual_analysis(user: User, video_path_str: str, asset_id: str) -> str:
    task_id = str(uuid.uuid4())
    register_and_launch(
        task_id=task_id,
        user_id=user.user_id,
        task_type="analyze-visual",
        resource_id=asset_id,
        coro=run_visual_analysis(task_id, video_path_str),
    )
    return task_id


# OTHER
def check_analysis_size_limit(meta) -> None:
    file_size_mb = (int(meta.size) if meta.size else 0) / (1024 * 1024)
    if file_size_mb > MAX_ANALYZE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=(
                f"视频文件过大（{file_size_mb:.1f} MB），"
                f"超过分析上限 {MAX_ANALYZE_SIZE_MB} MB。"
                "请先调用 /compress 压缩后再分析。"
            ),
        )


async def upload(session: Session, user: User, file: UploadFile) -> dict:
    ext = Path(file.filename or "upload.bin").suffix.lower()
    is_video = (
        ext in ALLOWED_VIDEO_EXTENSIONS
        or file.content_type in ALLOWED_VIDEO_MIME_TYPES
    )
    is_image = (
        ext in ALLOWED_IMAGE_EXTENSIONS
        or file.content_type in ALLOWED_IMAGE_MIME_TYPES
    )
    if not is_video and not is_image:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    if is_video:
        asset_type = "video"
        storage_dir = VIDEO_STORAGE_DIR
    else:
        asset_type = "image"
        storage_dir = IMAGES_STORAGE_DIR

    storage_dir.mkdir(parents=True, exist_ok=True)

    asset_id = str(uuid.uuid4())
    filename = f"{asset_id}{ext}"
    filepath = storage_dir / filename

    content = await file.read()
    filepath.write_bytes(content)

    try:
        if asset_type == "video":
            meta = probe_video(filepath)
        else:
            meta = probe_image(filepath)
    except Exception as e:
        filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"文件元数据探测失败: {e}",
        )

    asset = Asset(
        asset_id=asset_id,
        user_id=user.user_id,
        path=str(filepath),
        type=asset_type,
    )
    create_asset(session, asset)

    result = {
        "asset_id": asset_id,
        "type": asset_type,
        "path": str(filepath),
        "metadata": meta.to_dict(),
    }

    if asset_type == "video":
        loop = asyncio.get_running_loop()
        cover_id = await loop.run_in_executor(
            None,
            extract_cover_for_video,
            session,
            str(filepath),
            user.user_id,
            asset_id,
        )
        result["cover_image_asset_id"] = cover_id

    return result
