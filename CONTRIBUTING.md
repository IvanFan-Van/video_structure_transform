# 开发贡献指南

## 项目概述

本项目是一个**爆款视频结构分析 & 迁移引擎**。上传一段短视频后，系统通过多阶段管道分析其脚本结构、BGM 音频特征、视觉特效与转场，并以场景为单位进行切分。最终可以将分析结果迁移为 Remotion 可渲染的 TypeScript 项目。

| 包 | 目录 | 包管理器 | 语言 | 核心框架 |
|---|------|---------|------|---------|
| backend | `backend/` | **uv** | Python 3.12 | FastAPI + SQLModel |
| frontend | `frontend/` | **pnpm** | TypeScript 5 | React 18 + Vite 5 |
| videos | `videos/` | **pnpm** | TypeScript 5 | Remotion 4 |

三个包**各自独立**，没有 root workspace 配置、lockfile 或 CI 管道。

---

## 环境搭建

### 前置依赖

- **Python 3.12+** + [`uv`](https://docs.astral.sh/uv/)
- **Node 20+** + [`pnpm`](https://pnpm.io/)
- **FFmpeg**（必须在 PATH 中，Backend 和 Videos 均依赖）

### Backend

```bash
cd backend

# 1. 安装依赖（uv 自动管理虚拟环境 .venv/）
uv sync

# 2. 创建 .env 文件
cp .env.example .env
# 编辑 .env，填入：
#   API_KEY=        # LLM API Key（必填）
#   MODEL=          # 模型名称（必填）
#   BASE_URL=       # API Base URL（必填）
#   SECRET_KEY=     # JWT 签名密钥（必填）
#   ALGORITHM=HS256
#   ACCESS_TOKEN_EXPIRE_MINUTES=30

# 3. 初始化测试视频
mkdir -p tests/videos
# 将一段 .mp4 放入 tests/videos/1.mp4（没有则集成测试自动跳过）
```

### Frontend

```bash
cd frontend
pnpm install
```

Vite 开发服务器自动将 `/api` 代理到 `http://127.0.0.1:8000`（路径重写：去掉 `/api` 前缀）。

### Videos

```bash
cd videos
pnpm install
```

> 注意：`videos/` 是 AI 代码生成引擎，`src/Root.tsx` 在运行时才由生成管道写入。生成的项目位于 `videos/output/`（gitignore）。

### VSCode

`.vscode/settings.json` 已配置 Python 解释器路径为 `backend/.venv/Scripts/python.exe`。

---

## 日常开发命令

### Backend

```bash
cd backend

uv run src/main.py              # 启动服务器 (127.0.0.1:8000)
uv run ruff check .             # Lint（规则：I, UP, E, F, W, C90）
uv run pytest tests/            # 运行全部测试
uv run pytest tests/test_video.py   # 运行单个文件
uv run pytest tests/test_video.py -k compress  # 按关键字筛选
```

### Frontend

```bash
cd frontend

pnpm dev      # Vite 开发服务器 + HMR
pnpm build    # tsc 类型检查 + vite build
pnpm preview  # 预览构建产物
```

### Videos

```bash
cd videos

pnpm dev     # Remotion Studio（如果 Output 中有已生成项目）
pnpm build   # Remotion bundle
pnpm lint    # eslint src && tsc
```

---

## Backend 架构详解

### 分层结构 (MVC)

```
src/
├── main.py           # FastAPI 入口, lifespan（自动建表）, 异常处理
├── database.py        # SQLite 引擎 (sqlite:///database.db)
├── deps.py            # FastAPI 依赖注入：auth, asset 所有权校验
├── schemas.py         # Pydantic 请求模型
├── prompts.py         # LLM Prompt 模板 (~600 行)
├── utils.py           # bcrypt + JWT + JSON 提取 + timer
├── core.py            # 核心异步任务：LLM 分析, 压缩, 切分
├── models/            # SQLModel 表定义
│   ├── user.py        # User (user_id, email, password_hash)
│   ├── asset.py       # Asset (asset_id, user_id, source_asset_id, path, type)
│   └── user_oauth.py  # UserOAuth (OAuth 绑定)
├── routers/           # 路由处理器
│   ├── auth.py        # POST /register, /login
│   ├── pipeline.py    # POST /upload, /compress, /analyze-*, /split
│   ├── task.py        # GET /task/{id}/stream (SSE), POST /task/{id}/cancel
│   └── asset.py       # GET /files/{asset_id}
├── services/          # 业务逻辑层
├── repositories/      # 数据访问层 (user_repo, asset_repo)
├── tasks/             # 内存异步任务系统 (TaskRegistry, 非 Celery)
│   ├── model.py       # TaskInfo dataclass
│   └── registry.py    # TaskRegistry 单例
└── lib/               # 底层库
    ├── video.py       # FFmpeg, OpenCV, scenedetect 操作
    ├── audio.py       # BGM 分离 + 音频特征流式提取
    └── schemas/       # LLM 输出 Pydantic 模型 (script, visual, split, video_meta)
```

### 数据模型关系

- **User** 1 → N **Asset**（通过 `asset.user_id = user.user_id`）
- **Asset** 自引用：`source_asset_id` 记录派生链（如压缩视频 → 源视频，切分片段 → 父视频）
- **UserOAuth** 1 → 1 **User**（通过 user_id）
- 数据库自动创建（`SQLModel.metadata.create_all`），**没有迁移工具**。重置：删除 `database.db`

### 认证流程

1. 注册：`POST /register` → bcrypt 12 轮哈希 → 创建 User (UUID user_id)
2. 登录：`POST /login` → 验证 bcrypt → 签发 JWT (HS256, SECRET_KEY)
3. 中间件：`get_current_user` (FastAPI Depends) 从 Bearer token 解析 JWT，查库返回 User
4. 所有权：`get_video_asset(asset_id, current_user)` 校验 `asset.user_id == current_user.user_id`

### 管道阶段

| 阶段 | 接口 | 说明 |
|------|------|------|
| 上传 | `POST /upload` | 保存视频到 `storage/videos/`，提取 cover image，创建 Asset |
| 压缩 | `POST /compress` | ffmpeg 压缩 (libx264, crf/bitrate/scale/fps 可配置)，返回 task_id |
| 脚本分析 | `POST /analyze-script` | base64 视频 → LLM 多模态 → 6 阶段叙事结构 (hook/setup/story/insight/cta/outro) |
| 视觉分析 | `POST /analyze-visual` | base64 视频 → LLM → 镜头列表/转场/文字元素/节奏分析 |
| 音频分析 | `POST /analyze-audio` | UVR BGM 分离 → aubio 流式特征提取 (RMS, 频谱质心, 频谱通量, BPM) |
| 切分 | `POST /split` | PySceneDetect ContentDetector 或 AI 切分 → ffmpeg 裁剪片段 |

> 视频 > 50MB 需要先压缩才能进行分析（`MAX_ANALYZE_SIZE_MB` 环境变量）。

### 任务系统

- **纯内存**，服务重启后丢失
- `TaskRegistry` 单例：`dict[task_id, TaskInfo]`
- `TaskInfo` 包含 `asyncio.Task` 引用（用于取消）和 `asyncio.Event`（用于完成通知）
- 状态流转：`running` → `completed` / `failed` / `cancelled`
- SSE 流：`GET /task/{id}/stream` 返回 `text/event-stream`，15s 心跳保活
- 音频分析额外使用 `asyncio.Queue` 流式传输帧数据，队列满时阻塞

### API 约定

所有响应使用类 JSend 格式：
```json
{"status": "success", "data": {...}}
{"status": "fail", "message": "..."}     // 4xx
{"status": "error", "message": "..."}    // 5xx
```

异步操作返回 `202` + `{task_id}`，前端通过 SSE 订阅进度。

### 存储

本地文件系统，`backend/storage/`（gitignore）：

```
storage/
├── videos/    # 上传、压缩、切分片段
├── audios/    # BGM 提取结果
├── images/    # Cover images (JPEG, quality 85)
└── tmp/       # 临时 WAV 文件
```

文件命名：视频 `{uuid}.mp4`，音频 `{uuid}_bgm.wav`，图片 `{uuid}.jpg`，片段 `{prefix}_{index:03d}.mp4`。

### LLM 集成

- 使用 `instructor` 库解析 LLM 输出为 Pydantic 模型
- 视频以 base64 编码作为多模态输入
- Prompt 模板在 `prompts.py`，中文指令，严格 JSON Schema 约束
- `src/lib/components_description.json` 包含 292 行排版特效目录，供 LLM 在生成设计时参考

---

## Frontend 架构详解

### 页面路由 (React Router v7)

```
/login    → LoginPage         (公开)
/register → RegisterPage      (公开)
/         → ProtectedRoute → App  (需登录)
```

`ProtectedRoute` 检查 `useAuthStore.isAuthenticated`，未登录则重定向到 `/login`。

### 组件树

`App.tsx` 渲染一个全窗口无限画布：

- **Header**：左上 "VIRAL STYLE" Logo + 右上 用户下拉（Save layout / Log out）
- **Footer**：快捷键提示（Ctrl+滚轮=缩放, 拖拽节点=移动, 拖拽背景=平移）
- **Wires**：SVG 覆盖层，用 cubic Bezier 曲线连接节点
- **NodeErrorToast**：右下固定位置的错误堆栈
- **9 个核心节点**（管线从左到右）：

```
ReferenceNode → CompressConfigNode → CompressNode → ExtractingNode
                                                       ├→ SplitNode → SplitSegmentNode × N
                                                       ├→ ScriptAnalysisNode
                                                       ├→ AudioAnalysisNode
                                                       └→ VisualAnalysisNode
```

### 状态管理 (Zustand 5)

| Store | 持久化 | 职责 |
|-------|--------|------|
| `useAuthStore` | localStorage | token, user, login/logout |
| `useCanvasStore` | sessionStorage | zoom, pan, 节点位置；手动保存布局到 localStorage |
| `useVideoStore` | 无 | 整个视频分析管线状态：上传/压缩/分析进度、结果、错误 |
| `useAppStore` | 无 | 遗留 GPT 训练状态（Web Worker，未激活） |

### API 调用模式

- **REST**：axios + `Authorization: Bearer <token>`，用于所有管道 POST 请求
- **通用 SSE**：原生 `fetch` + `response.body.getReader()` 手动解析 `data:` 行
- **音频 SSE**：`@microsoft/fetch-event-source`，逐帧读取 AudioStreamChunk
- 所有 SSE 流通过全局 `streamControllers` Record 管理，支持 abort

### 画布系统

- 缩放/平移通过 CSS `transform: translate(panX, panY) scale(zoom)` + `transformOrigin: top left`
- 缩放范围 0.2–2.0，Ctrl+滚轮触发
- 拖拽使用原生 mouse 事件，区分节点拖拽 vs 背景平移
- Wires 组件将逻辑坐标转换为屏幕坐标，自动计算源节点最近边到目标节点的曲线

### 样式

全组件使用内联 `style` props，统一字体 **JetBrains Mono**，无 CSS 文件（除主应用外的 index.css）。

---

## Videos 架构详解

### 本质

Videos 包**不是**一个可以直接 `pnpm dev` 运行的独立 Remotion 项目。它是一个 **AI 代码生成引擎**：输入一段短视频，自动分析其结构并生成可渲染的 Remotion TypeScript 项目。

### 核心组件

```
videos/
├── _templates/               # 项目脚手架模板 → 复制到 output/
│   └── src/                  # 12 个可复用动画组件 (TypewriterText, GlitchText, ...)
├── src/components/remocn/    # 58 个预构建 Remotion 动画组件（排版、转场、UI 块等）
├── effects/                  # 每个 remocn 组件的 Markdown 文档
├── generator.py              # 主生成管道 v6.0（5 阶段 VLM + CV 测量）
├── test_generator.py         # 备选管道 v3（两阶段 LLM）
├── video_measure.py          # OpenCV 逐帧动画参数测量（透明度、位移、缩放、打字机速度）
├── audio_analysis.py         # librosa BGM 分析（BPM, 节拍, 起始点, 能量）
├── remocn_components.json    # 58 组件目录（名称、分类、描述）
└── output/                   # 生成的项目落地位置（gitignore）
```

### 生成管道流程

1. **Stage 0**：从 `_templates/` 复制脚手架到 `output/{name}_{timestamp}/`
2. **Stage 1**：提取音频 (ASR 转录)、检测场景切换 (cv2)、分析 BGM (librosa)、捕获关键帧
3. **Stage 2**：将视频 (base64) + 分析数据发给多模态 LLM 提取结构 → `structure.json`
4. **Stage 3** (可选)：OpenCV 逐帧测量动画参数 → `animation_phases`
5. **Stage 4**：LLM 生成 Remotion TSX 代码（使用 58 remocn 组件 + Remotion API）
6. **Stage 5**：`pnpm build` / `npx remotion render` 验证

### 动画组件库 (remocn)

58 个 shadcn/ui 风格的 Remotion 组件，分类：
- **Typography**：BlurReveal, Typewriter, GlitchText, HighlightText, SpringPopIn, ...
- **Core Primitives**：SuccessConfetti, AnimatedCheck, ...
- **UI Blocks**：GlassCodeBlock, AnimatedLineChart, ...
- **Transitions**：DirectionalWipe, ChromaticAberrationWipe, ...
- **Compositions**：BrowserFlow, DashboardPopulate, ...

注册在 `components.json`，registry 指向 `remocn.dev`。

### 代码生成约束

- 缓动函数白名单仅 10 个：`linear, ease, quad, cubic, sin, circle, exp, elastic, back, bounce`
- `sine`, `expo`, `easeIn`, `smooth` 等别名**明确禁止**
- 可用 Remotion 包：`@remotion/shapes`, `@remotion/noise`, `@remotion/paths`, `@remotion/transitions`, `@remotion/light-leaks`
- 中文字体回退列表有镜像 URL 替换逻辑

---

## 测试

### Backend

- 框架：pytest + pytest-cov
- 约定：`{action}_works` / `{action}_fails_with_{reason}` / `{action}_handles_{condition}`
- FFmpeg 必须在 PATH 中
- `tests/conftest.py` 提供的 `sample_video` fixture 指向 `tests/videos/1.mp4`，文件不存在则自动 skip
- 测试文件：`tests/test_video.py`（视频处理），`tests/test_scenedetect.py`（批处理脚本非 pytest）
- 运行：`uv run pytest tests/ -v`（加 -v 查看 skip 原因）

### Frontend & Videos

目前没有测试配置。

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 修改了数据模型但启动报错 | 删除 `backend/database.db` 重新建表（无迁移系统） |
| LLM 调用失败 | 检查 `.env` 中 `API_KEY`, `MODEL`, `BASE_URL` 是否正确 |
| 上传/分析接口 401 | 先调 `/login` 获取 token，请求头加 `Authorization: Bearer <token>` |
| 任务重启后丢失 | 任务系统纯内存，SSE 也会断开。考虑后期迁移到 Celery/Redis |
| 视频分析报错超过 50MB | 先调 `/compress` 压缩后再分析，或调高 `MAX_ANALYZE_SIZE_MB` |
| 前端代理不通 | 确认 backend 在 `127.0.0.1:8000` 运行；Vite 配置在 `frontend/vite.config.ts` |
| 测试 skip 说不存在视频 | 往 `backend/tests/videos/1.mp4` 放一段 .mp4 文件 |
| storage/ 目录为空 | 该目录 gitignore，生产使用时会自动创建子目录 |
| pnpm 命令找不到 | 确认已安装 pnpm：`npm install -g pnpm` |

---

## 代码风格

### Backend (Python)

- Lint：Ruff（规则：I=isort, UP=pyupgrade, E/W=pycodestyle, F=pyflakes, C90=mccabe）
- 遵循 MVC 分层：Router → Service → Repository → Model
- 异步操作用 `async def` + `await`，`core.py` 中的任务函数签名保持一致
- 新增异步任务遵循 `_register_and_launch()` 模式

### Frontend (TypeScript)

- TypeScript strict mode
- 内联 style props，JetBrains Mono 字体统一
- 新节点组件参照 `src/components/nodes/*.tsx` 模式
- 状态放 `useVideoStore`，避免创建新 store 除非独立关注点
- SSE 流管理使用 `subscribeTaskStream` 工具函数

### Videos (TypeScript)

- ESLint 配置：`@remotion/eslint-config-flat`
- Prettier 3.8.1 格式化
- 新 Remotion 组件放 `videos/src/components/remocn/`，需在 `remocn_components.json` 注册
