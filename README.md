# 爆款结构迁移引擎 — 项目交付文档

> **比赛课题**：ByteDance Challenge — 爆款结构迁移引擎：从样例拆解、素材补全到视频重组的 AI 创作平台
>
> **作者**：范谢逸 王培旭
>
> **项目名称**：VIDEO_STRUCTURE_TRANSFORM
>
> **代码仓库**：(https://github.com/IvanFan-Van/video_structure_transform.git)
>
> **演示视频**：(https://drive.google.com/file/d/1_UVm80NZq5OzuHRALEXAeZHByeYhQ0KA/view?usp=sharing)

---

## 目录

- [一、项目概述](#一项目概述)
  - [1.0 竞赛亮点（TL;DR）](#10-竞赛亮点tldr-for-judges)
  - [1.1 项目背景](#11-项目背景)
  - [1.2 核心能力](#12-核心能力)
- [二、整体 AI 架构](#二整体-ai-架构)
- [三、工具协议](#三工具协议)
- [四、安全边界](#四安全边界)
- [五、代码结构与运行说明](#五代码结构与运行说明)
- [附录 A：技术栈总览](#附录-a技术栈总览)
- [附录 B：API 端点速查表](#附录-bapi-端点速查表)
- [附录 C：59 个特效组件目录](#附录-c59-个特效组件目录)

---

## 一、项目概述

### 1.0 竞赛亮点（TL;DR for Judges）

| 维度           | 本项目的做法                                                 |
| -------------- | ------------------------------------------------------------ |
| **核心创新**   | 不复制内容，复制"结构"——从爆款视频中抽象叙事骨架，迁移到任意新主题 |
| **端到端闭环** | 上传参考视频 → 四路并行 AI 分析 → LLM 生成模板 → 素材补全 → Remotion 渲染成片，全程无需手动剪辑 |
| **多模态深度** | 脚本/视觉/音频/特效四个维度独立分析，LLM 视觉理解 + 信号处理 + ML 分类并行运行 |
| **特效库集成** | 59 个 remocn 动效组件通过注册表动态调度，LLM 可直接在生成计划时指定组件名称 |
| **工程规范**   | FastAPI + SQLModel 分层架构，instructor 强制结构化输出，SSE 全链路流式推送，JSend 统一响应规范 |
| **人机协同**   | 节点式画布 UI，每步可视化、可中断、可手动干预，非黑盒全自动  |

---

### 1.1 项目背景

短视频创作中，优质内容的效果往往不只取决于素材本身，还取决于其在开头吸引（Hook）、镜头节奏、字幕包装、音乐卡点、卖点推进和结尾表达（CTA）等方面形成的"结构能力"。创作者通常能感受到哪些视频更容易出效果，但很难把这种经验抽象、复用，并迁移到新的创作任务中。

本项目设计并实现了一套 **AI 驱动的短视频结构迁移平台**，核心思路是：**从爆款样例中学习"结构"，再迁移到新主题中生成视频**——而非简单复制内容。

### 1.2 核心能力

本系统实现了以下完整闭环：

```
参考爆款视频 → 多模态AI拆解 → 结构模板生成 → 用户主题输入
       ↓                                              ↓
  【脚本结构】                                    【素材缺口识别】
  【视觉结构】                                    【AIGC内容补全】
  【音频特征】      ──→  结构迁移引擎  ←──      【人工调整槽位】
  【特效分析】
       ↓
  Remotion 程序化渲染 → 竖屏短视频成品 (1080×1920)
```

具体而言：

| 能力维度              | 实现情况                                                     |
| --------------------- | ------------------------------------------------------------ |
| **样例视频解析**      | 支持上传参考视频，自动提取时长、分辨率、码率、封面等基础信息 |
| **脚本/段落结构拆解** | LLM 多模态分析，拆解为 Hook / Setup / Story / Insight / CTA / Outro 六阶段叙事结构 |
| **视觉结构拆解**      | LLM 识别镜头切分、运镜方式、转场类型、文字元素位置与时间轴、节奏摘要 |
| **音频特征分析**      | BGM 分离 (UVR-MDX-NET)、BPM 节拍检测、能量曲线、频谱质心、流派分类 (HuggingFace) |
| **特效/包装分析**     | LLM 匹配内置 59 个 remocn 特效组件库，识别视频中使用的动效类型 |
| **结构迁移生成**      | 基于参考视频结构 + 用户主题，LLM 生成包含 segment/slot/constraints 的视频模板 |
| **素材缺口处理**      | 识别 pending 槽位，支持手动填入 / 上传素材 / AIGC 批量生成（LLM 文案 + AI 背景图） |
| **多版本渲染**        | 5 种风格版本：标准版、高点击版、高转化版、高节奏版、高质感版 |
| **人机协同编辑**      | 节点式画布 UI，每个分析/生成步骤可视化，支持手动修改槽位内容 |
| **视频渲染成片**      | Remotion 程序化渲染，支持文字动画 (5种)、BGM 节拍同步脉冲、KenBurns 效果、转场溶解 |
| **迁移过程可视化**    | 前端画布展示完整 pipeline 各节点状态与结果，SSE 实时推送任务进度 |

---

## 二、整体 AI 架构

### 2.1 AI 模型分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
│   React 前端 (Vite + TypeScript + Zustand)                      │
│   节点式画布 UI，SSE 实时状态推送                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP / SSE
┌───────────────────────────▼─────────────────────────────────────┐
│                     FastAPI 业务编排层                           │
│   routers/ → services/ → tasks/ (异步任务注册与流式推送)         │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┐     │
│   │ 脚本分析  │ 视觉分析  │ 音频分析  │ 特效分析  │ 视频渲染  │     │
│   └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘     │
└────────┼──────────┼──────────┼──────────┼──────────┼────────────┘
         │          │          │          │          │
┌────────▼──────────▼──────────▼──────────▼──────────▼────────────┐
│                        AI / ML 能力层                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  LLM 层 (OpenAI-compatible API)                       │       │
│  │  - 多模态输入：视频 base64 → LLM 视觉理解              │       │
│  │  - 结构化输出：instructor 库强制 Pydantic 模型         │       │
│  │  - 模型：可配置（默认火山方舟 Doubao-Seed-2.0-lite）   │       │
│  │  - 11 组 Prompt 模板（见 2.3 节）                     │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────┐  ┌──────────────────────────┐      │
│  │  AI 图像生成层           │  │  音频分析层               │      │
│  │  - Agnes AI              │  │  - BGM 分离：              │      │
│  │  - 模型：agnes-image-    │  │    UVR-MDX-NET-Inst_HQ_3 │      │
│  │    2.0-flash             │  │  - 特征分析：librosa       │      │
│  │  - 输出：1024×1792 竖屏  │  │    (BPM/能量/频谱/Onset)  │      │
│  │    背景图                 │  │  - 流派分类：HuggingFace   │      │
│  └─────────────────────────┘  └──────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       视频处理与渲染层                            │
│                                                                  │
│  ┌──────────────────────┐   ┌─────────────────────────────┐    │
│  │ 视频处理 (lib/)       │   │ 渲染引擎 (Remotion)          │    │
│  │ - ffmpeg: 压缩/切割   │   │ - viral-structure-engine:    │    │
│  │ - scenedetect: 场景   │   │   生产级竖屏渲染 (1080×1920) │    │
│  │   检测 (ContentDetect)│   │ - effects-renderer:          │    │
│  │ - OpenCV: 封面提取    │   │   特效展示与组合渲染          │    │
│  └──────────────────────┘   │ - 59 个 remocn 动效组件       │    │
│                              │ - 5 种风格配置                │    │
│                              └─────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 系统架构图（技术视角）

```
┌────────────────────┐     ┌──────────────────────────────┐
│   Frontend (React) │     │        Backend (FastAPI)      │
│   Vite + TypeScript│────▶│   Python 3.12+                │
│   Zustand 状态管理  │     │                              │
│   SSE 流式消费      │     │  ┌────────────────────────┐  │
│   Vite Proxy → /api │     │  │  routers/              │  │
│   localhost:5173    │     │  │  ├─ auth_router        │  │
└────────────────────┘     │  │  ├─ pipeline_router    │  │
                            │  │  ├─ plan_router        │  │
                            │  │  ├─ render_router      │  │
                            │  │  ├─ effect_router      │  │
                            │  │  ├─ task_router        │  │
                            │  │  └─ files_router       │  │
                            │  └───────────┬────────────┘  │
                            │              │               │
                            │  ┌───────────▼────────────┐  │
                            │  │  services/             │  │
                            │  │  ├─ pipeline.py (拆解) │  │
                            │  │  ├─ plan_service.py    │  │
                            │  │  ├─ render_service.py  │  │
                            │  │  ├─ image_service.py   │  │
                            │  │  └─ task.py (SSE)      │  │
                            │  └───────────┬────────────┘  │
                            │              │               │
                            │  ┌───────────▼────────────┐  │
                            │  │  lib/                  │  │
                            │  │  ├─ video.py (ffmpeg)  │  │
                            │  │  ├─ audio.py (librosa) │  │
                            │  │  └─ image.py           │  │
                            │  └────────────────────────┘  │
                            │              │               │
                            │  ┌───────────▼────────────┐  │
                            │  │  存储层                 │  │
                            │  │  ├─ SQLite (database)  │  │
                            │  │  └─ storage/ (文件)    │  │
                            │  └────────────────────────┘  │
                            └──────────────────────────────┘
                                       │ Remotion CLI
                            ┌──────────▼────────────┐
                            │  viral-structure-engine│
                            │  Remotion 4.0.433      │
                            │  1080×1920 / 30fps     │
                            └────────────────────────┘
```

### 2.3 LLM Prompt 体系（11 组）

本系统的 AI 核心由 **11 组精心设计的 Prompt 模板** 驱动，覆盖从视频理解到内容生成的全链路：

| #    | Prompt 名称                                                  | 模型输入                         | 结构化输出               | 核心任务                                                     |
| ---- | ------------------------------------------------------------ | -------------------------------- | ------------------------ | ------------------------------------------------------------ |
| 1    | **脚本结构分析**                                             | 视频 base64                      | `VideoStructure` (6阶段) | 将视频拆解为 Hook/Setup/Story/Insight/CTA/Outro，提取每阶段的 visual_text、audio_text、emotional_tone、hook_type、cta_type |
| 2    | **视觉层分析**                                               | 视频 base64                      | `VideoVisualAnalysis`    | 识别镜头切分点、运镜方式 (static/zoom_in/zoom_out/pan/tilt/handheld)、转场类型、文字元素时间轴、节奏摘要 |
| 3    | **特效分析**                                                 | 视频 base64 + 特效库             | `EffectAnalysisResult`   | 两步法：① 纯视觉观察（不引库）；② 基于观察证据匹配特效库——宁可少报不错报 |
| 4    | **AI 切割**                                                  | 视频 base64                      | `CutPointList`           | 按特效对象边界语义切割，与 scenedetect（画面差异切割）互补   |
| 5    | **计划生成**                                                 | 脚本分析 + 视觉分析 + 用户 brief | `PlanOutput`             | 生成 VideoTemplate：segments（按叙事阶段）、slots（visual_text/narration/background_image）、constraints（位置/动效/镜头） |
| 6    | **槽位内容生成**                                             | 模板上下文 + 用户 brief          | `SlotGenerationOutput`   | 批量生成 pending 槽位的具体 visual_text 和 narration 内容    |
| 7    | **旁白清洗**                                                 | 原始 ASR 文本                    | 纯文本                   | 英文缩写拆字母、数字汉字化、去除口语填充词（已定义，当前未接入管线） |

**Prompt 设计亮点**：

- **结构化输出强制**：所有 LLM 调用通过 `instructor` 库强制输出符合 Pydantic 模型的结构化 JSON，杜绝格式漂移
- **多模态输入**：视频以 `data:video/mp4;base64,...` 形式送入 LLM，实现端到端的视觉理解
- **特效分析两步法**：先自由观察（Free Observation），再基于证据匹配（Evidence-based Matching），有效抑制幻觉
- **叙事结构分类体系**：自定义 8 种 Hook 类型、8 种 CTA 类型、8 种情绪基调，覆盖短视频创作全场景
- **文案筛选规则**：LLM 指导下自动区分"核心叙事文字"与"水印/UI/无关文字"

### 2.4 数据流（完整管线）

```
Step 1: UPLOAD
  用户上传参考视频 (.mp4/.mov 等)
  → ffmpeg 提取元数据 → 自动提取封面图 (OpenCV 关键帧评分)
  → 存入 storage/ + SQLite Asset 表

Step 2: COMPRESS (可选)
  配置编码器/CRF/码率/分辨率/帧率
  → ffmpeg 压缩 → 生成压缩版 Asset

Step 3: ANALYZE (4 路并行异步任务)
  ┌─ /analyze-script  → LLM 提取 6 阶段叙事结构
  ├─ /analyze-visual  → LLM 提取镜头/转场/文字/节奏
  ├─ /analyze-audio   → ffmpeg 提取音轨 → UVR-MDX-NET 分离 BGM
  │                    → librosa 提取 BPM/节拍/能量/频谱/Onset
  │                    → HuggingFace 流派分类
  └─ /analyze-effect  → LLM 匹配 59 个特效组件库

Step 4: SPLIT
  scenedetect ContentDetector (默认) 或 LLM 语义切割
  → 生成分段视频片段 (clip_assets) + 封面

Step 5: PLAN
  收集 Step 3-4 所有分析结果
  → LLM 生成 VideoTemplate:
     - segments[]: 按叙事阶段划分
     - slots[visual_text, narration, background_image]: 每段 3 槽位
     - constraints: 位置/动效/镜头/BGM情绪

Step 6: FILL SLOTS
  用户对每个 slot 选择处理方式：
  - 手动输入文案
  - 上传自定义素材 (图片/视频)
  - 标记为 AI 生成 (pending)

Step 7: GENERATE (批量 AI 补全)
  → LLM: 批量生成 pending narration + visual_text
  → Agnes AI: 为每个 segment 生成 1024×1792 竖屏背景图

Step 8: PREVIEW (可选)
  选择渲染风格 (standard/high_click/high_convert/high_rhythm/high_quality)
  → Remotion still 渲染关键帧预览

Step 9: RENDER
  构建 Remotion props JSON (场景/文字/BGM/节拍/特效/风格)
  → 复制 BGM 到 public/ 目录
  → Remotion CLI 渲染 1080×1920 30fps MP4
  → 成品存入 Asset 表，可通过 /files/{id} 下载
```

---

## 三、工具协议

### 3.1 异步任务协议

本系统所有耗时操作均采用**异步任务模式**，统一通过 `TaskRegistry` 管理：

**任务生命周期**：

```
POST /xxx (发起) → 202 { task_id }
     │
     ▼
  [running] ──→ GET /task/{id}/stream (SSE 实时推送)
     │              ├─ data: {"status":"running"}
     │              ├─ : keepalive (每 15s)
     │              └─ data: {"status":"completed", "result":{...}}
     │
     ├── [completed] → result 字段包含业务数据
     ├── [failed]    → error 字段包含错误描述
     └── [cancelled] → POST /task/{id}/cancel 触发
```

**SSE 流式协议**：

| 帧类型    | 格式                                                         | 说明                              |
| --------- | ------------------------------------------------------------ | --------------------------------- |
| 初始状态  | `data: {"task_id":"...","status":"running"}\n\n`             | 连接建立后立即发送                |
| Keepalive | `: keepalive\n\n`                                            | 每 15s 发送，防止中间代理断开连接 |
| 最终状态  | `data: {"task_id":"...","status":"completed","result":{...}}\n\n` | 任务结束后发送并关闭连接          |

**轮询降级**：客户端不支持 SSE 时，可通过 `GET /task/{task_id}` 轮询获取状态。

**取消机制**：`POST /task/{task_id}/cancel` → `asyncio.Task.cancel()` → 任务协程捕获 `CancelledError` 后清理资源。

**注意事项**：任务注册表为**内存存储**，服务重启后所有任务记录丢失。

### 3.2 视频处理协议

| 操作             | 工具                          | 参数                                                         | 输出                                                     |
| ---------------- | ----------------------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| **元数据提取**   | `ffmpeg.probe()`              | —                                                            | codec, width, height, fps, bitrate, duration, audio 信息 |
| **压缩**         | `ffmpeg`                      | vcodec (libx264/libx265), crf (0-51), target_v_bitrate, scale_width, max_fps, acodec (aac/libmp3lame), target_a_bitrate | 压缩后 .mp4                                              |
| **场景检测**     | `scenedetect` ContentDetector | threshold (默认 25.0), min_scene_len (默认 15 帧)            | 切割时间点列表 + cut_score                               |
| **视频切割**     | `ffmpeg` segment              | start_sec, duration                                          | 分段 .mp4 文件                                           |
| **封面提取**     | OpenCV                        | 关键帧 + 模糊度/亮度评分                                     | 最优封面图 .jpg                                          |
| **Base64 编码**  | Python base64                 | —                                                            | `data:video/mp4;base64,...` (用于 LLM 多模态输入)        |
| **文件大小限制** | 应用层校验                    | `MAX_ANALYZE_SIZE_MB` (默认 50MB)                            | 超出限制时拒绝分析，提示先压缩                           |

### 3.3 音频处理协议

| 操作             | 工具/模型                                         | 说明                                  |
| ---------------- | ------------------------------------------------- | ------------------------------------- |
| **音轨提取**     | `ffmpeg`                                          | 从视频中提取音频流                    |
| **BGM 分离**     | `audio_separator` + UVR-MDX-NET-Inst_HQ_3         | 人声/伴奏分离，保留伴奏用于分析       |
| **BPM 检测**     | `librosa.beat.tempo()`                            | 全局 BPM                              |
| **节拍时间点**   | `librosa.beat.beat_track()`                       | 所有重拍时间点列表                    |
| **RMS 能量曲线** | `librosa.feature.rms()`                           | 逐帧能量值                            |
| **频谱质心**     | `librosa.feature.spectral_centroid()`             | 逐帧频谱质心 (Hz)，反映音色"亮度"     |
| **频谱通量**     | `librosa.onset.onset_strength()`                  | 逐帧频谱变化率                        |
| **Onset 包络**   | `librosa.onset.onset_strength()`                  | 逐帧 onset 强度                       |
| **动态范围**     | max(RMS) − min(RMS)                               | 整体响度变化范围                      |
| **流派分类**     | HuggingFace `dima806/music_genres_classification` | 输出流派标签 (pop/rock/electronic 等) |

### 3.4 渲染协议

**渲染引擎**：Remotion 4.0.433 (React-based programmatic video)

**渲染命令** (由后端 `render_service.py` 自动调用)：

```bash
# 预览静态帧
remotion still src/index.ts --props=<JSON> --frame=N --output=<path>

# 渲染完整视频
remotion render src/index.ts VideoComposition <output.mp4> --props=<JSON>
```

**Remotion Props 结构**：

```typescript
{
  fps: 30,
  width: 1080,
  height: 1920,
  durationInFrames: number,
  bgmPath: string,
  voiceoverPath: string | null,
  scenes: SceneData[]
}

SceneData {
  id, slot_id, startFrame, durationInFrames,
  type: "text_overlay" | "emphasis_text" | "remocn_composed",
  text, textStyle (fontSize, color, animation, position),
  beatFrames[], backgroundVideo, backgroundImage,
  remocnEffects[]  // 动态注册的 59 个特效组件
}
```

**5 种渲染风格** (定义于 `backend/config/styles.yaml`)：

| 风格           | 策略                                 |
| -------------- | ------------------------------------ |
| `standard`     | 标准版，按原比例映射时长             |
| `high_click`   | 高点击版，压缩 Hook 阶段时长         |
| `high_convert` | 高转化版，延长 CTA 阶段时长          |
| `high_rhythm`  | 高节奏版，所有阶段压缩 25%           |
| `high_quality` | 高质感版，使用电影感 typewriter 动画 |

**场景类型**：

| 类型              | 渲染器            | 效果                                                         |
| ----------------- | ----------------- | ------------------------------------------------------------ |
| `text_overlay`    | TextOverlayScene  | 逐句替换显示 + 5 种文字动画 (typewriter/fade_in/bounce/slide_in/glitch) |
| `emphasis_text`   | EmphasisTextScene | 同上 + KenBurns 缓慢缩放 (1.0→1.04) + BGM 节拍金色脉冲线     |
| `remocn_composed` | RemocnScene       | 动态加载 59 个 remocn 特效组件，支持递归组件树               |

### 3.5 API 响应规范

所有接口统一遵循 **JSend 规范**：

```json
// 成功
{ "status": "success", "data": { ... } }

// 客户端错误 (4xx)
{ "status": "fail", "message": "错误描述" }

// 服务端错误 (5xx)
{ "status": "error", "message": "错误描述", "data": { "code": "ERROR_CODE", "details": "..." } }
```

### 3.6 特效组件协议

系统内置 **59 个 remocn 视觉效果组件**（定义于 `backend/components_description.json` 和 `effects-renderer/src/effects/index.ts`），分为 6 大类：

| 类别                        | 数量 | 示例                                                         |
| --------------------------- | ---- | ------------------------------------------------------------ |
| Typography（文字动效）      | 14   | BlurReveal, Typewriter, ShimmerSweep, RGBGlitchText, SlotMachineRoll, MarkerHighlight, MatrixDecode |
| Core Primitives（核心原语） | 7    | SpringPopIn, PulsingIndicator, SuccessConfetti, CursorFlow, BrushStrokeSimulator |
| Environment & Lighting      | 3    | MeshGradientBg, DynamicGrid, SpotlightCard                   |
| UI Blocks（UI 模块）        | 11   | GlassCodeBlock, TerminalSimulator, CodeDiffWipe, StaggeredBentoGrid, AIGenerateOverlay, AnimatedBarChart |
| Transitions（转场）         | 10   | ZoomThroughTransition, DirectionalWipe, SwipeTransitionWipe, ChromaticAberrationWipe, FrostedGlassWipe, GridPixelateWipe |
| Compositions（组合场景）    | 14   | HeroDeviceAssemble, EcosystemConstellation, BrowserFlow, AIGenerationCanvas, LiveCodeCompilation, PipelineJourney, ProductLaunchTrailer |

所有组件在两个 Remotion 项目中**共享实现**（`viral-structure-engine` 和 `effects-renderer`），通过注册表动态加载。

---

## 四、安全边界

### 4.1 认证机制

| 项目           | 实现                                                         |
| -------------- | ------------------------------------------------------------ |
| **认证方式**   | JWT (JSON Web Token)                                         |
| **签名算法**   | HS256                                                        |
| **密钥**       | 环境变量 `SECRET_KEY`                                        |
| **有效期**     | 环境变量 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置（默认 30 分钟）  |
| **密码存储**   | bcrypt 哈希，12 rounds                                       |
| **OAuth 支持** | 数据库模型已预留 `UserOAuth` 表，支持 Google 登录扩展（当前未激活端点） |

**Token 验证流程** (`backend/app/deps.py`)：

```
请求头 Authorization: Bearer <token>
  → 解码 JWT → 提取 user_id
  → 查库验证用户存在
  → 注入 get_current_user 依赖
```

### 4.2 授权机制

**资源级权限控制**：每个 API 端点均校验资源归属：

```
asset.user_id == current_user.user_id  → 通过
asset.user_id != current_user.user_id  → 403 Forbidden
```

覆盖范围：

- `/files/{asset_id}` — 文件下载
- `/task/{task_id}` — 任务查询
- `/task/{task_id}/stream` — SSE 流订阅
- `/task/{task_id}/cancel` — 任务取消
- 所有 Pipeline 端点 (`/compress`, `/analyze-*`, `/split`)

### 4.3 输入验证

| 验证维度                | 规则                                                         |
| ----------------------- | ------------------------------------------------------------ |
| **文件扩展名白名单**    | 视频: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`, `.wmv` |
|                         | 图片: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`               |
| **MIME 类型校验**       | 视频: `video/*`；图片: `image/*`                             |
| **文件大小限制**        | LLM 分析前校验 `MAX_ANALYZE_SIZE_MB`（默认 50MB），超限提示先压缩 |
| **路径遍历防护**        | `/effects/demo/{filename}` 拒绝 `..`、`/`、`\` 字符          |
| **Pydantic 请求体验证** | 所有请求体通过 Pydantic 模型严格校验，字段类型/必填/约束自动验证 |
| **Null 字符串处理**     | `null_str_validator` 将 `"null"` 字符串转为 Python `None`    |

### 4.4 异常处理

```python
# 全局 HTTPException 处理器 → 区分 4xx (fail) / 5xx (error)
# 全局 RequestValidationError 处理器 → 422 + 详细字段错误列表
```

### 4.5 已知安全注意事项

| 事项             | 说明                                                         | 风险等级                                                     |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 任务内存存储     | 任务注册表为进程内存，服务重启后全部丢失                     | 低 (不影响安全，影响可用性)                                  |
| 无 CORS 中间件   | FastAPI 未配置 CORS，依赖 Vite 开发代理或反向代理            | 中 (生产部署需配置)                                          |
| 无速率限制       | API 端点无限流机制                                           | 中 (生产环境需添加)                                          |
| 文档含硬编码密钥 | `docs/REQUIREMENT.md` 含火山方舟 API Key（比赛资源，赛后需清理） | **高** ⚠️ **提交前务必执行 `git filter-repo` 或替换为脱敏占位符** |

### 4.6 前端安全

- **Token 存储**：Zustand persist 中间件存储于 `localStorage`
- **Token 过期检查**：`ProtectedRoute` 组件解码 JWT 检查 `exp`，过期自动跳转登录
- **401 自动登出**：Axios 拦截器 + fetch 包装器，收到 401 响应自动清除 token
- **无 XSS 风险**：React 默认 JSX 转义 + 无 `dangerouslySetInnerHTML` 使用

---

## 五、代码结构与运行说明

### 5.1 项目目录结构

```
video_structure_transform/
├── backend/                          # FastAPI 后端 (Python 3.12+)
│   ├── app/
│   │   ├── main.py                   # FastAPI 应用入口，路由注册，异常处理
│   │   ├── database.py               # SQLite 引擎 + Session 依赖
│   │   ├── deps.py                   # JWT 认证依赖注入
│   │   ├── llm.py                    # OpenAI 客户端初始化
│   │   ├── prompts.py                # 11 组 LLM Prompt 模板 (764 行)
│   │   ├── utils.py                  # 密码哈希、JWT 创建、JSON 提取
│   │   ├── routers/                  # API 路由层
│   │   │   ├── auth.py               # /login, /register
│   │   │   ├── pipeline.py           # /upload, /compress, /analyze-*, /split
│   │   │   ├── plan.py               # /plan, /plan/{id}/slot, /plan/{id}/generate
│   │   │   ├── render.py             # /render, /render/preview, /render/still
│   │   │   ├── effect.py             # /effects (GET/PATCH)
│   │   │   ├── task.py               # /task/{id}, /task/{id}/stream, /task/{id}/cancel
│   │   │   └── files.py              # /files/{asset_id}
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── pipeline.py           # 上传/压缩/分析/切割核心逻辑 (721 行)
│   │   │   ├── plan_service.py       # 计划生成、槽位填充、批量生成 (511 行)
│   │   │   ├── render_service.py     # Remotion 渲染编排 (615 行)
│   │   │   ├── image_service.py      # Agnes AI 图像生成
│   │   │   ├── auth.py               # 用户注册/登录
│   │   │   ├── asset.py              # 文件服务
│   │   │   └── task.py               # 任务注册/SSE/取消 (100 行)
│   │   ├── tasks/                    # 异步任务模块
│   │   │   ├── registry.py           # 内存任务注册表
│   │   │   └── model.py              # TaskInfo 数据类
│   │   ├── models/                   # SQLModel ORM 模型 (User, Asset, Effect)
│   │   ├── repositories/             # 数据库访问层
│   │   ├── lib/                      # 底层处理库
│   │   │   ├── video.py              # ffmpeg/OpenCV/scenedetect (368 行)
│   │   │   ├── audio.py              # librosa/BGM分离 (186 行)
│   │   │   └── image.py              # 图片元数据
│   │   ├── schemas/                  # Pydantic 请求/响应模型
│   │   └── config/
│   │       └── style_config.py       # YAML 风格配置加载
│   ├── config/
│   │   └── styles.yaml               # 5 种渲染风格定义
│   ├── components_description.json   # 59 个特效组件目录
│   ├── models/                       # 本地 ML 模型缓存
│   ├── storage/                      # 上传文件存储 (videos/images/audios/aigc)
│   ├── output/                       # Remotion props JSON 输出
│   ├── docs/                         # API 文档
│   ├── tests/                        # 测试文件
│   ├── pyproject.toml                # Python 项目配置
│   ├── .env.example                  # 环境变量模板
│   └── uv.lock                       # 依赖锁定
│
├── frontend/                         # React 前端
│   ├── src/
│   │   ├── main.tsx                  # React 入口 + 路由配置
│   │   ├── App.tsx                   # 主画布应用
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx         # 登录页
│   │   │   └── RegisterPage.tsx      # 注册页
│   │   ├── components/
│   │   │   ├── nodes/                # 管线节点组件 (12 个)
│   │   │   │   ├── ReferenceNode.tsx # 视频上传节点
│   │   │   │   ├── CompressConfigNode.tsx
│   │   │   │   ├── CompressNode.tsx
│   │   │   │   ├── ExtractingNode.tsx
│   │   │   │   ├── SplitNode.tsx
│   │   │   │   ├── EffectAnalysisNode.tsx
│   │   │   │   ├── ScriptAnalysisNode.tsx
│   │   │   │   ├── AudioAnalysisNode.tsx
│   │   │   │   ├── VisualAnalysisNode.tsx
│   │   │   │   ├── PlanNode.tsx
│   │   │   │   ├── SlotNode.tsx
│   │   │   │   ├── GenerateNode.tsx
│   │   │   │   ├── VersionPreviewNode.tsx
│   │   │   │   └── RenderNode.tsx
│   │   │   ├── shared/               # 公共 UI 组件
│   │   │   │   ├── BaseNode.tsx      # 可拖拽节点容器
│   │   │   │   ├── Wires.tsx         # SVG 连接线
│   │   │   │   ├── StatusHeader.tsx
│   │   │   │   ├── ActionButton.tsx
│   │   │   │   ├── AccordionItem.tsx
│   │   │   │   ├── Tooltip.tsx       # 双语提示
│   │   │   │   ├── CoverImage.tsx
│   │   │   │   ├── PreviewStill.tsx
│   │   │   │   ├── NodeErrorToast.tsx
│   │   │   │   ├── SelectionRect.tsx
│   │   │   │   ├── TourGuide.tsx     # 12 步引导教程
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   └── charts/               # SVG 图表组件
│   │   │       ├── EnergyChart.tsx
│   │   │       ├── CentroidChart.tsx
│   │   │       ├── FluxChart.tsx
│   │   │       └── OnsetChart.tsx
│   │   ├── store/                    # Zustand 状态管理
│   │   │   ├── useVideoStore.ts      # 核心视频管线状态 (1844 行)
│   │   │   ├── useCanvasStore.ts     # 画布缩放/平移/选中状态
│   │   │   ├── useAuthStore.ts       # 认证状态 (持久化)
│   │   │   ├── useAppStore.ts        # 旧版模型训练状态 (遗留)
│   │   │   └── types.ts              # 完整 TypeScript 类型定义 (354 行)
│   │   ├── hooks/                    # 自定义 Hooks
│   │   │   ├── useDraggable.ts       # 节点拖拽
│   │   │   ├── useZoom.ts            # 滚轮缩放
│   │   │   ├── usePan.ts             # 画布平移
│   │   │   ├── useBoxSelect.ts       # 框选
│   │   │   ├── useNodeError.ts       # 节点错误检查
│   │   │   └── useTour.ts            # 引导教程状态
│   │   ├── lib/
│   │   │   └── api.ts                # Axios 实例 + Token 管理
│   │   ├── utils/
│   │   │   ├── index.ts              # 格式化工具函数
│   │   │   └── chart.ts              # 图表数据聚合
│   │   └── constants/
│   │       └── index.ts              # 预设值 + 连线定义
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts                # Vite 配置 + API 代理
│   └── tsconfig.json
│
├── viral-structure-engine/           # Remotion 生产渲染引擎
│   └── remotion-video/
│       ├── src/
│       │   ├── index.ts              # Remotion 入口 (registerRoot)
│       │   ├── Root.tsx              # Composition 注册 (1080×1920, 30fps)
│       │   ├── VideoComposition.tsx  # 主编排器 (BGM+配音+场景序列)
│       │   ├── types.ts              # TypeScript 接口定义
│       │   ├── scenes/
│       │   │   ├── TextOverlayScene.tsx
│       │   │   ├── EmphasisTextScene.tsx   # KenBurns + BGM 节拍脉冲
│       │   │   └── RemocnScene.tsx         # 动态特效组件渲染
│       │   └── components/
│       │       ├── AnimatedText.tsx        # 5 种文字动画 + BGM 节拍光晕
│       │       ├── CrossDissolveWrapper.tsx # 场景淡入淡出转场
│       │       ├── SceneBackground.tsx      # 3 级背景 (视频>图片>纯色)
│       │       └── remocn/                  # 59 个特效组件
│       │           ├── registry.ts          # 组件注册表
│       │           └── *.tsx                # 各特效组件实现
│       ├── package.json
│       └── tsconfig.json
│
├── effects-renderer/                 # Remotion 特效展示/组合渲染器
│   ├── src/
│   │   ├── index.ts                  # Remotion 入口
│   │   ├── Root.tsx                  # 双 Composition (render + compose)
│   │   ├── VideoComposer.tsx         # 全场景组合编排器
│   │   ├── SceneRenderer.tsx         # 场景渲染器
│   │   ├── BackgroundRenderer.tsx    # 6 种背景类型
│   │   ├── OverlayRenderer.tsx       # 特效/图片/视频叠加
│   │   ├── DynamicRenderer.tsx       # 单特效渲染模式
│   │   ├── effects/
│   │   │   └── index.ts              # EFFECT_REGISTRY + 元数据
│   │   ├── types/
│   │   │   └── composition.ts        # VideoProject JSON Schema
│   │   ├── lib/
│   │   │   └── timeline.ts           # 时间线预计算
│   │   └── components/
│   │       └── remocn/               # 59 个特效组件 (共享实现)
│   ├── scripts/
│   │   ├── render-all.ts             # 批量渲染 59 个特效 Demo
│   │   └── render-compose.ts         # 组合渲染 CLI
│   ├── compose-example.json          # 示例组合项目
│   ├── demo-comprehensive.json       # 综合演示 (7 场景)
│   ├── render_commands.jsonl         # 59 个特效渲染命令
│   ├── package.json
│   └── remotion.config.ts
│
├── 7d5e4d15-7026-414a-bacf-1ffa1732d32b.mp4  # 产出视频示例
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── PROJECT_DOCS.md                   # 本文档
```

### 5.2 环境要求

| 依赖                 | 版本要求 | 用途                          |
| -------------------- | -------- | ----------------------------- |
| Python               | ≥ 3.12   | 后端运行                      |
| Node.js              | ≥ 18     | 前端 + Remotion 渲染引擎      |
| pnpm                 | 最新版   | 前端 + Remotion 包管理        |
| ffmpeg               | 最新版   | 视频处理 (压缩/切割/提取音轨) |
| UV (Python 包管理器) | 最新版   | Python 依赖管理               |
| Git LFS              | (可选)   | 大文件版本管理                |

### 5.3 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境并安装依赖
uv sync

# 3. 配置环境变量 (复制模板后填入实际值)
cp .env.example .env
# 编辑 .env 文件，填入：
#   API_KEY=<你的 OpenAI-compatible API Key>
#   MODEL=<模型名称，如 doubao-seed-2.0-lite>
#   BASE_URL=<API 地址>
#   SECRET_KEY=<JWT 签名密钥，随机字符串>
#   ACCESS_TOKEN_EXPIRE_MINUTES=30

# 4. 首次启动 (自动创建 SQLite 数据库 + 初始化特效表)
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# 或者
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**验证**：访问 `http://127.0.0.1:8000/`，应返回 `{"status":"success","data":"ok"}`。

**运行测试**：

```bash
cd backend
uv run pytest tests/ -v
```

### 5.4 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
pnpm install

# 3. 启动开发服务器
pnpm run dev
# 访问 http://localhost:5173

# 4. 生产构建
pnpm run build
```

**说明**：前端开发服务器通过 Vite Proxy 将 `/api` 请求代理到 `http://127.0.0.1:8000`（后端），因此前后端需同时运行。

### 5.5 Remotion 渲染引擎

```bash
cd viral-structure-engine/remotion-video

# 安装依赖
pnpm install

# 启动 Remotion Studio (预览/调试)
pnpm run dev

# 命令行渲染 (由后端自动调用)
pnpm run render

# 使用自定义 Props 渲染
pnpm run render:props
```

### 5.6 完整启动流程

```bash
# 终端 1: 启动后端
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 终端 2: 启动前端
cd frontend
pnpm run dev

# 浏览器访问 http://localhost:5173
# 注册 → 登录 → 上传参考视频 → 按 pipeline 节点逐步操作
```

---

## 附录 A：技术栈总览

### 后端

| 类别        | 技术                                        | 版本                 | 用途                             |
| ----------- | ------------------------------------------- | -------------------- | -------------------------------- |
| Web 框架    | FastAPI                                     | ≥0.136               | HTTP API 服务                    |
| ASGI 服务器 | Uvicorn                                     | ≥0.48                | 服务运行                         |
| ORM         | SQLModel                                    | ≥0.0.38              | 数据库 ORM (SQLite)              |
| 认证        | python-jose + bcrypt                        | ≥3.5 / ≥5.0          | JWT 生成/验证 + 密码哈希         |
| LLM 客户端  | openai + instructor                         | ≥2.38 / ≥1.14        | OpenAI API 调用 + 结构化输出强制 |
| 重试机制    | tenacity                                    | ≥9.1                 | LLM 调用失败自动重试             |
| 视频处理    | ffmpeg-python + opencv-python + scenedetect | ≥0.2 / ≥4.13 / ≥0.7  | 视频压缩/切割/场景检测/封面提取  |
| 音频处理    | librosa + audio-separator                   | ≥0.11 / ≥0.44        | BPM/节拍/频谱 + BGM 人声分离     |
| ML 推理     | transformers + torch + torchaudio           | ≥5.9 / ≥2.12 / ≥2.11 | HuggingFace 流派分类             |
| 语音转写    | faster-whisper                              | ≥1.2                 | ASR (备用)                       |
| 数据校验    | pydantic                                    | (FastAPI 内置)       | 请求/响应模型校验                |
| 环境变量    | python-dotenv                               | ≥1.2                 | .env 加载                        |

### 前端

| 类别     | 技术                            | 版本 | 用途                                                         |
| -------- | ------------------------------- | ---- | ------------------------------------------------------------ |
| 框架     | React                           | 18.3 | UI 框架                                                      |
| 构建     | Vite                            | 5.3  | 开发/构建                                                    |
| 语言     | TypeScript                      | 5.2  | 类型安全                                                     |
| 状态管理 | Zustand                         | 5.0  | 全局状态 + persist 中间件                                    |
| 路由     | react-router-dom                | 7.16 | 页面路由                                                     |
| HTTP     | axios                           | 1.16 | API 请求                                                     |
| SSE      | 原生 `fetch` + `ReadableStream` | —    | 服务端事件流消费（自研通用 `subscribeTaskStream`，已移除 `@microsoft/fetch-event-source` 依赖） |
| 图标     | react-icons                     | 5.6  | UI 图标                                                      |
| 引导教程 | driver.js                       | 1.4  | 12 步新手指引                                                |
|          |                                 |      |                                                              |

### 渲染引擎

| 类别     | 技术                                        | 版本                               | 用途                 |
| -------- | ------------------------------------------- | ---------------------------------- | -------------------- |
| 视频框架 | Remotion                                    | 4.0.433 (prod) / 4.0.474 (effects) | React 程序化视频渲染 |
| UI 框架  | React                                       | 19.x                               | 组件渲染             |
| CSS      | Tailwind CSS 4 (effects-renderer)           | 4.0                                | 样式                 |
| UI 组件  | shadcn/ui + lucide-react (effects-renderer) | —                                  | UI 组件库            |
| CLI 工具 | tsx                                         | ≥4.22                              | TypeScript 脚本执行  |

---

## 附录 B：API 端点速查表

### 认证端点

| 方法   | 路径        | 认证 | 说明               |
| ------ | ----------- | ---- | ------------------ |
| `POST` | `/register` | 否   | 用户注册           |
| `POST` | `/login`    | 否   | 用户登录，返回 JWT |

### 管线端点

| 方法   | 路径              | 认证 | 说明                    |
| ------ | ----------------- | ---- | ----------------------- |
| `POST` | `/upload`         | 是   | 上传视频/图片           |
| `POST` | `/compress`       | 是   | 压缩视频 (异步)         |
| `POST` | `/analyze-script` | 是   | LLM 脚本结构分析 (异步) |
| `POST` | `/analyze-visual` | 是   | LLM 视觉层分析 (异步)   |
| `POST` | `/analyze-audio`  | 是   | 音频特征分析 (异步)     |
| `POST` | `/analyze-effect` | 是   | LLM 特效分析 (异步)     |
| `POST` | `/split`          | 是   | 视频切割 (异步)         |

### 计划与生成端点

| 方法    | 路径                             | 认证 | 说明                        |
| ------- | -------------------------------- | ---- | --------------------------- |
| `POST`  | `/plan`                          | 是   | 生成视频模板 (异步)         |
| `PATCH` | `/plan/{plan_id}/slot/{slot_id}` | 是   | 填充单个槽位                |
| `POST`  | `/plan/{plan_id}/generate`       | 是   | 批量 AI 生成槽位内容 (异步) |

### 渲染端点

| 方法   | 路径                                 | 认证 | 说明                    |
| ------ | ------------------------------------ | ---- | ----------------------- |
| `GET`  | `/styles`                            | 是   | 获取可用渲染风格列表    |
| `POST` | `/render/preview`                    | 是   | 生成风格预览静帧 (异步) |
| `POST` | `/render`                            | 是   | 渲染最终视频 (异步)     |
| `GET`  | `/render/still/{task_id}/{filename}` | 是   | 获取预览静帧图片        |

### 任务与文件端点

| 方法    | 路径                       | 认证 | 说明                 |
| ------- | -------------------------- | ---- | -------------------- |
| `GET`   | `/task/{task_id}`          | 是   | 查询任务状态 (轮询)  |
| `GET`   | `/task/{task_id}/stream`   | 是   | SSE 实时推送任务状态 |
| `POST`  | `/task/{task_id}/cancel`   | 是   | 取消任务             |
| `GET`   | `/effects`                 | 是   | 查询/搜索特效库      |
| `PATCH` | `/effects`                 | 是   | 校正特效分析结果     |
| `GET`   | `/effects/demo/{filename}` | 否   | 获取特效 Demo 视频   |
| `GET`   | `/files/{asset_id}`        | 是   | 下载素材文件         |

---

## 附录 C：59 个特效组件目录

### Typography（文字动效）- 14 个

| 组件名             | 说明                     |
| ------------------ | ------------------------ |
| BlurReveal         | 文字从严重模糊聚焦至锐利 |
| StaggeredFadeUp    | 交错淡入上移             |
| MaskedSlideReveal  | 遮罩滑动揭示             |
| TrackingIn         | 字间距收紧入场           |
| InlineHighlight    | 行内高亮标记             |
| MarkerHighlight    | 荧光笔标记动画           |
| ShimmerSweep       | 闪光扫过文字             |
| Typewriter         | 打字机逐字出现 + 光标    |
| TextFadeReplace    | 文字淡入淡出替换         |
| SlotMachineRoll    | 老虎机滚动文字           |
| InfiniteMarquee    | 无限滚动跑马灯           |
| PerspectiveMarquee | 透视滚动跑马灯           |
| MatrixDecode       | 矩阵解码文字             |
| RGBGlitchText      | RGB 通道分离故障文字     |

### Core Primitives（核心原语）- 7 个

| 组件名               | 说明         |
| -------------------- | ------------ |
| SpringPopIn          | 弹簧弹出入场 |
| PulsingIndicator     | 脉冲指示器   |
| SuccessConfetti      | 成功彩纸效果 |
| CursorFlow           | 光标流动轨迹 |
| BrushStrokeSimulator | 笔触模拟绘制 |
| BoundingBoxSelector  | 边界框选择器 |
| ToastNotification    | 弹窗通知     |

### Environment & Lighting（环境与光照）- 3 个

| 组件名         | 说明         |
| -------------- | ------------ |
| MeshGradientBg | 网格渐变背景 |
| DynamicGrid    | 动态网格背景 |
| SpotlightCard  | 聚光灯卡片   |

### UI Blocks（UI 模块）- 11 个

| 组件名              | 说明            |
| ------------------- | --------------- |
| GlassCodeBlock      | 毛玻璃代码块    |
| TerminalSimulator   | 终端模拟器      |
| CodeAccordion       | 代码手风琴展开  |
| CodeDiffWipe        | 代码差异滑入    |
| StaggeredBentoGrid  | 交错 Bento 网格 |
| ChatToPreviewLayout | 聊天转预览布局  |
| AIGenerateOverlay   | AI 生成叠加层   |
| ToolMenuSlideIn     | 工具栏滑入      |
| AnimatedLineChart   | 动画折线图      |
| AnimatedBarChart    | 动画柱状图      |
| DragAndDropFlow     | 拖放流程动画    |

### Transitions（转场）- 10 个

| 组件名                  | 说明           |
| ----------------------- | -------------- |
| ZoomThroughTransition   | 缩放穿越转场   |
| DeviceMockupZoom        | 设备模型缩放   |
| MorphingModal           | 变形模态框     |
| ImageExpandToFullscreen | 图片展开至全屏 |
| DirectionalWipe         | 定向擦除       |
| SwipeTransitionWipe     | 滑动擦除转场   |
| SpatialPush             | 空间推入       |
| FrostedGlassWipe        | 磨砂玻璃擦除   |
| GridPixelateWipe        | 网格像素化擦除 |
| ChromaticAberrationWipe | 色差擦除转场   |

### Compositions（组合场景）- 14 个

| 组件名                  | 说明             |
| ----------------------- | ---------------- |
| HeroDeviceAssemble      | 英雄设备组装     |
| EcosystemConstellation  | 生态系统星座图   |
| InfiniteBentoPan        | 无限 Bento 平移  |
| BrowserFlow             | 浏览器操作流程   |
| AIGenerationCanvas      | AI 生成画布      |
| LiveCodeCompilation     | 实时代码编译     |
| TerminalToBrowserDeploy | 终端到浏览器部署 |
| DashboardPopulate       | 仪表盘数据填充   |
| PipelineJourney         | 管道流程图旅程   |
| PricingTierFocus        | 定价层级聚焦     |
| ProductLaunchTrailer    | 产品发布预告片   |
| ChangelogBite           | 更新日志快照     |
| VisualDocsSnippet       | 可视化文档片段   |
| FocusZoom               | 聚焦缩放         |

---

> **文档版本**：v1.1
>
> **最后更新**：2025-06
