import asyncio
import json
import os
import re
import sys
from pathlib import Path

import ffmpeg
from audio_separator.separator import Separator
from dotenv import find_dotenv, load_dotenv
from faster_whisper import WhisperModel
from openai import AsyncOpenAI, OpenAI
from scenedetect import ContentDetector, detect
from tenacity import retry, stop_after_attempt

from prompts import (
    COMPOSITION_HTML_SYSTEM_PROMPT,
    COMPOSITION_HTML_TEMPLATE,
    DESIGN_MD_TEMPLATE,
    DESIGN_SYSTEM_PROMPT,
    NARRATION_CLEAN_SYSTEM_PROMPT,
    SCRIPT_MD_TEMPLATE,
    SCRIPT_SYSTEM_PROMPT,
    STORYBOARD_MD_TEMPLATE,
    STORYBOARD_SYSTEM_PROMPT,
)
from utils import timer
from video import VideoClip

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
aclient = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)


@timer
def extract_vocal_and_bgm(video: VideoClip, output_dir: Path):
    video_path = video.filepath
    print("📢 正在提取音频并分离人声与伴奏...")
    audio_path = output_dir / "audio.mp3"
    ffmpeg.input(str(video_path)).output(str(audio_path)).run(
        overwrite_output=True, quiet=True
    )
    print(f"✅ 音频提取完成: {audio_path}")

    print("🎚️  正在分离人声与伴奏...")
    separator = Separator(output_dir=str(output_dir), output_format="mp3")
    separator.load_model("UVR-MDX-NET-Inst_HQ_3.onnx")
    output_names = {
        "Vocals": "audio_vocals",
        "Instrumental": "audio_bgm",
    }
    output_files = separator.separate(str(audio_path), output_names)
    print(f"✅ 分离完成: {output_files}")

    return output_dir / output_files[0], output_dir / output_files[1]


@timer
def extract_transcript(audio_vocals_path: Path):
    print("📝 正在使用 Whisper 提取字幕...")
    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8",
        download_root=str(PROJECT_DIR / "models"),
    )

    result, info = model.transcribe(str(audio_vocals_path), beam_size=5)

    segments = [
        {
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text,
        }
        for seg in result
    ]

    total_text = " ".join([seg["text"] for seg in segments])
    print(f"✅ 字幕提取完成: {len(segments)} 段，{info.language}，{info.duration:.2f}s")
    return segments, total_text


@timer
def analyze_video_rhythm(video: VideoClip):
    print("🎬 正在分析视频节奏...")
    video_path = video.filepath
    scene_list = detect(str(video_path), ContentDetector())
    print(f"✅ 时长: {video.duration:.1f}s | 切镜: {len(scene_list)}个")
    return scene_list


@timer
def build_script_prompt(segments, total_text, cuts, duration, design_content):
    print("🧠 正在构建 SCRIPT.md 生成提示词...")
    segs = "\n".join(f"[{s['start']}s-{s['end']}s]: {s['text']}" for s in segments)
    scene_list_str = "\n".join(
        [
            f"cut {idx + 1}. {start.get_timecode()} - {end.get_timecode()}"
            for idx, (start, end) in enumerate(cuts)
        ]
    )
    return SCRIPT_MD_TEMPLATE.format(
        design_content=design_content,
        duration=duration,
        scene_list_str=scene_list_str,
        total_text=total_text,
        segs=segs,
    )


@timer
def build_storyboard_prompt(segments, duration, design_content, script_content):
    segs = "\n".join(f"[{s['start']}s-{s['end']}s]: {s['text']}" for s in segments)
    return STORYBOARD_MD_TEMPLATE.format(
        design_content=design_content,
        script_content=script_content,
        duration=duration,
        segs=segs,
    )


@timer
@retry(stop=stop_after_attempt(3))
def call_model(system_prompt: str, user_prompt: str, video_b64: str | None = None):
    print("🤖 正在调用多模态模型生成内容...")
    user_content: list[dict] = [
        {
            "type": "text",
            "text": user_prompt,
        }
    ]
    if video_b64:
        user_content.append(
            {
                "type": "video_url",
                "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
            }
        )

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL"),  # type: ignore
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },  # type: ignore
            ],
        )
    except Exception as e:
        traceback.print_exc()
        print(f"⚠️ 模型调用失败: {e}")
        raise e

    return response.choices[0].message.content


@timer
def _parse_beats_from_storyboard(storyboard_content: str) -> list:
    beats = []
    pattern = re.compile(
        r"###\s+Beat\s+(\d+)\s*[—–-]\s*\[([^\]]+)\]\s*\((\d+\.?\d*)s\s*-\s*(\d+\.?\d*)s\)",
        re.IGNORECASE,
    )
    fn_pattern = re.compile(r"\*\*Composition filename\*\*:\s*`([^`]+)`")
    narration_pattern = re.compile(r"\*\*Narration\*\*:\s*[\"「]([^\"「」\n]+)[\"」]?")

    lines = storyboard_content.split("\n")
    current_beat = None

    for line in lines:
        m = pattern.search(line)
        if m:
            if current_beat:
                beats.append(current_beat)
            num, label, start, end = m.groups()
            safe_label = re.sub(r"[^a-zA-Z0-9]", "-", label.lower())
            beat_id = f"beat-{num}-{safe_label}"
            current_beat = {
                "num": int(num),
                "id": beat_id,
                "label": label,
                "start": float(start),
                "end": float(end),
                "filename": f"{beat_id}.html",
                "narration": "",
            }
            continue

        if current_beat:
            fn_m = fn_pattern.search(line)
            if fn_m:
                fname = fn_m.group(1).strip()
                current_beat["filename"] = fname
                current_beat["id"] = fname.replace(".html", "")

            nar_m = narration_pattern.search(line)
            if nar_m:
                current_beat["narration"] = nar_m.group(1).strip()

    if current_beat:
        beats.append(current_beat)

    return beats


@timer
def build_composition_prompt(
    beat: dict,
    design_content: str,
    storyboard_beat_section: str,
    transcript_words: list,
    is_final: bool,
) -> str:
    beat_words = [
        w
        for w in transcript_words
        if w["start"] >= beat["start"] - 0.1 and w["end"] <= beat["end"] + 0.1
    ]
    beat_duration = round(beat["end"] - beat["start"], 2)

    # 台词单词转为相对时间（相对于 beat 开始）
    relative_words = [
        {
            "text": w["text"],
            "start": round(w["start"] - beat["start"], 3),
            "end": round(w["end"] - beat["start"], 3),
        }
        for w in beat_words
    ]

    return COMPOSITION_HTML_TEMPLATE.format(
        beat=beat,
        design_content=design_content,
        storyboard_beat_section=storyboard_beat_section,
        relative_words=relative_words,
        beat_duration=beat_duration,
        is_final=is_final,
    )


@timer
def extract_beat_section(storyboard_content: str, beat_num: int) -> str:
    lines = storyboard_content.split("\n")
    in_section = False
    section_lines = []
    beat_header = re.compile(rf"###\s+Beat\s+{beat_num}\b", re.IGNORECASE)
    next_beat = re.compile(r"###\s+Beat\s+\d+", re.IGNORECASE)

    for line in lines:
        if beat_header.search(line):
            in_section = True
        elif in_section and next_beat.search(line) and not beat_header.search(line):
            break
        if in_section:
            section_lines.append(line)

    return "\n".join(section_lines) if section_lines else f"Beat {beat_num} 无详细描述"


def extract_design_tokens(design_content: str) -> dict:
    """提取 DESIGN.md 中的关键 token，用于代码层面校验/注入。"""
    tokens = {
        "primary": "#0a0a0a",
        "on_primary": "#ffffff",
        "accent": "#c84f1c",
        "headline_font": "Noto Serif SC",
        "body_font": "Noto Sans SC",
    }
    for line in design_content.split("\n"):
        l = line.strip()
        if l.startswith("primary:") and "#" in l:
            m = re.search(r"#[0-9a-fA-F]{6}", l)
            if m:
                tokens["primary"] = m.group()
        elif l.startswith("on-primary:") and "#" in l:
            m = re.search(r"#[0-9a-fA-F]{6}", l)
            if m:
                tokens["on_primary"] = m.group()
        elif l.startswith("accent:") and "#" in l:
            m = re.search(r"#[0-9a-fA-F]{6}", l)
            if m:
                tokens["accent"] = m.group()
        elif "fontFamily:" in l:
            m = re.search(r'fontFamily:\s*["\']?([^"\'#\n]+)["\']?', l)
            if m:
                font = m.group(1).strip().strip("\"'")
                if (
                    "headline"
                    in design_content[
                        max(0, design_content.find(l) - 200) : design_content.find(l)
                    ]
                ):
                    tokens["headline_font"] = font
                else:
                    tokens["body_font"] = font
    return tokens


def generate_index_html(beats: list, design_content: str, total_duration: float) -> str:
    """
    根时间线 index.html。
    - 为每个 beat 生成 sub‑composition 容器
    - 扫描 audio_file/ 目录，将所有音频文件添加为全局音轨
    - 处理 track‑index 冲突，确保所有索引唯一
    """
    tokens = extract_design_tokens(design_content)

    # ── 1. 生成 beat clips ──────────────────────────────────────
    clip_lines = []
    for i, beat in enumerate(beats):
        beat_duration = round(beat["end"] - beat["start"], 2)
        # beat clips 的 track-index 从 1 开始
        clip_lines.append(
            f"    <div\n"
            f'      id="beat-clip-{i + 1}"\n'
            f'      data-composition-id="{beat["id"]}"\n'
            f'      data-composition-src="compositions/{beat["filename"]}"\n'
            f'      data-start="{beat["start"]}"\n'
            f'      data-duration="{beat_duration}"\n'
            f'      data-width="1080"\n'
            f'      data-height="1920"\n'
            f'      data-track-index="{i + 1}"\n'
            f"    ></div>"
        )
    clips_html = "\n".join(clip_lines)

    # ── 2. 扫描 audio_file/ 目录，生成所有音频标签 ────────────────
    audio_dir = PROJECT_DIR / "audio_file"  # 与 AUDIO_DIR 常量保持一致
    audio_tags = []
    if audio_dir.exists():
        # 按文件名排序，保证顺序稳定
        audio_files = sorted(audio_dir.glob("*.*"))
        for idx, audio_path in enumerate(audio_files):
            # 只保留常见音频格式
            if audio_path.suffix.lower() not in (".mp3", ".wav", ".ogg"):
                continue
            # track-index 从 len(beats)+1 开始，避免与 beat clips (1~len(beats)) 冲突
            track_idx = len(beats) + 1 + idx
            # 简单的音量推断：文件名含 bgm/music 给 0.4，其余（如旁白）给 1.0
            vol = (
                "0.4"
                if (
                    "bgm" in audio_path.stem.lower()
                    or "music" in audio_path.stem.lower()
                )
                else "1.0"
            )
            # 相对于项目根目录的路径（index.html 所在目录）
            rel_path = audio_path.relative_to(PROJECT_DIR).as_posix()
            audio_tags.append(
                f"    <audio\n"
                f'      id="el-audio-{idx}"\n'
                f'      data-start="0"\n'
                f'      data-duration="{total_duration:.2f}"\n'
                f'      data-track-index="{track_idx}"\n'
                f'      data-volume="{vol}"\n'
                f'      src="{rel_path}"\n'
                f"    ></audio>"
            )
    bgm_html = "\n\n".join(audio_tags) if audio_tags else ""

    # ── 3. 组装完整 HTML ─────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>爆款结构迁移 — 合成视频</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: {tokens["primary"]};
      width: 1080px;
      height: 1920px;
      overflow: hidden;
    }}
  </style>
</head>
<body>
  <!-- ★ root composition 必须有 data-start="0" -->
  <div
    id="root-composition"
    data-composition-id="root"
    data-start="0"
    data-duration="{total_duration:.2f}"
    data-width="1080"
    data-height="1920"
  >
{clips_html}{bgm_html}

    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script>
      // 根时间线：各 beat sub-composition 各自管理自己的 timeline
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["root"] = tl;
    </script>
  </div>
</body>
</html>
"""


def pipeline(video_path: str | Path, output_dir: str | Path):
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        print(f"❌ 未找到视频文件: {video_path}")
        sys.exit(1)

    print(f"\n{'=' * 62}")
    print("  爆款视频结构迁移引擎  v3.0")
    print(f"  视频 : {video_path.resolve()}")
    print(f"  输出 : {PROJECT_DIR}")
    print(f"{'=' * 62}\n")

    video = VideoClip(str(video_path))

    audio_vocal_path, audio_bgm_path = extract_vocal_and_bgm(video, output_dir)
    segments, total_text = extract_transcript(audio_vocal_path)
    scene_list = analyze_video_rhythm(video)

    # ── Step A: DESIGN.md ─────────────────────────────────────────
    print("【Step A】生成 DESIGN.md ...")
    design_md_path = output_dir / "DESIGN.md"
    design_content = (
        call_model(DESIGN_SYSTEM_PROMPT, DESIGN_MD_TEMPLATE, video.to_base64()) or ""
    )
    design_md_path.write_text(design_content, encoding="utf-8")
    print(f"✅ DESIGN.md → {design_md_path}")

    # ── Step B: SCRIPT.md ─────────────────────────────────────────
    print("\n【Step B】生成 SCRIPT.md ...")
    script_md_path = output_dir / "SCRIPT.md"
    script_prompt = build_script_prompt(
        segments, total_text, scene_list, video.duration, design_content
    )
    script_content = (
        call_model(SCRIPT_SYSTEM_PROMPT, script_prompt, video.to_base64()) or ""
    )
    script_md_path.write_text(script_content, encoding="utf-8")
    print(f"✅ SCRIPT.md → {script_md_path}")

    # ── Step C: STORYBOARD.md ────────────────────────────────────
    print("\n【Step C】生成 STORYBOARD.md ...")
    storyboard_md_path = output_dir / "STORYBOARD.md"
    sb_prompt = build_storyboard_prompt(
        segments, video.duration, design_content, script_content
    )
    storyboard_content = (
        call_model(STORYBOARD_SYSTEM_PROMPT, sb_prompt, video.to_base64()) or ""
    )
    storyboard_md_path.write_text(storyboard_content, encoding="utf-8")
    print(f"✅ STORYBOARD.md → {storyboard_md_path}")

    # ── Step D: narration.txt + transcript.json ───────────────────
    print("\n【Step D】生成 narration.txt + transcript.json ...")
    narration_txt_path = output_dir / "narration.txt"
    narration_clean = call_model(NARRATION_CLEAN_SYSTEM_PROMPT, script_content or "")

    narration_txt_path.write_text(narration_clean or "", encoding="utf-8")
    print(f"✅ narration.txt → {narration_txt_path}")

    # ── Step E: compositions/*.html + index.html ──────────────────
    print("\n【Step E】解析 Beat 结构并生成 compositions/ ...")
    beats = _parse_beats_from_storyboard(storyboard_content or "")

    if not beats:
        print("⚠️  STORYBOARD.md 中未解析到 Beat")
        sys.exit(1)

    print(f"检测到 {len(beats)} 个 Beat")
    compositions_dir = output_dir / "compositions"
    compositions_dir.mkdir(exist_ok=True)
    for idx, beat in enumerate(beats):
        is_final = idx == len(beats) - 1
        beat_filename = f"beat_{idx + 1}.html"
        beat_file = compositions_dir / beat_filename
        print(f"   → 生成 {beat_filename} (Beat {beat['num']}: {beat['label']}) ...")
        beat_section = extract_beat_section(storyboard_content, beat["num"])
        beat_prompt = build_composition_prompt(
            beat, design_content, beat_section, segments, is_final
        )
        html_content = call_model(COMPOSITION_HTML_SYSTEM_PROMPT, beat_prompt) or ""
        beat_file.write_text(html_content, encoding="utf-8")
        print(f"     ✅ {beat_file}")

    print("\n   → 生成 index.html ...")
    index_html_path = output_dir / "index.html"
    index_content = generate_index_html(beats, design_content, video.duration or 0)
    index_html_path.write_text(index_content, encoding="utf-8")
    print(f"✅ index.html → {index_html_path}")

    # ── 完成摘要 ─────────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print("  🎉 全部完成！")
    print(f"  DESIGN.md        → {design_md_path}")
    print(f"  SCRIPT.md        → {script_md_path}")
    print(f"  STORYBOARD.md    → {storyboard_md_path}")
    print(f"  narration.txt    → {narration_txt_path}")
    for b in beats:
        print(f"  compositions/{b['filename']}")
    print(f"  index.html       → {index_html_path}")
    print(f"{'=' * 62}")
    print()
    print("下一步（在 my-video/ 目录下执行）：")
    print("  npx hyperframes lint        # 应零 error")
    print("  npx hyperframes validate    # 运行时检查")
    print("  npx hyperframes preview     # 本地预览")
    print("  # 如需 TTS 配音：")
    print("  npx hyperframes tts SCRIPT.md --voice af_nova --output narration.wav")
    print("  npx hyperframes render --output output.mp4")
    print()


if __name__ == "__main__":
    import traceback

    video_path = "tests/videos/6.mp4"  # 替换为你的测试视频路径
    output_dir = "output"

    try:
        pipeline(video_path, output_dir)
    except Exception as e:
        traceback.print_exc()
        print(f"\n❌ 流水线失败: {e}")
        sys.exit(1)
