# STORYBOARD.md

## Global Direction
- **Format**: 9:16 vertical, 20s
- **Visual style**: 极致黑白红高反差极简动态文字视觉体系，全片无实景元素，所有文字自带径向发光悬浮效果，高能量快节奏动效，底部统一品牌水印锚点，完全遵循DESIGN.md三色视觉规范
- **Scene rhythm**: hook-build-up-punchline-proof-cta
- **Primary transition**: velocity-matched-upward
- **Guardrails**: 全程保持底部wuqr品牌水印位置样式统一，核心高亮关键词必须使用#FF2222正红色，禁止添加多余装饰图形元素，所有动效保持统一高能量向上跳转节奏，不引入任何外部实拍素材，所有文字层级严格匹配预设字体规范

---

## Beat-by-Beat Direction

### Beat 1 — [Hook Opening] (0.0s - 1.7s)

**Composition filename**: `beat-1-hook-opening.html`
**Narration**: "那天我问了个问题"
**Concept**: 纯黑背景上大标题从无到有发光弹出，开篇直接抛出叙事引子，瞬间抓住用户注意力，底部固定品牌水印首次露出。
**Mood & camera**: 居中对称构图，文字悬浮于画面正中心，无镜头位移，靠径向发光营造强烈沉浸感。

**Depth layers**:
- BG: #000000 纯黑背景，低强度全局径向柔光
- MG: 大字号Noto Serif SC白色发光标题“那天我问了个问题”
- FG: 底部居中固定wuqr哥特风格品牌水印

**Animation choreography**:
- `主标题`: SLAMS in from top, 0.4s, power3.out
- `品牌水印`: FADES up from bottom, 0.3s, power2.out
- `背景光晕`: breathe scale 1.0→1.07, 2s loop, sine.inOut

**Techniques**: Per-Word Typography, Radial Glow Rendering, Velocity Transitions

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件

---

### Beat 2 — [Hook Question] (1.7s - 2.47s)
**Composition filename**: `beat-2-hook-question.html`
**Narration**: "什么东西比10亿更有价值？"
**Concept**: 切换纯白背景，用浅灰色大字号展示反常识灵魂拷问，制造强烈视觉反差，瞬间激发用户好奇心。
**Mood & camera**: 文字居中排布，画面完全干净无多余元素，最大化突出设问内容。

**Depth layers**:
- BG: #FFFFFF 纯白背景，无多余装饰
- MG: 大字号Noto Serif SC #888888 文字“什么东西比10亿更有价值？”
- FG: 底部居中固定wuqr品牌水印

**Animation choreography**:
- `设问文字`: FADES in with soft blur, 0.3s, power3.out
- `背景`: crossfade from black to white, 0.2s, linear

**Techniques**: Ghost Type Effect, Velocity Transitions

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件

---

### Beat 3 — [Value Cards] (2.47s - 4.87s)
**Composition filename**: `beat-3-value-cards.html`
**Narration**: "友谊、时光、自由"
**Concept**: 回到纯黑背景，三个红色吊绳悬挂的发光白色吊牌依次从画面上方坠落，展示大众普遍认知的高价值非物质选项，铺垫悬念。
**Mood & camera**: 三个吊牌呈三角分布在画面中上部，下落过程带轻微弹性回弹效果。

**Depth layers**:
- BG: #000000 纯黑背景
- MG: 三个红色吊绳悬挂的发光吊牌，依次显示“友谊”“时光”“自由”红色文字
- FG: 底部居中固定wuqr品牌水印

**Animation choreography**:
- `吊牌1`: DROPS in from top left, 0.5s, bounce.out
- `吊牌2`: DROPS in from top center, 0.5s, bounce.out, delay 0.15s
- `吊牌3`: DROPS in from top right, 0.5s, bounce.out, delay 0.3s

**Techniques**: CSS 3D Card Rotation, SVG Path Drawing, Velocity Transitions

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件

---

### Beat 4 — [Story Build] (4.87s - 7.3s)
**Composition filename**: `beat-4-story-build.html`
**Narration**: "直到有一天，一个“傻子”回答道"
**Concept**: 吊牌全部消失，纯黑背景上文字逐段弹出，其中“傻子”三个字用红色高亮块衬托，制造强烈反差感，铺垫颠覆性答案的到来。
**Mood & camera**: 文字居中排布，红色高亮部分成为绝对视觉焦点，强化反差记忆点。

**Depth layers**:
- BG: #000000 纯黑背景
- MG: 白色大标题文字，“傻子”二字被#FF2222红色发光背景块高亮
- FG: 底部居中固定wuqr品牌水印

**Animation choreography**:
- `第一行文字`: FADES in, 0.4s, power3.out
- `红色高亮块`: SCALE in from center, 0.3s, power3.out
- `第二行文字`: FADES in, 0.4s, power3.out, delay 0.2s

**Techniques**: Per-Word Typography, Radial Glow Rendering, Velocity Transitions

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件

---

### Beat 5 — [Punchline 11亿] (7.3s - 9.87s)
**Composition filename**: `beat-5-punchline-11yi.html`
**Narration**: "11亿"
**Concept**: 核心答案“11亿”大标题弹出，随后触发RGB色彩错位故障特效，强化网感冲击力，完全打破用户之前的心理预期。
**Mood & camera**: 超大字号文字占据画面核心位置，故障特效带来强烈的视觉冲击感。

**Depth layers**:
- BG: #000000 纯黑背景
- MG: 白色超大字号“11亿”标题，随后触发RGB三色错位故障效果
- FG: 底部居中固定wuqr品牌水印

**Animation choreography**:
- `11亿主标题`: SLAMS in from center, 0.4s, expo.out
- `RGB故障特效`: GLITCH offset x/y 12px, 0.8s, sine.inOut
- `故障消散`: 色彩偏移逐步归零，恢复清晰文字状态

**Techniques**: RGB Glitch Effect, Per-Word Typography, Velocity Transitions

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件

---

### Beat 6 — [Proof Scroll] (9.87s - 17.5s)
**Composition filename**: `beat-6-proof-scroll.html`
**Narration**: "11项远超物质财富的人生珍贵事物快速闪回"
**Concept**: 切换#1A1A1A深灰背景，11项人生价值点条目以极快速度向上滚动展示，快速输出所有共识性价值内容，支撑核心观点。
**Mood & camera**: 文字列表居中向上高速滚动，节奏紧凑信息密度高，适配短视频快节奏传播逻辑。

**Depth layers**:
- BG: #1A1A1A 深灰色背景
- MG: 白色Noto Sans SC正文文字，11条价值点条目依次向上滚动展示
- FG: 底部居中固定wuqr品牌水印

**Animation choreography**:
- `滚动列表`: VELOCITY SCROLL upward, 7.5s total duration, constant speed
- `条目文字`: 每一条文字进入画面时淡入，离开画面时淡出，全程保持清晰可读性

**Techniques**: Canvas 2D High Speed Scrolling, Velocity Transitions

**Transition out**: velocity-matched upward — exit y:-150 blur:30px 0.33s power2.in

**SFX**: 不使用外部音效文件

---

### Beat 7 — [CTA Conclusion] (17.5s - 20.1s)
**Composition filename**: `beat-7-cta-conclusion.html`
**Narration**: "10亿<11亿"
**Concept**: 回到纯黑背景，先后展示“10亿<11亿”和“11亿>10亿”的数值对比，最后画面缓慢淡出，强化核心结论，引导用户评论互动。
**Mood & camera**: 对比文字居中排布，厚重沉稳，作为全片最终情绪落点。

**Depth layers**:
- BG: #000000 纯黑背景
- MG: 白色大字号数值对比文字，先后展示“10亿<11亿”和“11亿>10亿”
- FG: 底部居中固定wuqr品牌水印

**Animation choreography**:
- `第一组对比文字`: FADES in, 0.4s, power3.out
- `第二组对比文字`: crossfade replace, 0.3s, power2.out
- `最终画面`: FADE OUT to pure black, 0.5s, linear

**Techniques**: Ghost Type Effect, Radial Glow Rendering

**Transition out**: fade out to pure black, no velocity transition

**SFX**: 不使用外部音效文件

---

## Asset Audit

| Asset | Type | Used in | Notes |
|-------|------|---------|-------|
| Noto Serif SC | font | All headline beats | Google Fonts 官方字体，用于所有大标题展示 |
| Noto Sans SC | font | Beat 6 | Google Fonts 官方字体，用于滚动价值点正文展示 |
| wuqr logo | text asset | All beats | 底部固定品牌水印，全程保持位置样式统一 |

## Migration Notes
所有动效参数完全匹配DESIGN.md中定义的高能量动效规范，所有色彩严格使用预设的5种配色，无需引入任何外部实拍素材、音频文件和第三方图片资源，仅使用CSS+SVG+Canvas 2D即可完成全片所有效果渲染，完全适配Hyperframes短视频制作引擎的输出要求。