import os
import sys
import whisper
import json
import base64
import cv2
from pathlib import Path
from moviepy import VideoFileClip
from openai import OpenAI

VIDEO_FILENAME = "抖音2026529-207530.mp4"
VIDEO_PATH = Path.cwd().parent / "tests" / "videos" / VIDEO_FILENAME

OUTPUT_DIR = Path.cwd().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_AUDIO_PATH = OUTPUT_DIR / "temp_audio.wav"

client = OpenAI(
    # 火山引擎的 API Key，对应你截图中的 api-key
    api_key=os.getenv("API_KEY", ""),
    # 火山引擎的官方 OpenAI 兼容接入地址
    base_url=os.getenv("BASE_URL", ""),
)


def extract_audio_and_transcript(VIDEO_PATH, output_audio_path):
    # 提取音频
    print("正在提取音频...")
    video = VideoFileClip(VIDEO_PATH)
    video.audio.write_audiofile(output_audio_path, logger=None)
    video.close()

    print("正在进行ASR转录...")

    model = whisper.load_model("base")
    result = model.transcribe(output_audio_path, word_timestamps=True)

    # 提取带有时间戳的文本片段
    segments = []
    for seg in result["segments"]:
        segments.append(
            {
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"],
            }
        )
    return segments, result["text"]


def analyze_video_rhythm(VIDEO_PATH, threshold=30.0):
    print("正在分析视频节奏...")
    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS)

    ret, prev_frame = cap.read()
    if not ret:
        return []

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    cut_timestamps = []
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_index += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_diff = cv2.absdiff(gray, prev_gray)
        mean_diff = frame_diff.mean()

        if mean_diff > threshold:
            timestamps = round(frame_index / fps, 2)
            cut_timestamps.append(timestamps)

        prev_gray = gray

    cap.release()
    return cut_timestamps


def generate_structure_analysis(transcript_segments, total_text, cut_timestamps):
    segments_str = "\n".join(
        [
            f"[{seg['start']}s - {seg['end']}s]: {seg['text']}"
            for seg in transcript_segments
        ]
    )
    cuts_str = ", ".join([f"{t}s" for t in cut_timestamps])

    prompt = f"""
你是一个精通自动化视频生产线（AI Video Pipeline）架构的顶尖专家。
系统已经向你输入了一个爆款短视频。请结合你看到的画面和底层特征数据，完成两件事：
1. 分拆生产结构契约。
2. 决策该视频的【素材采集策略】，判断其是否依赖现实物理拍摄。

【辅助底层数据】
1. 完整台词：{total_text}
2. 台词精准时间戳：\n{segments_str}
3. 物理切镜点：[{cuts_str}]

【黄金任务：构建视频生产线协议与素材决策】
请输出一个规范的 JSON 格式报告（不要包含任何 markdown 标记包裹，确保可以直接被 json.loads 解析），结构必须严格包含以下字段：

1. production_strategy (生产路径决策大脑 - 🌟核心新增🌟):
   - video_category: 视频的细分类别（例如：实物带货、真人出镜口播、旅游 Vlog、纯文字剪辑、情感语录混剪、AI虚拟人解说等）。
   - requires_physical_shooting: 布尔值（true 或 false）。如果视频必须依赖真实世界的人像、特定线下场景、特定实物道具拍摄，填 true；如果可以完全通过 AI 绘图、文生视频、动态文字、素材库混剪合成，填 false。
   - user_action_required: 字符串数组。
     * 当 requires_physical_shooting 为 true 时，在此详细列出【需要用户线下拍摄并提供的物理素材清单】（例如：["拍摄3段产品正面在强光下的微距特写", "拍摄1段手持产品展示使用过程的镜头"]）。
     * 当 requires_physical_shooting 为 false 时，固定填写：["无需人工拍摄，下游系统可全自动触发 AI 画面合成及自动剪辑"]。

2. global_config (全局视听调性):
   - visual_style: 给视频生成 AI（如 Kling/Sora）的全局画面风格提示词。
   - audio_bgm_vibe: 建议配置的背景音乐风格和节奏类型。

3. global_placeholders (新视频填充变量定义):
   - 列出生成新视频时，用户或下游 AI 必须输入的变量列表，并给出基于当前爆款视频的填充示例（例如：{{"{{{{商品特写}}}}": "原视频中是西红柿切面，可替换为新商品的核心切面特写"}}）。

4. storyboard_scenes (分镜级生产线提示词 - 核心数组):
   - 结合台词时间戳和切镜点，将视频切分为连续的分镜。每个分镜对象包含：
     * scene_id: 分镜序号（如 1, 2, 3）。
     * time_slot: 时间区间（如 "0.0s - 3.5s"）。
     * scene_role: 该分镜在爆款结构中的功能（如 "Hook黄金开头", "痛点共鸣", "产品登场"）。
     * ai_video_prompt: 专门写给“视频生成大模型”的视觉描述提示词（需包含镜头运动、主体、光影，含占位符）。
     * script_template: 带占位符的台词文案公式。
     * screen_overlay: 此时画面上应该出现的“花字/标题条/卡片”的内容模板与样式提示。
     * transition_effect: 该分镜结束时的转场方式。

请严格遵循 JSON 规范，直接输出 JSON 文本，不要带有任何反引号。
"""
    return prompt


try:
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"未找到视频文件: {VIDEO_PATH}")

    # 第一阶段：提取离线音视频特征数据
    transcript_segments, total_text = extract_audio_and_transcript(
        str(VIDEO_PATH), str(OUTPUT_AUDIO_PATH)
    )
    cut_timestamps = analyze_video_rhythm(str(VIDEO_PATH), threshold=30.0)

    # 第二阶段：生成融合提示词
    final_prompt = generate_structure_analysis(
        transcript_segments, total_text, cut_timestamps
    )

    # 第三阶段：编码原生视频文件
    print("💾 正在将视频转码为大模型多模态数据流...")
    with open(VIDEO_PATH, "rb") as video_file:
        video_base64 = base64.b64encode(video_file.read()).decode("utf-8")

    # 第四阶段：投喂火山引擎 Seed-2.0-lite
    print("🤖 正在请求全模态大模型进行视听联合深度分析...")
    completion = client.chat.completions.create(
        model=os.getenv("MODEL", ""),
        messages=[
            {
                "role": "system",
                "content": "你是一个专门用来解析短视频结构并输出标准 JSON 的后台 Agent。请勿包含任何 Markdown 格式包裹（如 ```json）。",
            },
            {
                "role": "user",
                "content": [
                    # 🌟 1. 视频组件：类型改为 "video_url"，且 Base64 字符串需要嵌套在 "video_url" 对象的 "url" 字段中
                    {
                        "type": "video_url",
                        "video_url": {"url": f"data:video/mp4;base64,{video_base64}"},
                    },
                    # 🌟 2. 文本组件：类型改为标准的 "text"
                    {"type": "text", "text": final_prompt},
                ],
            },
        ],
        temperature=0.2,
    )

    # 第五阶段：解析、落盘与保存
    response_content = completion.choices[0].message.content
    if response_content.startswith("```json"):
        response_content = response_content.strip("```json").strip("```").strip()
    elif response_content.startswith("```"):
        response_content = response_content.strip("```").strip()

    analysis_json = json.loads(response_content)
    output_json_path = OUTPUT_DIR / f"{VIDEO_FILENAME.split('.')[0]}_structure.json"

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(analysis_json, f, ensure_ascii=False, indent=4)

    print(f"🎉 成功！爆款结构协议已沉淀至知识库: {output_json_path}")
    print(json.dumps(analysis_json, ensure_ascii=False, indent=2))

except Exception as e:
    print(f"❌ 运行流水线失败: {e}")
