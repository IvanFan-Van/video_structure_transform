"""迁移层数据模型 — 定义结构迁移管道的所有Pydantic模型

本文件是 transfer 包的"类型契约"，定义了:
  输入层:  NewContent — 用户填写的新内容（主题、槽位文案、素材路径）
          SlotInput — 单个槽位的用户输入
  输出层:  RemotionProps — 发送给Remotion渲染的完整配置
          SceneProps — 单个场景的渲染参数
          TextStyle — 文字样式（字号、颜色、位置、动画类型）
          RemocnEffect — remocn组件调用描述（支持嵌套children实现组件组合）
  报告层:  GapItem — 素材缺口项
          MigrationSummary — 迁移过程摘要

模型关系:
  NewContent.slots: dict[str, SlotInput]  — label → 用户输入
  RemotionProps.scenes: list[SceneProps]  — 渲染场景列表
  SceneProps.remocnEffects: list[RemocnEffect] — 场景上的remocn组件层
  RemocnEffect.children: list[RemocnEffect] — 递归嵌套子组件
"""

from pydantic import BaseModel, Field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# 用户输入模型
# ═══════════════════════════════════════════════════════════════════


class SlotInput(BaseModel):
    """用户为单个槽位提供的内容

    从 new_content.json 中 slots.<label> 字段读取。
    用户需要填写:
      - text: 该槽位的文案（可选，留空则用模板+变量填充）
      - user_video/user_image: 素材路径（可选，留空则用纯色背景）
      - variables: 模板变量值 {变量名: 实际值}
    """
    text: str = Field(default="", description="该槽位的文案内容")
    user_video: Optional[str] = Field(default=None, description="用户提供的视频文件路径（绝对路径）")
    user_image: Optional[str] = Field(default=None, description="用户提供的图片文件路径（绝对路径）")
    variables: dict = Field(default_factory=dict, description="模板变量填充，如{'产品名':'谢逸牌蛋糕','核心香气':'蛋香味'}")


class NewContent(BaseModel):
    """用户输入的新内容 — 整个结构迁移的输入数据

    从 transfer/new_content.json 读取，用户需在运行 transfer 前填写完整。

    slots 的 key 必须与 analysis_result.json 中 slot_template[].label 对应，
    这样 transfer 才能将原视频的槽位结构映射到新内容上。
    """
    theme: str = Field(description="新视频主题，如'儿童零食推荐——谢逸牌蛋糕'")
    target_audience: str = Field(default="", description="目标受众，如'宝妈群体'")
    slots: dict[str, SlotInput] = Field(default_factory=dict, description="槽位填充，key与analysis_result的label对应")
    voiceover_text: str = Field(default="", description="TTS旁白完整文案，留空则从所有slots的text自动拼接")
    user_materials: list[str] = Field(
        default_factory=lambda: ["text"],
        description="用户拥有的素材类型列表，如 ['text','voiceover','video','image']"
    )
    output_ratio: str = Field(default="9:16", description="输出画面比例: 9:16(竖屏) 或 16:9(横屏)")


# ═══════════════════════════════════════════════════════════════════
# Remotion 渲染配置输出模型
# ═══════════════════════════════════════════════════════════════════


class TextStyle(BaseModel):
    """文字样式 — 定义场景中文本的视觉属性

    position_x/position_y 是百分比位置:
      - 水平: 0=左边缘, 50=画面中心, 100=右边缘
      - 垂直: 0=顶部, 50=画面中心, 100=底部
      文案通过 transform:translate(-50%,-50%) 居中于该坐标点

    数据来源优先级:
      1. packaging_structure.subtitle_style（来自原视频LLM分析）
      2. 情绪映射默认值（_EMOTION_TO_COLOR 等 fallback）
    """
    fontSize: int = Field(default=48, description="字体大小(px)")
    color: str = Field(default="#FFFFFF", description="文字颜色(hex)")
    fontWeight: str = Field(default="bold", description="字重: bold/normal/lighter")
    animation: str = Field(default="fade_in", description="动画类型: typewriter/fade_in/slide_in/bounce/glitch/static")
    position_x: float = Field(default=50, description="水平位置 0-100%，中心=50")
    position_y: float = Field(default=50, description="垂直位置 0-100%，底部=82")


class RemocnEffect(BaseModel):
    """单个 remocn 组件调用描述

    支持通过 children 字段实现组件嵌套（如 SpringPopIn 容器包裹 BlurReveal 文字特效）。
    组件名必须在 REMOCN_REGISTRY 的白名单中（59个组件），渲染时动态查找。

    示例:
      {"component":"SpringPopIn", "props":{"damping":12}, "children":[
        {"component":"BlurReveal", "props":{"text":"产品展示","fontSize":64}}
      ]}
    """
    component: str = Field(description="remocn组件名，如Typewriter/BlurReveal/FocusZoom")
    props: dict = Field(default_factory=dict, description="组件props键值对，如{'fontSize':64,'charsPerSecond':15}")
    children: list["RemocnEffect"] = Field(default_factory=list, description="子组件列表，用于容器型组件包裹")


class SceneProps(BaseModel):
    """单个场景的完整渲染参数

    一个场景 = Remotion 的一个 <Sequence>，包含:
      - 时间信息: startFrame(起始帧), durationFrames(持续帧数)
      - 渲染类型: text_overlay / emphasis_text / remocn_composed
      - 文案内容: text + textStyle + remocnEffects
      - 背景素材: backgroundVideo / backgroundImage / backgroundColorFallback（三级优先级）
      - BGM卡点: beatFrames（该场景时间内的相对帧位置）
      - 缺口信息: gapFilled / gapStrategy / fill_method
    """
    id: str                           # 场景唯一标识（与 slot label 对应，如 "hook"）
    slot_id: int                      # 槽位序号（从1开始）
    startFrame: int                   # 场景起始帧号（30fps）
    durationFrames: int               # 场景持续帧数
    type: str = Field(description="scene渲染类型: text_overlay/emphasis_text/remocn_composed")
    text: str = Field(default="")    # 渲染的文字内容
    textStyle: TextStyle = Field(default_factory=TextStyle)
    visualHint: str = Field(default="")  # 画面描述线索
    emotion: str = Field(default="neutral")  # 情绪标签
    beatFrames: list[int] = Field(default_factory=list, description="该场景内的BGM卡点相对帧号")
    hasMaterial: bool = Field(default=False, description="用户是否提供了视频/图片素材")
    backgroundVideo: Optional[str] = None      # 背景视频文件名（已拷贝到public/）
    backgroundImage: Optional[str] = None      # 背景图片文件名（已拷贝到public/）
    backgroundColorFallback: str = Field(default="#000000", description="无素材时的纯色背景")
    requiredElements: list[str] = Field(default_factory=list, description="关键视觉元素清单")
    gapFilled: bool = Field(default=False, description="是否触发了素材缺口补全")
    gapStrategy: str = Field(default="", description="补全策略: color_bg+text/aigc_image/text_subtitle_only")
    fill_method: str = Field(default="", description="具体补全方式: color_bg/text_only/aigc_image")
    remocnEffects: list["RemocnEffect"] = Field(
        default_factory=list,
        description="仅type=remocn_composed时有效，按顺序渲染的remocn组件列表",
    )


class GapItem(BaseModel):
    """素材缺口项 — 记录一个slot用户缺少的素材"""
    slot_id: int       # 槽位序号
    label: str         # 槽位标签
    missing_type: str  # 缺失类型: video/image/voiceover
    impact: str        # 影响等级: high/medium/low
    strategy: str      # LLM推荐的补全策略描述
    filled: bool = False       # 是否已被管道自动补全
    fill_method: str = ""      # 补全方式: color_bg/text_only/aigc_image


class MigrationSummary(BaseModel):
    """迁移过程摘要 — 记录结构迁移的核心信息"""
    sourceVideo: str      # 源爆款视频文件名
    theme: str            # 迁移后的新主题
    slotsCount: int       # 场景槽位总数
    gapsCount: int        # 素材缺口总数
    filledGapsCount: int  # 已填充的缺口数
    rhythmPattern: str    # 节奏模式
    visualStyle: str      # 视觉风格


class RemotionProps(BaseModel):
    """Remotion 渲染入参 — 完整输出JSON文件的结构

    这是 transfer 管线的最终产物，写入 remotion_props.json。
    Remotion 渲染时通过 --props 参数读取此文件。
    """
    fps: int = 30                          # 输出帧率
    durationInFrames: int                  # 总帧数 = sum of all scene.durationFrames
    width: int = 1080                      # 画面宽度(px) — 9:16竖屏标准
    height: int = 1920                     # 画面高度(px) — 9:16竖屏标准
    scenes: list[SceneProps]               # 场景列表（按startFrame排序）
    bgmPath: str = Field(default="bgm.wav")        # BGM文件名（从原视频分离的伴奏）
    voiceoverPath: str = Field(default="voiceover.wav")  # TTS旁白文件名
    voiceoverText: str = Field(default="")  # TTS实际朗读的文本
    ttsRate: str = Field(default="+0%", description="edge-tts语速参数，如'+65%'")
    rhythmPattern: str = Field(default="")  # 节奏模式标签
    visualStyle: str = Field(default="")    # 视觉风格标签
    gapReport: list[GapItem] = Field(default_factory=list)  # 缺口报告
    migrationSummary: MigrationSummary = Field(...)          # 迁移摘要
