"""transfer 包 — 结构迁移模块

将 analysis_result.json（爆款视频分析结果）+ new_content.json（用户新内容）
→ 映射为 remotion_props.json（Remotion渲染配置），自动处理：
  - 槽位文案填充（{变量}占位符替换）
  - 素材缺口检测与补全（纯色背景 / AIGC生图 / 纯文字）
  - 3级remocn视觉组件后备链（LLM推荐 → 特效类型映射 → 情绪映射）
  - TTS语速自动推算（从原视频ASR语速反推edge-tts rate参数）
  - 4种风格变异（standard / high_click / high_convert / high_rhythm）

核心入口: transfer.transfer() — 结构迁移主函数
"""
