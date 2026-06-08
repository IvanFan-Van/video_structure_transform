"""analysis 包 — 视频结构分析模块

整个分析管线分为 4 个阶段：
  阶段0 (preprocess.py):  本地预处理 — ASR语音识别、镜头切分、关键帧、BGM分析、人声分离
  阶段1 (analyzer.py):    宏观LLM分析 — 全视频 + 关键帧 → beat边界、视觉风格、脚本结构
  阶段2 (analyzer.py):    逐beat并发LLM分析 — 每个beat的视频片段 → 文字元素、特效、转场
  阶段3 (analyzer.py):    跨beat高层汇总 — 纯文本LLM → 卖点策略、槽位模板、素材需求
  阶段4 (assembler.py):   规则统计+最终组装 → analysis_result.json

核心数据模型定义在 models.py，LLM提示词在 prompts.py，
ffmpeg工具函数在 video_utils.py，人声分离在 audio_separator.py。
"""
