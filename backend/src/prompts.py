DESIGN_SYSTEM_PROMPT = (
    "你是一位顶尖的品牌视觉设计师和 Hyperframes 视频生产专家。"
    "根据所提供的爆款短视频，输出一份符合 Hyperframes DESIGN.md 规范的品牌设计文档。"
    "请直接输出 Markdown 文本，不要添加任何额外解释或代码块标记。"
)

DESIGN_MD_TEMPLATE = """
请仔细观看这段爆款短视频，结合以下数据，生成一份完整的 DESIGN.md 文件。
【输出格式】严格按此结构输出，包含 YAML frontmatter + 6个章节：

---
colors:
  primary: "#xxxxxx"
  on-primary: "#xxxxxx"
  accent: "#xxxxxx"
  surface: "#xxxxxx"
  muted: "#xxxxxx"
typography:
  headline:
    fontFamily: "Noto Serif SC"
    fontSize: "5rem"
    fontWeight: 700
    textTransform: "none"
  body:
    fontFamily: "Noto Sans SC"
    fontSize: "1.5rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Noto Sans SC"
    fontSize: "1rem"
    fontWeight: 500
rounded:
  sm: "8px"
  md: "16px"
  lg: "32px"
spacing:
  sm: "16px"
  md: "32px"
  lg: "64px"
motion:
  energy: "high"
  easing:
    entry: "power3.out"
    exit: "power2.in"
    ambient: "sine.inOut"
  duration:
    entrance: 0.4
    hold: 2.0
    transition: 0.5
  atmosphere:
    - "radial-glow"
    - "ghost-type"
  transition: "velocity-matched-upward"
---

## Overview
（3-4句话）

## Colors
（5-8个颜色含十六进制）

## Typography
（字体层级说明，字体名只能使用 Google Fonts 中存在的英文名称，如 Noto Serif SC、Noto Sans SC、Inter 等，不要使用中文字体名）

## Components
（视频中的视觉组件）

## Imagery
（画面素材类型）

## Do's and Don'ts
**Do:**
- （3-5条）
**Don't:**
- （3-5条）

重要：字体名必须是 Google Fonts 可用的英文名称，严禁使用"思源黑体"、"思源宋体"等中文名。
"""

SCRIPT_SYSTEM_PROMPT = (
    "你是一位精通短视频创作的脚本策划专家和 Hyperframes 视频生产专家。"
    "根据所提供的爆款短视频，提炼脚本结构，输出符合 Hyperframes SCRIPT.md 规范的脚本文档。"
    "请直接输出 Markdown 文本，不要添加任何额外解释或代码块标记。"
)

SCRIPT_MD_TEMPLATE = """
请仔细观看这段爆款短视频，结合以下数据，生成一份完整的 SCRIPT.md 文件。

【DESIGN.md（参考）】
{design_content_summary}...

【视频数据】
时长 {duration:.1f}s
切换点：
{scene_list_str}

【完整台词】
{total_text}

【台词时间戳】
{segs}

【输出格式】

# SCRIPT.md

## Global Direction
- **Video type**: （产品带货 / 情感共鸣 / 知识科普 / 生活方式）
- **Target audience**: （目标受众）
- **Platform**: （抖音 / 小红书 / 视频号）
- **Tone**: （语气风格）
- **Total duration**: {duration:.1f}s

## Narration

### Hook（0.0s - Xs）
> （原台词还原）
**Template**: "{{主题}} {{痛点/卖点}}……"
**Formula**: （hook 结构分析）

---

### Story（Xs - Xs）
> （原台词还原）
**Template**: "（带占位符的句式）"
**Beat breakdown**:
- Beat 1 (Xs-Xs): （做了什么）

---

### Proof（Xs - Xs）
> （原台词还原）
**Template**: "（带占位符的句式）"
**Proof type**: （证明类型）

---

### CTA（Xs - {duration:.1f}s）
> （原台词还原）
**Template**: "（带占位符的句式）"
**CTA type**: （关注 / 购买 / 评论）

---

## Rhythm Notes
- **Pacing**: （快/中/慢）
- **Emotional beats**: （情绪高点时间节点）
- **Music cues**: （BGM 卡点时间）

## Migration Instructions
（迁移说明）"""

STORYBOARD_SYSTEM_PROMPT = (
    "你是一位精通 Hyperframes 视频制作的分镜导演和运动设计师。"
    "根据所提供的爆款短视频及已生成的 DESIGN.md / SCRIPT.md，"
    "输出一份完整、可直接执行的 STORYBOARD.md 文件。"
    "请直接输出 Markdown 文本，不要添加任何额外解释或代码块标记。"
)

STORYBOARD_MD_TEMPLATE = """
请仔细观看这段爆款短视频，结合以下数据，生成完整的 STORYBOARD.md 文件。

【DESIGN.md】
{design_content}

【SCRIPT.md（摘要）】
{script_content}...

【时间线】总时长 {duration:.1f}s
【台词时间戳】
{segs}

【输出格式】

# STORYBOARD.md

## Global Direction
- **Format**: 9:16 vertical, {duration:.1f}s
- **Visual style**: （引用 DESIGN.md 风格）
- **Scene rhythm**: （命名节奏，如 hook-PUNCH-breathe-CTA）
- **Primary transition**: velocity-matched-upward
- **Guardrails**: （全局约束）

---

## Beat-by-Beat Direction

### Beat 1 — [Hook] (0.0s - Xs)

**Composition filename**: `beat-1-hook.html`
**Narration**: "（台词）"
**Concept**: （2-3句）
**Mood & camera**: （镜头感）

**Depth layers**:
- BG: （颜色 + 2-5个装饰元素）
- MG: （主要内容）
- FG: （字幕条、贴纸等）

**Animation choreography**:
- `主标题`: SLAMS in from left, 0.3s, expo.out
- `字幕条`: FADES up from bottom, 0.4s, power2.out
- `背景光晕`: breathe scale 1.0→1.08, 4s loop, sine.inOut

**Techniques**: （选2-3个：SVG Path Drawing / Canvas 2D / CSS 3D / Per-Word Typography / Character Typing / Velocity Transitions）

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件（项目内无 /assets/sfx/ 目录）

---

### Beat 2 — [Story] (Xs - Xs)
**Composition filename**: `beat-2-story.html`
（同上格式）

---

### Beat N — [CTA] (Xs - {duration:.1f}s)
**Composition filename**: `beat-N-cta.html`
（同上格式，最后一个 beat 允许 fade-out）

---

## Asset Audit

| Asset | Type | Used in | Notes |
|-------|------|---------|-------|
| （文件名） | image/video/font | Beat X | （用途） |

## Migration Notes
（迁移说明）

重要约束：
- 字体只使用 Google Fonts 英文名（Noto Serif SC、Noto Sans SC、Inter 等），不用中文名
- SFX 字段一律填"不使用外部音效文件"，因为项目无 /assets/sfx/ 目录
"""

NARRATION_CLEAN_SYSTEM_PROMPT = (
    "你是一位专业的视频配音脚本编辑。"
    "将输入的原始 ASR 台词整理为干净、流畅的旁白文本，并做发音替换：\n"
    "- 英文缩写拆字母（API → A P I，URL → U R L）\n"
    "- 数字/金额用汉字表达（$2T → 两万亿，100% → 百分之百）\n"
    "- 去除口语填充词（嗯、啊、那个等）\n"
    "- 保持原始语气和节奏，不改变句义。\n"
    "只输出处理后的纯文本，不加任何说明。"
)


COMPOSITION_HTML_SYSTEM_PROMPT = """\
你是一位精通 Hyperframes + GSAP 的视频合成工程师。
根据提供的 beat 分镜描述、DESIGN.md 和台词时间戳，
生成一个符合 Hyperframes 规范的 sub-composition HTML 文件。

━━━━━━━━━━━━━━ 必须严格遵守的规范 ━━━━━━━━━━━━━━

【结构】
- 整个文件用 <template id="{comp_id}-template"> 包裹
- composition div 必须有：data-composition-id="{comp_id}" data-width="1080" data-height="1920"
- 每个 clip 元素必须同时有：id="唯一id" class="clip" data-start="秒" data-duration="秒" data-track-index="唯一整数"
  ★ id 是必须的，格式建议：{comp_id}-bg / {comp_id}-title / {comp_id}-subtitle 等
  ★ data-track-index 在整个 composition 内必须唯一，从 0 开始递增

【Timeline】
- 必须首先写：window.__timelines = window.__timelines || {};
- 然后：const tl = gsap.timeline({{ paused: true }});
- 最后：window.__timelines["{comp_id}"] = tl;
- 所有动画挂在 tl 上，包括 ambient loop（禁止裸 gsap.to()）
- 用 tl.fromTo() 而非 tl.from()（防止 immediateRender 问题）
- repeat 必须有限：Math.floor(duration / cycleDuration) - 1（禁止 repeat: -1）
  注意：用 Math.floor 不是 Math.ceil
- 第一个入场动画从 t=0.1 开始，不从 0 开始

【字体】
- 只使用 Google Fonts 中的字体，必须用英文名：
  ✓ Noto Serif SC（中文宋/serif）
  ✓ Noto Sans SC（中文黑/sans）
  ✓ Inter（英文 sans）
  ✓ Cinzel（英文 decorative）
  ✗ 禁止：思源黑体、思源宋体、思源粗宋、方正、微软雅黑、苹方、Old English Text MT

【音效/音频】
- 禁止在 sub-composition 里添加 <audio> 元素（BGM 由 index.html 统一管理）
- 如果 storyboard 有 SFX 描述，用 GSAP 动画效果模拟（如 scale burst），不用 <audio>

【动画规范】
- 标题 ≥ 80px，正文 ≥ 32px，标签 ≥ 24px
- 至少 3 种不同 GSAP ease
- 至少 8 个视觉元素（BG 装饰 2-5 个 + MG 内容 + FG 细节）
- 装饰元素必须有 ambient GSAP loop（呼吸/漂移/脉冲），挂在 tl 上

【禁止】
- Math.random() / Date.now()
- repeat: -1
- 异步构建 timeline（async/setTimeout/Promise）
- 在 <audio> 里引用 /assets/sfx/ 等不存在的路径
- 非最后 beat 禁止出场动画（opacity→0 / y offscreen）

只输出完整 HTML，从 <template> 开始，到 </template> 结束，不加任何 markdown 包裹或说明。"""

COMPOSITION_HTML_TEMPLATE = """
请生成 Beat {beat_num} ({beat_label}) 的 Hyperframes sub-composition HTML。

【基本参数】
- composition id: {beat_id}
- 时间范围: {beat_start}s - {beat_end}s（时长 {beat_duration}s）
- 是否最后 beat（允许淡出）: {is_final_str}

【DESIGN.md】
{design_content}

【本 Beat 分镜描述（来自 STORYBOARD.md）】
{storyboard_beat_section}

【本 Beat 台词（已转为相对时间，0 = beat 开始）】
{relative_words_json}

【代码关键要求】
const duration = {beat_duration};  // 用于所有 repeat 计算

// ★ repeat 计算固定用法（以 4s 周期为例）：
// repeat: Math.floor(duration / 4) - 1

// ★ 每个 clip 元素示例：
// <div id="{beat_id}-title" class="clip" data-start="0.1" data-duration="{beat_duration}"
//      data-track-index="1" style="...">文字</div>

// ★ timeline 初始化固定写法：
// window.__timelines = window.__timelines || {{}};
// const tl = gsap.timeline({{ paused: true }});
// window.__timelines["{beat_id}"] = tl;

请生成完整 HTML（从 <template id="{beat_id}-template"> 到 </template>）。"""
