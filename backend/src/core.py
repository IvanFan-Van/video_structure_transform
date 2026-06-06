import asyncio
import os
import sys
from pathlib import Path

import instructor
from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, OpenAI
from sqlmodel import Session

from audio import extract_bgm, stream_audio_features
from models import (
    Asset,
    VideoStructure,
    VideoVisualAnalysis,
    compute_text_density_curve,
    engine,
)
from prompts import (
    TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT,
    TRANSCRIPT_EXTRACTION_USER_PROMPT,
    VIDEO_VISUAL_ANALYSIS_SYSTEM_PROMPT,
    VIDEO_VISUAL_ANALYSIS_USER_PROMPT,
)
from task_registry import task_registry
from video import compress_video_async, probe_video, video_to_base64

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

        task_registry.set_result(
            task_id,
            {
                "asset_id": compressed_asset_id,
                "source_asset_id": source_asset_id,
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
