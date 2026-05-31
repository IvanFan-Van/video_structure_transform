import asyncio
import edge_tts
import re


async def generate_voice(
    text, output_file="narration.wav", voice="zh-CN-XiaoxiaoNeural"
):
    """使用 Edge TTS 生成音频"""
    # 文本预处理：去除多余换行，确保标点后有停顿
    text = re.sub(r"\s+", " ", text).strip()
    # 创建通信对象并生成音频
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    print(f"✅ 音频已生成: {output_file}")


def main():
    # 读取 narration.txt
    with open("narration.txt", "r", encoding="utf-8") as f:
        text = f.read()
    # 可选：如果你想要更自然的效果，可以手动调整文本中的数字（如 10亿 -> 十亿）
    text = text.replace("10亿", "十亿").replace("11亿", "十一亿")
    # 运行异步函数
    asyncio.run(generate_voice(text, "narration.wav", voice="zh-CN-XiaoxiaoNeural"))


if __name__ == "__main__":
    main()
