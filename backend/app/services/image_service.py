import asyncio
import logging
import os
import uuid
from pathlib import Path

import requests

STORAGE_DIR = Path("storage")
AIGC_DIR = STORAGE_DIR / "aigc"

AGNES_BASE_URL_DEFAULT = "https://apihub.agnes-ai.com/v1"
AGNES_MODEL_DEFAULT = "agnes-image-2.0-flash"

logger = logging.getLogger(__name__)


async def generate_image(prompt: str) -> tuple[str | None, str | None]:
    api_key = os.getenv("AGNES_API_KEY")
    if not api_key:
        logger.warning("AGNES_API_KEY not set, skipping image generation")
        return None, "AGNES_API_KEY not configured"

    base_url = os.getenv("AGNES_BASE_URL", AGNES_BASE_URL_DEFAULT)
    model = os.getenv("AGNES_IMAGE_MODEL", AGNES_MODEL_DEFAULT)

    safe_prompt = prompt.strip()[:500]
    if not safe_prompt:
        return None, "empty prompt"

    full_prompt = f"{safe_prompt}，竖版构图"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "size": "1024x1792",
        "n": 1,
    }

    try:
        resp = await asyncio.to_thread(
            requests.post,
            f"{base_url}/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        image_url = data["data"][0]["url"]
    except Exception:
        logger.exception("Agnes API call failed")
        return None, "Agnes API call failed"

    try:
        img_resp = await asyncio.to_thread(
            requests.get, image_url, timeout=60
        )
        img_resp.raise_for_status()

        AIGC_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"aigc_{uuid.uuid4().hex[:12]}.png"
        output_path = AIGC_DIR / filename

        def _write():
            output_path.write_bytes(img_resp.content)

        await asyncio.to_thread(_write)

        return str(output_path.resolve()), None
    except Exception:
        logger.exception("Failed to download generated image")
        return None, "Failed to download generated image"
