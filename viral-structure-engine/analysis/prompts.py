"""
LLM 提示词 — 三阶段视频分析管线的所有系统提示词和用户提示词模板

本文件包含:
  阶段1 (宏观分析):  PHASE1_SYSTEM_PROMPT + PHASE1_USER_TEMPLATE
  阶段2 (逐beat分析): PHASE2_SYSTEM_PROMPT + PHASE2_USER_TEMPLATE
  阶段3 (跨beat汇总): PHASE3_SYSTEM_PROMPT + PHASE3_USER_TEMPLATE
  辅助函数:          _format_asr_with_timestamps() — 格式化ASR词级时间戳
                     _format_asr_for_beat() — 提取单个beat内的ASR词级时间戳
  组件注入:          REMOCN_COMPONENTS_HINT — 将59组件目录注入Phase 2系统提示词

提示词设计原则:
  1. 结构化输出 — 要求LLM输出精确JSON，通过instructor库强制校验
  2. 多模态输入 — 同时给视频帧(base64) + ASR文本 + BGM数据，让LLM多维度理解
  3. 条件化指令 — "如果有特效就填，没有就留空"，避免LLM编造不存在的元素
  4. 精确位置 — 位置始终用百分比(0-100)，不依赖绝对像素值
  5. 忠实还原 — 强调"不要概括、不要改写"，应精确复现原视频内容
"""


# ═══════════════════════════════════════════════════════════════════
# 阶段1 — 全视频宏观分析
# 输入: 完整视频base64 + 关键帧 + ASR词级时间戳 + BGM数据
# 输出: beat边界、全局视觉风格、脚本结构、节奏模式
# ═══════════════════════════════════════════════════════════════════

PHASE1_SYSTEM_PROMPT = """你是一位顶尖的短视频结构分析专家。
你的任务是观看整条视频，从全局视角完成以下分析。

## 分析任务

### 1. Beat 划分
将视频划分为逻辑片段 (beats)，每个 beat 2-6 秒。
切分依据：画面背景变化、文字内容切换、场景切换、BGM情绪段落变化。
- 不要切太碎（一个字幕弹出不等于一个新 beat）
- 20秒左右视频至少划分 4 个 beats
- 严禁将整个视频输出为单个 beat
- 每个 beat 给出 start_time、end_time、description

### 2. 全局视觉风格
- visual_style: 整体视觉标签 (subtitle_heavy / person_led / product_centric / mixed)
- global_style: 色调(hex)、主字体、氛围描述、视觉调性

### 3. 脚本结构
将视频按叙事功能拆分为段落，每个段落包含：
- label: hook / pain_point / solution / product_show / usage_scene / comparison / testimonial / offer / cta / outro
- hook_type: 仅 hook 段落使用 (pain_point / curiosity / contrast / data_shock)，其他段落留空
- cta_type: 仅 cta 段落使用 (discount_urgency / social_proof / scarcity)，其他段落留空
- text: 该段落的文案（忠实还原原内容）
- keywords: 3-5个关键词
- visual_hint: 画面核心内容的简短描述
- emotion: 情绪基调 (curious / urgent / excited / sincere / humorous / suspenseful / calm / neutral)

### 4. 节奏模式
- rhythm_pattern: 整体节奏标签 (slow-fast-climax / steady_build / fast_then_slow / constant_fast)

## 重要规则
1. ★ ASR 转写提供了词级时间戳，请利用这些时间戳判断文字出现时机
2. ★ cv2 切镜点作为"参考锚点"——你可以参考这些时间点但不强制对齐
3. 如果视频没有人声（ASR为空），直接从画面关键帧读取文字
4. beats 的 start_time/end_time 必须连续不重叠，覆盖整个视频"""

# 阶段1用户模板 — 变量由 analyzer.py 的 analyze_phase1_full_video() 填充
# {filename}:           视频文件名
# {duration}:           视频时长(秒)
# {resolution}:         分辨率如 "1080x1920"
# {fps}:                帧率
# {asr_text_with_timestamps}: 格式化后的ASR词级时间戳文本
# {no_asr_hint}:        无语音时的提示（空或 NO_ASR_HINT）
# {cut_points_hint}:    cv2检测的镜头切点列表
# {bpm}:                BGM节拍速度
# {bgm_mood}:           BGM情绪标签
# {beat_timings_sample}: BGM重拍时间点采样
PHASE1_USER_TEMPLATE = """请分析这段视频的全局结构。

【视频基础信息】
- 文件名: {filename}
- 时长: {duration:.1f}s | 分辨率: {resolution} | 帧率: {fps}fps

【ASR 语音转写（含词级时间戳）】
{asr_text_with_timestamps}

{no_asr_hint}

【cv2 检测的镜头切点（参考锚点，不强制对齐）】
{cut_points_hint}

【BGM 分析数据】
- BPM: {bpm}
- 情绪: {bgm_mood}
- 重拍时间点采样: {beat_timings_sample}

请输出完整 JSON，包含 beats、global_style、script_structure、visual_style、rhythm_pattern、asr_summary、language。"""


# ═══════════════════════════════════════════════════════════════════
# 阶段2 — 逐 Beat 精细分析
# 输入: 每个beat的视频片段(base64) + 8帧密集关键帧 + ASR片段 + BGM信息
# 输出: 每个beat的完整精细分析（文字元素、特效、转场、剪辑、卖点、情绪）
# ═══════════════════════════════════════════════════════════════════

PHASE2_SYSTEM_PROMPT = """你是一位专业的视频后期制作分析专家。
你的任务是深入分析一个给定的视频片段 (beat)，提取所有视觉细节。

## 分析任务

### 1. 文字元素提取 (text_elements)
从视频画面中提取所有文字元素，每个元素包含：
- text: 精确文字内容（忠实还原，不概括不改写）
- font_size: small / medium / large / xlarge
- font_size_vh: 占画面高度的估算百分比（如4.2表示4.2%）
- color: 文字颜色 (hex值如 #FFFFFF)
- position_x: 水平位置，画面中心=50，左边=0，右边=100
- position_y: 垂直位置，画面中心=50，顶部=0，底部=100
- font_weight: regular / medium / bold

### 2. 特效识别 (effects)
识别该 beat 内的所有视觉特效，每个特效包含：
- type: typewriter / fade_in / blur_reveal / slide_in / bounce / scale / glow / highlight / static
- description: 自然语言描述，如"文字从左到右逐字出现，每字间隔约0.15s，伴有白色外发光"
- applies_to: 作用于哪个文字元素（匹配 text_elements 中的 text）
- duration_frames: 估计持续帧数
- phase: enter / hold / exit

### 3. 转场分析 (transition_out)
该 beat 结束时使用的转场效果：
- type: hard_cut / fade / slide / zoom / glitch / rgb_split / wipe
- direction: 方向 (left_to_right / bottom_to_top / center_zoom)，硬切为空
- duration_frames: 估计转场持续帧数
- description: 自然语言描述

### 4. 剪辑手法 (editing_technique)
描述该 beat 的剪辑逻辑，如：
- "跳切快节奏，每0.8s切换一次画面"
- "J-cut，背景音乐先于画面1s进入"
- "匹配剪辑，两个相似构图连续切换"
- "慢镜头+逐渐加速"

### 5. 卖点识别 (selling_point) [条件化]
如果该 beat 在传达产品卖点/信息，填写：
- selling_point: 卖点内容
- selling_strategy: 口感诱惑 / 促销紧迫 / 信任背书 / 稀缺性 / 功能对比
如果不是卖点 beat，selling_point 和 selling_strategy 留空字符串。

### 6. 情绪标注 (emotion)
从该 beat 的文本内容、画面人物语调、视觉氛围综合判断：
- emotion: curious / urgent / excited / sincere / humorous / suspenseful / calm / neutral

### 7. BGM 配合 (bg_sync_note)
描述该 beat 中画面与 BGM 的配合关系，如"画面切换准确卡在重拍上"。

## 重要规则
1. ★ 你收到的视频片段向前多取了 0.5s（actual_start 到 end），请用 actual_start 作为真实时间基准
2. ★ ASR 词级时间戳给出了每个字出现的时间，是判断 Typewriter 特效的关键线索
3. 所有文字必须从画面中精确提取，不能概括或编造
4. 位置始终用百分比（中心=50/50）
5. 如果该 beat 没有特效/转场/卖点，对应字段留默认值"""

# 阶段2用户模板 — 变量由 analyzer.py 的 _analyze_single_beat() 填充
# {beat_id}:           beat序号
# {start_time}:        原始开始时间(秒)
# {end_time}:          原始结束时间(秒)
# {beat_duration}:     beat时长(秒)
# {beat_description}:  Phase 1给出的beat描述
# {actual_start_s}:    视频片段实际起始时间（向前多取了0.5s）
# {beat_asr_hint}:     该beat时间范围内的ASR词级时间戳
# {bpm}:               BGM节拍速度
# {bgm_mood}:          BGM情绪
# {resolution}:        视频分辨率
# {fps}:               帧率
PHASE2_USER_TEMPLATE = """请详细分析这个视频片段。

【Beat 信息】
- Beat #{beat_id}: {start_time:.1f}s — {end_time:.1f}s (时长 {beat_duration:.1f}s)
- 描述: {beat_description}
- ★ 视频片段实际起始时间: {actual_start_s:.1f}s（向前多取了0.5s用于看跨镜头转场）

【该 Beat 的 ASR 词级时间戳】
{beat_asr_hint}

【BGM 信息】
- BPM: {bpm} | 情绪: {bgm_mood}

【视频分辨率】{resolution} | FPS: {fps}

请输出该 beat 的完整分析 JSON。"""


# ═══════════════════════════════════════════════════════════════════
# 阶段3 — 跨 Beat 高层汇总
# 输入: 纯文本 — 脚本结构 + 所有beat分析摘要 + BGM特征
# 输出: 卖点策略分析 + 结构槽位模板 + 素材需求清单
# ═══════════════════════════════════════════════════════════════════

PHASE3_SYSTEM_PROMPT = """你是一位短视频策略分析专家。
你已看过视频所有 beat 的精细分析结果，现在需要从全局视角做高层策略汇总。

## 分析任务

### 1. 卖点策略分析 (selling_point_analysis)
- progression: 卖点推进逻辑 (progressive/parallel)
  - progressive = 卖点递进式展开（先讲功能→再讲体验→最后讲优惠）
  - parallel = 卖点并列展示（多个卖点是平级的）
- emphasized: 在视觉包装上被重点强调的卖点（最突出那个）
- density: 卖点密度 (appropriate/sparse/dense)

### 2. 结构槽位模板 (slot_template)
对脚本结构的每个段落，生成一个可复用的槽位。每个槽位包含：
- slot_id: 序号
- label: 功能标签（与脚本结构对应）
- duration: 建议时长(秒)
- required_material_type: video / image / text / voiceover
- visual_content_desc: 画面内容描述
- text_template: 文案模板（将具体品牌/人/数据替换为{占位符}）
- required_elements: 关键视觉元素清单
- alternative_if_missing: 缺失时的补全方案（具体可执行）
- migration_hint: 迁移到新内容时的创作建议

### 3. 素材需求清单 (material_requirements)
根据槽位生成素材需求，每个需求：
- type: video / image / text / voiceover
- description: 素材描述
- priority: high / medium / low
- can_generate: 是否可AIGC生成

## 重要规则
1. text_template 必须将具体品牌/人/数据替换为通用{占位符}
2. alternative_if_missing 必须是具体可执行的方案
3. migration_hint 要对新创作者有实际指导意义"""

# 阶段3用户模板 — 变量由 analyzer.py 的 analyze_phase3_summary() 填充
# {filename}:                视频文件名
# {duration}:                视频时长(秒)
# {resolution}:              视频分辨率
# {visual_style}:            Phase 1产出的视觉风格标签
# {rhythm_pattern}:          Phase 1产出的节奏模式标签
# {script_structure_json}:   脚本结构JSON
# {beats_json}:              所有beat的压缩摘要JSON（仅含卖点、情绪、转场）
# {bgm_json}:                BGM特征JSON（BPM、情绪、卡点匹配率）
PHASE3_USER_TEMPLATE = """请基于以下完整分析，做高层策略汇总。

【视频基础信息】
- 文件名: {filename} | 时长: {duration:.1f}s | 分辨率: {resolution}
- 视觉风格: {visual_style} | 节奏模式: {rhythm_pattern}

【脚本结构】
{script_structure_json}

【所有 Beat 详细分析】
{beats_json}

【BGM 特征】
{bgm_json}

请输出 selling_point_analysis、slot_template、material_requirements 的完整 JSON。"""


# ═══════════════════════════════════════════════════════════════════
# 辅助 Prompt 片段
# ═══════════════════════════════════════════════════════════════════

# 无语音提示 — 当ASR转写结果为空时，注入到阶段1用户提示词中
# 告诉LLM不要再找语音了，直接从画面读取文字
NO_ASR_HINT = """【注意】ASR转写结果为空，说明该视频没有旁白/人声。
请直接从视频画面中读取所有出现的文字内容，并按时间顺序组织为 beat 和段落结构。"""


def _format_asr_with_timestamps(segments: list[dict]) -> str:
    """格式化ASR片段为阶段1 LLM可读的文本

    将 faster-whisper 输出的 ASR 片段（含词级时间戳）
    格式化为自然可读的多行文本，每行包含:
      - 片段时间范围 [start-end]
      - 片段文本
      - 逐字时间戳（用于判断文字出现节奏）

    Args:
        segments: faster-whisper输出的片段列表，每个片段包含:
                  start/end(秒), text(文本), words(词级时间戳列表)

    Returns:
        格式化的多行字符串
    """
    if not segments:
        return "(无语音转写内容)"

    lines = []
    for seg in segments:
        start = seg.get("start", 0)  # 片段开始时间
        end = seg.get("end", 0)      # 片段结束时间
        text = seg.get("text", "")   # 片段文本
        words = seg.get("words")     # 词级时间戳列表 [{"word": "我", "start": 0.5}, ...]

        if words:
            # 有词级时间戳：格式化逐字时间信息
            word_parts = []
            for w in words:
                word_parts.append(f"{w['word']}({w['start']:.2f}s)")
            lines.append(f"[{start:.1f}s-{end:.1f}s] {text}")
            lines.append(f"  逐字: {' '.join(word_parts)}")
        else:
            lines.append(f"[{start:.1f}s-{end:.1f}s] {text}")

    return "\n".join(lines)


def _format_asr_for_beat(segments: list[dict], start_s: float, end_s: float) -> str:
    """提取单个beat时间范围内的ASR词级时间戳

    这是判断 Typewriter 打字机效果的关键线索:
      - 如果相邻字符间隔0.1-0.3s且均匀 → 大概率是Typewriter
      - 如果字符几乎同时出现 → 可能是fade_in/blur_reveal等整体动画
      - 如果没有语音 → 该beat可能是纯视觉/纯文字段落

    Args:
        segments: faster-whisper输出的所有片段
        start_s:  beat开始时间(秒)
        end_s:    beat结束时间(秒)

    Returns:
        该beat内的ASR词级时间戳文本（最多30个词，避免token超限）
    """
    if not segments:
        return "(该时间段内无语音)"

    # 展平该时间范围内的所有词
    all_words = []
    for seg in segments:
        words = seg.get("words")
        if words:
            for w in words:
                ws = w.get("start", 0)  # 词开始时间
                we = w.get("end", 0)    # 词结束时间
                # 词的任何部分与beat时间范围有重叠就算
                if we >= start_s and ws <= end_s:
                    all_words.append(f"  {ws:.2f}s: 「{w['word']}」")

    if not all_words:
        # 回退：如果没有词级数据，使用片段级数据
        for seg in segments:
            ss = seg.get("start", 0)
            se = seg.get("end", 0)
            if se >= start_s and ss <= end_s:
                all_words.append(f"  {ss:.1f}s-{se:.1f}s: {seg.get('text', '')}")

    if not all_words:
        return "(该时间段内无语音)"

    # 构造输出：先给出提示（教LLM如何判断），再列出词级时间戳
    lines = [
        "【ASR逐字时间戳 — 判断文字动画类型的关键线索】",
        "↓ 如果相邻字符间隔0.1-0.3s均匀 → 大概率是 Typewriter 打字机效果",
        "↓ 如果字符几乎同时出现 → 可能是 fade_in / blur_reveal 等整体动画",
    ]
    lines.extend(all_words[:30])  # 限制最多30个词
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# remocn 组件注入 — 追加到 Phase 2 系统提示词
# ═══════════════════════════════════════════════════════════════════

# 将59个remocn组件目录注入Phase 2系统提示词，
# 让LLM在分析特效时从目录中选择最匹配的组件名。
# {catalog_json} 由 _get_remocn_catalog() 填充为JSON数组，
# 每个元素为 {"name": "组件名", "desc": "组件描述"}
REMOCN_COMPONENTS_HINT = """
## 可用的 remocn 视觉组件库

以下是项目中已内置的 remocn 视觉组件列表。在分析 effects 时：
1. effects[].type 保持原有通用类型（typewriter / fade_in / blur_reveal / slide_in / bounce / scale / glow / highlight / static）
2. 新增 effects[].remocn_component 字段，从下方列表中选择最匹配的组件名（必须是列表中确切存在的名称，区分大小写）
3. 新增 effects[].remocn_props 字段，填写该组件推荐的关键参数（如 fontSize, charsPerSecond, intensity, blur, damping, stiffness 等）

{catalog_json}
"""
