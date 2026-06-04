"""
爆款视频结构迁移引擎 v2 — 基于 remocn 组件库的两阶段 LLM 管线

    Stage 0: 项目脚手架（从 _templates/ 复制骨架，离线安装依赖）
    Stage 1: 特征提取（ASR 转录 + 场景切镜检测）
    Stage 2: ★ 第一轮 LLM — 特效检测
             输入: 视频 + remocn 58 组件紧凑目录
             输出: { matched: [...], missing: [...] }
    Stage 3: ★ 第二轮 LLM — 参数推导 + 代码生成
             输入: 视频 + matched 组件完整文档 + missing 描述
             输出: 完整 TSX 源码
    Stage 4: 构建验证（pnpm build）

用法:
    python test_generator.py [video_path]
    python test_generator.py --dry-run [video_path]
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

# Python 路径：使 src/ 下的模块（video.py）可被导入
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from video import probe_video, video_to_base64, VideoMeta  # noqa: E402
from audio_analysis import analyze_bgm, format_bgm_features

# ═══════════════════════════════════════════════════════════════════════
# 环境初始化
# ═══════════════════════════════════════════════════════════════════════

_DOTENV_PATH = Path(__file__).resolve().parent.parent / "backend" / ".env"
if _DOTENV_PATH.exists():
    load_dotenv(_DOTENV_PATH, override=True)
else:
    load_dotenv(find_dotenv(), override=True)

PROJECT_DIR = Path(__file__).resolve().parent  # videos/
TEMPLATES_DIR = PROJECT_DIR / "_templates"
EFFECTS_DIR = PROJECT_DIR / "effects"
COMPONENTS_JSON = PROJECT_DIR / "remocn_components.json"
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
    print("📦 正在离线安装依赖 (pnpm install --offline)...")
    try:
        result = subprocess.run(
            [_PNPM, "install", "--offline", "--no-frozen-lockfile"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = OUTPUT_DIR / f"{video_name}_{timestamp}"
    print(f"\n🏗️  Stage 0: 创建 Remotion 项目 → {project_dir}")

    print("📋 正在复制项目模板...")
    shutil.copytree(TEMPLATES_DIR, project_dir)

    # 替换字体占位符
    font_mirror = _get_font_mirror()
    css_path = project_dir / "src" / "index.css"
    css_content = css_path.read_text(encoding="utf-8")
    css_content = css_content.replace("__FONT_MIRROR_URL__", font_mirror)
    css_path.write_text(css_content, encoding="utf-8")
    print(f"🔤 字体源已配置: {font_mirror}")

    (project_dir / "public").mkdir(exist_ok=True)

    _install_deps_offline(project_dir)
    print(f"✅ Stage 0 完成: {project_dir}")
    return project_dir


# ═══════════════════════════════════════════════════════════════════════
# Stage 1: 特征提取
# ═══════════════════════════════════════════════════════════════════════


def extract_audio_and_transcript(video_path: str, audio_out: str):
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

    indices = [
        int(i * (total_frames - 1) / max(num_keyframes - 1, 1))
        for i in range(num_keyframes)
    ]
    indices = sorted(set(indices))

    keyframes = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
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
# LLM 调用
# ═══════════════════════════════════════════════════════════════════════


def call_model(
    system_prompt: str,
    user_prompt: str,
    video_b64: str | None = None,
    max_tokens: int = 16384,
) -> str:
    """调用多模态模型，返回文本内容。"""
    client = OpenAI(
        api_key=os.getenv("API_KEY", ""),
        base_url=os.getenv("BASE_URL", ""),
    )

    user_content: list[dict] = []

    if video_b64:
        user_content.append(
            {
                "type": "video_url",
                "video_url": {"url": f"data:video/mp4;base64,{video_b64}"},
            }
        )

    user_content.append({"type": "text", "text": user_prompt})

    response = client.chat.completions.create(
        model=os.getenv("MODEL", ""),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()


# ═══════════════════════════════════════════════════════════════════════
# remocn 组件目录管理
# ═══════════════════════════════════════════════════════════════════════


def _pascal_to_kebab(name: str) -> str:
    """PascalCase → kebab-case"""
    result = []
    for i, ch in enumerate(name):
        if ch.isupper():
            if i > 0 and (
                name[i - 1].islower() or (i + 1 < len(name) and name[i + 1].islower())
            ):
                result.append("-")
            result.append(ch.lower())
        else:
            result.append(ch)
    return "".join(result)


# 组件名 → effect 文件名 slug 的手动覆盖（少数不遵循命名规则的情况）
_COMPONENT_SLUG_OVERRIDES: dict[str, str] = {}


def _component_to_slug(name: str) -> str:
    """组件 PascalCase 名 → kebab-case slug"""
    if name in _COMPONENT_SLUG_OVERRIDES:
        return _COMPONENT_SLUG_OVERRIDES[name]
    return _pascal_to_kebab(name)


def _component_to_import_path(name: str) -> str:
    """组件名 → import 路径"""
    return f"./components/remocn/{_component_to_slug(name)}"


def load_remocn_catalog() -> list[dict]:
    """加载 remocn 组件目录"""
    if not COMPONENTS_JSON.exists():
        raise FileNotFoundError(f"组件目录不存在: {COMPONENTS_JSON}")
    with open(COMPONENTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def build_compact_catalog(components: list[dict]) -> str:
    """构建紧凑版组件目录（~2-3KB），供 Step 1 LLM 进行特效匹配。"""
    categories = {
        "文字 Reveal": [
            "BlurReveal",
            "StaggeredFadeUp",
            "MaskedSlideReveal",
            "TrackingIn",
        ],
        "高亮/强调": [
            "InlineHighlight",
            "MarkerHighlight",
            "ShimmerSweep",
        ],
        "动态文字": [
            "Typewriter",
            "TextFadeReplace",
            "SlotMachineRoll",
        ],
        "Hero & Display": [
            "InfiniteMarquee",
            "PerspectiveMarquee",
        ],
        "Tech & Glitch": [
            "MatrixDecode",
            "RGBGlitchText",
        ],
        "Core Primitives": [
            "SpringPopIn",
            "PulsingIndicator",
            "SuccessConfetti",
            "CursorFlow",
            "BrushStrokeSimulator",
            "BoundingBoxSelector",
            "ToastNotification",
        ],
        "环境 & 氛围": [
            "MeshGradientBg",
            "DynamicGrid",
            "SpotlightCard",
        ],
        "代码 & CLI": [
            "GlassCodeBlock",
            "TerminalSimulator",
            "CodeAccordion",
            "CodeDiffWipe",
            "AIGenerateOverlay",
            "ToolMenuSlideIn",
        ],
        "布局 & 数据": [
            "StaggeredBentoGrid",
            "ChatToPreviewLayout",
            "AnimatedLineChart",
            "AnimatedBarChart",
            "DragAndDropFlow",
        ],
        "转场": [
            "ZoomThroughTransition",
            "DeviceMockupZoom",
            "MorphingModal",
            "ImageExpandToFullscreen",
            "DirectionalWipe",
            "SwipeTransitionWipe",
            "SpatialPush",
            "FrostedGlassWipe",
            "GridPixelateWipe",
            "ChromaticAberrationWipe",
        ],
        "完整场景": [
            "HeroDeviceAssemble",
            "EcosystemConstellation",
            "InfiniteBentoPan",
            "BrowserFlow",
            "AIGenerationCanvas",
            "LiveCodeCompilation",
            "TerminalToBrowserDeploy",
            "DashboardPopulate",
            "PipelineJourney",
            "PricingTierFocus",
            "ProductLaunchTrailer",
            "ChangelogBite",
            "VisualDocsSnippet",
        ],
    }

    desc_map = {c["name"]: c["description"] for c in components}

    lines = [
        "可用特效组件列表（只能从中选择）:",
        "",
        "注意:",
        "- 组件名精确匹配: 大小写必须一致",
        "- 所有 58 个组件已内置于项目 src/components/remocn/，无需安装",
        '- import 格式: import { Xxx } from "./components/remocn/slug"',
        "- 一个常见错误: 看到'文字逐行出现' → Typewriter，而非自己写逐字逻辑",
        "- 另一个常见错误: 看到'画面切换有动画' → 检查 Transition 类，如 DirectionalWipe 等",
        "",
    ]

    for cat, names in categories.items():
        lines.append(f"【{cat}】")
        for name in names:
            if name in desc_map:
                slug = _component_to_slug(name)
                lines.append(f"  {name}: {desc_map[name]}")
        lines.append("")

    return "\n".join(lines)


def load_matched_sources(matched_names: list[str]) -> str:
    """读取匹配组件的实际 TypeScript 源码（含准确的 Props interface + JSDoc 注释）。

    为什么不用 effects/*.md 手写文档:
    - 手写文档可能遗漏 prop 或描述不准确（如把 speed 注为 Typing speed，实际是倍速）
    - 源码的 TypeScript interface 精确定义了 prop 名、类型、可选性、默认值
    - JSDoc 注释明确标注每个 prop 的真实语义
    """
    sources = []
    for name in matched_names:
        slug = _component_to_slug(name)
        src_path = TEMPLATES_DIR / "src" / "components" / "remocn" / f"{slug}.tsx"
        if src_path.exists():
            content = src_path.read_text(encoding="utf-8")
            sources.append(
                f"// ===== {name} ({slug}.tsx) =====\n"
                f"// 以下为组件完整源码，注意: TypeScript interface 定义了准确的 Props\n"
                f"// ★ 传参必须与 interface 中的字段名完全一致\n"
                f"{content}"
            )
            print(f"  ✅ 已加载组件源码: {slug}.tsx ({len(content)} 字符)")
        else:
            print(f"  ⚠️  组件源码不存在: {slug}.tsx (组件: {name})")
            sources.append(f"// {name}: source file not found at {slug}.tsx\n")

    return "\n\n".join(sources)


# ═══════════════════════════════════════════════════════════════════════
# Stage 2: 第一轮 LLM — 特效检测
# ═══════════════════════════════════════════════════════════════════════

_STEP1_SYSTEM_PROMPT = """\
你是视频结构分析专家。你的任务是输出一份完整的 video_spec（视频规格书），帮助 Stage 3 代码生成。

━━━━ 分析流程 ━━━━

★ 第一步: 划分时间片段 (beats)
  切分依据: 画面背景变化、文字出现方式变化、场景切换、BGM 能量变化边界
  每个 beat 2~6 秒,不切太碎也不覆盖大半视频

★ 第二步: 逐 beat 详细分析
  对每个 beat 必须提取:
  - 所有文字元素: 精确文字内容、估计字号(px)、颜色(hex)、屏幕位置(x/y 百分比)
  - 背景: 类型(solid/gradient/video)、颜色或描述
  - 特效: 匹配到组件目录中的组件名
  - 转场: 该 beat 结束时使用的过渡效果

★ 第三步: 组件匹配 + 行为观察
  匹配组件后,必须提供 observed_behavior: 描述你观察到的视觉表现
  不要写 API 参数名(如 blurAmount),用自然语言描述:
  → 正确的: { "type": "blur_to_sharp", "duration_frames": 20, "peak_intensity": "完全模糊不可辨认" }
  → 错误的: { "blurAmount": 40 }

━━━━ 核心规则 ━━━━

1. ★ 只能从提供的组件列表中选择特效名称,严禁编造
2. ★ 所有文字必须从视频画面中精确提取内容,不能猜测或总结
3. ★ 位置用 x_percent/y_percent (画面中心=50/50, 左上=0/0, 右下=100/100)
4. 置信度 confidence: high / medium / low

━━━━ 输出格式 (纯 JSON,无 Markdown 包裹) ━━━━

{
  "video_config": {
    "fps": <视频fps>, "width": <宽>, "height": <高>,
    "total_frames": <总帧数>, "duration_seconds": <时长秒>
  },
  "global_style": {
    "background_color": "<hex>",
    "primary_text_color": "<hex>",
    "accent_color": "<hex>",
    "font_family": "<字体>",
    "visual_tone": "<一句话描述整体视觉风格,如: 黑底白字红强调快节奏>"
  },
  "beats": [
    {
      "id": 1,
      "start_time": "0:00",
      "end_time": "0:03",
      "start_frame": 0,
      "end_frame": 90,
      "description": "<画面内容描述>",
      "content": {
        "text_elements": [
          {
            "text": "<精确文字内容>",
            "font_size_px": 72,
            "color": "#FFFFFF",
            "position": { "x_percent": 50, "y_percent": 45 }
          }
        ],
        "background": { "type": "solid", "color": "#000000" }
      },
      "effects": [
        {
          "component": "Typewriter",
          "confidence": "high",
          "reason": "<为什么匹配>",
          "observed_behavior": {
            "type": "character_by_character_reveal",
            "duration_frames": 20,
            "visual_description": "<一句话描述你看到的>"
          }
        }
      ],
      "missing_effects": [
        { "description": "<无法匹配的视觉效果的详细描述>",
          "observed_behavior": { "type": "<类型>", "duration_frames": 0 } }
      ],
      "transition_out": {
        "type": "cut" 或 "DirectionalWipe" 或 "ChromaticAberrationWipe" 等,
        "start_frame": 80,
        "duration_frames": 10
      }
    }
  ]
}

★ fill in all fields, no skipping. transition_out.type 默认 "cut". observed_behavior 每个 effect 必填."""


def _parse_step1_json(raw: str) -> dict:
    """解析 Step 1 LLM 的 JSON 输出。兼容旧 flat 格式和新的 beats 格式。"""
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json") :].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```") :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    result = json.loads(cleaned)

    # 向后兼容: 旧格式 {"matched":[...], "missing":[...]}
    # → 自动包装为 beats 格式
    if "beats" not in result and "matched" in result:
        print("ℹ️  LLM 返回了旧格式，自动转换为 beats 格式")
        result = {
            "beats": [
                {
                    "start_time": "0:00",
                    "end_time": "N/A",
                    "description": "自动转换（未按 beat 划分）",
                    "effects": result.get("matched", []),
                    "missing": result.get("missing", []),
                }
            ]
        }

    return result


def _log_beat_analysis(beats: list[dict], fps: float) -> None:
    """打印 beat-by-beat 分析日志。"""
    if not beats:
        print("  (无 beats)")
        return

    total = len(beats)
    time_col = max(
        len(f"{b.get('start_time', '?')} → {b.get('end_time', '?')}") for b in beats
    )

    print(f"\n{'─' * 72}")
    print("  Beat-by-Beat 分析日志")
    print(f"{'─' * 72}")

    for i, beat in enumerate(beats, 1):
        start = beat.get("start_time", "?")
        end = beat.get("end_time", "?")
        desc = beat.get("description", "")
        effects = beat.get("effects", [])
        missing = beat.get("missing_effects", beat.get("missing", []))

        start_frame = int(_time_to_seconds(start) * fps)
        end_frame = int(_time_to_seconds(end) * fps)

        time_range = f"{start} → {end}"
        print(
            f"\n┌─ Beat {i}/{total}  "
            f"{time_range:<{time_col}}  "
            f"frames {start_frame} → {end_frame}"
        )
        if desc:
            print(f"│  画面: {desc}")

        if effects:
            first = True
            for e in effects:
                comp = e.get("component", "?")
                conf = e.get("confidence", "")
                reason = e.get("reason", "")
                if comp:
                    prefix = "│  ✅" if first else "│    "
                    print(f"{prefix} {comp} ({conf}) — {reason}")
                    first = False
                else:
                    prefix = "│  ⚠️ " if first else "│    "
                    print(f"{prefix} (无匹配组件) — {reason}")
                    first = False

        if missing:
            for m in missing:
                print(f"│  ⚠️  missing — {m.get('description', '')}")

        if not effects and not missing:
            print("│  (无特效检测)")

        print("└" + "─" * 69)

    print(f"\n{'─' * 72}")
    all_effects = [
        (i, e)
        for i, b in enumerate(beats, 1)
        for e in b.get("effects", [])
        if e.get("component")
    ]
    all_missing = [
        (i, m)
        for i, b in enumerate(beats, 1)
        for m in b.get("missing_effects", b.get("missing", []))
    ]
    print(
        f"  总计: {total} beats, {len(all_effects)} matched, {len(all_missing)} missing"
    )
    if all_effects:
        names = set(e[1].get("component", "") for e in all_effects)
        print(f"  匹配组件: {', '.join(sorted(names))}")
    if all_missing:
        msgs = [m[1].get("description", "") for m in all_missing]
        print(f"  缺失特效: {', '.join(msgs)}")
    print(f"{'─' * 72}\n")


def step1_detect_effects(
    video_b64: str,
    compact_catalog: str,
    fps: float,
    duration: float,
    meta: VideoMeta,
    bgm_features_text: str = "",
) -> dict:
    """第一轮 LLM: 分析视频输出完整 video_spec（规格书）。"""
    print("\n🎯 Stage 2: 第一轮 LLM — 生成 video_spec 规格书")

    total_frames = int(duration * fps)
    user_prompt = f"""请分析以下短视频，输出完整 video_spec。

【视频信息】
- 分辨率: {meta.width or 1080}x{meta.height or 1920}
- FPS: {fps}
- 时长: {duration:.1f}s
- 总帧数: {total_frames}

【要求】
1. 先划分 beats（时间片段），再逐 beat 详细分析
2. 每个 beat 必须提取所有文字元素的: 精确内容、字号、颜色、屏幕位置
3. 每个匹配的组件必须附带 observed_behavior（观察到的视觉表现，用自然语言）
4. 每个 beat 标注 transition_out（默认为 "cut"）

{compact_catalog}

请仔细观察视频的每一段，按 video_spec 格式输出完整 JSON。"""

    # 注入 BGM 特征
    if bgm_features_text:
        user_prompt += f"""

{bgm_features_text}

★ 可参考 BGM 的 beat 时间点来判定转场/特效触发时机和 drive 边界。"""

    raw = call_model(
        _STEP1_SYSTEM_PROMPT, user_prompt, video_b64=video_b64, max_tokens=8192
    )
    print(f"\n📝 Step 1 原始响应 ({len(raw)} 字符)")

    try:
        result = _parse_step1_json(raw)
    except json.JSONDecodeError:
        print("⚠️  Step 1 JSON 解析失败")
        print(f"原始输出前 500 字符:\n{raw[:500]}")
        result = {
            "beats": [
                {
                    "start_time": "0:00",
                    "end_time": str(duration),
                    "description": "JSON 解析失败",
                    "effects": [],
                    "missing_effects": [{"description": "LLM 输出解析失败"}],
                }
            ]
        }

    beats = result.get("beats", [])
    total_effects = sum(len(b.get("effects", [])) for b in beats)
    total_missing = sum(
        len(b.get("missing_effects", b.get("missing", []))) for b in beats
    )
    print(
        f"✅ 检测到 {len(beats)} 个 beats, {total_effects} 个匹配特效, {total_missing} 个缺失特效"
    )

    # 打印详细的 beat-by-beat 分析日志
    _log_beat_analysis(beats, fps)

    return result


# ═══════════════════════════════════════════════════════════════════════
# Stage 3: 第二轮 LLM — 参数推导 + 代码生成
# ═══════════════════════════════════════════════════════════════════════

_STEP2_SYSTEM_PROMPT = """\
你是 Remotion (React 视频框架) 代码生成专家。根据视频和提供的特效组件**源码**，生成完整的可运行 Remotion 项目代码。

━━━━━━ 技术规范（必须严格遵守）━━━━━━

【核心规则】
1. 所有动画必须用 useCurrentFrame() + interpolate() 或 spring() 实现
   ★ 所有用到的 Remotion API 必须显式 import：
     import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig,
              interpolate, spring, Easing } from "remotion";
     代码中每用一个 API 就必须在 import 中列出来，缺一个就运行时报错 ReferenceError
2. ★ 绝对禁止 CSS transition / animation / Tailwind animate-*
3. 用 <Sequence from={...} durationInFrames={...}> 控制多元素时序
4. 用 <AbsoluteFill> 做全屏容器
   ★ 包含绝对定位组件（Typewriter/MarkerHighlight/BlurReveal等）的 wrapper
     必须使用 AbsoluteFill 或有 explicit 全宽全高的容器。
     严禁用普通 <div style={{transform:...}}> 包裹它们 — plain div 无尺寸，
     导致组件内 position:absolute;inset:0 塌缩到 (0,0)，文字跳到左上角。
5. interpolate() 必须设 extrapolateLeft/Right: "clamp"
6. spring() 必须传入 fps: const { fps } = useVideoConfig()

【Easing 白名单（仅允许以下 10 个）】
  linear, ease, quad, cubic, sin, circle, exp, elastic, back, bounce
  ★ 注意: 是 sin 不是 sine, 是 exp 不是 expo!

━━━━━━ 特效实现 — 两层决策 ━━━━━━

【Layer 1: remocn 组件（已内置于 src/components/remocn/）】
  import 路径: import { Xxx } from "./components/remocn/xxx"
  ★ 下方提供组件的完整 TypeScript 源码，请严格按以下规则使用:
  ★ 组件文件已在项目中内置，你只需要 import 即可，严禁输出 ### FILE: 块来重写它们

  1. ★ Props 名称必须与源码 interface 中的字段名完全一致（大小写敏感）
  2. ★ Props 类型必须匹配 interface 定义（string/number/boolean/ReactNode）
  3. ★ required props（无 ? 标记）必须提供
  4. ★ 注意 JSDoc 注释中对每个 prop 的语义说明
  5. ★ 不要编造 interface 中不存在的 prop
  6. 参考源码中的默认值理解组件行为
  7. 组件已经封装了所有动画逻辑，只传 Props 即可，不要给组件包额外的动画层
  8. MarkerHighlight: 设置 delayFrames 与 Sequence.from 相同值可对齐 spring 时间轴

【observed_behavior → 组件参数映射（关键）】
  prompt 中的 "observed_behavior" 描述了你需要在代码中实现的效果（例:"文字从模糊到清晰,持续20帧"）。
  你的任务:
  1. 阅读该组件的 TypeScript 源码,找到控制此效果的 Props
  2. 将 observed_behavior 中的视觉描述映射为具体参数值
  3. 例: "duration_frames: 20" → 找到源码中的 duration/speed 等参数,设 duration={20}
  4. text_elements 中的字号/颜色/位置直接使用,不要自己编

【Layer 2: 无匹配的特效 → 自行实现】
  可用底层工具:
    - Remotion API: useCurrentFrame, interpolate, spring, Easing, Sequence, AbsoluteFill
    - @remotion/shapes: Circle, Rect, Star, Triangle
    - @remotion/noise: noise2D, noise3D
    - @remotion/paths: interpolatePath, getLength
  要求: 独立组件文件 (### FILE: src/EffectName.tsx)

━━━━━━ 代码组织规则 — beat + BGM 驱动 ━━━━━━

★ Step 1 已经将视频划分成了 time beats（时间片段），每个 beat 有自己的 start_time/end_time。
  你需要:

  1. 每个 beat → 一个 <Sequence from={startFrame} durationInFrames={endFrame - startFrame}>
  2. beat 内如果有转场（transition）→ 转场横跨当前 beat 和下一个 beat
  3. beat 的时间戳 = Sequence 的帧范围（fps 已知，可直接换算）

★ 如果你的 prompt 中提供了 BGM 音频特征（BPM、beat 时间点、onset 时间点）:
  1. ★ 将关键特效的触发帧（转场、高亮、弹入、文字出现）对齐到最近的 BGM beat
  2. BGM energy 分段可辅助判断该段的视觉节奏:
     - high energy → 快节奏、使用 chroma glitch / swipe 转场
     - low energy → 慢节奏、使用 blur fade / typewriter
  3. 特效持续时长可参考 beat 间隔（= 60/BPM 秒）

━━━━━━ 参数推导规则 ━━━━━━

1. 观察视频中特效的具体表现: 颜色、速度、延迟、时长、字号
2. 从组件源码的 TypeScript interface 中找到准确的 prop 名
3. interface 中带 ? 的是可选的，不带的是必填的
4. 视频中的视觉特征 → 映射到 interface 的对应 prop → 确定值

━━━━━━ 文件结构 ━━━━━━

- 如果 Layer 1 组件够用: 只需 MainComposition + Root
- 如果需要 Layer 2: 新组件在前，MainComposition 在中间，Root 在最后

【Root.tsx 规范】
- import { Composition } from "remotion";
- import MainComposition from "./MainComposition";
- 不要 import registerRoot, 不要调用 registerRoot()
- 直接 export const RemotionRoot

【输出格式 — 必须严格遵守】

★ 输出前自查: 返回的每个 .tsx 文件中，所有用到的函数（interpolate/spring/Easing/
  Sequence/useCurrentFrame）是否都在文件顶部的 import 语句中列出？缺一个就 ReferenceError。

以文件块格式输出，零解释文字:

### FILE: src/MainComposition.tsx
```tsx
// 主合成源码，必须是 default export
```

### FILE: src/Root.tsx
```tsx
// 根注册源码
```

(如有 Layer 2 自行实现的组件，在其之上输出 ### FILE: src/ComponentName.tsx)

━━━━━━ Sequence 与 useCurrentFrame() 关系（极其重要，错误导致全片时间错乱）━━━━━━

  ★ useCurrentFrame() 始终返回全局帧号，不受 <Sequence from={...}> 影响。
  
  例: Beat 2 从全局帧 30 开始 → <Sequence from={30} durationInFrames={30}>
      组件内部 useCurrentFrame() 在第 30 帧时返回 30（不是 0）！

  ★ spring() 的 frame 参数:
    - 如果你想让 spring 从 Sequence 起点开始: 
      spring({{ frame: frame - 30, fps, ... }})   ← 减去 Sequence 的 from 值
    - 如果你想让 spring 从组件 mount 就立即开始:
      直接传 frame，不偏移
    - ❌ 错误: spring({{ frame: frame - 15, ... }}) — 15 是什么帧？
      必须从 Sequence 的 from 帧号开始减，不能写死一个 magic number

  ★ 全局帧号映射（直接使用）:
    每个 beat 的 "frames N-M" = Sequence from={N} durationInFrames={M-N}
    组件内 useCurrentFrame() = N（beat 开始时的全局帧号）"""


def _build_step2_user_prompt(
    meta: VideoMeta,
    duration: float,
    fps: float,
    match_sources: str,
    step1_result: dict,
    bgm_features_text: str = "",
) -> str:
    """构建 Step 2 的 user prompt,消费 video_spec 格式。"""

    global_style = step1_result.get("global_style", {})
    beats = step1_result.get("beats", [])
    total_frames = int(duration * fps)

    # ── 全局样式摘要 ──
    style_lines = []
    if global_style:
        for key, label in [
            ("background_color", "背景色"),
            ("primary_text_color", "主文字色"),
            ("accent_color", "强调色"),
            ("font_family", "字体"),
            ("visual_tone", "视觉风格"),
        ]:
            if global_style.get(key):
                style_lines.append(f"  {label}: {global_style[key]}")
    style_text = "\n".join(style_lines) if style_lines else "（无）"

    # ── 逐 beat 详细摘要 ──
    beat_lines = []
    all_matched_names = set()

    for i, beat in enumerate(beats, 1):
        start_s = _time_to_seconds(beat.get("start_time", "0:00"))
        end_s = _time_to_seconds(beat.get("end_time", str(duration)))
        start_frame = int(start_s * fps)
        end_frame = int(end_s * fps)
        desc = beat.get("description", "")

        beat_lines.append(
            f"  Beat {i} | {beat.get('start_time', '?')}-{beat.get('end_time', '?')} "
            f"| frames {start_frame}-{end_frame} | {desc}"
        )
        beat_lines.append(
            f"         ⚠ Sequence from={{{start_frame}}} useCurrentFrame()在第{start_frame}帧时返回{start_frame}(非0)"
        )

        # 文字元素
        content = beat.get("content", {})
        text_elements = content.get("text_elements", [])
        for te in text_elements:
            pos = te.get("position", {})
            beat_lines.append(
                f"         文字:'{te.get('text', '?')}' "
                f"字号≈{te.get('font_size_px', '?')}px "
                f"颜色={te.get('color', '?')} "
                f"位置=({pos.get('x_percent', '?')}%,{pos.get('y_percent', '?')}%)"
            )

        # 背景
        bg = content.get("background", {})
        if bg:
            beat_lines.append(
                f"         背景: {bg.get('type', '?')} {bg.get('color', '?')}"
            )

        # 匹配的特效
        effects = beat.get("effects", [])
        for e in effects:
            comp = e.get("component", "")
            if comp:
                all_matched_names.add(comp)
            reason = e.get("reason", "")
            beat_lines.append(
                f"         ├ {comp} ({e.get('confidence', '?')}): {reason}"
            )
            obs = e.get("observed_behavior", {})
            if obs:
                beat_lines.append(
                    f"         │  观察: {obs.get('type', '?')} "
                    f"持续≈{obs.get('duration_frames', '?')}帧 | "
                    f"{obs.get('visual_description', '')}"
                )

        # 缺失特效
        missing = beat.get("missing_effects", beat.get("missing", []))
        for m in missing:
            beat_lines.append(f"         ├ ⚠ missing: {m.get('description', '')}")
            obs = m.get("observed_behavior", {})
            if obs:
                beat_lines.append(
                    f"         │  观察: {obs.get('type', '?')} "
                    f"持续≈{obs.get('duration_frames', '?')}帧"
                )

        # 转场
        tr = beat.get("transition_out", {})
        if tr and tr.get("type", "cut") != "cut":
            tr_start = tr.get("start_frame", end_frame)
            tr_dur = tr.get("duration_frames", 6)
            beat_lines.append(
                f"         └ 转场: {tr.get('type', '?')} @帧{tr_start}({tr_dur}帧)"
            )

        beat_lines.append("")

    beat_summary = "\n".join(beat_lines) if beat_lines else "（无）"

    # 汇总所有 missing
    all_missing_lines = []
    for b in beats:
        for m in b.get("missing_effects", b.get("missing", [])):
            all_missing_lines.append(f"  - {m.get('description', '')}")
    missing_text = "\n".join(all_missing_lines) if all_missing_lines else "（无）"

    # ── 组装最终 prompt ──
    main_text = f"""请根据以下 video_spec 规格书生成完整的 Remotion 项目代码。

【视频信息】
- 分辨率: {meta.width or 1080}x{meta.height or 1920}
- FPS: {fps} | 时长: {duration:.1f}s | 总帧数: {total_frames}

【全局样式】
{style_text}

【时间片段 (beats) 分析 — 每个 beat 对应一个 <Sequence>】
{beat_summary}

【缺失的特效 — 需自行实现 (Layer 2)】
{missing_text}

【已匹配组件的 TypeScript 源码 — 含准确的 Props interface】
{match_sources}"""

    # 注入 BGM 特征
    if bgm_features_text:
        main_text += f"""

{bgm_features_text}

★ 代码生成时: 参考 BGM beat/onset 时间点,将特效触发帧对齐到最近的 beat 帧。"""

    main_text += """

━━━━━ 代码组织规则 ━━━━━

1. ★ 每个 beat = 一个 <Sequence from={{startFrame}} durationInFrames={{endFrame - startFrame}}>
2. ★ 直接使用规格书中的 text_elements 参数（字号、颜色、位置），不要自行猜测
3. ★ observed_behavior 描述了目标视觉效果,请将其映射到组件源码中对应的 Props
4. beat 内的 matched 组件放在该 Sequence 中
5. beat 内的 missing 特效自行实现（Layer 2）,也放在该 Sequence 中
6. 如 beat 有 transition_out → 放在该 beat 末尾,横跨过渡区域

━━━━━ 请观察视频 + 对照规格书 + 阅读源码,输出完整代码 ━━━━━

请现在输出文件块。"""

    return main_text


def _time_to_seconds(ts: str) -> float:
    """将 "0:03" 或 "0:03.5" 转为秒数。"""
    ts = ts.strip()
    if ":" in ts:
        parts = ts.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    try:
        return float(ts)
    except ValueError:
        return 0.0


def _parse_codegen_response(raw: str) -> dict[str, str]:
    """解析代码生成响应中的 ### FILE: 块。"""
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
    """写入代码文件到项目 src/ 目录。"""
    written = []
    src_dir = project_dir / "src"
    for rel_path, code in files.items():
        target = src_dir / Path(rel_path).name
        target.write_text(code, encoding="utf-8")
        written.append(str(target))
        print(f"  ✅ 已写入: {Path(rel_path).name}")
    return written


def step3_generate_code(
    video_b64: str,
    meta: VideoMeta,
    fps: float,
    duration: float,
    step1_result: dict,
    project_dir: Path,
    bgm_features_text: str = "",
) -> dict[str, str]:
    """第二轮 LLM: 参数推导 + 代码生成。"""
    print("\n🧬 Stage 3: 第二轮 LLM — 代码生成")

    beats = step1_result.get("beats", [])

    # 从所有 beats 中收集匹配的组件名（去重）
    matched_names = []
    seen = set()
    for beat in beats:
        for effect in beat.get("effects", []):
            name = effect.get("component", "")
            if name and name not in seen:
                matched_names.append(name)
                seen.add(name)

    # 查表加载组件源码
    print(f"\n📚 正在加载 {len(matched_names)} 个组件的 TypeScript 源码...")
    match_sources = load_matched_sources(matched_names)

    # 构建 user prompt（beat 驱动）
    user_prompt = _build_step2_user_prompt(
        meta,
        duration,
        fps,
        match_sources,
        step1_result,
        bgm_features_text,
    )

    print(f"\n🤖 正在请求模型生成 Remotion 代码...")
    raw = call_model(
        _STEP2_SYSTEM_PROMPT, user_prompt, video_b64=video_b64, max_tokens=16384
    )
    print(f"📝 Step 2 原始响应 ({len(raw)} 字符)")

    # 保存原始输出
    raw_path = project_dir / "codegen_raw.txt"
    raw_path.write_text(raw, encoding="utf-8")
    print(f"📄 原始输出已保存: {raw_path}")

    # 解析文件块
    files = _parse_codegen_response(raw)

    if not files:
        print("⚠️  未能从响应中解析出文件块")
        print(f"原始输出前 500 字符:\n{raw[:500]}")

    return files


# ═══════════════════════════════════════════════════════════════════════
# Stage 4: 渲染视频
# ═══════════════════════════════════════════════════════════════════════


def _render_video(project_dir: Path, video_name: str) -> Path:
    """Stage 4: 使用 Remotion 直接渲染视频为 MP4 文件。"""
    output_mp4 = project_dir / f"{video_name}_rendered.mp4"
    print(f"\n🎬 Stage 4: 渲染视频 → {output_mp4}")
    print("   (最长等待 10 分钟)...")

    try:
        result = subprocess.run(
            [_PNPM, "exec", "remotion", "render", "RecreatedVideo", str(output_mp4)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
        )
        if result.returncode != 0:
            error_lines = [
                l for l in result.stderr.split("\n") if "ERROR" in l or "error" in l
            ]
            raise RuntimeError("渲染失败！\n错误摘要:\n" + "\n".join(error_lines[:15]))
        for line in result.stdout.split("\n"):
            if "Rendering" in line or "Frame" in line or "Done" in line:
                print(f"   {line.strip()}")
        print(f"✅ 视频已渲染: {output_mp4}")
    except FileNotFoundError:
        raise RuntimeError("未找到 pnpm 或 remotion 命令")
    except subprocess.TimeoutExpired:
        raise RuntimeError("remotion render 超时 (600s)")

    return output_mp4


# ═══════════════════════════════════════════════════════════════════════
# 输出工具
# ═══════════════════════════════════════════════════════════════════════


def _print_missing_effects(step1_result: dict) -> list[dict]:
    """打印无法复现的特效列表。"""
    beats = step1_result.get("beats", [])
    missing = []
    for beat in beats:
        items = beat.get("missing_effects", beat.get("missing", []))
        for m in items:
            m_copy = dict(m)
            m_copy["beat_time"] = (
                f"{beat.get('start_time', '?')}-{beat.get('end_time', '?')}"
            )
            missing.append(m_copy)

    if not missing:
        return []

    print("=" * 62)
    print("⚠️  以下特效在 remocn 组件库中无匹配 — 需要手动实现:")
    print("=" * 62)
    for i, m in enumerate(missing, 1):
        desc = m.get("description", "")
        bt = m.get("beat_time", "")
        print(f"  {i}. {desc}")
        print(f"     位置: {bt}")
    print()

    return missing


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
    print("  爆款视频结构迁移引擎 v3 — video_spec 规格书驱动")
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

    # ── BGM 音频特征分析 ────────────────────────────────────────
    print("\n🎵 分析 BGM 音频特征 (librosa)...")
    try:
        bgm_features = analyze_bgm(str(output_audio), segment_seconds=2.0)
        bgm_text = format_bgm_features(bgm_features, fps=fps)
        print(
            f"   BPM: {bgm_features['bpm']:.0f} | beats: {len(bgm_features['beat_times'])}个 | onsets: {len(bgm_features['onset_times'])}个"
        )
    except Exception as e:
        print(f"   ⚠️  BGM 分析失败 ({e})，跳过音乐特征")
        bgm_features = None
        bgm_text = ""

    # ── 加载 remocn 组件目录 ────────────────────────────────────
    print("\n📋 加载 remocn 组件目录...")
    components = load_remocn_catalog()
    print(f"✅ 已加载 {len(components)} 个 remocn 组件")
    compact_catalog = build_compact_catalog(components)

    # ── Stage 2: 第一轮 LLM — 特效检测 ──────────────────────────
    print("\n【Stage 2】第一轮 LLM — 特效检测")
    video_b64 = video_to_base64(str(vpath))

    step1_result = step1_detect_effects(
        video_b64,
        compact_catalog,
        fps,
        video_duration,
        meta,
        bgm_text,
    )

    # 保存 Step 1 结果
    step1_path = project_dir / f"{video_name}_video_spec.json"
    step1_path.write_text(
        json.dumps(step1_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"📄 video_spec 已保存: {step1_path}")

    # 输出缺失特效
    missing_effects = _print_missing_effects(step1_result)

    if dry_run:
        print(f"\n{'=' * 62}")
        print(f"  🔍 dry-run 完成 — 项目已创建: {project_dir}")
        print(f"{'=' * 62}\n")
        return

    # ── Stage 3: 第二轮 LLM — 代码生成 ──────────────────────────
    files = step3_generate_code(
        video_b64,
        meta,
        fps,
        video_duration,
        step1_result,
        project_dir,
        bgm_text,
    )

    if not files:
        print("❌ 代码生成失败：未能解析出文件块")
        print(f"项目目录: {project_dir}")
        sys.exit(1)

    print(f"\n📝 解析到 {len(files)} 个文件:")
    for fp in files:
        print(f"   - {fp}")
    _write_code_files(files, project_dir)

    # ── Stage 4: 渲染视频 ────────────────────────────────────────
    try:
        output_video = _render_video(project_dir, video_name)
    except RuntimeError as e:
        print(f"\n⚠️  {e}")
        output_video = None

    # ── 完成 ──────────────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print("  ✅ 全流程完成！")
    print(f"  项目目录: {project_dir}")
    print(f"{'=' * 62}")
    if output_video and output_video.exists():
        print(f"\n🎬 输出视频: {output_video}")
    else:
        print(
            f"\n▶️  手动渲染: cd {project_dir} && npx remotion render RecreatedVideo output.mp4"
        )

    if missing_effects:
        print(f"\n⚠️  以下特效无法复现，需要在代码中手动实现:")
        for i, m in enumerate(missing_effects, 1):
            print(f"  {i}. {m.get('description', '')} ({m.get('beat_time', '')})")

    print()


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
