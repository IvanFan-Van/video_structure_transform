import os
import sys
from pathlib import Path

import instructor
from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, OpenAI

from models import VideoStructure
from prompts import (
    TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT,
    TRANSCRIPT_EXTRACTION_USER_PROMPT,
)
from utils import timer
from video import video_to_base64

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


@timer
def analyze_video_script(video_path: str | Path) -> VideoStructure:
    """使用多模态模型将视频按叙事结构拆解为多个阶段元素。

    同步版本，供 notebooks 使用。
    """
    instructor_client = instructor.from_openai(client)

    video_b64 = video_to_base64(video_path)

    user_content: list[dict] = [
        {"type": "text", "text": TRANSCRIPT_EXTRACTION_USER_PROMPT},
        {
            "type": "video_url",
            "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
        },
    ]

    print("🤖 正在调用多模态模型拆解视频结构...")
    response = instructor_client.chat.completions.create(
        model=os.getenv("MODEL"),  # type: ignore
        response_model=VideoStructure,
        messages=[
            {"role": "system", "content": TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},  # type: ignore
        ],
    )

    return response


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
