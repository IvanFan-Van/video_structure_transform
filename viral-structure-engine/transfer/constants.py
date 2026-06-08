"""transfer 层共享常量

本文件定义结构迁移过程中使用的所有硬编码常量和映射表。
"""

# edge-tts 中文默认语速（chars/sec），用于推算语速调整参数
# 来源: 实测 zh-CN-XiaoxiaoNeural 在 rate="+0%" 时的输出速度
# 用途: _calc_tts_rate() 用此值计算原视频语速与默认语速的偏差百分比
DEFAULT_TTS_SPEED = 4.2

# label → 背景色映射表
# 用途: SceneProps 初始化时设置 backgroundColorFallback，
#       以及 gap fill 时作为纯色背景的兜底颜色
# 设计: 深色背景用于沉浸感强的段落(hook/pain_point等)，
#       暖白色用于展示类段落(solution)，红色用于CTA促转化
LABEL_BG_COLORS = {
    "hook":                 "#0D0D0D",   # 钩子 — 深黑
    "pain_point":           "#0D0D0D",   # 痛点 — 深黑
    "solution":             "#F5F5F0",   # 解决方案 — 暖白
    "product_show":         "#1A1A2E",   # 产品展示 — 深蓝黑（科技感）
    "usage_scene":          "#0D1A2E",   # 使用场景 — 深蓝
    "comparison":           "#1A1A1A",   # 对比 — 深灰
    "testimonial":          "#0D0D0D",   # 用户证言 — 深黑
    "offer":                "#1A0A0A",   # 优惠 — 暗红底
    "cta":                  "#FF4444",   # 行动号召 — 红色（高转化色）
    "outro":                "#111111",   # 结尾 — 深黑
    "outro_platform_guide": "#111111",   # 平台引导结尾 — 深黑
}
