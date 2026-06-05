## 项目结构

```
frontend/
├── index.html                          # HTML 入口，挂载 #root，加载 /src/main.tsx，引入 JetBrains Mono 字体
├── package.json                        # 项目依赖 (React 18, Zustand, React Router, Axios) 与脚本 (dev/build/preview)
├── vite.config.ts                      # Vite 构建配置：React 插件 + API 代理 (/api → http://127.0.0.1:8000)
├── tsconfig.json                       # TypeScript 编译配置：ES2020, bundler 模块, strict 模式, JSX react-jsx
├── tsconfig.node.json                  # Vite Node 端 TypeScript 配置
├── pnpm-workspace.yaml                 # pnpm workspace 配置
└── src/
    ├── main.tsx                        # 应用入口：<BrowserRouter> 包裹路由 (/login, /register, /)，主路由受 ProtectedRoute 保护
    ├── App.tsx                         # 根组件：组合所有流水线节点、Wires 连线、zoom/pan 画布变换、Worker 生命周期、用户菜单、错误提示
    ├── context/
    │   └── ZoomContext.ts              # 缩放上下文，默认值 1，由 useDraggable 消费以计算拖拽偏移
    ├── hooks/
    │   ├── useDraggable.ts             # 节点拖拽：优先读取 useCanvasStore 持久化坐标，考虑全局 zoom，忽略表单元素拖拽
    │   ├── useNodePositions.ts         # 封装 useCanvasStore 的 positions 读取与 updatePosition 写入
    │   ├── usePan.ts                   # 画布平移：鼠标在空白区域拖拽，偏移量存入 useCanvasStore
    │   └── useZoom.ts                  # 画布缩放：Ctrl + 鼠标滚轮，缩放值存入 useCanvasStore（限幅 0.2～2）
    ├── store/
    │   ├── types.ts                    # 全局 TypeScript 类型定义：Pos, VideoMeta, CompressConfig, TranscriptResult, AudioStreamChunk, VisualResult, NodeError 等
    │   ├── useAppStore.ts              # GPT 训练流水线状态：数据集、模型配置、训练控制、损失/生成追踪、运行历史、Web Worker 管理
    │   ├── useAuthStore.ts             # 认证状态：JWT token、用户信息、login/register/logout 操作（对接 FastAPI 后端）
    │   ├── useCanvasStore.ts           # 画布状态：缩放、平移、所有节点位置 (Record<string, Pos>)，持久化至 sessionStorage
    │   └── useVideoStore.ts            # 视频处理流水线状态：上传、压缩、三路分析任务 (脚本/BGM/视觉)、SSE 音频流、轮询状态、错误汇总
    ├── constants/
    │   └── index.ts                    # 常量定义：PRESETS（数据集预设），WIRES（节点连线拓扑，定义有向图边集）
    ├── utils/
    │   └── index.ts                    # 工具函数：fmt（毫秒→时间字符串）、fmtF（数字→K/M/G 缩写）、fmtSize（字节→B/KB/MB/GB）、sliderStyle（range input 样式）
    ├── components/
    │   ├── ProtectedRoute.tsx          # 路由守卫：通过 useAuthStore 检查登录状态，未认证则重定向到 /login
    │   ├── ui/
    │   │   ├── BaseNode.tsx            # 节点容器组件：统一边框、阴影、主题色，集成 useDraggable 实现拖拽
    │   │   ├── NodeErrorToast.tsx      # 错误提示浮层：右下角展示 videoErrors，支持展开详情与逐条关闭
    │   │   └── Wires.tsx              # SVG 连线组件：根据 WIRES 拓扑与 positions 坐标绘制贝塞尔连接线，随 zoom/pan 变换
    │   ├── nodes/
    │   │   ├── ReferenceNode.tsx       # 参考视频上传：缩略图、元信息展示、文件拖拽上传、上传进度
    │   │   ├── CompressConfigNode.tsx  # 压缩参数配置：编码器、CRF/码率、分辨率、帧率
    │   │   ├── CompressNode.tsx        # 视频压缩执行：前后体积/分辨率对比，开始/停止控制
    │   │   ├── ExtractingNode.tsx      # 特征提取入口：一键触发脚本/BGM/视觉三路分析，旋转加载器与进度状态
    │   │   ├── ScriptAnalysisNode.tsx  # 脚本结构分析：6 阶段拆解 (Hook/Setup/Story/Insight/CTA/Outro)，叙事视角、情绪基调、钩子类型，可折叠卡片
    │   │   ├── AudioAnalysisNode.tsx   # 音频特征分析：全局特征 (BPM/流派/亮度/动态范围) + 四张内联波形图 (Energy/Centroid/Flux/Onset)
    │   │   ├── VisualAnalysisNode.tsx  # 视觉特征分析：镜头切分、运镜分类、文字元素检测、剪辑节奏统计、转场类型、文字密度曲线
    │   │   ├── DatasetNode.tsx         # [已停用] 数据集选择与加载：预设下拉、自定义文本、拖拽上传 .txt
    │   │   ├── TokenizerNode.tsx       # [已停用] 字符级分词器信息展示：词汇量、字符网格、示例分词
    │   │   ├── ArchitectureNode.tsx    # [已停用] 模型架构配置：嵌入维度、注意力头数、层数、步数等超参数滑块
    │   │   ├── TrainingNode.tsx        # [已停用] 训练控制：启动/停止、进度条、当前损失、实时样本输出
    │   │   ├── MetricsNode.tsx         # [已停用] 训练指标汇总：损失变化、每步耗时、运行历史表
    │   │   └── GenerateNode.tsx        # [已停用] 文本生成：提示词输入、温度滑块、快速生成、结果展示
    │   └── charts/
    │       ├── LossChart.tsx           # 训练损失曲线：EMA 平滑，少量点时显示散点，否则显示折线
    │       ├── StepTimeChart.tsx       # 每步训练耗时直方图
    │       ├── EnergyChart.tsx         # RMS 能量面积图：紫色渐变填充 + 折线 + 端点标记
    │       ├── CentroidChart.tsx       # 频谱质心折线图：分段 HSL 着色 (低→紫, 高→青)
    │       ├── FluxChart.tsx           # 频谱通量柱状图
    │       └── OnsetChart.tsx          # 起始包络柱状图
    └── pages/
        ├── LoginPage.tsx              # 登录页：邮箱/密码表单，调用 useAuthStore.login，成功后跳转到 /
        └── RegisterPage.tsx           # 注册页：邮箱/密码/确认密码表单，调用 useAuthStore.register，成功后跳转到 /login
```

### 数据流概览

```
用户上传视频 (ReferenceNode)
    → 配置压缩参数 (CompressConfigNode)
        → 执行压缩 (CompressNode)
            → 一键提取 (ExtractingNode)
                ├→ 脚本结构分析 (ScriptAnalysisNode)
                ├→ BGM 特征分析 (AudioAnalysisNode)
                └→ 视频特征分析 (VisualAnalysisNode)
```

状态管理采用 Zustand，各 store 职责隔离：
- `useVideoStore` — 视频流水线的所有任务状态、结果与错误
- `useCanvasStore` — 画布视口 (zoom/pan) 与节点坐标，持久化至 sessionStorage
- `useAuthStore` — JWT 认证，持久化至 localStorage
- `useAppStore` — 已停用的 GPT 训练管线（历史遗留）

## 节点主题色

每个节点通过 `BaseNode` 的 `accent` prop 控制其边框、阴影及内部关键元素的主题色。主题色在节点激活时（`active=true`）显示，未激活时统一为灰色边框（`#e0e0e0`）。

### 视频分析流水线节点

| 节点 | 组件 | 主题色 | 色样 | 作用 |
|------|------|--------|------|------|
| Reference | `ReferenceNode` | `#6366f1` | ██ indigo | 上传参考视频，解析视频元信息（分辨率、码率、时长等） |
| Compress Config | `CompressConfigNode` | `#14b8a6` | ██ teal | 配置压缩参数（编码器、CRF、分辨率、帧率等） |
| Compress | `CompressNode` | `#06b6d4` | ██ cyan | 执行视频压缩，展示前后体积/分辨率对比 |
| Extracting | `ExtractingNode` | `#7c3aed` | ██ violet | 统一入口，一键触发脚本结构分析、BGM 特征分析、视频特征分析三个子任务 |
| Script Analysis | `ScriptAnalysisNode` | `#10b981` | ██ emerald | 分析口播文案结构，拆解为 Hook/Setup/Story/Insight/CTA/Outro 六阶段，识别叙事视角、情绪基调与钩子类型 |
| Audio Analysis | `AudioAnalysisNode` | `#f59e0b` | ██ amber | 分析音频全局特征（BPM、流派、亮度、动态范围），绘制 RMS/频谱质心/频谱通量/起始包络四张波形图 |
| Visual Analysis | `VisualAnalysisNode` | `#06b6d4` | ██ cyan | 分析视觉镜头（切分、运镜、文本帧），统计剪辑节奏、转场类型与文字密度曲线 |

### 主题色设计原则

- 相邻节点使用不同色系，便于在画布上快速区分
- 同级分支节点（Script / Audio / Visual Analysis）各自使用独立颜色，与父节点 Extracting（violet）形成对比
- 节点内部元素（标题图标、卡片、下拉箭头、高亮边框）跟随主题色联动