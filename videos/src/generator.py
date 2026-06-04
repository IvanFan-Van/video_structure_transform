"""
爆款视频结构迁移引擎 — 全自动 Remotion 项目生成管线

    Stage 0: 项目脚手架（从 _templates/ 复制骨架，离线安装依赖）
    Stage 1: 特征提取（ASR 转录 + 场景切镜检测）
    Stage 2: 多模态结构分析（seed-lite 视频 → structure.json）
    Stage 3: Remotion Prompt 生成（JSON → Markdown）
    Stage 4: AI 代码生成（Prompt → seed-lite → TSX 源码）
    Stage 5: 构建验证（pnpm build）

用法:
    python generator.py [video_path]
    python generator.py --dry-run [video_path]
    FONT_MIRROR="https://mirror1.com,https://mirror2.com" python generator.py
"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path

import cv2
import whisper
from dotenv import find_dotenv, load_dotenv
from moviepy import VideoFileClip
from openai import OpenAI

from video import probe_video, video_to_base64, VideoMeta

# ═══════════════════════════════════════════════════════════════════════
# 环境初始化
# ═══════════════════════════════════════════════════════════════════════

_DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / "backend" / ".env"
if _DOTENV_PATH.exists():
    load_dotenv(_DOTENV_PATH, override=True)
else:
    load_dotenv(find_dotenv(), override=True)

PROJECT_DIR = Path(__file__).resolve().parent.parent  # videos/
SRC_DIR = PROJECT_DIR / "src"
TEMPLATES_DIR = PROJECT_DIR / "_templates"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = PROJECT_DIR / "audio_file"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_FILENAME = "6-Scene-001.mp4"
VIDEO_PATH = PROJECT_DIR.parent / "backend" / "notebooks" / VIDEO_FILENAME

# ── 字体镜像配置 ──────────────────────────────────────────────────────
_FONT_MIRROR_TIMEOUT = 30

_FONT_MIRRORS: list[str] = []
_env_mirrors = os.getenv("FONT_MIRROR", "").strip()
if _env_mirrors:
    _FONT_MIRRORS = [m.strip() for m in _env_mirrors.split(",") if m.strip()]
else:
    _FONT_MIRRORS = [
        "https://fonts.gitee.com",
        "https://fonts.font.im",
    ]


def _check_font_mirror(mirror: str) -> str | None:
    """检测字体镜像是否可达，返回可用 URL 或 None。"""
    test_url = f"{mirror}/css2?family=Noto+Sans+SC:wght@400&display=swap"
    try:
        req = urllib.request.Request(test_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=_FONT_MIRROR_TIMEOUT) as resp:
            if resp.status == 200:
                return mirror
    except Exception:
        pass
    return None


def _get_font_mirror() -> str:
    """按顺序检测所有镜像源，返回第一个可用的 URL。"""
    for mirror in _FONT_MIRRORS:
        print(f"🔍 检测字体镜像 ({_FONT_MIRROR_TIMEOUT}s 超时): {mirror}")
        result = _check_font_mirror(mirror)
        if result:
            print(f"✅ 可用: {result}")
            return result
        print(f"⚠️ 不可用: {mirror}")
    raise RuntimeError(
        f"所有字体镜像均不可用，请设置 FONT_MIRROR 环境变量\n已尝试: {_FONT_MIRRORS}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Stage 0: 项目脚手架
# ═══════════════════════════════════════════════════════════════════════

_PNPM = shutil.which("pnpm")
if _PNPM is None:
    raise RuntimeError("未找到 pnpm，请先安装: npm install -g pnpm")


def _install_deps_offline(project_dir: Path) -> None:
    """离线安装依赖（利用 pnpm 全局 store 创建硬链接，无需网络）。"""
    print("📦 正在离线安装依赖 (pnpm install --offline)...")
    try:
        result = subprocess.run(
            [_PNPM, "install", "--offline", "--no-frozen-lockfile"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                "pnpm install --offline",
                output=result.stdout,
                stderr=result.stderr,
            )
        print("✅ 依赖安装完成")
    except FileNotFoundError:
        raise RuntimeError("未找到 pnpm，请先安装: npm install -g pnpm")
    except subprocess.TimeoutExpired:
        raise RuntimeError("pnpm install 超时 (120s)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"pnpm install --offline 失败\n"
            f"请确认已在 videos/ 下执行过 pnpm install\n"
            f"stderr:\n{e.stderr}"
        ) from e


def scaffold_remotion_project(video_name: str) -> Path:
    """Stage 0: 从 _templates/ 复制完整 Remotion 项目骨架。"""
    if not TEMPLATES_DIR.exists():
        raise FileNotFoundError(f"模板目录不存在: {TEMPLATES_DIR}")

    # Step 1: 确定输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = OUTPUT_DIR / f"{video_name}_{timestamp}"
    print(f"\n🏗️  Stage 0: 创建 Remotion 项目 → {project_dir}")

    # Step 2: 复制模板
    print("📋 正在复制项目模板...")
    shutil.copytree(TEMPLATES_DIR, project_dir)

    # Step 3: 替换字体占位符
    font_mirror = _get_font_mirror()
    css_path = project_dir / "src" / "index.css"
    css_content = css_path.read_text(encoding="utf-8")
    css_content = css_content.replace("__FONT_MIRROR_URL__", font_mirror)
    css_path.write_text(css_content, encoding="utf-8")
    print(f"🔤 字体源已配置: {font_mirror}")

    # Step 4: 创建 public/ 目录
    (project_dir / "public").mkdir(exist_ok=True)

    # Step 5: 离线安装依赖
    _install_deps_offline(project_dir)

    print(f"✅ Stage 0 完成: {project_dir}")
    return project_dir


# ═══════════════════════════════════════════════════════════════════════
# Stage 1: 特征提取
# ═══════════════════════════════════════════════════════════════════════


def extract_audio_and_transcript(video_path: str, audio_out: str):
    """提取音频并用 Whisper 做 ASR 转录。"""
    print("📢 正在提取音频...")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_out, logger=None)
    video.close()

    print("🗣️  正在 ASR 转录...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_out, word_timestamps=True)

    segments = [
        {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"]}
        for s in result["segments"]
    ]
    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append(
                {
                    "text": w["word"].strip(),
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3),
                }
            )
    return segments, result["text"], words


def analyze_video_rhythm(video_path: str, threshold: float = 30.0):
    """基于帧差检测镜头切点，返回 (切点列表, fps, 总时长)。"""
    print("🎬 正在分析视频节奏...")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    ret, prev_frame = cap.read()
    if not ret:
        cap.release()
        return [], fps, 0.0

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    cut_timestamps = []
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_index += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if cv2.absdiff(gray, prev_gray).mean() > threshold:
            cut_timestamps.append(round(frame_index / fps, 2))
        prev_gray = gray

    cap.release()
    video_duration = frame_index / fps if fps > 0 else 0.0
    return cut_timestamps, fps, video_duration


def extract_keyframes(video_path: str, num_keyframes: int = 5) -> list[dict]:
    """从视频均匀提取关键帧，返回 [{frame, time, image_b64}, ...] 列表。"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    if total_frames <= 0 or num_keyframes <= 0:
        cap.release()
        return []

    # 均匀选取帧索引
    indices = [
        int(i * (total_frames - 1) / max(num_keyframes - 1, 1))
        for i in range(num_keyframes)
    ]
    # 去重
    indices = sorted(set(indices))

    keyframes = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        # 压缩为 JPEG 再 base64
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        img_b64 = base64.b64encode(buf).decode("utf-8")
        keyframes.append(
            {
                "frame": idx,
                "time": round(idx / fps, 2),
                "image_b64": img_b64,
            }
        )

    cap.release()
    print(f"📸 已提取 {len(keyframes)} 个关键帧")
    return keyframes


# ═══════════════════════════════════════════════════════════════════════
# Stage 2: 单片多模态结构分析
# ═══════════════════════════════════════════════════════════════════════

_VLM_ANALYSIS_SYSTEM_PROMPT = (
    "你是一个专门解析短视频结构并输出标准 JSON 的后台 Agent。"
    "你精通 Remotion（React 视频框架）的动画模式，包括 useCurrentFrame、"
    "interpolate、spring、Easing、Sequence、AbsoluteFill 等 API。"
    "严禁包含任何 Markdown 格式包裹（如 ```json），只输出纯 JSON。"
)


def _build_vlm_analysis_prompt(
    segments: list,
    total_text: str,
    words: list,
    cuts: list,
    duration: float,
    fps: float,
    meta: VideoMeta,
) -> str:
    segs_str = "\n".join(
        f"[{s['start']}s - {s['end']}s]: {s['text']}" for s in segments
    )
    cuts_str = ", ".join(f"{t}s" for t in cuts[:40])
    total_frames = int(duration * fps)

    return f"""你是一个短视频结构分析专家。请先做创意分析，再转化为 Remotion 技术参数。

【视频数据】
- 分辨率: {meta.width}x{meta.height} | FPS: {fps} | 总帧数: {total_frames} | 时长: {duration:.1f}s
- 切镜点: [{cuts_str}] | 切镜数: {len(cuts)}

【台词】（可能为空）
{total_text}

【台词时间戳】
{segs_str}

━━━━━━ 第一部分: 创意分析层（先理解视频"为什么这样设计"）━━━━━━

{{
  "creative_analysis": {{
    "script_structure": {{
      "genre": "<视频类型: 纯文字快闪 / 知识口播 / 产品带货 / 情感共鸣 / 搞笑反转 / Vlog>",
      "sections": [
        {{ "label": "<Hook / 铺垫 / 反转 / 强化 / CTA收尾>", "start_s": <秒>, "end_s": <秒>,
           "core_message": "<这一段的叙事目标，一句话>",
           "text_focus": "<本段画面上的核心文字是什么>" }}
      ],
      "narrative_arc": "<叙事弧线: 设问→好奇→反转→强化→收尾>",
      "tone": "<语气: 悬疑/搞笑/严肃/温情/燃/治愈>"
    }},  // script_structure 结束

    // ★ rhythm/packaging/footage 与 script_structure 平级，不要嵌套在 script_structure 里面
    "rhythm_structure": {{
      "cut_frequency": "<切镜频率: 高频快切/匀速/单镜头长hold>",
      "perceived_bpm": "<感知BPM: ~80慢/~120中/~160快>",
      "climax_frame": <情绪最高点的帧号>,
      "emotion_curve": [
        {{ "start_frame": 0, "end_frame": <帧>, "intensity": "<low/mid/high/peak>", "label": "<情绪标签>" }}
      ]
    }},
    "packaging_structure": {{
      "global_watermark": {{ "text": "<常驻标识文字>", "position": "<bottom-center/top-right>", "font_size_px": <字号> }},
      "text_animation_style": "<文字动画总体风格: 弹性缩放+柔光外发光/故障glitch/手写描边/硬切快闪>",
      "highlight_strategy": {{
        "trigger": "<高亮触发条件: 打字完成后/特定帧/一直显示>",
        "target_text": "<被高亮的文字>",
        "style": "<红色半透明块/荧光笔扫过/闪烁强调>",
        "color": "<hex>"
      }},
      "primary_transition": "<主要转场: 淡出/硬切/滑动/缩放>"
    }},
    "footage_structure": {{
      "visual_type": "<纯文字渲染 / 实拍素材 / AI生成素材 / 混剪>",
      "color_palette_summary": "<配色一句话: 黑底白字红强调/白底黑字/...>",
      "requires_external_assets": false,
      "keyframe_snapshots": [
        {{ "frame": 0, "description": "<这一帧画面描述>" }},
        {{ "frame": <中段帧>, "description": "<这一帧画面描述>" }},
        {{ "frame": <末尾帧>, "description": "<这一帧画面描述>" }}
      ]
    }}
  }},  // ← creative_analysis 对象到此结束！

  // ═══ 以下字段与 creative_analysis 平级（顶级属性），不要嵌套在 creative_analysis 里面！═══

  "video_config": {{
    "fps": {fps},
    "width": {meta.width or 1080},
    "height": {meta.height or 1920},
    "durationInFrames": {total_frames},
    "duration_seconds": {duration}
  }},

  "global_style": {{
    "background_color": "<hex>",
    "text_color": "<hex>",
    "accent_color": "<hex>",
    "font_family": "\\"Noto Serif SC\\", serif",
    "visual_tone": "<与 creative_analysis.tone 一致>",
    "text_shadow": {{ "enabled": true/false, "color": "<hex>", "blur_px": <数值>, "description": "<描述>" }},
    "bgm_description": "<BGM风格>"
  }},

  "layers": [
    {{ "name": "<如 bg / watermark / main_text / highlight>", "z_index": <0起>, "element_type": "<solid/text/shape>", "always_visible": true/false }}
  ],

  "scenes": [
    {{
      "scene_id": 1,
      "start_frame": 0,
      "end_frame": <帧号>,
      "role": "<必须与 creative_analysis.script_structure.sections[].label 一致>",
      "background": {{ "type": "solid", "value": "<hex>" }},
      "elements": [
        {{
          "element_id": "<唯一名>",
          "type": "<text / shape>",
          "text": "<文字内容>",
          "font_size_px": <数值>,
          "color": "<hex>",
          "font_weight": <400/500/700>,
          "position": {{ "x_percent": <0-100>, "y_percent": <0-100> }},
          "animation_phases": [
            {{ "phase": "<enter/hold/shift/exit>", "start_frame": <绝对帧号>, "end_frame": <绝对帧号>,
               "property": "<opacity/translateX_px/scale/...>", "from_value": <数值>, "to_value": <数值>,
               "easing": "<Easing.out(Easing.exp) / Easing.linear / 等>",
               "note": "<描述>" }}
          ],
          "effect": "<typewriter/highlight/glow/glitch/fade/static>",
          "effect_params": {{
            "typewriter": {{ "chars_per_second": 0 }},
            "highlight": {{ "color": "<hex>", "delay_frames": 0, "duration_frames": 0 }},
            "glow": {{ "intensity_px": 0 }}
          }},
          "animation_phases": []  // ★ cv2 测量引擎会填充，LLM 不需要填数值
        }}
      ],
      "motion_effects": [
        {{ "type": "<focus_zoom/ken_burns>", "start_frame": <帧>, "end_frame": <帧>,
           "params": {{ "scale_from": <数值>, "scale_to": <数值>, "target_x_percent": <0-100>, "target_y_percent": <0-100> }} }}
      ],
      "transition_out": {{ "type": "<cut/fade/slide>", "start_frame": <帧>, "duration_frames": <≥6> }},
      "narration_text": "<台词原文>"
    }}
  ],

  "remotion_techniques": ["<需要的 Remotion API 列表>"],
  "existing_components_to_reuse": ["<TypewriterText/ZoomWrapper/FocusZoomWrapper/HighlightText>"],
  "new_components_needed": [
    {{ "name": "<PascalCase>", "reason": "<why>", "props": {{}}, "implementation_hint": "<how>" }}
  ]
}}

【分析铁律】
1. creative_analysis 必须优先完成——它是后续所有技术参数的基础
2. scenes[].role 必须与 creative_analysis.script_structure.sections[].label 保持一致
3. 每个元素的动画必须拆分为多个 phase（enter → hold → shift → exit）
4. 位置用百分比（x_percent/y_percent），画布中心为 (50, 50)
5. 分层描述遮挡关系（layers 数组）
6. 所有 frame 值在 0~{total_frames - 1} 范围内
7. transition_out.duration_frames ≥ 6
"""


def _parse_llm_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json") :].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```") :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return json.loads(cleaned)


def _call_seed_lite_multimodal(
    system_prompt: str,
    user_prompt: str,
    video_b64: str | None = None,
    images: list[str] | None = None,
    max_tokens: int = 8192,
) -> str:
    """调用火山引擎 seed-lite（支持视频或图片输入）。"""
    client = OpenAI(
        api_key=os.getenv("API_KEY", ""),
        base_url=os.getenv("BASE_URL", ""),
    )
    model = os.getenv("MODEL", "")
    content: list[dict] = []
    if video_b64:
        content.append(
            {
                "type": "video_url",
                "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
            }
        )
    if images:
        for img in images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img}",
                        "detail": "low",
                    },
                }
            )
    content.append({"type": "text", "text": user_prompt})
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content.strip()


# ═══════════════════════════════════════════════════════════════════════
# Stage 3: Remotion Prompt 生成
# ═══════════════════════════════════════════════════════════════════════


def _generate_remotion_prompt(analysis: dict) -> str:
    ca = analysis.get("creative_analysis", {})

    # 兼容两种嵌套：video_config 可能在顶层，也可能在 creative_analysis 内部
    def _get(*keys, default=None):
        for k in keys:
            if k in analysis:
                return analysis[k]
        if isinstance(ca, dict):
            for k in keys:
                if k in ca:
                    return ca[k]
        return default

    vc = _get("video_config", default={})
    gs = _get("global_style", default={})
    ca_data = ca if ca else analysis
    scenes = _get("scenes", default=[])
    techniques = _get("remotion_techniques", default=[])
    existing = _get("existing_components_to_reuse", default=[])
    new_needed = _get("new_components_needed", default=[])

    lines = []
    lines.append("# Remotion 视频代码生成 Prompt\n")

    # ── 创意分析摘要（新增）──
    if ca_data:
        lines.append("## 创意分析摘要\n")
        ss = ca_data.get("script_structure", {})
        # 兼容 rhythm/packaging/footage 在 creative_analysis 顶层或 script_structure 内部
        rs = ca_data.get("rhythm_structure") or ss.get("rhythm_structure", {})
        ps = ca_data.get("packaging_structure") or ss.get("packaging_structure", {})
        fs = ca_data.get("footage_structure") or ss.get("footage_structure", {})

        if ss.get("genre"):
            lines.append(f"- **类型**: {ss['genre']}")
        if ss.get("narrative_arc"):
            lines.append(
                f"- **叙事**: {ss['narrative_arc']} | 语气: {ss.get('tone', '')}"
            )
        if rs.get("perceived_bpm"):
            lines.append(
                f"- **节奏**: {rs['perceived_bpm']} | 高潮帧: {rs.get('climax_frame', 'N/A')}"
            )
        if isinstance(ps.get("highlight_strategy"), dict):
            hs = ps["highlight_strategy"]
            lines.append(
                f'- **高亮**: "{hs.get("target_text", "")}" | 触发: {hs.get("trigger", "")} | 样式: {hs.get("style", "")} | 色: {hs.get("color", "")}'
            )
        if fs.get("visual_type"):
            lines.append(
                f"- **素材**: {fs['visual_type']} | {fs.get('color_palette_summary', '')}"
            )
        if fs.get("requires_external_assets"):
            lines.append(f"- ⚠️ 需要外部素材: 是")
        lines.append("")

    lines.append("## 1. 视频配置\n```tsx")
    lines.append(
        f'<Composition id="RecreatedVideo" component={{MainComposition}}\n'
        f"  durationInFrames={{ {vc['durationInFrames']} }} fps={{ {vc['fps']} }}"
        f" width={{ {vc['width']} }} height={{ {vc['height']} }} />\n```\n"
    )
    lines.append("## 2. 全局设计\n")
    lines.append(
        f"- 背景: `{gs.get('background_color', '#000')}` | 文字: `{gs.get('text_color', '#fff')}` | 强调: `{gs.get('accent_color', '#f00')}`"
    )
    ts = gs.get("text_shadow", {})
    if ts and ts.get("enabled"):
        lines.append(
            f"- 发光: {ts.get('color', '#fff')} {ts.get('blur_px', 10)}px | {gs.get('visual_tone', '')}"
        )

    layers = _get("layers", default=[])
    if layers:
        lines.append("## 3. 图层\n")
        for layer in sorted(layers, key=lambda x: x["z_index"]):
            lines.append(
                f"  z={layer['z_index']}: {layer['name']} ({layer['element_type']})"
            )
        lines.append("")

    if existing:
        lines.append(f"### 现有组件: {', '.join(existing)}")
    if new_needed:
        lines.append("### 需新建组件:")
        for nc in new_needed:
            if isinstance(nc, str):
                lines.append(f"  - {nc}")
            else:
                lines.append(
                    f"  - **{nc['name']}**: {nc['reason']} | Hint: {nc.get('implementation_hint', '')}"
                )
        lines.append("")

    lines.append("## 4. 分场景帧级描述\n")
    for scene in scenes:
        sid = scene["scene_id"]
        sf = scene.get(
            "start_frame", int(scene.get("start_time", 0) * vc.get("fps", 30))
        )
        ef = scene.get("end_frame", int(scene.get("end_time", 0) * vc.get("fps", 30)))
        role = scene.get("role", "")
        bg = scene.get("background", {})

        lines.append(f"### Scene {sid} — {role} (帧 {sf}~{ef}, {ef - sf} 帧)\n")
        lines.append(f"背景: {bg.get('type', 'solid')} — {bg.get('value', '#000')}")

        for elem in scene.get("elements", []):
            eid = elem.get("element_id", "")
            text = elem.get("text", "")
            fs = elem.get("font_size_px", 60)
            color = elem.get("color", "#fff")
            pos = elem.get("position", {})
            px = pos.get("x_percent", 50) if isinstance(pos, dict) else "center"
            py = pos.get("y_percent", 50) if isinstance(pos, dict) else "center"
            eff = elem.get("effect", "static")
            ep = elem.get("effect_params", {})

            lines.append(
                f'  [{eid}] "{text}" | {fs}px | {color} | ({px}%, {py}%) | {eff}'
            )
            if eff == "typewriter" and isinstance(ep, dict) and "typewriter" in ep:
                cps = ep["typewriter"].get("chars_per_second", 5)
                tlen = len(text) if text else 8
                lines.append(
                    f"    ★ speed={{{cps}}} (text.length={tlen}, {tlen / cps:.1f}s)"
                )
            if eff == "highlight" and isinstance(ep, dict) and "highlight" in ep:
                hi = ep["highlight"]
                lines.append(
                    f"    ★ HighlightText delay={{{hi.get('delay_frames', 0)}}} duration={{{hi.get('duration_frames', 30)}}}"
                )

            for ph in elem.get("animation_phases", []):
                lines.append(
                    f"    [{ph.get('phase', '')}] f{ph.get('start_frame', 0)}→{ph.get('end_frame', 0)} "
                    f"{ph.get('property', '')}: {ph.get('from_value', 0)}→{ph.get('to_value', 0)} "
                    f"({ph.get('easing', 'linear')})"
                )

        for m in scene.get("motion_effects", []):
            p = m.get("params", {})
            lines.append(
                f"  镜头: {m.get('type', '')} f{m.get('start_frame', 0)}→{m.get('end_frame', 0)} scale {p.get('scale_from', 1)}→{p.get('scale_to', 1)}"
            )

        tr = scene.get("transition_out", {})
        if isinstance(tr, dict):
            lines.append(
                f"  转场: {tr.get('type', 'cut')} @f{tr.get('start_frame', 0)} ({tr.get('duration_frames', 1)}帧)"
            )
        nar = scene.get("narration_text", "")
        if nar:
            lines.append(f'  台词: "{nar}"')
        lines.append("")

    lines.append("## 5. 代码生成指南\n")
    lines.append(
        "1. 禁止 CSS transition/animation — 用 useCurrentFrame + interpolate/spring"
    )
    lines.append("2. animation_phases 中的帧号和属性值必须精确复现")
    lines.append("3. TypewriterText speed 值见上方 ★ 标注，直接使用不重新计算")
    lines.append("4. HighlightText delay/duration 值见上方 ★ 标注，直接使用不重新计算")
    lines.append("5. 文字高亮必须用 HighlightText 组件，禁止手写绝对定位色块")
    lines.append(
        "6. Easing 白名单: linear, ease, quad, cubic, sin, circle, exp, elastic, back, bounce"
    )
    lines.append(
        "   ★ 禁止: Easing.sine, Easing.smooth, Easing.expo — 这些会导致运行时报错"
    )
    lines.append("7. JSX 中 > < & 等特殊字符用 {''} 包裹或 HTML 实体")
    lines.append("8. 不要编造不存在的文件路径，不要使用 Audio/Video\n")
    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════════════════
# Stage 4: AI 代码生成
# ═══════════════════════════════════════════════════════════════════════

_CODEGEN_SYSTEM_PROMPT = """\
你是一个精通 Remotion 4.x (React 19 + TypeScript) 的视频代码生成专家。
请根据提供的分析 JSON 和 Prompt，直接生成**可运行**的 Remotion TypeScript 源代码。

━━━━━━ 技术规范（必须严格遵守）━━━━━━

【Remotion 核心规则】
1. 绝对禁止 CSS transition/animation/Tailwind animate-*
2. 所有动画必须用 useCurrentFrame() + interpolate() 或 spring()
3. Easing 白名单（仅允许以下 10 个，写错立即崩溃）:
   linear, ease, quad, cubic, sin, circle, exp, elastic, back, bounce
   ★ 注意: sin 不是 sine | exp 不是 expo | quad 不是 quadOut
   禁止: Easing.sine, Easing.smooth, Easing.expo, Easing.easeIn, Easing.easeOut
4. 用 <Sequence from={...} durationInFrames={...}> 控制时序
5. 用 <AbsoluteFill> 做全屏容器
6. spring() 必须提供 fps: const { fps } = useVideoConfig()
7. interpolate() 必须设 extrapolateLeft/Right: "clamp"
8. ★ 关键帧参考: 仔细对照 prompt 中的截图，复现文字的像素位置、字号、颜色和间距

━━━━━━ 三层组件决策树（按优先级选择）━━━━━━

【第 1 层: @remotion/* 生态包（已安装，直接 import 使用）】

  @remotion/transitions — 转场特效 ★ 仅多场景（scenes.length > 1）可用
    import {{ TransitionSeries }} from "@remotion/transitions";
    用法: <TransitionSeries><TransitionSeries.Sequence durationInFrames={{30}}>...</TransitionSeries.Sequence></TransitionSeries>
    ★ 单场景视频（只有 1 个 scene）禁止使用 TransitionSeries，直接渲染即可

  @remotion/shapes — 几何图形
    import { Circle, Rect, Star, Triangle, Heart, Ellipse, Pie, Polygon, Arrow } from "@remotion/shapes";
    用法: <Circle radius={100} fill="#fff" stroke="#f00" strokeWidth={4} />

  @remotion/paths — SVG 路径动画
    import { interpolatePath, evolvePath, getLength, getPointAtLength } from "@remotion/paths";
    用法: const d = interpolatePath(currentProgress, [0, 1], [pathA, pathB]);

  @remotion/noise — 程序化噪点/纹理
    import { noise2D, noise3D, noise4D } from "@remotion/noise";
    用法: const value = noise2D("seed", frame * 0.05, 0); // → 0~1 用于随机位移/闪烁

  @remotion/light-leaks — 漏光叠层
    import { LightLeaks } from "@remotion/light-leaks";
    用法: <LightLeaks type="3" overlayOpacity={0.4} />

【第 2 层: 项目现有组件（位于 src/，直接 import）】
  文件名 → 导出:
    TypewriterText.tsx → TypewriterText
      Props: {{ text: string, speed?: number, fontSize?: number, color?: string, fontFamily?: string }}
      ★ speed 计算公式: speed = text.length / 持续秒数 (如 8字/1.1s = 7.3)
      ★ speed 必须 ≥ 2，禁止 speed={{1}} 或 speed={{30/fps}}
      ★ 限制: 不接受 children，不能在其中嵌套其他组件
      ★ 如果文字需要同时打字+高亮 → 看下方「组件组合模式」

    ZoomWrapper.tsx → ZoomWrapper
      Props: {{ children: ReactNode, zoomStartFrame: number, zoomScale?: number }}
    FocusZoom.tsx → FocusZoomWrapper
      Props: {{ children: ReactNode, zoomStartFrame: number, zoomScale: number, targetX: number, targetY: number }}
    HighlightText.tsx → HighlightText
      Props: {{ children: ReactNode, color?: string, delay?: number, duration?: number }}
      ★ 作用: 在文字后方渲染水平展开的高亮色条
      ★ 强制: 任何文字高亮必须用 HighlightText，禁止手写 position:absolute 色块
      ★ delay 含义: 从当前 Sequence/时间轴起点算起的帧偏移（组件内部用 frame - delay 处理）
      ★ 用法: <span>那天我问了个<HighlightText delay={{35}} duration={{20}}>问题</HighlightText></span>
      ★ delay 计算公式: delay = (高亮起始字符索引 / chars_per_second) * fps

【组件组合模式 — 必须遵守】

当一段文字需要「逐字打字 + 部分文字高亮」时:
  TypewriterText 不接受 children → 无法嵌套 HighlightText

  ★ 正确做法: 手写打字逻辑（放弃 TypewriterText），显式控制高亮出现时机:

  const fullText = "那天我问了个问题";
  const speed = 7.0;  // 与 structure.json 中 effect_params.typewriter.chars_per_second 相同
  const charCount = Math.floor(frame / (fps / speed));
  const visible = fullText.slice(0, charCount);  // ★ 变量名必须叫 visible，禁止改名 visibleText/slicedText
  const highlightStartIdx = fullText.length - 2;  // 高亮最后 N 个字

  // HighlightText delay = 高亮文字在打字序列中出现的那一帧
  // 公式: (高亮起始字符索引 / chars_per_second) * fps
  const highlightFrame = Math.floor((highlightStartIdx / speed) * fps);

  return (
    <span style={{...}}>
      {{visible.slice(0, highlightStartIdx)}}
      {{highlightStartIdx < charCount ? (
        <HighlightText delay={{highlightFrame}} duration={{...}}>
          {{fullText.slice(highlightStartIdx)}}
        </HighlightText>
      ) : fullText.slice(highlightStartIdx)}}
    </span>
  );

【第 3 层: AI 自行生成新组件 ★ 极其重要 ★】
  如果所需特效/剪辑手法在第 1 层和第 2 层都找不到匹配 → 你必须自行生成新组件！
  新组件必须同时满足:
    (a) 是独立文件 — 用 ### FILE: src/EffectName.tsx 输出
    (b) 有明确的 Props 接口（接受时间控制参数）
    (c) 完全用 useCurrentFrame + interpolate/spring + CSS transform/SVG 实现
    (d) 每个组件只做一件事（单一职责）
  新组件的命名规范: PascalCase，文件名 = 组件名.tsx
  新组件的文件块放在 MainComposition 和 Root 之前

【导入规范】
  // from remotion:
  import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing, spring, Sequence } from "remotion";
  // from 生态包（仅在需要时导入）:
  import { Circle, Rect, Star } from "@remotion/shapes";
  import { noise2D } from "@remotion/noise";
  // ★ @remotion/transitions 仅多场景视频（scenes.length > 1）可用，单场景禁止使用
  // from 现有组件:
  import { TypewriterText } from "./TypewriterText";
  import { ZoomWrapper } from "./ZoomWrapper";
  import { FocusZoomWrapper } from "./FocusZoom";
  import { HighlightText } from "./HighlightText";

【JSX 注意】
  - 文本中的 < > & 必须用 {""} 包裹：{"11亿 > 10亿"}
  - 不要编造不存在的文件路径
  - 不要使用 Audio/Video 组件（项目无素材文件）
  - fontFamily 统一用: '"Noto Serif SC", serif'

【精度铁律 — 必须遵守，不允许偏差】
  1. 所有数值必须从 analysis_json.animation_phases 中提取，不得编造
  2. 帧号、缩放值、透明度、位移必须与 animation_phases 的 start_frame/end_frame/from_value/to_value 一致
  3. easing 必须与 animation_phases 中声明的完全一致
  4. 颜色必须与 scene.elements[].color 一致
  5. 禁止 position:absolute + 硬编码像素偏移，位移用 interpolate → translateX/translateY

【Root.tsx 规范】
  import { Composition } from "remotion";
  import MainComposition from "./MainComposition";
  import "./index.css";
  export const RemotionRoot = () => {
    return (<Composition id="RecreatedVideo" component={MainComposition}
      durationInFrames={...} fps={...} width={...} height={...} />);
  };
  ★ Root.tsx 绝对不要 import registerRoot，不要调用 registerRoot()

【输出格式 — 必须严格遵守】
以文件块格式输出，新组件文件在前，MainComposition 在中间，Root.tsx 在最后：

### FILE: src/NewEffect.tsx
```tsx
// ...新组件源码...
```

### FILE: src/MainComposition.tsx
```tsx
// ...主合成源码...
```

### FILE: src/Root.tsx
```tsx
// ...根注册源码...
```

注意: ### FILE: 独占一行，代码块以 ```tsx 开头 ``` 结尾，不输出任何解释文字。
"""


def _build_codegen_user_prompt(
    remotion_prompt: str,
    analysis_json: dict,
    meta: VideoMeta,
    keyframes: list[dict],
) -> list[dict]:
    """构造代码生成的 user prompt（含关键帧图片）。"""
    content: list[dict] = []

    # 先放文字指令（让模型先理解任务，再参考图片）
    content.append(
        {
            "type": "text",
            "text": f"""请根据以下分析、Prompt 和**视频关键帧截图**，精确生成 Remotion TypeScript 源代码。

【视频元数据】
- 分辨率: {meta.width}x{meta.height}, FPS: {meta.fps}, 时长: {meta.duration}s

【结构分析 JSON（帧级精度）】
{json.dumps(analysis_json, ensure_ascii=False, indent=2)}

【Remotion 项目 Prompt】
{remotion_prompt}

【关键要求】
- MainComposition 必须是 default export
- 所有动画用 useCurrentFrame + interpolate/spring，参考 animation_phases 中的精确帧号
- 单场景视频（scenes.length=1）禁止使用 TransitionSeries，直接用 AbsoluteFill 包裹即可
- 参考关键帧中的像素级位置，精确复现 position.x_percent / y_percent
- 特效实现按三层决策: @remotion/* 生态包 → 现有组件 → 自行生成新组件
- 现有组件: TypewriterText, ZoomWrapper, FocusZoomWrapper, HighlightText
- 无匹配特效时必须自行生成新组件文件（### FILE: src/YourEffect.tsx）
- 代码必须完整可运行
- Root.tsx 不包含 registerRoot

以下是视频关键帧截图，用于验证文字位置、颜色、大小和间距：""",
        }
    )

    # 再放关键帧图片
    for kf in keyframes:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{kf['image_b64']}",
                    "detail": "low",
                },
            }
        )

    # 最后追加执行指令
    content.append(
        {
            "type": "text",
            "text": "现在请输出文件块。",
        }
    )

    return content


def _call_seed_lite_codegen(
    system_prompt: str,
    user_content: list[dict],
) -> str:
    """调用 seed-lite 生成代码（支持图片输入）。"""
    client = OpenAI(
        api_key=os.getenv("API_KEY", ""),
        base_url=os.getenv("BASE_URL", ""),
    )
    model = os.getenv("MODEL", "")
    print(
        f"🤖 正在请求模型生成 Remotion 代码（含 {sum(1 for c in user_content if c['type'] == 'image_url')} 张关键帧参考）..."
    )
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=16384,
    )
    return completion.choices[0].message.content.strip()


def _parse_codegen_response(raw: str) -> dict[str, str]:
    files: dict[str, str] = {}
    pattern = re.compile(
        r"###\s*FILE:\s*(src/[\w./-]+)\s*\n\s*```(?:tsx|typescript)?\s*\n(.*?)```",
        re.DOTALL,
    )
    for m in pattern.finditer(raw):
        filepath = m.group(1).strip()
        code = m.group(2).rstrip()
        files[filepath] = code + "\n"
    return files


def _write_code_files(files: dict[str, str], project_dir: Path) -> list[str]:
    written = []
    src_dir = project_dir / "src"
    for rel_path, code in files.items():
        target = src_dir / Path(rel_path).name
        target.write_text(code, encoding="utf-8")
        written.append(str(target))
        print(f"✅ 已写入: {target}")
    return written


def _recycle_new_components(project_dir: Path) -> list[str]:
    """构建成功后，将新生成的组件回收到 _templates/src/ 供下次复用。"""
    known = {
        "index.ts",
        "index.css",
        "Root.tsx",
        "MainComposition.tsx",
        "TypewriterText.tsx",
        "ZoomWrapper.tsx",
        "FocusZoom.tsx",
        "HighlightText.tsx",
    }
    recycled = []
    src_dir = project_dir / "src"
    template_src = TEMPLATES_DIR / "src"

    if not src_dir.exists():
        return recycled

    for f in sorted(src_dir.glob("*.tsx")):
        if f.name not in known:
            dest = template_src / f.name
            shutil.copy2(f, dest)
            recycled.append(f.name)
            print(f"♻️  回收新组件 → _templates/src/{f.name}")

    if recycled:
        print(f"✅ 已回收 {len(recycled)} 个新组件到模板库")
    return recycled


# ═══════════════════════════════════════════════════════════════════════
# Stage 5: 构建验证
# ═══════════════════════════════════════════════════════════════════════


def _verify_build(project_dir: Path) -> None:
    """验证项目能否成功构建。"""
    print("🔨 正在验证构建 (pnpm build)...")
    try:
        result = subprocess.run(
            [_PNPM, "build"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            error_lines = [
                l for l in result.stderr.split("\n") if "ERROR" in l or "error" in l
            ]
            raise RuntimeError(
                f"构建失败！项目无法编译\n错误摘要:\n" + "\n".join(error_lines[:10])
            )
        print("✅ 构建验证通过")
    except FileNotFoundError:
        raise RuntimeError("未找到 pnpm 命令")
    except subprocess.TimeoutExpired:
        raise RuntimeError("pnpm build 超时 (120s)")


# ═══════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════


def main(video_path: str = "", dry_run: bool = False):
    vpath = Path(video_path) if video_path else VIDEO_PATH
    if not vpath.exists():
        print(f"❌ 未找到视频文件: {vpath}")
        sys.exit(1)

    video_name = vpath.stem
    output_audio = AUDIO_DIR / f"{video_name}_temp_audio.wav"

    print(f"\n{'=' * 62}")
    print("  爆款视频结构迁移引擎  v6.0 — 全自动 Remotion 项目生成")
    print(f"  视频 : {vpath.name}")
    print(f"{'=' * 62}")

    # ── Stage 0: 项目脚手架 ──────────────────────────────────────
    project_dir = scaffold_remotion_project(video_name)

    # ── Stage 1: 特征提取 ────────────────────────────────────────
    print("\n【Stage 1】提取音视频特征...")
    meta = probe_video(str(vpath))
    segments, total_text, whisper_words = extract_audio_and_transcript(
        str(vpath), str(output_audio)
    )
    cuts, fps, video_duration = analyze_video_rhythm(str(vpath))
    print(
        f"✅ 时长 {video_duration:.1f}s | 切镜 {len(cuts)}个 | "
        f"段落 {len(segments)}段 | 单词 {len(whisper_words)}个"
    )

    # ── Stage 2: 多模态结构分析 ──────────────────────────────────
    print("\n【Stage 2】多模态模型结构分析...")
    video_b64 = video_to_base64(str(vpath))
    analysis_prompt = _build_vlm_analysis_prompt(
        segments, total_text, whisper_words, cuts, video_duration, fps, meta
    )
    llm_raw = _call_seed_lite_multimodal(
        _VLM_ANALYSIS_SYSTEM_PROMPT,
        analysis_prompt,
        video_b64=video_b64,
        max_tokens=16384,
    )
    analysis_json = _parse_llm_json(llm_raw)

    # ── Stage 2b: cv2 逐帧测量动画参数 ─────────────────────────
    print("\n【Stage 2b】cv2 逐帧测量动画参数...")
    from video_measure import measure_scene_animation

    for scene in analysis_json.get("scenes", []):
        sf = scene.get("start_frame", 0)
        ef = scene.get("end_frame", 0)
        if ef - sf <= 1:
            continue
        print(f"  📐 场景{scene['scene_id']} [{scene.get('role', '')}] 帧{sf}~{ef}...")
        measured = measure_scene_animation(str(vpath), scene, fps)
        for me in measured.get("elements", []):
            eid = me["element_id"]
            # 找到对应的 element 并填入 cv2 测量结果
            for elem in scene.get("elements", []):
                if elem.get("element_id") == eid:
                    elem["animation_phases"] = me.get("animation_phases", [])
                    if me.get("effect_params"):
                        elem["effect_params"].update(me["effect_params"])
                    count = len(elem["animation_phases"])
                    print(f"    ✓ {eid}: {count} phases measured")
                    break

    structure_path = project_dir / f"{video_name}_structure.json"
    structure_path.write_text(
        json.dumps(analysis_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"📄 结构分析: {structure_path}")

    # ── Stage 3: Remotion Prompt ─────────────────────────────────
    print("\n【Stage 3】生成 Remotion 代码 Prompt...")
    remotion_prompt = _generate_remotion_prompt(analysis_json)
    prompt_path = project_dir / f"{video_name}_remotion_prompt.md"
    prompt_path.write_text(remotion_prompt, encoding="utf-8")
    print(f"📄 Remotion Prompt: {prompt_path}")

    if dry_run:
        print(f"\n{'=' * 62}")
        print(f"  🔍 dry-run 完成 — 项目已创建: {project_dir}")
        print(f"{'=' * 62}\n")
        return

    # ── Stage 4: AI 代码生成 ─────────────────────────────────────
    print("\n【Stage 4】seed-lite 生成 Remotion 源代码...")
    keyframes = extract_keyframes(str(vpath), num_keyframes=5)
    codegen_content = _build_codegen_user_prompt(
        remotion_prompt, analysis_json, meta, keyframes
    )
    codegen_raw = _call_seed_lite_codegen(_CODEGEN_SYSTEM_PROMPT, codegen_content)

    raw_path = project_dir / f"{video_name}_codegen_raw.txt"
    raw_path.write_text(codegen_raw, encoding="utf-8")
    print(f"📄 原始输出: {raw_path}")

    files = _parse_codegen_response(codegen_raw)
    if not files:
        raise RuntimeError(f"未能从模型输出中解析出文件块\n请检查原始输出: {raw_path}")
    print(f"\n📝 解析到 {len(files)} 个文件:")
    for fp in files:
        print(f"   - {fp}")
    _write_code_files(files, project_dir)

    # ── Stage 5: 构建验证 ────────────────────────────────────────
    print("\n【Stage 5】构建验证...")
    _verify_build(project_dir)

    # ── 回收新组件到模板库 ──────────────────────────────────────
    recycled = _recycle_new_components(project_dir)

    # ── 完成 ──────────────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print("  ✅ 全流程完成！")
    print(f"  项目目录: {project_dir}")
    if recycled:
        print(f"  新组件已回收: {', '.join(recycled)}")
    print(f"{'=' * 62}")
    print(f"\n▶️  运行预览: cd {project_dir} && pnpm dev")
    print(
        f"🎬 渲染视频: cd {project_dir} && npx remotion render RecreatedVideo output.mp4\n"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")
    video_arg = args[0] if args else ""

    try:
        main(video_arg, dry_run=dry_run)
    except Exception as e:
        traceback.print_exc()
        print(f"\n❌ 流水线终止: {e}")
        sys.exit(1)
