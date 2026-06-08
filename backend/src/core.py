import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import instructor
from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, OpenAI
from sqlmodel import Session

from database import engine
from lib.audio import extract_bgm, stream_audio_features
from lib.schemas import (
    CutPointList,
    EffectAnalysisResult,
    VideoStructure,
    VideoVisualAnalysis,
    compute_text_density_curve,
)
from lib.video import (
    compress_video_async,
    detect_scenes_scenedetect,
    get_video_duration,
    probe_video,
    split_video_by_segments,
    video_to_base64,
)
from models import Asset
from prompts import (
    EFFECT_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
    EFFECT_ANALYSIS_USER_PROMPT,
    SPLIT_DETECTION_SYSTEM_PROMPT,
    SPLIT_DETECTION_USER_PROMPT,
    TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT,
    TRANSCRIPT_EXTRACTION_USER_PROMPT,
    VIDEO_VISUAL_ANALYSIS_SYSTEM_PROMPT,
    VIDEO_VISUAL_ANALYSIS_USER_PROMPT,
)
from services.cover import extract_cover_for_video
from tasks import _STREAM_EOF, task_registry

load_dotenv(find_dotenv(), override=True)
PROJECT_DIR = Path.cwd()
print(f"📁 项目目录: {PROJECT_DIR}")

if not os.getenv("API_KEY") or not os.getenv("BASE_URL") or not os.getenv("MODEL"):
    print("❌ 请在 .env 文件中设置 API_KEY, BASE_URL, MODEL")
    sys.exit(1)

print("🔑 API_KEY, BASE_URL, MODEL 已加载")
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)
async_client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)


async def analyze_video_script_async(video_path: str | Path) -> VideoStructure:
    """使用多模态模型将视频按叙事结构拆解为多个阶段元素。

    异步版本，供 API 端点使用。
    """
    instructor_client = instructor.from_openai(async_client)

    video_b64 = video_to_base64(video_path)

    user_content: list[dict] = [
        {"type": "text", "text": TRANSCRIPT_EXTRACTION_USER_PROMPT},
        {
            "type": "video_url",
            "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
        },
    ]

    response = await instructor_client.chat.completions.create(
        model=os.getenv("MODEL"),  # type: ignore
        response_model=VideoStructure,
        messages=[
            {"role": "system", "content": TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},  # type: ignore
        ],
    )

    return response


async def analyze_video_visual_async(video_path: str | Path) -> VideoVisualAnalysis:
    """异步版本，供 API 端点调用。"""
    video_path = Path(video_path)
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
    return result


async def run_compress_task(
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

        with Session(engine) as session:
            compressed_asset = Asset(
                asset_id=compressed_asset_id,
                user_id=user_id,
                path=str(compressed_path),
                type="video",
            )
            session.add(compressed_asset)
            session.commit()

        loop = asyncio.get_running_loop()
        cover_id = await loop.run_in_executor(
            None,
            extract_cover_for_video,
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


async def run_script_analysis(task_id: str, video_path_str: str) -> None:
    try:
        structure = await analyze_video_script_async(video_path_str)
        task_registry.set_result(task_id, structure.model_dump())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


async def run_visual_analysis(task_id: str, video_path_str: str) -> None:
    try:
        result = await analyze_video_visual_async(video_path_str)
        task_registry.set_result(task_id, result.model_dump())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


async def run_audio_analysis(
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

        gen = stream_audio_features(str(bgm_path), audio_asset_id=audio_asset_id)
        task_info = task_registry.get(task_id)
        queue: asyncio.Queue | None = task_info._stream_queue if task_info else None

        last_frame = None
        try:
            while True:
                frame = await loop.run_in_executor(None, next, gen, None)
                if frame is None:
                    break
                last_frame = frame
                if queue is not None:
                    try:
                        queue.put_nowait(frame)
                    except asyncio.QueueFull:
                        pass
        finally:
            gen.close()  # type: ignore[attr-defined]

        if queue is not None:
            try:
                queue.put_nowait(_STREAM_EOF)
            except asyncio.QueueFull:
                pass

        if last_frame is None:
            raise RuntimeError("No audio frames produced")

        with Session(engine) as session:
            session.add(
                Asset(
                    asset_id=audio_asset_id,
                    user_id=user_id,
                    path=str(bgm_path),
                    type="audio",
                )
            )
            session.commit()

        task_registry.set_result(
            task_id,
            {
                "audio_asset_id": audio_asset_id,
                "bgm_path": str(bgm_path),
                **last_frame["running_global"],
            },
        )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        task_registry.set_error(task_id, str(e))


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
        with Session(engine) as session:
            for i, clip_path in enumerate(clip_paths):
                meta = probe_video(clip_path)
                asset = Asset(
                    asset_id=str(uuid.uuid4()),
                    user_id=user_id,
                    source_asset_id=source_asset_id,
                    path=str(clip_path),
                    type="video",
                )
                session.add(asset)
                session.commit()

                cover_id = await loop.run_in_executor(
                    None,
                    extract_cover_for_video,
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
    effects_path = Path(__file__).parent / "lib" / "components_description.json"
    with open(effects_path, encoding="utf-8") as f:
        return json.load(f)


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
