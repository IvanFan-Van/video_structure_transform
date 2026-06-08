import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, OpenAI

load_dotenv(find_dotenv(), override=True)

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
