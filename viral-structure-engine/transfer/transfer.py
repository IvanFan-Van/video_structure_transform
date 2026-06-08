"""结构迁移引擎 — 将爆款视频分析结果映射到用户新内容，输出Remotion渲染配置

本模块是整个项目的"胶水层"，连接分析管道和渲染引擎:

  analysis_result.json  ──┐
  new_content.json  ──────┤
                          ├── transfer() → remotion_props.json → Remotion渲染
                          │
                          └── 自动生成: TTS语音 + BGM拷贝 + 4种风格MP4

核心功能:
  1. 槽位→场景映射:  将原视频的slot_template映射到Remotion的SceneProps
  2. 文案模板填充:    将{变量占位符}替换为用户输入的具体值
  3. 3级remocn后备链: LLM推荐 → 特效类型映射 → 情绪映射
  4. TTS语速推算:    从原视频ASR语速反推edge-tts的rate参数
  5. 4种风格变异:    standard / high_click / high_convert / high_rhythm
  6. 素材缺口处理:    调用gap_handler检测→补全→降级

风格变异说明:
  standard:     原版结构，无变异
  high_click:   Hook LLM重写为疑问句 + RGBGlitchText特效 + 语速+5%
  high_convert: 产品展示段拉长20% + ShimmerSweep强调卖点
  high_rhythm:  所有场景压缩25% + SpringPopIn快速弹入 + 语速+10%

CLI 用法:
  python -m transfer.transfer <analysis.json> <new_content.json> <output.json>
    [--use-remocn] [--no-render] [--style <name|all>]
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

load_dotenv(find_dotenv(), override=True)

from .schema import (
    NewContent, SlotInput, SceneProps, TextStyle,
    RemotionProps, MigrationSummary, GapItem
)
from .gap_handler import detect_gaps, apply_gap_fill
from .constants import LABEL_BG_COLORS, DEFAULT_TTS_SPEED
from .tts import run_tts


# ═══════════════════════════════════════════════════════════════════
# 静态映射表
# ═══════════════════════════════════════════════════════════════════

# label → Remotion 场景组件类型
# 每个脚本段落的 label 对应一种 Remotion 渲染模式:
#   text_overlay:  逐句打字文本（TextOverlayScene）
#   emphasis_text: KenBurns缩放+卡点脉冲（EmphasisTextScene）
#   remocn_composed: 59个remocn视觉组件（RemocnScene）
#   其他: 特定场景类型（curiosity_text/product_centric等）
_LABEL_TO_SCENE_TYPE = {
    "hook":                 "curiosity_text",
    "pain_point":           "contrast_reveal",
    "solution":             "value_list",
    "product_show":         "product_centric",
    "usage_scene":          "usage_scene",
    "comparison":           "comparison_card",
    "testimonial":          "testimonial_card",
    "offer":                "offer_card",
    "cta":                  "cta_card",
    "outro":                "emphasis_text",
    "outro_platform_guide": "emphasis_text",
}

# emotion → 默认动画类型
# 当LLM没有给出具体特效类型时，根据情绪标签选择最适合的动画
_EMOTION_TO_ANIMATION = {
    "curious":      "typewriter",  # 好奇心 → 打字机（逐字出现制造悬念）
    "suspenseful":  "glitch",      # 悬疑 → 故障效果
    "excited":      "bounce",      # 激动 → 弹入动画
    "urgent":       "slide_in",    # 紧迫 → 滑入
    "sincere":      "fade_in",     # 真诚 → 淡入
    "humorous":     "bounce",      # 幽默 → 弹入
    "calm":         "fade_in",     # 平和 → 淡入
    "neutral":      "fade_in",     # 中性 → 淡入
}

# emotion → 默认文字颜色
# 不同情绪使用不同颜色增强氛围:
#   兴奋(金色) → 暗示高价值/高情绪
#   紧迫(橙色) → 视觉刺激/冲动消费
#   悬疑(红色) → 制造紧张感
_EMOTION_TO_COLOR = {
    "curious":      "#FFFFFF",  # 白色 → 好奇心
    "suspenseful":  "#FF4444",  # 红色 → 悬疑紧张
    "excited":      "#FFD700",  # 金色 → 兴奋/高价值
    "urgent":       "#FF6600",  # 橙色 → 紧迫/冲动
    "sincere":      "#F0F0F0",  # 浅灰白 → 真诚
    "humorous":     "#FFFFFF",  # 白色 → 幽默
    "calm":         "#E0E0E0",  # 浅灰 → 平和
    "neutral":      "#FFFFFF",  # 白色 → 中性
}


# emotion → 默认 remocn 组件（三级 fallback 的最后一层兜底）
# 格式: (组件名, 默认props).
# 仅当 Phase 2 的 beat 分析和 effects[].type 都不可用时才使用此映射。
_EMOTION_TO_REMOCN = {
    "curious":      ("Typewriter",       {"fontSize": 64, "charsPerSecond": 15, "cursor": False}),
    "suspenseful":  ("RGBGlitchText",    {"fontSize": 64, "glitchAt": 0, "glitchDuration": 20, "intensity": 8}),
    "excited":      ("SpringPopIn",      {"damping": 12, "stiffness": 100}),
    "urgent":       ("BlurReveal",       {"fontSize": 64, "blur": 12, "speed": 1}),
    "sincere":      ("BlurReveal",       {"fontSize": 64, "blur": 8, "speed": 1}),
    "humorous":     ("SpringPopIn",      {"damping": 10, "stiffness": 120}),
    "calm":         ("BlurReveal",       {"fontSize": 64, "blur": 6, "speed": 1}),
    "neutral":      ("BlurReveal",       {"fontSize": 64, "blur": 4, "speed": 1}),
}

# effects[].type → remocn 组件（三级 fallback 的第二层）
# LLM 分析出的特效类型 → 最匹配的 remocn 组件名
# 例如: LLM说"typewriter" → 使用Typewriter组件 + 15字/秒打字速度
_EFFECT_TYPE_TO_REMOCN = {
    "typewriter":   ("Typewriter",       {"charsPerSecond": 15, "cursor": False}),
    "fade_in":      ("BlurReveal",       {"blur": 6, "speed": 1}),
    "blur_reveal":  ("BlurReveal",       {"blur": 8, "speed": 1}),
    "slide_in":     ("BlurReveal",       {"blur": 6, "speed": 1}),
    "bounce":       ("SpringPopIn",      {"damping": 12, "stiffness": 100}),
    "scale":        ("SpringPopIn",      {"damping": 14, "stiffness": 80}),
    "glow":         ("ShimmerSweep",     {}),
    "highlight":    ("InlineHighlight",  {}),
    "glitch":       ("RGBGlitchText",    {"glitchAt": 0, "glitchDuration": 20, "intensity": 8}),
    "static":       ("BlurReveal",       {"blur": 0, "speed": 1}),
}

# 59个合法 remocn 组件名白名单（与 REMOCN_REGISTRY 保持一致）
# LLM 输出的 remocn_component 必须命中此白名单，否则降级到第二级映射
_VALID_REMOCN_COMPONENTS = {
    "AIGenerateOverlay", "AIGenerationCanvas", "AnimatedBarChart", "AnimatedLineChart",
    "BlurReveal", "BoundingBoxSelector", "BrowserFlow", "BrushStrokeSimulator",
    "ChangelogBite", "ChatToPreviewLayout", "ChromaticAberrationWipe", "CodeAccordion",
    "CodeDiffWipe", "CursorFlow", "DashboardPopulate", "DeviceMockupZoom",
    "DirectionalWipe", "DragAndDropFlow", "DynamicGrid", "EcosystemConstellation",
    "FocusZoom", "FrostedGlassWipe", "GlassCodeBlock", "GridPixelateWipe",
    "HeroDeviceAssemble", "ImageExpandToFullscreen", "InfiniteBentoPan", "InfiniteMarquee",
    "InlineHighlight", "LiveCodeCompilation", "MarkerHighlight", "MaskedSlideReveal",
    "MatrixDecode", "MeshGradientBg", "MorphingModal", "PerspectiveMarquee",
    "PipelineJourney", "PricingTierFocus", "ProductLaunchTrailer", "PulsingIndicator",
    "RGBGlitchText", "ShimmerSweep", "SlotMachineRoll", "SpatialPush", "SpotlightCard",
    "SpringPopIn", "StaggeredBentoGrid", "StaggeredFadeUp", "SuccessConfetti",
    "SwipeTransitionWipe", "TerminalSimulator", "TerminalToBrowserDeploy", "TextFadeReplace",
    "ToastNotification", "ToolMenuSlideIn", "TrackingIn", "Typewriter",
    "VisualDocsSnippet", "ZoomThroughTransition",
}


# ═══════════════════════════════════════════════════════════════════
# remocn 组件选择 — 3级后备链
# ═══════════════════════════════════════════════════════════════════


def _build_remocn_effects_by_emotion(emotion: str, text: str, color: str) -> list[dict]:
    """根据情绪标签映射到 remocn 组件（三级 fallback 的最后一层）

    children 字段用于容器型组件（如 SpringPopIn 包裹内部元素）。
    容器组件列表: SpringPopIn, FocusZoom, SpotlightCard — 这些组件可接受子组件。
    非容器组件直接接收 text prop。
    """
    entry = _EMOTION_TO_REMOCN.get(emotion, ("BlurReveal", {"fontSize": 64, "blur": 8, "speed": 1}))
    component, base_props = entry

    base_props["color"] = color  # 注入文字颜色

    container_components = {"SpringPopIn", "FocusZoom", "SpotlightCard"}

    if component in container_components:
        # 容器组件包裹一个 BlurReveal + 文字（双层效果）
        return [{
            "component": component,
            "props": base_props,
            "children": [{
                "component": "BlurReveal",
                "props": {"text": text, "fontSize": 64, "color": color, "blur": 6, "speed": 1},
            }],
        }]
    else:
        # 叶组件直接接收 text
        return [{
            "component": component,
            "props": {**base_props, "text": text},
        }]


def _find_beat_for_slot(beats: list[dict], start_s: float, end_s: float) -> dict | None:
    """找到与 slot 时间范围重叠的 beat

    Phase 2 每个 beat 都分析了视觉效果和特效，
    slot 需要找到对应的 beat 来获取其 remocn_component 推荐。
    """
    for b in beats:
        if b.get("start_time", -1) <= start_s < b.get("end_time", -1):
            return b
    return None


def _build_remocn_effects_from_beat(beat: dict, text: str, color: str, emotion: str) -> list[dict]:
    """三级 fallback 选择 remocn 组件

    Level 1: LLM 直接输出的 remocn_component（白名单校验）
              ↓ 未命中白名单时降级
    Level 2: effects[].type → 静态映射表（_EFFECT_TYPE_TO_REMOCN）
              ↓ 无匹配时降级
    Level 3: emotion → 默认组件（_build_remocn_effects_by_emotion）

    Args:
        beat:    Phase 2 分析的单个beat dict
        text:    该场景要渲染的文字
        color:   文字颜色
        emotion: 情绪标签

    Returns:
        remocn effects 列表
    """
    effects = beat.get("effects", [])

    # Level 1: LLM 直接推荐的组件名（需要白名单校验）
    for ef in effects:
        candidate = ef.get("remocn_component", "")
        if candidate and candidate in _VALID_REMOCN_COMPONENTS:
            props = {**ef.get("remocn_props", {}), "color": color, "text": text}
            return [{"component": candidate, "props": props, "children": []}]

    # Level 2: effects[].type → 特效类型静态映射
    for ef in effects:
        effect_type = ef.get("type", "")
        if effect_type in _EFFECT_TYPE_TO_REMOCN:
            component, base_props = _EFFECT_TYPE_TO_REMOCN[effect_type]
            return [{"component": component,
                     "props": {**base_props, "color": color, "text": text},
                     "children": []}]

    # Level 3: emotion fallback（最后兜底）
    return _build_remocn_effects_by_emotion(emotion, text, color)


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════


def _fill_template(text_template: str, variables: dict) -> str:
    """将 text_template 中的 {占位符} 替换为 variables 中对应的值

    替换策略:
      1. 优先按占位符名称精确匹配（如 {高额数字} → variables["高额数字"]）
      2. 若 variables 中没有对应 key，则按顺序依次替换（兜底）
      3. list 值自动用中文顿号 '、' 连接

    Args:
        text_template: 含 {变量名} 的模板字符串
        variables:     变量名到值的映射

    Returns:
        替换后的字符串
    """
    result = text_template

    # 精确匹配替换
    for key, value in variables.items():
        if isinstance(value, list):
            value = "、".join(str(v) for v in value)  # 列表用顿号连接
        result = result.replace(f"{{{key}}}", str(value))

    # 兜底: 按顺序替换剩余 {占位符}
    remaining_values = [str(v) if not isinstance(v, list) else "、".join(v)
                        for v in variables.values()]
    idx = 0
    def _replace_one(m):
        nonlocal idx
        if idx < len(remaining_values):
            val = remaining_values[idx]
            idx += 1
            return val
        return m.group(0)  # 没有对应值时保留原占位符

    result = re.sub(r'\{[^}]+\}', _replace_one, result)
    return result


def _get_beat_frames(beat_timings: list[float], start_s: float,
                     end_s: float, fps: int) -> list[int]:
    """找出 [start_s, end_s) 时间范围内的 BGM 卡点，转为相对帧数

    用途: 在场景渲染时，在这些帧位置触发卡点脉冲/发光效果。

    Args:
        beat_timings: 所有BGM重拍时间点（绝对秒）
        start_s:      场景起始时间（绝对秒）
        end_s:        场景结束时间（绝对秒）
        fps:          帧率

    Returns:
        相对帧号列表（相对于场景的startFrame）
    """
    start_frame = round(start_s * fps)
    return [
        round(t * fps) - start_frame
        for t in beat_timings
        if start_s <= t < end_s
    ]


def _build_text_style(emotion: str, slot: dict, packaging: dict) -> TextStyle:
    """根据情绪 + packaging_structure 推断文字样式

    优先使用 packaging_structure.subtitle_style 中的颜色和位置（来自原视频LLM分析），
    emotion 决定动画类型。

    Args:
        emotion:    情绪标签（如 "excited"）
        slot:       当前槽位数据
        packaging:  analysis_result 中的 packaging_structure

    Returns:
        TextStyle 对象
    """
    pkg_subtitle = packaging.get("subtitle_style", {})
    # 颜色：优先用原视频字幕颜色
    color = pkg_subtitle.get("color") or _EMOTION_TO_COLOR.get(emotion, "#FFFFFF")
    # 动画：由情绪决定
    animation = _EMOTION_TO_ANIMATION.get(emotion, "fade_in")

    # font_size_hint → 实际px
    size_map = {"small": 32, "medium": 48, "large": 64, "xlarge": 80}
    font_size_hint = pkg_subtitle.get("font_size_hint", "large")
    font_size = size_map.get(font_size_hint, 48)

    # 位置：直接从原视频分析结果读取
    position_x = pkg_subtitle.get("position_x", 50)
    position_y = pkg_subtitle.get("position_y", 82)

    return TextStyle(
        fontSize=font_size,
        color=color,
        fontWeight="bold",
        animation=animation,
        position_x=position_x,
        position_y=position_y,
    )


def _resolve_output_dimensions(ratio: str) -> tuple[int, int]:
    """根据输出比例返回 (width, height)"""
    if ratio == "16:9":
        return 1280, 720
    return 1080, 1920  # 默认 9:16 竖屏


def _add_rate(rate_str: str, delta: int) -> str:
    """对 TTS rate 字符串做整数偏移

    例: _add_rate("+65%", 10) → "+75%"
         _add_rate("+65%", -5) → "+60%"
    """
    num = int(rate_str.replace("%", "").replace("+", "").replace("-", ""))
    sign = "-" if "-" in rate_str else "+"
    return f"{sign}{num + delta}%"


def _rewrite_hook_for_click(text: str) -> str:
    """LLM 重写 hook 文案为疑问/对比句式（high_click 风格专用）

    将平铺直叙的文案改写为更抓眼球的疑问句或对比句，
    前5个字制造悬念。失败则返回原文案。

    Args:
        text: 原始 hook 文案

    Returns:
        改写后的文案（失败则返回原文案）
    """
    try:
        client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        resp = client.chat.completions.create(
            model=os.getenv("MODEL", "doubao-seed-2-0-lite"),
            messages=[{
                "role": "user",
                "content": (
                    "把以下短视频开场文案改写为更抓眼球的疑问句或对比句，"
                    "前5个字要制造悬念，长度不超过原文。只输出改写后的文案，不加任何解释。\n"
                    f"原文案：{text}"
                ),
            }],
            max_tokens=100,
        )
        rewritten = resp.choices[0].message.content
        if rewritten and rewritten.strip():
            return rewritten.strip()
        return text
    except Exception:
        return text  # LLM调用失败，回退到原文案


# ═══════════════════════════════════════════════════════════════════
# 风格变异 — 4种风格版本的场景修改
# ═══════════════════════════════════════════════════════════════════


def _apply_style_mutation(
    scenes: list[SceneProps],
    tts_rate: str,
    total_frames: int,
    style: str,
) -> tuple[str, int]:
    """对场景列表做风格化变异（in-place修改）

    执行顺序很重要:
      1. 先变内容（修改scene.text文案、scene.durationFrames时长）
      2. 再调整语速偏移
      3. 最后重新计算帧位置

    变异后强制重现 startFrame，确保场景帧位置连续无缝。

    Args:
        scenes:       场景列表
        tts_rate:     当前TTS语速参数
        total_frames: 当前总帧数
        style:        目标风格

    Returns:
        (更新后的tts_rate, 更新后的total_frames)
    """
    if style == "standard":
        return tts_rate, total_frames

    for scene in scenes:
        label = scene.id

        if style == "high_click":
            # Hook改写为疑问句 + RGBGlitchText特效 + 时长压缩20%
            if label == "social_proof_hook":
                scene.text = _rewrite_hook_for_click(scene.text)
                scene.durationFrames = round(scene.durationFrames * 0.8)
                if scene.remocnEffects:
                    scene.remocnEffects[0].component = "RGBGlitchText"
                    scene.remocnEffects[0].props = {
                        **scene.remocnEffects[0].props,
                        "intensity": 10,
                        "glitchDuration": 15,
                    }

        elif style == "high_convert":
            # 产品展示段拉长20% + ShimmerSweep高光扫过效果
            if label in ("product_unboxing_show", "taste_experience_display"):
                scene.durationFrames = round(scene.durationFrames * 1.2)
                if scene.remocnEffects:
                    scene.remocnEffects[0].component = "ShimmerSweep"
            if label == "platform_official_outro":
                scene.durationFrames = round(scene.durationFrames * 1.1)

        elif style == "high_rhythm":
            # 所有场景压缩25% + SpringPopIn快速弹入（高stiffness=更快更弹）
            scene.durationFrames = max(30, round(scene.durationFrames * 0.75))
            if scene.remocnEffects:
                scene.remocnEffects[0].component = "SpringPopIn"
                scene.remocnEffects[0].props = {
                    **scene.remocnEffects[0].props,
                    "damping": 8,      # 低阻尼 → 更多回弹
                    "stiffness": 150,  # 高刚度 → 更快速
                }

    # 强制重新计算 startFrame（修复 in-place mutation 后帧位置错乱）
    current = 0
    for scene in scenes:
        scene.startFrame = current
        current += scene.durationFrames
    total_frames = current

    # TTS 语速偏移（不同风格有不同的语速调整）
    style_rate_offsets = {"high_click": 5, "high_convert": 0, "high_rhythm": 10}
    offset = style_rate_offsets.get(style, 0)
    if offset:
        tts_rate = _add_rate(tts_rate, offset)

    return tts_rate, total_frames


# ═══════════════════════════════════════════════════════════════════
# Remotion 渲染
# ═══════════════════════════════════════════════════════════════════


def _render_props(props_path: str, output_mp4: str) -> bool:
    """调用 Remotion CLI 渲染 remotion_props.json → mp4

    执行: npx remotion.cmd render src/index.ts VideoComposition output.mp4 --props=...json

    Returns:
        渲染成功 → True，失败 → False
    """
    remotion_dir = Path(__file__).resolve().parent.parent / "remotion-video"
    remotion_cli = str(remotion_dir / "node_modules" / ".bin" / "remotion.cmd")
    props_abs = str(Path(props_path).resolve())

    result = subprocess.run(
        [
            remotion_cli, "render",
            "src/index.ts", "VideoComposition",  # 组合ID
            output_mp4,
            f"--props={props_abs}",  # 传入JSON配置
        ],
        cwd=str(remotion_dir),
    )
    return result.returncode == 0


def transfer_all_styles(analysis_path: str, new_content: NewContent, output_dir: str) -> dict[str, str]:
    """一次性生成全部4个风格版本的 remotion_props.json 并渲染 MP4

    TTS 去重优化: 如果 standard 和 high_convert 使用相同的 rate 值，
    则只生成一次 TTS，另一版本复用已缓存的 voiceover.wav。

    Returns:
        {风格名: MP4路径}
    """
    with open(analysis_path, encoding="utf-8") as f:
        analysis = json.load(f)
    base_rate = _calc_tts_rate(analysis)  # 从原视频推算的基础语速

    styles = ["standard", "high_click", "high_convert", "high_rhythm"]
    style_configs = {
        "standard":     {"rate_offset": 0},
        "high_click":   {"rate_offset": 5},
        "high_convert": {"rate_offset": 0},   # 复用standard的TTS
        "high_rhythm":  {"rate_offset": 10},
    }

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 记录每个 rate 值是否已生成过 TTS（去重）
    rates_generated: set[str] = set()
    mp4_paths: dict[str, str] = {}

    # 第一步: 生成所有风格的 remotion_props.json
    for i, style in enumerate(styles):
        props_path = out / f"remotion_props_{style}.json"
        expected_rate = _add_rate(base_rate, style_configs[style]["rate_offset"])
        skip_audio = expected_rate in rates_generated  # 同rate → 跳过TTS生成
        rates_generated.add(expected_rate)

        transfer(
            analysis_path,
            new_content,
            str(props_path),
            use_remocn=True,
            style=style,
            skip_audio=skip_audio,
            skip_render=True,  # 先不渲染，生成完再统一渲染
        )

        mp4_output = str(out.resolve() / f"demo_{style}.mp4")
        mp4_paths[style] = mp4_output

    # 第二步: 统一渲染全部4个版本
    for style in styles:
        props_path = out / f"remotion_props_{style}.json"
        print(f"\n🎬 渲染 [{style}] ...")
        ok = _render_props(str(props_path), mp4_paths[style])
        if ok:
            print(f"  ✅ {mp4_paths[style]}")
        else:
            print(f"  ❌ 渲染失败: {style}")

    return mp4_paths


# ═══════════════════════════════════════════════════════════════════
# TTS 语速推算 — 从原视频实际语速反推 edge-tts rate 参数
# ═══════════════════════════════════════════════════════════════════

# 有语音的段落标签 — outro 通常只有背景音乐（无旁白），不纳入语速计算
_SPOKEN_LABELS = {
    "hook", "pain_point", "solution", "product_show",
    "usage_scene", "comparison", "testimonial", "offer", "cta",
}


def _calc_tts_rate(analysis: dict) -> str:
    """根据原视频 script_structure 中口语段落的语速，推算 edge-tts rate 参数

    计算步骤:
      1. 统计有语音段落的 总字符数 和 总时长
      2. 原视频语速 = 总字符数 / 总时长 (chars/sec)
      3. rate偏移 = (原视频语速 / DEFAULT_TTS_SPEED - 1) × 100
      4. 以5%为步长取整，限制在 -50% ~ +100% 范围

    例: 如果原视频语速是6.93字/秒，DEFAULT_TTS_SPEED是4.2，
        则 rate = (6.93/4.2 - 1) × 100 = +65%

    Returns:
        edge-tts rate 字符串，如 "+65%" / "-20%" / "+0%"
    """
    script = analysis.get("script_structure", [])

    total_chars = 0       # 总字符数
    total_duration = 0.0  # 总时长(秒)

    for seg in script:
        if seg.get("label") not in _SPOKEN_LABELS:
            continue  # 跳过无语音段落
        text = seg.get("text", "")
        duration = seg.get("end_time", 0) - seg.get("start_time", 0)
        if duration > 0 and text:
            total_chars += len(text)
            total_duration += duration

    if total_chars == 0 or total_duration == 0:
        return "+0%"  # 无有效数据 → 默认语速

    # 原视频实际语速
    original_speed = total_chars / total_duration
    # 相对于 edge-tts 默认语速的偏差百分比
    rate_float = (original_speed / DEFAULT_TTS_SPEED - 1) * 100

    # 以5%为步长取整
    rate_int = int(round(rate_float / 5) * 5)
    rate_int = max(-50, min(100, rate_int))  # 限制安全范围

    if rate_int >= 0:
        return f"+{rate_int}%"
    return f"{rate_int}%"


# ═══════════════════════════════════════════════════════════════════
# 主函数 — 结构迁移
# ═══════════════════════════════════════════════════════════════════


def transfer(
    analysis_path: str,
    new_content: NewContent,
    output_path: str,
    use_remocn: bool = False,
    skip_render: bool = False,
    style: str = "standard",
    skip_audio: bool = False,
) -> RemotionProps:
    """结构迁移主函数

    这是整个 transfer 层的核心入口。将 analysis_result.json（爆款视频结构分析）
    和 new_content.json（用户新内容）映射为 remotion_props.json（Remotion渲染配置）。

    处理流程:
      1. 读取分析结果（slot_template、script_structure、rhythm等）
      2. 逐slot构建SceneProps（文案填充、文字样式、remocn组件选择）
      3. 素材缺口检测与补全
      4. 风格变异（4选1）
      5. 拼接旁白文案 → TTS生成
      6. 拷贝BGM
      7. 组装RemotionProps → 写入JSON
      8. （可选）自动调用Remotion渲染

    Args:
        analysis_path: analysis_result.json 文件路径
        new_content:   用户输入的新内容
        output_path:   remotion_props.json 输出路径
        use_remocn:   是否启用59个remocn视觉组件（type=remocn_composed）
        skip_render:   是否跳过自动渲染
        style:         目标风格: standard/high_click/high_convert/high_rhythm
        skip_audio:    是否跳过TTS+BGM拷贝（当已有同rate TTS缓存时用）

    Returns:
        RemotionProps 对象（同时写入 output_path）
    """
    # ── 读取分析结果 ──
    with open(analysis_path, encoding="utf-8") as f:
        analysis = json.load(f)

    # 提取关键字段
    slot_template: list[dict] = analysis.get("slot_template", [])       # LLM产出的槽位模板
    script_structure: list[dict] = analysis.get("script_structure", []) # Phase 1脚本结构
    rhythm: dict = analysis.get("rhythm_structure", {})                 # Phase 4节奏结构
    bgm: dict = analysis.get("bgm_features", {})                       # Phase 0 BGM特征
    packaging: dict = analysis.get("packaging_structure", {})           # Phase 4包装结构
    video_info: dict = analysis.get("video_info", {})                   # 视频元数据
    beats: list[dict] = analysis.get("beats", [])                       # Phase 2 beat分析

    fps = 30  # 固定输出帧率
    total_duration_s = video_info.get("duration", 20.0)  # 原视频时长
    total_frames = round(total_duration_s * fps)          # 初始总帧数（mutation后会变）
    beat_timings: list[float] = bgm.get("beat_timings", [])  # BGM重拍时间点

    # emotion 查找表: label → emotion（从 script_structure 读取）
    emotion_map = {seg["label"]: seg.get("emotion", "neutral") for seg in script_structure}

    # ── 输出尺寸 ──
    width, height = _resolve_output_dimensions(new_content.output_ratio)

    # ── 素材缺口检测 ──
    gaps: list[GapItem] = detect_gaps(slot_template, new_content.user_materials)
    gap_map = {g.slot_id: g for g in gaps}  # slot_id → gap 快速查找

    # ── 拷贝用户素材到 Remotion public/ 目录 ──
    public_dir = Path(__file__).resolve().parent.parent / "remotion-video" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    for slot_input in new_content.slots.values():
        if slot_input.user_video:
            src = Path(slot_input.user_video)
            if src.exists():
                shutil.copy(src, public_dir / src.name)  # 拷贝到public/
                slot_input.user_video = src.name          # 改为相对路径
            else:
                print(f"⚠️  用户视频不存在: {src}")
                slot_input.user_video = None
        if slot_input.user_image:
            src = Path(slot_input.user_image)
            if src.exists():
                shutil.copy(src, public_dir / src.name)
                slot_input.user_image = src.name
            else:
                print(f"⚠️  用户图片不存在: {src}")
                slot_input.user_image = None

    # ── 逐 slot 构建 scene ──
    scenes: list[SceneProps] = []

    for i, slot in enumerate(slot_template):
        label = slot["label"]            # 槽位标签
        slot_id = slot["slot_id"]        # 槽位序号
        duration_s = slot.get("duration", 3.0)  # 推荐时长

        # 从 script_structure 匹配 label 获取起始时间
        script_seg = next(
            (seg for seg in script_structure if seg["label"] == label),
            None
        )
        if script_seg:
            start_s = script_seg.get("start_time", 0)
        else:
            # fallback: 累加前序slot的时长
            start_s = sum(s.get("duration", 3.0) for s in slot_template[:i])

        start_frame = round(start_s * fps)
        duration_frames = round(duration_s * fps)

        # 用户为该slot提供的内容
        slot_input: SlotInput = new_content.slots.get(label, SlotInput())

        # 文案填充: 优先用slot_input.text，否则用模板+变量
        if slot_input.text:
            filled_text = slot_input.text
        else:
            filled_text = _fill_template(slot["text_template"], slot_input.variables)

        # 情绪标签
        emotion = emotion_map.get(label, "neutral")

        # 文字样式（颜色+动画+位置）
        text_style = _build_text_style(emotion, slot, packaging)

        # 该场景内的BGM卡点（相对帧号）
        beat_frames = _get_beat_frames(beat_timings, start_s, start_s + duration_s, fps)

        # 用户是否有素材
        has_material = bool(slot_input.user_video or slot_input.user_image)

        # 场景类型
        scene_type = _LABEL_TO_SCENE_TYPE.get(label, "text_overlay")

        # ── 构建 remocn effects（仅在 use_remocn 模式下生效）──
        remocn_effects = []
        if use_remocn:
            scene_type = "remocn_composed"  # 切换为remocn组件渲染模式
            subtitle_style = packaging.get("subtitle_style", {})
            color = subtitle_style.get("color") or _EMOTION_TO_COLOR.get(emotion, "#FFFFFF")

            # 找到与slot时间重叠的beat（获取LLM分析的remocn推荐）
            beat = _find_beat_for_slot(beats, start_s, start_s + duration_s)
            if beat:
                remocn_effects = _build_remocn_effects_from_beat(beat, filled_text, color, emotion)
            else:
                # 没有对应beat → 直接用情绪fallback
                remocn_effects = _build_remocn_effects_by_emotion(emotion, filled_text, color)

        # 场景对象
        scene = SceneProps(
            id=label,
            slot_id=slot_id,
            startFrame=start_frame,
            durationFrames=duration_frames,
            type=scene_type,
            text=filled_text,
            textStyle=text_style,
            visualHint=slot.get("visual_content_desc", ""),
            emotion=emotion,
            beatFrames=beat_frames,
            hasMaterial=has_material,
            backgroundVideo=slot_input.user_video,
            backgroundImage=slot_input.user_image,
            backgroundColorFallback=LABEL_BG_COLORS.get(label, "#000000"),
            requiredElements=slot.get("required_elements", []),
            remocnEffects=remocn_effects,
        )

        # 素材缺口补全
        if slot_id in gap_map:
            scene = apply_gap_fill(scene, gap_map[slot_id], slot,
                                   theme=new_content.theme,
                                   filled_text=scene.text)

        scenes.append(scene)

    # ── TTS 语速推算（基础速率，mutation后可能调整）──
    tts_rate = _calc_tts_rate(analysis)

    # ── 风格变异（in-place 修改 scenes + rate + total_frames）──
    tts_rate, total_frames = _apply_style_mutation(
        scenes, tts_rate, total_frames, style,
    )

    # ── 旁白文案: 留空则从各 slot text 拼接（使用变异后的文案）──
    voiceover_text = new_content.voiceover_text
    if not voiceover_text:
        voiceover_text = "。".join(
            s.text for s in scenes if s.text
        )

    # ── 组装 RemotionProps ──
    filled_gaps = [g for g in gaps if g.filled]  # 已补全的缺口

    props = RemotionProps(
        fps=fps,
        durationInFrames=total_frames,
        width=width,
        height=height,
        scenes=scenes,
        bgmPath="bgm.wav",
        voiceoverPath="voiceover.wav",
        voiceoverText=voiceover_text,
        ttsRate=tts_rate,
        rhythmPattern=rhythm.get("rhythm_pattern", ""),
        visualStyle=video_info.get("visual_style", ""),
        gapReport=gaps,
        migrationSummary=MigrationSummary(
            sourceVideo=video_info.get("filename", ""),  # 源视频文件名
            theme=new_content.theme,                     # 新主题
            slotsCount=len(scenes),                      # 场景数
            gapsCount=len(gaps),                         # 缺口总数
            filledGapsCount=len(filled_gaps),            # 已补全数
            rhythmPattern=rhythm.get("rhythm_pattern", ""),
            visualStyle=video_info.get("visual_style", ""),
        ),
    )

    # ── BGM 拷贝 + TTS 旁白生成 ──
    audio_dir = Path(analysis_path).parent / "audio"  # 分析阶段的音频输出目录
    public_dir = Path(__file__).resolve().parent.parent / "remotion-video" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    # 拷贝 BGM（如果 skip_audio 且目标已存在则跳过）
    bgm_src = audio_dir / "bgm.wav"
    if bgm_src.exists():
        bgm_dst = public_dir / "bgm.wav"
        if not skip_audio or not bgm_dst.exists():
            shutil.copy(bgm_src, bgm_dst)
            print(f"🎵 BGM 已拷贝: {bgm_dst}")
    else:
        print(f"⚠️  BGM 源文件不存在: {bgm_src}")

    # 生成 TTS（如果 skip_audio 且目标已存在则跳过）
    tts_path = public_dir / "voiceover.wav"
    if skip_audio and tts_path.exists():
        print(f"🔊 TTS 使用已缓存: {tts_path} (rate={tts_rate})")
    else:
        run_tts(voiceover_text, str(tts_path), rate=tts_rate)
        print(f"🔊 TTS 语音已生成: {tts_path} (rate={tts_rate})")

    # ── 写入 JSON 文件 ──
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(props.model_dump(), f, ensure_ascii=False, indent=2)

    print(f"✅ 结构迁移完成 [{style}]")
    print(f"   场景数: {len(scenes)}")
    print(f"   素材缺口: {len(gaps)} 个（已补全: {len(filled_gaps)} 个）")
    print(f"   输出: {output_path}")

    # ── 自动渲染 ──
    if not skip_render:
        remotion_dir = Path(__file__).resolve().parent.parent / "remotion-video"
        mp4_out = str(remotion_dir / "out" / "demo.mp4")
        print(f"\n🎬 开始渲染 [{style}] ...")
        ok = _render_props(output_path, mp4_out)
        if ok:
            print(f"🎬 视频已渲染: {mp4_out}")
        else:
            print(f"⚠️  渲染失败")
            remotion_cli = str(remotion_dir / "node_modules" / ".bin" / "remotion.cmd")
            print(f"    可手动: {remotion_cli} render src/index.ts VideoComposition out/demo.mp4 --props={Path(output_path).resolve()}")

    return props


# ═══════════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Fix Windows console encoding for emojis
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # 用法: python -m transfer.transfer <analysis.json> <new_content.json> <output.json> [--use-remocn] [--no-render] [--style <name|all>]
    if len(sys.argv) < 4:
        print("用法: python -m transfer.transfer <analysis.json> <new_content.json> <output.json> [--use-remocn] [--no-render] [--style <name|all>]")
        sys.exit(1)

    use_remocn = "--use-remocn" in sys.argv
    skip_render = "--no-render" in sys.argv

    style = "standard"
    if "--style" in sys.argv:
        idx = sys.argv.index("--style")
        if idx + 1 < len(sys.argv):
            style = sys.argv[idx + 1]

    # 读取用户新内容
    with open(sys.argv[2], encoding="utf-8") as f:
        raw = json.load(f)
    content = NewContent(**raw)

    if style == "all":
        # 一次性生成全部4种风格
        mp4_paths = transfer_all_styles(sys.argv[1], content, sys.argv[3])
        print(f"\n🎬 全部渲染完成:")
        for s, path in mp4_paths.items():
            print(f"  [{s}] {path}")
    else:
        # 单风格
        transfer(
            sys.argv[1], content, sys.argv[3],
            use_remocn=use_remocn,
            skip_render=skip_render,
            style=style,
        )
