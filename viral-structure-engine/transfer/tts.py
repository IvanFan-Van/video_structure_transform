"""TTS 旁白语音生成 — 使用 Microsoft Edge TTS（免费，无需API密钥）

本模块封装 edge-tts 库，将文本转换为中文语音文件（WAV格式）。
支持可调节语速（rate参数），用于匹配原视频的实际说话速度。

核心函数:
  generate_voiceover() — 异步生成语音
  run_tts()            — 同步包装器，方便在同步代码中调用
"""

import asyncio
import edge_tts


async def generate_voiceover(
    text: str,
    output_path: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+0%",
) -> None:
    """异步生成TTS语音文件

    Args:
        text:        要朗读的中文文本
        output_path: 输出WAV文件路径
        voice:       语音角色（默认: 晓晓-女性-标准）
                     其他可选: zh-CN-YunxiNeural(男性), zh-CN-XiaoyiNeural(台湾)
        rate:        语速调节，格式如 "+65%" / "-20%"
                     正值加速，负值减速，由transfer.py根据原视频语速动态计算
    """
    # Communicate 对象负责文本→语音的转换和保存
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def run_tts(
    text: str,
    output_path: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+0%",
) -> None:
    """同步调用TTS（封装 asyncio.run）

    这是供 transfer.py 等同步代码直接调用的入口。
    内部启动事件循环执行 generate_voiceover()。
    """
    asyncio.run(generate_voiceover(text, output_path, voice, rate))
