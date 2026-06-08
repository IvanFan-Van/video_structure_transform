# Viral Structure Engine — 爆款短视频结构分析与迁移引擎

> 分析爆款短视频 → 提取可复用的结构模板（含视觉特效识别） → 迁移到新内容 → 自动渲染为高质量 MP4

全自动管道：输入一个爆款短视频，AI 分析其脚本结构、视觉特效、文字位置、BGM 卡点节奏，产出结构模板。填入新产品信息后，自动生成带 TTS 语音、BGM、59 种视觉特效组件、4 种风格变体的渲染结果。

---

## 完整流程图

```
                            ┌──────────────────────┐
                            │   input_videos/*.mp4  │  用户投放爆款短视频
                            └──────────┬───────────┘
                                       │
                    python main.py video.mp4 --output-dir output/
                                       │
           ┌───────────────────────────┴───────────────────────────────────────┐
           │                                                                   │
           ▼                                                                   │
┌─────────────────────┐                                                        │
│   Phase 0  本地预处理 │  6个纯本地步骤，不涉及任何LLM                           │
│                     │                                                        │
│  ① ffprobe 元数据    │  提取: 文件名, 时长, 分辨率, 帧率, 编码, 是否有音轨     │
│  ② ffmpeg 提取音频   │  提取WAV → UVR-MDX-NET 人声/伴奏分离                  │
│  ③ ASR 语音转写      │  faster-whisper(small) → 词级时间戳转写                │
│  ④ OpenCV 镜头切分   │  HSV直方图差异法 → 镜头切换点列表                       │
│  ⑤ 关键帧抽取        │  每个镜头中点+首尾帧 → JPEG+base64编码                  │
│  ⑥ librosa BGM分析   │  BPM检测 + 节拍定位 + 能量曲线 + 情绪推断              │
│                     │  + 卡点同步率计算(切点与重拍距离<50ms)                   │
└─────────┬───────────┘                                                        │
          │                                                                    │
          │  PreprocessResult (data class，26个字段)                             │
          │  包含: ASR词级时间戳, 镜头切点, 关键帧base64, BPM,                    │
          │        节拍时间点, 能量曲线, 卡点匹配率 ...                            │
          ▼                                                                    │
┌─────────────────────┐                                                        │
│   Phase 1  宏观分析   │  ★ 1次 LLM Vision API 调用                            │
│                     │                                                        │
│  输入: 完整视频base64 + ASR词级时间戳 + BGM数据 + 镜头切点参考                  │
│  输出: beat边界(2-6秒/个), 全局视觉风格(subtitle_heavy/person_led/...),        │
│        脚本结构(hook→pain_point→solution→product_show→cta→outro),             │
│        节奏模式(slow-fast-climax/steady_build/...)                            │
│                     │                                                        │
│  Beat 后处理: 吸附切点(0.3s) → 修正首尾 → 填充间隙(>1.5s) → 合并短beat(<1s)  │
└─────────┬───────────┘                                                        │
          │  产出: N个beat (start_time, end_time, description)                   │
          ▼                                                                    │
┌─────────────────────┐                                                        │
│   Phase 2  逐Beat分析 │  ★ N次 LLM Vision API 并发调用 (ThreadPoolExecutor)    │
│                     │                                                        │
│  每个beat独立发送:                                                            │
│    - 视频片段(base64, 向前延展0.5s看转场)                                     │
│    - 8帧密集关键帧(base64)                                                    │
│    - 该beat的ASR词级时间戳 (用于判断Typewriter特效)                            │
│    - 注入59个remocn组件目录 (让LLM自动匹配组件名)                              │
│                     │                                                        │
│  输出每个beat:                                                                │
│    - 文字元素: text, font_size, color, position_x, position_y                 │
│    - 视觉特效: type(typewriter/fade_in/...), remocn_component, remocn_props   │
│    - 转场类型: hard_cut/fade/slide/zoom/glitch/rgb_split/wipe                │
│    - 剪辑手法: 跳切/J-cut/匹配剪辑/慢镜头                                     │
│    - 卖点内容: selling_point + selling_strategy                              │
│    - 情绪标签: curious/urgent/excited/sincere/humorous/suspenseful/calm       │
│    - BGM配合: 画面是否卡在重拍上                                              │
└─────────┬───────────┘                                                        │
          │  产出: N个 BeatAnalysis dict (含完整视觉细节)                         │
          ▼                                                                    │
┌─────────────────────┐                                                        │
│   Phase 3  高层汇总   │  ★ 1次 LLM Text API 调用 (纯文本，不下发视频)           │
│                     │                                                        │
│  输入: 所有beat的压缩摘要 (卖点+情绪+转场, 去掉了像素级细节)                    │
│        + 脚本结构 + BGM特征                                                    │
│  输出:                                                                        │
│    - 卖点策略分析: 递进式/并列式, 重点卖点, 密度评估                            │
│    - 结构槽位模板: 每个段落→{label, duration, material_type,                   │
│                              text_template(含{占位符}),                        │
│                              alternative_if_missing, migration_hint}          │
│    - 素材需求清单: {type, description, priority, can_generate}                │
└─────────┬───────────┘                                                        │
          │                                                                     │
          ▼                                                                     │
┌─────────────────────┐                                                        │
│   Phase 4  规则组装   │  纯代码统计，不涉及LLM                                  │
│                     │                                                        │
│  AS1: 卖点汇总 — 从所有beat收集非空selling_point (按时间排序)                  │
│  AS2: 转场分布 — 统计各类型转场出现次数                                        │
│  AS3: 包装主导类型 — subtitle_heavy/person_led/product_centric               │
│  AS4: 卡点同步数据 — 构建beat_alignments JSON                                 │
│  AS5: 节奏结构 — 每秒镜头频率曲线 + 快节奏段落 + 高潮位置                      │
│  AS7: 槽位规则兜底 — LLM槽位为空时从脚本结构推导                                │
│  AS8: 素材缺口分析 — 比对槽位需求 vs 用户素材 (集合差集运算)                    │
│                     │                                                        │
│  产出: analysis_result.json (16个顶层字段，完整分析)                            │
│  产出: material_template.json (用户素材填写模板)                               │
└─────────┬───────────┘                                                        │
          │                                                                     │
          └─────── 分析完成 ────────────────────────────────────────────────────┘

                                           │
                          【用户填写 material_template.json】
                          【另存为 transfer/new_content.json 】
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         transfer 结构迁移层                                    │
│                                                                              │
│   python -m transfer.transfer analysis_result.json new_content.json output.json │
│                                                                              │
│   ① 读取分析结果 (slot_template, script_structure, rhythm, bgm, packaging)    │
│   ② 逐slot构建SceneProps:                                                     │
│      - 文案填充 (_fill_template: {变量}→用户值)                                │
│      - 文字样式 (_build_text_style: 原视频字幕颜色+位置 → TextStyle)           │
│      - 3级remocn后备链:                                                       │
│        Level 1: LLM推荐的remocn_component (白名单校验)                         │
│        Level 2: effects[].type → 特效类型静态映射表                            │
│        Level 3: emotion → 情绪默认组件 (最后兜底)                               │
│      - BGM卡点: _get_beat_frames (绝对秒→相对帧)                              │
│   ③ 素材缺口检测 (detect_gaps: slot需求 vs user_materials)                    │
│   ④ 缺口补全 (apply_gap_fill):                                                │
│      - video缺失 → 纯色背景+降级场景类型                                       │
│      - image缺失 → 优先AIGC生图(Agnes API) → 失败则纯色背景                    │
│      - voiceover缺失 → 纯文字字幕                                              │
│   ⑤ TTS语速推算 (_calc_tts_rate):                                             │
│      原视频语速 = 口语字符数 / 口语时长                                          │
│      edge-tts rate = (原视频语速 / 4.2 - 1) × 100 → "+65%"                     │
│   ⑥ 风格变异 (_apply_style_mutation):                                         │
│      high_click:   Hook LLM重写疑问句 + RGBGlitchText + 时长×0.8 + 语速+5%    │
│      high_convert: 产品段时长×1.2 + ShimmerSweep                               │
│      high_rhythm:  全场景时长×0.75 + SpringPopIn + 语速+10%                   │
│   ⑦ TTS生成 (edge-tts): 旁白文案 → voiceover.wav                               │
│   ⑧ BGM拷贝: 从分析输出拷贝 bgm.wav → remotion-video/public/                  │
│   ⑨ 用户素材拷贝: user_video/user_image → remotion-video/public/              │
│   ⑩ 组装 RemotionProps → 写入 remotion_props_{style}.json                     │
│                                                                              │
│  产出: remotion_props.json (可用 --no-render 跳过渲染)                          │
│  或: 4个风格JSON + 4个MP4 (--style all)                                        │
└──────────────────────┬───────────────────────────────────────────────────────┘
                       │
                       │  remotion_props.json
                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Remotion 渲染 (React/TypeScript)                         │
│                                                                              │
│   入口: src/index.ts → Root.tsx → VideoComposition.tsx                        │
│                                                                              │
│   VideoComposition:                                                          │
│     ├── Audio (BGM, volume=35%)                                              │
│     ├── Audio (TTS旁白, volume=100%)                                          │
│     │                                                                        │
│     └── scenes.map(scene →                                                   │
│           <Sequence from={startFrame} durationInFrames={durationFrames}>      │
│             <CrossDissolveWrapper (场景间叠化过渡)>                            │
│               ├── TextOverlayScene    (type=text_overlay)                    │
│               │    → SceneBackground (视频>图片>纯色)                         │
│               │    → AnimatedText (5种动画: typewriter/fade_in/bounce/...)   │
│               │                                                              │
│               ├── EmphasisTextScene   (type=emphasis_text)                   │
│               │    → KenBurns 微缩放 (1.0→1.04)                              │
│               │    → BGM卡点脉冲装饰线 (金色竖线+发光)                          │
│               │                                                              │
│               └── RemocnScene         (type=remocn_composed)                 │
│                    → 逐句拆分Sequence                                          │
│                    → 递归渲染REMOCN_REGISTRY中的59个组件                       │
│                    → 支持children嵌套 (SpringPopIn>BlurReveal)               │
│           )                                                                  │
│         )                                                                     │
│                                                                              │
│   输出: demo_{style}.mp4 (1080×1920, 30fps, H.264)                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. 整体架构

本项目分为 **三层**:

| 层 | 语言 | 职责 | 输入 → 输出 |
|---|---|---|---|
| **分析层** (`analysis/`) | Python | 逆向工程爆款视频，提取结构模板 | input_video.mp4 → analysis_result.json |
| **迁移层** (`transfer/`) | Python | 将结构模板映射到新内容，生成渲染配置 | analysis_result.json + new_content.json → remotion_props.json |
| **渲染层** (`remotion-video/`) | TypeScript/React | 将渲染配置转为视频 | remotion_props.json → demo.mp4 |

**核心能力：**
- **爆款结构逆向**：AI 看视频 → 输出结构模板（几段、每段说什么、用什么特效、字幕在哪）
- **视觉特效自动匹配**：59 个 Remocn 组件库 + 3 级后备链（LLM 推荐 → 特效类型映射 → 情绪映射）
- **结构迁移**：同结构换内容，自动生成 TTS 语音，支持 4 种风格变异
- **零用户素材也能跑**：纯文字 + 纯色背景也能生成完整视频

---

## 2. 目录结构

```
viral-structure-engine/
├── main.py                          # ★ 分析管道入口 (Phase 0-4 串联)
├── requirements.txt                 # Python 依赖
├── .env                             # API 密钥配置 (火山方舟Ark + Agnes生图)
│
├── analysis/                        # 视频分析模块 (Python)
│   ├── __init__.py                  # 包描述 (分析管线4阶段概览)
│   ├── models.py                    # Pydantic 数据模型 (17个类)
│   ├── prompts.py                   # LLM 提示词 (3阶段 + ASR格式化 + 组件注入)
│   ├── video_utils.py               # ffmpeg 封装 (元数据/音频/帧/片段/base64)
│   ├── audio_separator.py           # UVR-MDX-NET 人声分离 + 波形相关性检测
│   ├── preprocess.py                # Phase 0: 本地预处理入口 + PreprocessResult
│   ├── analyzer.py                  # Phase 1/2/3: LLM调用编排 + Beat后处理
│   ├── assembler.py                 # Phase 4: 最终组装 + 8个规则统计任务
│   └── generate_material_template.py # 生成用户素材填写模板
│
├── transfer/                        # 结构迁移模块 (Python)
│   ├── __init__.py                  # 包描述 + 导出
│   ├── schema.py                    # 迁移层数据模型 (9个Pydantic类)
│   ├── constants.py                 # 共享常量 (TTS基准语速, 11种label→背景色)
│   ├── tts.py                       # edge-tts 语音生成 (微软免费TTS)
│   ├── gap_handler.py               # 缺口检测 + 补全策略 (纯色/AIGC/纯文字)
│   ├── transfer.py                  # ★ 迁移引擎核心 + CLI入口
│   └── new_content.json             # 用户新内容输入 (示例)
│
├── remotion-video/                  # Remotion 渲染工程 (TypeScript/React)
│   ├── package.json                 # React 19 + Remotion 4.0.433
│   ├── tsconfig.json                # TypeScript 配置
│   ├── public/                      # 运行时素材 (bgm.wav, voiceover.wav)
│   └── src/
│       ├── index.ts                 # Remotion 入口 (registerRoot)
│       ├── Root.tsx                 # Composition 定义 + 默认props
│       ├── VideoComposition.tsx     # ★ 主组合 (音频 + 场景序列 + 叠化)
│       ├── types.ts                 # TypeScript 类型定义
│       ├── scenes/                  # 场景渲染器
│       │   ├── TextOverlayScene.tsx     # 逐句打字文本
│       │   ├── EmphasisTextScene.tsx    # KenBurns + 卡点脉冲
│       │   └── RemocnScene.tsx          # 59个remocn组件渲染
│       └── components/
│           ├── AnimatedText.tsx         # 5种文字动画 + 卡点发光
│           ├── CrossDissolveWrapper.tsx # 场景叠化过渡
│           ├── SceneBackground.tsx      # 三级背景 (视频>图片>纯色)
│           ├── remocn_components.json  # 59组件目录 (name+desc)
│           └── remocn/                 # 59个视觉特效组件
│               ├── registry.ts          # 动态组件注册表
│               ├── typewriter.tsx
│               ├── blur-reveal.tsx
│               └── ... (共59个 .tsx)
│
├── input_videos/                    # 待分析爆款视频
├── output/                          # 分析输出 (按时间戳命名的子目录)
└── docs/                            # 文档
```

---

## 3. 数据流转

### 3.1 分析管道数据流

```
input_videos/1.mp4
        │
        ▼
Phase 0 → PreprocessResult (data class)
        │ .filename, .duration, .resolution, .fps, .codec
        │ .asr_segments (词级时间戳), .asr_full_text
        │ .shot_count, .shot_boundaries, .avg_shot_duration
        │ .keyframe_times, .keyframe_base64_list
        │ .bpm, .beat_timings, .energy_curve, .bgm_mood_hint
        │ .vocals_path, .bgm_path, .has_vocals
        │ .beat_sync_ratio, .beat_sync_matched_count
        │ .subtitle_density
        │
        ▼
Phase 1 → Phase1Output dict
        │ .beats[] → {beat_id, start_time, end_time, description}
        │ .global_style → {tone, primary_color, visual_mood}
        │ .script_structure[] → {label, start_time, end_time, text, keywords, emotion, hook_type, cta_type}
        │ .visual_style, .rhythm_pattern, .asr_summary, .language
        │
        ▼ (Beat后处理: snap→ensure→fill→merge)
        │
Phase 2 → list[BeatAnalysis dict]
        │ 每个beat: {beat_id, start_time, end_time,
        │           text_elements[], effects[] (含remocn_component),
        │           transition_out, editing_technique,
        │           selling_point, selling_strategy, emotion, bg_sync_note}
        │
        ▼ (压缩: 去像素级细节)
        │
Phase 3 → Phase3Output dict
        │ .selling_point_analysis → {progression, emphasized, density}
        │ .slot_template[] → {slot_id, label, duration, required_material_type,
        │                     text_template(含{占位符}), alternative_if_missing, migration_hint}
        │ .material_requirements[] → {type, description, priority, can_generate}
        │
        ▼ (规则统计: AS1-AS8)
        │
Phase 4 → analysis_result.json (16个顶层字段)
        ├── video_info           (video metadata + visual analysis summary)
        ├── script_structure     (narrative segments)
        ├── rhythm_structure     (derived rhythm statistics)
        ├── packaging_structure  (subtitle style, title cards, cover)
        ├── bgm_features         (BPM, mood, beat timings, beat alignments)
        ├── beats                (Phase 2 full output)
        ├── selling_points       (AS1: collected selling points)
        ├── selling_point_analysis (Phase 3 strategy)
        ├── slot_template        (Phase 3 template)
        ├── material_requirements (Phase 3 requirements)
        ├── gap_analysis         (AS8: material gap list)
        └── _summary             (human-readable Chinese summary)
```

### 3.2 迁移管道数据流

```
analysis_result.json  ────┐
new_content.json  ────────┤
                          ├── transfer() ─────────────────────────────────────
                          │                                                    │
                          │  loop over slot_template:                          │
                          │    slot[label] × script_seg[start_time, emotion]    │
                          │    → SceneProps {                                  │
                          │        id, startFrame, durationFrames,             │
                          │        type (text_overlay/emphasis_text/           │
                          │             remocn_composed),                      │
                          │        text (模板填充或用户提供),                     │
                          │        textStyle (原视频颜色+位置 + 情绪动画),      │
                          │        beatFrames (BGM卡点相对帧),                  │
                          │        backgroundVideo/Image/ColorFallback,        │
                          │        remocnEffects (3级后备链选择组件),           │
                          │        gapFilled/Strategy (缺口补全标记)            │
                          │      }                                             │
                          │                                                    │
                          │  gap detection:                                    │
                          │    slot.required_material_type ⊆ user_materials?    │
                          │      NO → GapItem → apply_gap_fill()               │
                          │                                                    │
                          │  style mutation (high_click/convert/rhythm):       │
                          │    modify scene.text, durationFrames,              │
                          │    remocnEffects, tts_rate                         │
                          │                                                    │
                          │  voiceover_text = join(scene.texts)                 │
                          │  TTS: voiceover_text → voiceover.wav (edge-tts)     │
                          │  BGM: copy bgm.wav → public/                       │
                          │                                                    │
                          └──▶ remotion_props_{style}.json ──▶ demo.mp4        │
```

---

## 4. 关键概念详解

### 4.1 分析管道四阶段

**Phase 0 — 预处理（纯本地）**
- `faster-whisper` ASR 语音识别（word 级时间戳）
- OpenCV 直方图差异法镜头分割
- 关键帧提取（每个镜头中点 + 首帧末帧）
- `librosa` BPM 检测 + 节拍追踪 + 能量曲线
- `UVR-MDX-NET` 人声/背景音乐分离 + 波形相关性检测

**Phase 1 — 宏观分析（1 次 LLM 调用）**
- 输入：全片 base64 + 关键帧 + ASR 文本 + cut points
- 输出：节拍边界（2-6 秒/个）、视觉风格分类、脚本结构（hook/pain_point/solution/CTA）、节奏模式

**Phase 2 — 逐节拍精细化（N 次并发 LLM 调用）**
- 输入：每个节拍的视频片段 + 8 帧密集关键帧 + ASR 片段
- 输出：文字元素（text/font_size/color/position_x/position_y）、视觉特效（含 remocn 组件名）、转场类型、剪辑技巧、卖点、情绪
- 系统提示词注入 59 个 remocn 组件目录，LLM 自动匹配组件名
- 后处理：节拍对齐 cut point、首尾补齐、间隙填充、短节拍合并

**Phase 3 — 跨节拍汇总（1 次 LLM 调用）**
- 输入：压缩后的全部分析结果（文本型，不下发视频）
- 输出：卖点策略分析、槽位模板（含 `{变量占位符}`）、素材需求清单

### 4.2 结构迁移 — 3 级 Remocn 后备链

为每个 scene 选择 remocn 视觉组件时，按以下优先级降级：

```
第 1 级：LLM 推荐 — Phase 2 分析时 LLM 从 59 目录中选择的 remocn_component
         ↓ 未命中白名单时降级
第 2 级：特效类型静态映射 — EFFECT_TYPE_TO_REMOCN[effects[].type]
         例："typewriter" → Typewriter、"glitch" → RGBGlitchText
         ↓ 无匹配时降级
第 3 级：情绪静态映射 — EMOTION_TO_REMOCN[beat.emotion]
         例："excited" → SpringPopIn、"neutral" → BlurReveal
         支持容器组件：SpringPopIn 包裹 Typewriter → 弹入+打字效果
```

### 4.3 逐句替换模式

所有场景使用**替换模式**渲染文字（而非累积模式）。原视频分析确认：多句字幕位于同一 `position_y`，说明是"当前句替换上一句"的做法。

实现方式：`Remotion <Sequence>` 为每句话分配独立时间段，同一位置渲染，无重叠。

### 4.4 字幕位置来源

`position_y` 完全来自爆款视频分析，非硬编码：
1. LLM (Phase 2) 分析视频帧 → 识别文字元素及其屏幕位置
2. `assembler.py` 筛选：过滤掉 `position_y < 15` 的水印残留 → 取最高值
3. `transfer.py` 继承到 `textStyle.position_y`
4. Path B 后备默认值：82%（竖屏视频字幕底部位置）

### 4.5 TTS 语速动态计算

```python
# 从原视频 ASR 采样到实际语速
原视频语速 = 口语总字符数 / 口语总时长（秒）
基准语速 = 4.2 chars/sec  # edge-tts 默认语速
速率偏移 = (原视频语速 - 基准语速) / 基准语速 * 100
# 例：(6.93 - 4.2) / 4.2 * 100 = +65%
```

风格变异在此基础上叠加：
| 风格 | TTS 速率 | 说明 |
|------|----------|------|
| standard | +65% | 原视频实际语速 |
| high_click | +70% | +5% 偏快，适配快节奏 hook |
| high_convert | +65% | 复用 standard 的 TTS 缓存 |
| high_rhythm | +75% | +10% 偏快，适配压缩时长 |

### 4.6 4 种风格变异策略

| 风格 | 关键改动 | 帧数 (30fps) | 适用场景 |
|------|----------|-------------|----------|
| **standard** | 原版结构，无变异 | ~498 | 日常发布、信息传达 |
| **high_click** | Hook LLM 重写为疑问句 + RGBGlitchText 特效 + 语速 +5% | ~468 | 提升点击率 |
| **high_convert** | 产品展示段拉长 20% + ShimmerSweep 强调卖点 + 复用 standard TTS | ~559 | 提升转化率 |
| **high_rhythm** | 所有场景压缩 25% + SpringPopIn 快速弹入 + 语速 +10% | ~374 | 高节奏、快闪 |

---

## 5. 环境准备

### 5.1 前置依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 分析管道 + 迁移层 |
| Node.js | ≥18 | Remotion 渲染 |
| FFmpeg | 任意 | 视频编解码、音频提取 |

### 5.2 Python 依赖

```bash
pip install -r requirements.txt
pip install edge-tts
```

`requirements.txt` 内容：
```
openai>=1.0.0           # LLM API 调用
instructor>=1.0.0       # 结构化输出
python-dotenv>=1.0.0    # .env 加载
pydantic>=2.0.0         # 数据校验
faster-whisper>=1.0.0   # 语音识别
opencv-python>=4.8.0    # 镜头分割
librosa>=0.10.0         # BPM 检测
soundfile>=0.12.0       # 音频 I/O
numpy>=1.24.0           # 数值计算
pillow>=10.0.0          # 图像处理
audio-separator[cpu]>=0.44.2  # 人声分离
onnxruntime>=1.18.0     # ONNX 推理
```

### 5.3 Node.js 依赖

```bash
cd remotion-video
npm install
```

### 5.4 API 配置

在项目根目录创建 `.env` 文件：

```env
API_KEY=your_volcengine_ark_api_key
MODEL=your_model_endpoint_id
BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

当前使用 **Volcengine Ark**（火山方舟）作为 LLM 后端，其 API 兼容 OpenAI 格式。模型为 **Doubao Seed-lite**。任何兼容 OpenAI chat/completions 的服务均可替换。

---

## 6. AI 工具使用说明

### 6.1 使用 LLM 的环节

| 环节 | 模型 | 触发时机 | 用途 |
|------|------|----------|------|
| Phase 1 宏观分析 | Doubao Seed-lite (Vision) | 分析管道 | 看图划分节拍、判断视觉风格、提取脚本结构 |
| Phase 2 逐节拍分析 | Doubao Seed-lite (Vision) | 分析管道 | 识别文字位置、视觉特效、转场、卖点、情绪 |
| Phase 3 跨节拍汇总 | Doubao Seed-lite (Text) | 分析管道 | 卖点策略归纳、槽位模板生成、素材需求清单 |
| Hook 文案重写 | Doubao Seed-lite (Text) | 迁移管道 `--style high_click` | 将原文案改写为高点击疑问句式 |

**模型信息：**
- 模型：Doubao Seed-lite（`doubao-seed-2-0-lite`）
- 调用方式：Volcengine Ark API（兼容 OpenAI 格式），通过 `instructor` 库实现结构化 JSON 输出
- Vision 调用使用 base64 视频帧作为输入

### 6.2 不使用 LLM 的环节

| 环节 | 实现方式 |
|------|----------|
| Phase 0 预处理 | 纯本地算法（faster-whisper ASR、OpenCV 镜头检测、librosa BPM） |
| 结构迁移映射 | 规则驱动（label→scene_type 映射表、emotion→animation 映射表） |
| 素材缺口检测 | 纯代码逻辑（集合运算 + 优先级排序） |
| TTS 语音生成 | edge-tts（微软 Edge 免费 TTS，无 LLM 参与） |
| Remotion 渲染 | React/TypeScript 声明式渲染（无 LLM 参与） |
| 3 级后备链的第 2/3 级 | 静态映射表（effects.type → remocn 组件、emotion → remocn 组件） |

### 6.3 安全边界

1. **Pydantic 校验**：所有 LLM 输出经过 Pydantic 模型强制类型校验，不合法的字段类型会被拒绝
2. **组件名白名单**：LLM 返回的 `remocn_component` 必须命中 59 组件白名单，否则降级到静态映射表
3. **LLM 重写失败后备**：`high_click` 风格的 Hook 重写如果 LLM 调用失败或返回空，自动 fallback 到用户原始文案
4. **无外部网络文件执行**：LLM 输出的所有路径、命令均不执行，仅作为数据字段存储

---

## 7. 完整运行步骤

### Step 1 — 视频分析

```bash
python main.py input_videos/your_video.mp4 --output-dir output/
```

**参数说明：**
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `video_path` | *必填* | 输入视频的绝对路径 |
| `--output-dir` | `output/` | 输出目录 |
| `--max-keyframes` | 20 | 最大关键帧数 |
| `--max-workers` | 5 | Phase 2 并发数 |
| `--verbose` | false | 详细日志 |

**运行时间参考：** 16.6 秒短视频约需 3-5 分钟（取决于 LLM 并发数）。

**产物：**
```
output/20260607_134912/                    # 时间戳命名
├── analysis_result.json                   # ★ 核心产物：完整分析结果
├── material_template.json                  # ★ 用户素材填写模板
├── intermediates/                          # 中间产物
│   ├── preprocess_result.json              # 预处理数据
│   ├── beats/beat_01.json ... beat_04.json # Phase 2 逐节拍结果
│   ├── phase1_macro.json
│   ├── phase3_summary.json
│   └── transcript.json                     # ASR 转录文本
├── keyframes/                              # 关键帧JPEG
└── audio/                                  # 音频（bgm.wav, vocals.wav, original.wav）
```

### Step 2 — 填写新内容

编辑 `output/<timestamp>/material_template.json`，填写：
1. **变量值**（必须）：`"variables": {"产品名": "谢逸牌蛋糕", ...}`
2. **素材路径**（可选）：`"user_video": "C:\\videos\\unboxing.mp4"`
3. **素材声明**：`"user_materials": ["text", "voiceover", "video"]`

填完后**另存为** `transfer/new_content.json`。

### Step 3 — 结构迁移与渲染

#### 3a. 标准版本（带 remocn 组件）

```bash
python -m transfer.transfer \
  output/20260607_134912/analysis_result.json \
  transfer/new_content.json \
  output/remotion_props.json \
  --use-remocn
```

**参数说明：**
| 参数 | 说明 |
|------|------|
| `analysis_result.json` | Step 1 的分析结果 |
| `new_content.json` | Step 2 的用户内容 |
| `output.json` | 输出的 Remotion 渲染配置文件 |
| `--use-remocn` | 启用 59 个 remocn 视觉组件（LLM 自动选择） |
| `--no-render` | 只生成 JSON，不渲染 MP4 |
| `--style standard\|all` | 指定风格（默认 standard） |

#### 3b. 仅生成配置不渲染（用于检查）

```bash
python -m transfer.transfer \
  output/20260607_134912/analysis_result.json \
  transfer/new_content.json \
  output/remotion_props.json \
  --use-remocn --no-render
```

#### 3c. 一次性生成全部 4 种风格

```bash
python -m transfer.transfer \
  output/20260607_134912/analysis_result.json \
  transfer/new_content.json \
  output/remotion_props.json \
  --use-remocn --style all
```

**运行时间参考：** 4 风格全量约需 3-5 分钟（含 2 次 TTS 生成 + 4 次 Remotion 渲染）。

---

## 8. 输出产物

### 8.1 分析产物

| 文件 | 说明 |
|------|------|
| `analysis_result.json` | 完整分析结果：脚本结构、节拍、特效、卖点、槽位模板、节奏数据 |
| `material_template.json` | 用户素材填写模板（含占位变量说明） |
| `intermediates/` | Phase 0-3 中间产物（调试用） |
| `audio/bgm.wav` | 从视频中分离的背景音乐 |

### 8.2 渲染产物

| 文件 | 说明 | 大小参考 |
|------|------|----------|
| `demo_standard.mp4` | 标准版，原始节奏 | ~1.5 MB |
| `demo_high_click.mp4` | 高点击版，Hook 疑问句 + RGBGlitch，语速 +5% | ~1.4 MB |
| `demo_high_convert.mp4` | 高转化版，产品段拉长 + ShimmerSweep | ~1.6 MB |
| `demo_high_rhythm.mp4` | 高节奏版，全场景压缩 + SpringPopIn，语速 +10% | ~1.0 MB |

### 8.3 配置文件

| 文件 | 说明 |
|------|------|
| `remotion_props.json` / `remotion_props_{style}.json` | Remotion 渲染输入（含所有 scene 数据、音频路径、迁移报告） |

---

## 9. 配置参考

### 9.1 `.env`

| 字段 | 说明 | 示例 |
|------|------|------|
| `API_KEY` | Volcengine Ark API Key | `ark-xxxxx` |
| `MODEL` | 模型端点 ID | `ep-20260508213828-7ntjl` |
| `BASE_URL` | API 地址 | `https://ark.cn-beijing.volces.com/api/v3` |

### 9.2 `new_content.json`

| 字段 | 类型 | 说明 |
|------|------|------|
| `theme` | `str` | 主题名（用于迁移报告） |
| `target_audience` | `str` | 目标人群 |
| `slots.<label>.text` | `str` | 槽位文本（含 `{变量}` 占位） |
| `slots.<label>.variables` | `dict` | `{变量名: 值}` 的键值对 |
| `slots.<label>.user_video` | `str \| null` | 用户视频素材的绝对路径 |
| `slots.<label>.user_image` | `str \| null` | 用户图片素材的绝对路径 |
| `user_materials` | `list[str]` | 用户提供了哪些素材：`"text"`, `"voiceover"`, `"video"`, `"image"` |
| `voiceover_text` | `str` | 语音文本（留空则自动从 slots 拼接） |
| `output_ratio` | `str` | 输出比例，默认 `"9:16"` 竖屏 |

### 9.3 预定义标签 → 背景色映射

| 标签 | 背景色 | 含义 |
|------|--------|------|
| `hook` | `#0D0D0D` | 钩子（深黑） |
| `pain_point` | `#1A1A2E` | 痛点（深蓝黑） |
| `solution` | `#F5F5F0` | 解决方案（暖白） |
| `product_show` | `#111111` | 产品展示（深黑） |
| `testimonial` | `#121212` | 用户证言（深黑） |
| `cta` | `#FF4444` | 行动号召（红色） |

---

## 10. Remocn 组件一览（59 个）

### 文字特效
| 组件 | 效果 |
|------|------|
| Typewriter | 逐字打字，闪烁光标 |
| BlurReveal | 从模糊到清晰 |
| StaggeredFadeUp | 逐词从下方弹入 |
| TrackingIn | 字间距收窄动画 |
| ShimmerSweep | 高光从左扫到右，点亮文字 |
| RGBGlitchText | 三色通道分离 + 水平抖动 |
| SpringPopIn | 弹性缩放弹入（可作容器） |
| MatrixDecode | 乱码逐位解码为目标文字 |
| SlotMachineRoll | 老虎机滚动数字 |
| MaskedSlideReveal | 遮罩滑动揭露 |
| InlineHighlight | 句中单字高亮变色 |
| MarkerHighlight | 标记笔扫过短语背景 |
| TextFadeReplace | 淡入淡出替换文字 |
| InfiniteMarquee | 无限横向滚动文字 |
| PerspectiveMarquee | 3D 透视无限滚动 |

### UI 模拟
| 组件 | 效果 |
|------|------|
| CursorFlow | 鼠标沿贝塞尔路径移动点击 |
| BrowserFlow | 完整浏览器模拟（URL输入→加载→滚动→点击） |
| TerminalSimulator | 终端命令行执行模拟 |
| ToastNotification | 系统弹窗弹出收起 |
| ToolMenuSlideIn | 工具图标菜单滑入 |
| BoundingBoxSelector | 选中框吸附目标 |
| BrushStrokeSimulator | 手指拖动模糊刷 |
| DragAndDropFlow | 拖拽文件到目标区域 |

### 过渡与转场
| 组件 | 效果 |
|------|------|
| DirectionalWipe | 滑动替换场景 |
| SwipeTransitionWipe | 手机滑动切换（视差+拖影） |
| SpatialPush | 新场景推入，旧场景压退 |
| FrostedGlassWipe | 磨砂玻璃滑过 |
| GridPixelateWipe | 网格像素化溶解 |
| ChromaticAberrationWipe | 色差效果快切 |
| ZoomThroughTransition | 放大穿透到下一场景 |
| MorphingModal | 卡片→全屏模态框 |

### 产品展示
| 组件 | 效果 |
|------|------|
| HeroDeviceAssemble | 设备零件飞入组装 |
| DeviceMockupZoom | 屏幕→带壳设备缩小 |
| ProductLaunchTrailer | 电影感产品发布预告 |
| ChangelogBite | 变更日志卡片 |
| PricingTierFocus | 定价卡片聚焦突出 |
| EcosystemConstellation | 核心+卫星生态图 |
| SpotlightCard | 光标跟随聚光灯卡片 |

### 背景与装饰
| 组件 | 效果 |
|------|------|
| MeshGradientBg | 动态噪点渐变色 |
| DynamicGrid | 动态网格/点阵背景 |
| InfiniteBentoPan | 无限 Bento 网格漂移 |
| StaggeredBentoGrid | Bento 卡片级联弹出 |
| ImageExpandToFullscreen | 缩略图→全屏展开 |

---

## 11. 故障排查

### 11.1 LLM 调用失败
```
Error: instructor 结构化输出解析失败
```
- **原因：** `doubao-seed-2-0-lite` 偶尔输出不合法的 JSON
- **解决：** 自动 fallback 到 JSON 解析重试，一般 1-2 次内恢复。

### 11.2 ASR 失败（无语音视频）
```
⚠ 未检测到有效语音，将使用静音节奏
```
- **原因：** 纯画面视频 / 背景音乐过大
- **影响：** Typewriter 检测失效，仍可正常运行

### 11.3 edge-tts 语音生成失败
```
edge_tts.exceptions.UnknownResponse: No audio data received
```
- **原因：** 网络问题或 edge-tts 服务更新
- **解决：** 重试 1-2 次；确保 `pip install edge-tts` 为最新版（≥7.2.8）

### 11.4 Remotion 渲染报错
```
Error: Component "xxx" not found in registry
```
- **原因：** transfer 输出的组件名不在 `REMOCN_REGISTRY` 中
- **解决：** 检查 `output/remotion_props.json` 中 `remocnEffects[].component` 字段

### 11.5 LLM 返回的 remocn 组件名不匹配
```
⚠ LLM 推荐 remocn 组件 "xxx" 不在白名单中，降级到特效类型映射
```
- **影响：** 正常。第 1 级后备降级到第 2 级静态映射，视频仍可正常渲染

---

## 快速回顾

```bash
# 1. 分析视频
python main.py input_videos/demo.mp4

# 2. 填写 transfer/new_content.json（素材+变量）

# 3. 迁移 + 渲染全部 4 种风格
python -m transfer.transfer \
  output/最新目录/analysis_result.json \
  transfer/new_content.json \
  output/remotion_props.json \
  --use-remocn --style all

# 产物在 remotion-video/out/multi_style/ 或 remotion-video/output/multi_style/
```
