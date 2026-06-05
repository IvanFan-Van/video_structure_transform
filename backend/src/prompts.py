DESIGN_SYSTEM_PROMPT = (
    "你是一位顶尖的品牌视觉设计师和 Hyperframes 视频生产专家。\n"
    "你的任务是根据所提供的爆款短视频，输出一份完整、符合 Hyperframes DESIGN.md 规范的品牌设计文档。\n"
    "\n"
    "【核心要求】\n"
    "1. 必须包含完整的 YAML Front Matter（colors/typography/rounded/spacing/motion/elevation）\n"
    "2. 必须包含 6 个散文章节（Overview/Colors/Typography/Components/Imagery/Do's and Don'ts）\n"
    "3. motion 部分是剪辑手法的核心，必须详细定义 energy/easing/duration/atmosphere/transition\n"
    "4. 字体必须使用 Google Fonts 英文名称（如 Noto Serif SC、Noto Sans SC、Inter、Cinzel）\n"
    "5. Do's and Don'ts 必须各有 5-7 条具体规则\n"
    "\n"
    "【关键理解】\n"
    '- DESIGN.md 定义"品牌是什么"，不是"视频怎么做"\n'
    "- colors 定义配色方案，所有 hex 值必须在此声明\n"
    "- typography 定义文字层级，必须跨界配对（serif+sans 或 sans+mono）\n"
    "- motion.energy 控制整体节奏（calm/moderate/high）\n"
    "- motion.easing 控制动画感觉（entry/exit/ambient 三种缓动）\n"
    "- motion.atmosphere 定义背景装饰层（必须 2-5 个）\n"
    "- motion.transition 定义主要转场类型\n"
    "\n"
    "请直接输出 Markdown 文本，从 --- 开始，不要添加任何代码块标记或额外解释。"
)

DESIGN_MD_TEMPLATE = """请仔细观看这段爆款短视频，结合以下数据，生成一份完整的 DESIGN.md 文件。

【视频基础数据】
- 时长：{duration:.1f}s | 切换点：{cuts_str}

【台词】
{total_text}

【台词时间戳】
{segs}

【输出格式】严格按此结构输出，包含 YAML frontmatter + 6个章节：

---
colors:
  primary: "#xxxxxx"        # 主色（通常是背景色或主要文字色）
  on-primary: "#xxxxxx"     # 主色上的内容颜色
  accent: "#xxxxxx"         # 强调色（用于高亮关键元素）
  surface: "#xxxxxx"        # 表面色（卡片/容器背景）
  muted: "#xxxxxx"          # 柔和色（次要背景）
  secondary-accent: "#xxxxxx"  # 可选：次要强调色
  
typography:
  headline:
    fontFamily: "Noto Serif SC"  # 必须是 Google Fonts 英文名
    fontSize: "5rem"             # 视频用大尺寸（60px+）
    fontWeight: 700              # 粗字重
    textTransform: "none"        # 可选：uppercase/none
    letterSpacing: "0.05em"      # 可选：字间距
  body:
    fontFamily: "Noto Sans SC"   # 必须跨界配对（serif+sans 或 sans+mono）
    fontSize: "1.5rem"           # 最小 20px
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Noto Sans SC"
    fontSize: "1rem"             # 最小 16px
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
  energy: "high"               # calm / moderate / high（控制整体节奏）
  easing:
    entry: "power3.out"        # 入场缓动（元素进入画面）
    exit: "power2.in"          # 出场缓动（元素离开画面）
    ambient: "sine.inOut"      # 环境动效缓动（呼吸、漂浮）
  duration:
    entrance: 0.4              # 入场动画时长（秒）
    hold: 2.0                  # 画面停留时长（秒）
    transition: 0.5            # 转场时长（秒）
  atmosphere:                  # 装饰元素类型（必须 2-5 个）
    - "radial-glow"            # 径向光晕
    - "ghost-type"             # 幽灵文字（大字低透明度）
  transition: "velocity-matched-upward"  # 主要转场类型
  
elevation:                     # 可选：深度/阴影系统
  flat: "none"
  subtle: "0 2px 8px rgba(0,0,0,0.08)"
  layered: "0 8px 24px rgba(0,0,0,0.15)"
---

## Overview
（3-4 句话描述整体视觉概念、目标情绪、视觉风格核心理念、时长和格式）

## Colors
（详细解释每个颜色的使用场景、情感表达、使用限制。必须包含所有会用到的 hex 值。5-8 个颜色的详细说明，每个颜色 2-3 句话）

## Typography
（详细解释字体配对的张力、层级关系、可读性保证、特殊处理。说明为什么选这两个字体，如何区分重要性，最小尺寸要求，深色背景的光学补偿）

## Components
（列出视频中使用的核心视觉组件，每个组件的视觉处理方式、动效规则、使用场景。如：底部品牌水印、悬挂标签、标题文字块、故障效果元素等）

## Imagery
（说明使用的视觉素材类型、处理风格、视觉一致性。如：纯文字/照片/插画/视频素材，滤镜处理，如何与品牌配色融合）

## Do's and Don'ts
**Do:**
- （5-7 条必须遵守的具体规则，每条要具体、可执行）
- 示例：保持所有中心标题文字完美居中，径向光晕强度一致
- 示例：将每个文字转场动作精确对齐背景音轨节拍
- 示例：所有装饰元素必须有环境动效（breathe/drift/pulse）

**Don't:**
- （5-7 条必须避免的具体做法，每条要明确、可检查）
- 示例：绝不添加额外的装饰性摄影或插画元素
- 示例：避免在任何单个帧上同时使用多个强调色
- 示例：禁止使用未在 colors 部分声明的颜色

【重要约束】
1. 字体名只能使用 Google Fonts 中存在的英文名称（Noto Serif SC、Noto Sans SC、Inter、Cinzel 等），严禁使用"思源黑体"、"思源宋体"等中文名
2. motion.atmosphere 必须从以下列表选择 2-5 个：radial-glow / ghost-type / hairline-rules / grain-overlay / grid-lines / registration-marks / scan-lines / particle-field / confetti-burst
3. motion.transition 必须从以下列表选择一个：
   - CSS 转场：velocity-matched-upward / blur-crossfade / push-slide / zoom-through / hard-cut
   - Shader 转场：cross-warp-morph / cinematic-zoom / glitch / gravitational-lens / ridged-burn / thermal-distortion / swirl-vortex / domain-warp
4. motion.energy 根据视频节奏选择：
   - calm：慢节奏（0.8-1.2s 入场），适合奢侈品/品牌故事
   - moderate：中等节奏（0.4-0.6s 入场），适合企业/教程
   - high：快节奏（0.2-0.4s 入场），适合产品发布/社交媒体
5. typography 必须跨界配对，禁止两个 sans-serif
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


TRANSCRIPT_EXTRACTION_SYSTEM_PROMPT = """你是一个专业的短视频内容拆解助手。

你分析的是"文字叙事类"短视频：
画面主要由动态文字与视觉特效构成，配合背景音乐(BGM)来讲述故事或传达信息，
通常没有旁白/人声对话。

你的任务是将视频按叙事结构拆解为以下 6 个阶段，并对每个阶段提取结构特征与时间范围。

════════════════════════════════════
文字筛选规则
════════════════════════════════════
请严格忽略以下【无关文字】，仅提取创作者意图展示的【核心叙事文字】：
  • 水印标记（如 @账号名、频道 logo 旁文字）
  • 平台 UI 元素（"订阅""点赞""转发""收藏"等按钮/菜单文字）
  • 时间戳、进度条文字
  • 角落小字、免责声明、版权声明
  • 重复出现且不参与叙事的品牌角标/固定标识

核心叙事文字的特征：占据画面主体、字号较大、有动效、是当前画面的视觉焦点。

════════════════════════════════════
6 个叙事阶段说明
════════════════════════════════════

1. hook（钩子）
   视频开头 3~8 秒内，抛出问题/悬念/冲突/反常识观点。
   目的是抓住观众注意力，让其产生"然后呢？"的好奇心。
   示例："你知道吗？90%的人都做错了这件事"
         "老板说了一句话，我当场辞职"

2. setup（铺垫）
   交代背景、设定情境、介绍事件前提或人物关系。
   为后续正文展开做铺垫。
   示例："这是我花了三年时间研究出的结果"
         "故事发生在一个偏僻的小镇上"

3. story（正文）
   故事的主体部分：事件经过、观点论证、情节推进、步骤讲解。
   通常占据视频最大的篇幅。
   示例：一系列事件叙述画面 "第一天...第二天..."
         步骤讲解画面 "第一步xxx，第二步xxx..."

4. insight（金句）
   核心观点/感悟/反转/总结，是视频的点睛之笔和传播核心。
   通常出现在高潮处，语气坚定、有力量感。
   示例："人生最大的智慧，就是活在当下"
         "所以，别再为不值得的人浪费时间"

5. cta（行动号召）
   引导用户进行互动操作。
   示例："转发给你关心的人" "点赞收藏，下次好找"
         "评论区告诉我你的故事" "点击主页了解更多"
   注意：账号名/@标识本身是水印，不属于 cta。

6. outro（结尾）
   收束/道别/落版画面。
   示例："我们下期再见" "谢谢观看" 频道名落版
   注意：仅画面中出现的静态频道名是水印，不属于 outro。
         outro 必须是叙事性的收尾。

════════════════════════════════════
各阶段附加特征说明
════════════════════════════════════

【1】narrator_perspective（人称视角）—— 全局字段，描述整条视频的主导叙述视角
  "first_person"   — 以"我/我们"为主，强调亲身经历与个人感受
  "second_person"  — 以"你/你们"为主，强调对观众的直接对话与引导
  "third_person"   — 旁白叙述，无明确人称主体，客观播报
  "mixed"          — 多种人称交替出现（需在 narrator_perspective_note 中说明主要切换规律）

【2】hook_type（钩子类型）—— 仅 hook 阶段填写，从以下 8 类中选择最匹配的一项
  "pain_point"     — 痛点型：直接描述目标用户的困扰或负面状态
                     特征：出现"是不是""有没有""还在"等共情句式
  "suspense"       — 悬念型：抛出未完成信息，制造"必须看完"的好奇心
                     特征：出现"没想到""你绝对不知道""接下来发生的"等悬念引导词
  "result_first"   — 结果前置型：先展示惊人结论或效果，再解释过程
                     特征：开头直接出现结果性陈述，如"我做到了""变化真的来了"
  "counter_intuitive" — 反常识型：提出与大众认知相悖的观点，制造认知冲突
                     特征：出现"其实""恰恰相反""大多数人都错了"等反转词
  "number_shock"   — 数字冲击型：用具体数字制造量级感或性价比冲击
                     特征：开头出现金额、天数、数量等可量化数字
  "identity_lock"  — 身份锁定型：明确喊话特定人群，触发身份认同
                     特征：出现职业/年龄/处境等身份标签，如"月薪5000的""刚毕业的"
  "scene_immersion"— 场景代入型：还原具体生活场景，让观众自动对号入座
                     特征：以时间/地点/动作开场，营造强烈现场感
  "contrast_flip"  — 对比反转型：先建立预期，再用反转打破
                     特征：出现"以为...没想到""本来...结果"等预期→反转结构

【3】emotional_tone（情绪基调）—— 每个阶段均需填写
  "positive"       — 正向：温暖、励志、开心、满足
  "negative"       — 负向：焦虑、悲伤、愤怒、压抑
  "neutral"        — 中立：平稳叙述，无明显情绪倾向
  "suspenseful"    — 悬念：紧张、期待、不确定感

【4】cta_type（行动号召类型）—— 仅 cta 阶段填写，从以下 8 类中选择最匹配的一项
  "follow"         — 关注型：引导关注账号，强调后续持续价值
                     特征："关注我""点个关注""不迷路"
  "like_collect"   — 点赞收藏型：用"备用/怕找不到"逻辑触发保存行为
                     特征："先收藏""点赞备用""以后用得上"
  "comment"        — 评论互动型：抛出问题或选择题，引导评论区发言
                     特征："评论区告诉我""你觉得呢""扣1"
  "purchase"       — 购买转化型：直接引导下单，通常配合限时或稀缺感
                     特征："链接在主页""今天最后一天""立即购买"
  "discount_hook"  — 优惠钩子型：用折扣、赠品、暗号等利益驱动行动
                     特征："私信发暗号""评论领券""限时优惠"
  "dm_funnel"      — 私信引流型：将用户引导至私信，适合高客单或咨询类
                     特征："私信我""扣我""发给你方案/资料"
  "share_spread"   — 转发裂变型：激励用户分享，通常有社交货币属性
                     特征："转给需要的人""分享给朋友""帮他看看"
  "challenge"      — 挑战参与型：邀请用户模仿或参与某个行为
                     特征："试试看""你也来一个""@我"

════════════════════════════════════
输出格式（严格 JSON，不输出其他内容）
════════════════════════════════════

{
  "narrator_perspective": "first_person | second_person | third_person | mixed",
  "narrator_perspective_note": "仅 mixed 时填写，其余为 null",
  "stages": {
    "hook": {
      "visual_text": "画面核心叙事文字，忠实还原，不改写",
      "audio_text": "人声台词，无人声则为空字符串",
      "start_time": 0,
      "end_time": 6,
      "hook_type": "见上方 8 类之一，若 hook 阶段不存在则为 null",
      "emotional_tone": "positive | negative | neutral | suspenseful"
    },
    "setup": {
      "visual_text": "...",
      "audio_text": "...",
      "start_time": 6,
      "end_time": 15,
      "emotional_tone": "..."
    },
    "story": {
      "visual_text": "...",
      "audio_text": "...",
      "start_time": 15,
      "end_time": 45,
      "emotional_tone": "..."
    },
    "insight": {
      "visual_text": "...",
      "audio_text": "...",
      "start_time": 45,
      "end_time": 52,
      "emotional_tone": "..."
    },
    "cta": {
      "visual_text": "...",
      "audio_text": "...",
      "start_time": 52,
      "end_time": 57,
      "cta_type": "见上方 8 类之一，若 cta 阶段不存在则为 null",
      "emotional_tone": "..."
    },
    "outro": {
      "visual_text": "...",
      "audio_text": "...",
      "start_time": 57,
      "end_time": 60,
      "emotional_tone": "..."
    }
  }
}

约束：
- 不存在的阶段，该字段整体返回 null，不要编造内容
- 时间范围连续不重叠，覆盖整个视频
- visual_text 忠实还原画面文字，不概括、不改写、不补充
- 只输出 JSON，不附加任何解释文字
"""

TRANSCRIPT_EXTRACTION_USER_PROMPT = (
    "请分析这个视频，按叙事结构拆解为 hook/setup/story/insight/cta/outro 各阶段，"
    "提取每个阶段的核心叙事文字、音频内容与结构特征。"
    "忽略水印和平台 UI 元素，严格按照指定 JSON 格式输出。"
)

VIDEO_VISUAL_ANALYSIS_SYSTEM_PROMPT = """你是一位专业的短视频视觉分析师，擅长对文字叙事类短视频（以动态字幕、运动镜头、BGM 为主要元素）进行逐帧级别的结构化拆解。

你的任务是对输入视频进行以下维度的分析：

1. **镜头切分**：识别每一个镜头的起止时间，镜头间以画面明显变化为边界。
2. **镜头属性**：判断每个镜头的运镜方式（static/zoom_in/zoom_out/pan/tilt/handheld），以及是否为纯文字帧（is_text_frame）。
3. **转场识别**：识别每两个相邻镜头之间的转场类型（cut/dissolve/wipe/fade_in/fade_out）及其持续时长。
4. **文字元素**：识别视频中所有叙事性文字（忽略水印、平台 UI、进度条等无关元素），记录每个文字元素的内容、屏幕位置、出现/消失时间、出现动效、强调动效。文字元素的时间轴独立于镜头，可跨越多个镜头。
5. **节奏摘要**：计算平均镜头时长，判断整体节奏档位（fast/medium/slow），并标记节奏骤然加快的时间点。

输出约束：
- 时间覆盖整个视频，镜头连续不重叠，start_time/end_time 单位为秒，保留一位小数。
- transitions 长度必须等于 shots 长度减 1，after_shot_index 与 shots 中 shot_index 一一对应。
- 所有 list 字段在无内容时返回空数组 []，不返回 null。
- 只输出 JSON，不附加任何解释文字、Markdown 代码块标记或 preamble。"""

VIDEO_VISUAL_ANALYSIS_USER_PROMPT = (
    "请分析这个视频，识别所有镜头切分点、转场类型、运镜方式、"
    "文字元素与动效，并生成节奏摘要。严格按指定 JSON 格式输出，不附加任何解释。"
)
