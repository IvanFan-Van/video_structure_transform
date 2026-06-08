"""Pydantic 数据模型 — 定义视频分析全流程的结构化数据

本文件包含17个 Pydantic BaseModel 类，覆盖以下领域：
  基础元素: TextElement(文字元素), EffectDescription(视觉特效), TransitionDetail(转场细节)
  Beat级:   BeatAnalysis(单个beat完整分析), SubtitleStyle(字幕样式)
  脚本级:   ScriptSegment(叙事段落), ScriptStructureResult(脚本结构)
  节奏级:   RhythmStructure(节奏结构), FastSlowSegment(快慢段落)
  包装级:   PackagingStructure(包装结构), PackagingDominance(主导类型)
  BGM级:    BGMFeatures(BGM特征), BeatAlignments(卡点对齐)
  槽位级:   SlotItem(结构槽位), SlotTemplateResult(槽位模板), MaterialRequirement(素材需求)
  全局级:   Phase1Output/Phase2Output/Phase3Output(三阶段LLM输出)
  迁移级:   GapAnalysis(缺口分析), SellingPoint(卖点), SellingPointAnalysis(卖点策略)

所有模型使用 Pydantic v2 的 field_validator 和 model_dump() 实现结构化校验和序列化。
LLM 的输出经过这些模型强制类型校验，不合法的字段会被拒绝（如字符串字段被填入数字）。
"""

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# 基础元素模型 — 描述视频画面中最小的视觉单元
# ═══════════════════════════════════════════════════════════════════


class TextElement(BaseModel):
    """画面上的一个文字元素（M2）

    代表视频某一帧上出现的一段文字，包含内容、大小、颜色和位置信息。
    由 Phase 2 LLM 从视频帧中提取。
    """
    text: str = Field(description="精确文字内容")
    font_size: str = Field(default="medium", description="字号: small/medium/large/xlarge")
    font_size_vh: float = Field(default=0, description="字体占画面高度的百分比，如4.2表示4.2%")
    color: str = Field(default="#FFFFFF", description="文字颜色 hex值")
    position_x: float = Field(default=50, description="水平位置 0-100%，画面左边缘=0，中心=50")
    position_y: float = Field(default=50, description="垂直位置 0-100%，画面顶部=0，中心=50")
    font_weight: str = Field(default="regular", description="字重: regular/medium/bold")


class EffectDescription(BaseModel):
    """一个视觉特效的描述（M3）

    描述文字元素上的动画效果，如打字机效果、弹入、发光等。
    Phase 2 LLM 分析视频帧序列，推断特效类型和参数。
    """
    type: str = Field(description="特效类型分类: typewriter/fade_in/blur_reveal/slide_in/bounce/scale/glow/highlight/static")
    description: str = Field(default="", description="自然语言描述，如'文字从左到右逐字出现，每字间隔约0.15s'")
    applies_to: str = Field(default="", description="作用于哪个文字元素，匹配 TextElement.text")
    duration_frames: int = Field(default=0, description="特效持续帧数（30fps基准）")
    phase: str = Field(default="hold", description="特效阶段: enter(进场) / hold(保持) / exit(退场)")
    remocn_component: str = Field(default="", description="匹配的59个remocn组件名，如Typewriter/BlurReveal/RGBGlitchText")
    remocn_props: dict = Field(default_factory=dict, description="推荐组件参数，如{'fontSize':64,'charsPerSecond':15}")


class TransitionDetail(BaseModel):
    """单个转场的详细描述（M4）

    描述两个beat之间的画面切换方式。
    由 Phase 2 LLM 分析 beat 边界处的视频帧变化推断。
    """
    type: str = Field(default="hard_cut", description="转场类型: hard_cut/fade/slide/zoom/glitch/rgb_split/wipe")
    direction: str = Field(default="", description="方向如 left_to_right/bottom_to_top/center_zoom，硬切时为空")
    duration_frames: int = Field(default=0, description="转场持续帧数（30fps基准）")
    at_time: float = Field(default=0, description="转场发生的时间点(秒)")
    description: str = Field(default="", description="自然语言描述")


class SubtitleStyle(BaseModel):
    """字幕样式

    描述视频中字幕的视觉风格，由 Phase 1 LLM 从全局视角评估。
    """
    position: str = Field(default="bottom_center", description="字幕位置如 bottom_center/top_center")
    color: str = Field(default="#FFFFFF", description="字幕文字颜色")
    stroke: str = Field(default="#000000", description="描边/阴影颜色")
    font_size_hint: str = Field(default="medium", description="字号感知: small/medium/large")
    animation: str = Field(default="none", description="字幕动画类型如 none/fade_in/typewriter")


class TitleCardTiming(BaseModel):
    """标题条/卖点卡片的出现时机"""
    time: float       # 出现时间(秒)
    description: str  # 卡片内容描述


class StickerTiming(BaseModel):
    """贴纸/动效的出现时机"""
    time: float        # 出现时间(秒)
    type: str          # 贴纸类型
    position: str = "" # 画面位置


# ═══════════════════════════════════════════════════════════════════
# Beat 级分析模型 — Phase 1/2 的核心产出
# ═══════════════════════════════════════════════════════════════════


class BeatAnalysis(BaseModel):
    """单个 beat 的完整分析结果（M1）

    一个 beat 是视频的逻辑最小片段（2-6秒），通常对应一个完整的镜头或一句话。
    Phase 1 产出 beat 边界（start_time/end_time），Phase 2 填充具体内容。
    """
    beat_id: int = Field(description="beat 序号，从1开始")
    start_time: float = Field(description="开始时间(秒)")
    end_time: float = Field(description="结束时间(秒)")
    text_elements: list[TextElement] = Field(default_factory=list, description="该beat内所有画面文字元素")
    effects: list[EffectDescription] = Field(default_factory=list, description="该beat内所有视觉特效")
    transition_out: TransitionDetail = Field(default_factory=TransitionDetail, description="该beat结束时的转场效果")
    editing_technique: str = Field(default="", description="剪辑手法，如'跳切快节奏'/'J-cut声音先入'/'匹配剪辑'")
    selling_point: str = Field(default="", description="如果该beat在传达卖点，注明内容+策略；否则留空")
    selling_strategy: str = Field(default="", description="卖点策略分类: 口感诱惑/促销紧迫/信任背书/稀缺性/功能对比")
    emotion: str = Field(default="neutral", description="情绪标签: curious/urgent/excited/sincere/humorous/suspenseful/calm/neutral")
    bg_sync_note: str = Field(default="", description="画面与BGM的配合说明，如'画面切换准确卡在重拍上'")


# ═══════════════════════════════════════════════════════════════════
# 全局脚本结构模型 — Phase 1 产出
# ═══════════════════════════════════════════════════════════════════


class ScriptSegment(BaseModel):
    """单个叙事段落（M8）

    按叙事功能将视频拆分为段落，比 beat 粒度更粗。
    一个段落可能包含多个 beat。
    """
    label: str = Field(description="段落标签: hook/pain_point/solution/product_show/usage_scene/comparison/testimonial/offer/cta/outro")
    start_time: float = Field(default=0, description="段落开始时间(秒)")
    end_time: float = Field(default=0, description="段落结束时间(秒)")
    text: str = Field(description="该段落的文案（忠实还原原视频内容）")
    keywords: list[str] = Field(default_factory=list, description="3-5个关键词")
    visual_hint: str = Field(default="", description="画面核心内容的简短描述")
    emotion: str = Field(default="neutral", description="情绪基调")
    hook_type: str = Field(default="", description="钩子子类型: pain_point(痛点)/curiosity(好奇心)/contrast(对比)/data_shock(数据冲击)，仅hook段落使用")
    cta_type: str = Field(default="", description="CTA子类型: discount_urgency(促销紧迫)/social_proof(社交验证)/scarcity(稀缺性)，仅cta段落使用")


class ScriptStructureResult(BaseModel):
    """脚本结构分析结果"""
    asr_summary: str = Field(default="", description="语音内容摘要(50字内)")
    language: str = Field(default="zh", description="语种如 zh/en")
    segments: list[ScriptSegment] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# 节奏结构模型 — Phase 4 assembler 规则统计产出
# ═══════════════════════════════════════════════════════════════════


class FastSlowSegment(BaseModel):
    """快慢节奏段落标记"""
    start: float  # 开始时间(秒)
    end: float    # 结束时间(秒)
    pace: str = Field(description="节奏快慢: fast/medium/slow")


class FastSegmentDetail(BaseModel):
    """快节奏段落详情"""
    start: float        # 开始时间(秒)
    end: float          # 结束时间(秒)
    avg_duration: float = Field(description="该段平均镜头时长(秒)，值越小节奏越快")


class TransitionTypeDistribution(BaseModel):
    """转场类型分布统计 — 计数字典"""
    hard_cut: int = 0  # 硬切数量
    fade: int = 0      # 淡入淡出数量
    slide: int = 0     # 滑动转场数量
    zoom: int = 0      # 缩放转场数量
    glitch: int = 0    # 故障效果转场数量
    wipe: int = 0      # 擦除转场数量
    other: int = 0     # 其他类型数量


class RhythmStructure(BaseModel):
    """节奏结构 — 纯派生/聚合字段

    不存储原始数据，所有字段由 assembler.py 从 beat 分析结果统计得出。
    """
    avg_shot_duration: float = Field(default=0, description="平均镜头时长(秒)")
    shot_frequency_curve: list[float] = Field(default_factory=list, description="每秒镜头数量曲线")
    rhythm_pattern: str = Field(default="", description="节奏模式: slow-fast-climax/steady_build/fast_then_slow/constant_fast")
    fast_segments: list[FastSegmentDetail] = Field(default_factory=list, description="快节奏段落列表")
    climax_position: float = Field(default=0, description="高潮位置(秒)，取情绪强度最大的beat中点")
    transition_type_distribution: TransitionTypeDistribution = Field(default_factory=TransitionTypeDistribution, description="转场类型分布")


# ═══════════════════════════════════════════════════════════════════
# 包装结构模型 — 描述视频的视觉包装层
# ═══════════════════════════════════════════════════════════════════


class PackagingDominance(BaseModel):
    """包装主导类型分布 — 判断视频主要靠什么类型的视觉元素支撑"""
    primary: str = Field(default="subtitle_heavy", description="主导类型")
    distribution: dict = Field(default_factory=dict, description="各类型beat数量分布，如{'subtitle_heavy':3,'product_centric':2}")


class PackagingStructure(BaseModel):
    """包装结构 — 字幕、标题条、贴纸、封面的整体描述"""
    subtitle_density: float = Field(default=0, description="字幕密度(条/分钟)")
    subtitle_style: SubtitleStyle = Field(default_factory=SubtitleStyle)
    title_card_timings: list[TitleCardTiming] = Field(default_factory=list)
    sticker_timings: list[StickerTiming] = Field(default_factory=list)
    cover_style: str = Field(default="", description="封面风格描述")


# ═══════════════════════════════════════════════════════════════════
# BGM 特征模型 — 音乐分析结果
# ═══════════════════════════════════════════════════════════════════


class BeatAlignments(BaseModel):
    """卡点对齐数据 — 衡量视频切点与BGM重拍的重合度"""
    match_rate: float = Field(default=0, description="卡点匹配率 0-1，1=全部切点都在重拍上")
    typical_offset: float = Field(default=0, description="典型偏移量(秒)")
    matched_count: int = Field(default=0, description="匹配的切点数（切点与重拍距离<50ms）")
    total_cuts: int = Field(default=0, description="总切点数")


class BGMFeatures(BaseModel):
    """BGM 特征 — 节拍、情绪、卡点对齐"""
    bpm: float = Field(default=0, description="每分钟节拍数")
    mood: str = Field(default="", description="BGM情绪标签: energetic/uplifting/moderate/calm/none")
    beat_timings: list[float] = Field(default_factory=list, description="所有重拍时间点列表(秒)")
    beat_alignments: BeatAlignments = Field(default_factory=BeatAlignments, description="卡点对齐数据")


# ═══════════════════════════════════════════════════════════════════
# 槽位模板模型 — Phase 3/4 产出，供结构迁移使用
# ═══════════════════════════════════════════════════════════════════


class SlotItem(BaseModel):
    """结构槽位 — 脚本段落对应的可复用模板

    每个槽位定义了一个视频段落的"填空框架"：
      - 需要什么类型的素材（视频/图片/文字/语音）
      - 画面应该是什么样的
      - 文案模板（品牌名等具体信息替换为{占位符}）
      - 缺少素材时的补全方案
    """
    slot_id: int   # 槽位序号
    label: str     # 功能标签，如 hook/product_show/cta
    duration: float = Field(description="建议时长(秒)")
    required_material_type: str = Field(description="所需素材类型: video/image/text/voiceover")
    visual_content_desc: str = Field(default="", description="画面内容描述")
    text_template: str = Field(default="", description="文案模板，品牌名/数据等替换为{占位符}")
    required_elements: list[str] = Field(default_factory=list, description="关键视觉元素清单")
    alternative_if_missing: str = Field(default="", description="素材缺失时的默认补全策略")
    migration_hint: str = Field(default="", description="迁移到新主题时的创作建议")


class SlotTemplateResult(BaseModel):
    """槽位模板集合"""
    slots: list[SlotItem] = Field(default_factory=list)


class MaterialRequirement(BaseModel):
    """素材需求 — 每个槽位需要什么素材"""
    type: str = Field(description="素材类型: video/image/text/voiceover")
    description: str = Field(description="素材描述，如'产品开箱特写镜头'")
    priority: str = Field(default="medium", description="优先级: high/medium/low")
    can_generate: bool = Field(default=False, description="是否可AIGC生成（如产品图可用AI生成）")


# ═══════════════════════════════════════════════════════════════════
# 缺口分析 & 卖点分析模型
# ═══════════════════════════════════════════════════════════════════


class GapAnalysis(BaseModel):
    """素材缺口分析 — 纯代码计算，不进LLM

    比对 slot_template 要求的素材类型 vs 用户实际提供的素材类型，
    用集合差集运算得出缺口列表。
    """
    slot_id: int                    # 槽位序号
    label: str = Field(description="槽位标签")
    missing_type: str = Field(description="缺失的素材类型: video/image/voiceover")
    impact: str = Field(default="medium", description="影响等级: high/medium/low")
    alternative_if_missing: str = Field(default="", description="补全方案")


class SellingPoint(BaseModel):
    """卖点信息 — 从 beat 分析中提取"""
    text: str = Field(description="卖点内容，如'每一片都做得又酥又脆'")
    time: float = Field(description="出现时间(秒)")
    strategy: str = Field(default="", description="卖点策略: 口感诱惑/促销紧迫/信任背书等")
    beat_id: int = Field(default=0, description="所在的beat编号")


class SellingPointAnalysis(BaseModel):
    """卖点策略高层分析 — Phase 3 LLM 从全局视角总结"""
    progression: str = Field(default="", description="推进逻辑: progressive(递进式) / parallel(并列式)")
    emphasized: str = Field(default="", description="被重点强调的卖点（最突出那个）")
    density: str = Field(default="", description="卖点密度: appropriate(适度) / sparse(稀疏) / dense(密集)")


# ═══════════════════════════════════════════════════════════════════
# 三阶段 LLM 输出模型 — 每个阶段产出的顶层模型
# ═══════════════════════════════════════════════════════════════════


class Phase1Output(BaseModel):
    """阶段1 LLM 输出（M10）— 全视频宏观分析结果

    LLM 看完整个视频后输出：beat划分、视觉风格、脚本结构、节奏模式。
    """
    beats: list[BeatAnalysis] = Field(default_factory=list, description="beat边界列表，此时仅含时间和描述，精细内容由阶段2填充")
    global_style: dict = Field(default_factory=dict, description="全局视觉风格，如{'tone':'dark','primary_color':'#1A1A2E'}")
    script_structure: list[ScriptSegment] = Field(default_factory=list, description="脚本结构段落")
    visual_style: str = Field(default="", description="视觉风格标签: subtitle_heavy/person_led/product_centric/mixed")
    rhythm_pattern: str = Field(default="", description="节奏模式标签")
    asr_summary: str = Field(default="", description="语音内容摘要")
    language: str = Field(default="zh", description="语种")


class Phase2Output(BaseModel):
    """阶段2 逐beat分析输出（M11）— 每个beat的精细视觉分析

    并发调用LLM，每个beat独立分析：文字元素、特效、转场、剪辑、卖点、情绪。
    """
    beats: list[BeatAnalysis] = Field(default_factory=list, description="所有beat的完整精细分析")


class Phase3Output(BaseModel):
    """阶段3 LLM 输出（M12）— 跨beat高层策略汇总

    纯文本调用（不传视频），从全局视角归纳卖点策略、生成槽位模板、列出素材需求。
    """
    selling_point_analysis: SellingPointAnalysis = Field(default_factory=SellingPointAnalysis)
    slot_template: list[SlotItem] = Field(default_factory=list, description="结构槽位模板")
    material_requirements: list[MaterialRequirement] = Field(default_factory=list, description="素材需求清单")


# ═══════════════════════════════════════════════════════════════════
# 向下兼容的旧模型 — 过渡期保留，供 analyzer 旧代码引用
# ═══════════════════════════════════════════════════════════════════


class RhythmPackagingResult(BaseModel):
    """阶段2 LLM 旧输出格式（过渡期保留，避免旧代码报错）"""
    fast_slow_segments: list[FastSlowSegment] = Field(default_factory=list)
    climax_position: float = Field(default=0)
    transition_types: TransitionTypeDistribution = Field(default_factory=TransitionTypeDistribution)
    subtitle_density: float = Field(default=0)
    subtitle_style: SubtitleStyle = Field(default_factory=SubtitleStyle)
    title_card_timings: list[TitleCardTiming] = Field(default_factory=list)
    sticker_timings: list[StickerTiming] = Field(default_factory=list)
    cover_style: str = Field(default="")
    bgm_mood: str = Field(default="")
    beat_alignment_match_rate: float = Field(default=0)
    beat_alignment_typical_offset: float = Field(default=0)
