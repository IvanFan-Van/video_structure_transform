"""最终输出组装器 — Phase 4 规则统计 + 组合输出

本模块接收 Phase 0/1/2/3 的所有数据和产出，通过纯代码规则
（不涉及LLM）计算派生统计量，组装为最终的 analysis_result.json。

核心任务 (AS1-AS8):
  AS1: 卖点汇总 — 从所有beat中收集 non-empty selling_point
  AS2: 转场类型分布 — 统计各类型转场的出现次数
  AS3: 包装主导类型 — 判断视频主要靠什么视觉类型支撑
  AS4: 卡点同步数据 — 构建BGM卡点对齐的JSON结构
  AS5: 节奏结构 — 派生节拍频率曲线、高端位置等
  AS6: 最终组装 — 将所有数据拼接为完整JSON
  AS7: 槽位规则兜底 — 当LLM槽位模板为空时，用规则从脚本结构推导
  AS8: 素材缺口分析 — 比对槽位需求 vs 用户素材（纯集合运算）

产出: analysis_result.json — 供 transfer 模块使用的完整分析结果
"""

import json
from pathlib import Path

from analysis.preprocess import PreprocessResult


# ═══════════════════════════════════════════════════════════════════
# AS1: 卖点汇总 — 从所有beat收集中非空的selling_point
# ═══════════════════════════════════════════════════════════════════


def aggregate_selling_points(beat_results: list[dict]) -> list[dict]:
    """收集所有beat中的卖点信息，按时间排序

    Phase 2 中每个beat的 selling_point 字段如果非空，
    表示该beat在向观众传递一个产品卖点（如"酥脆口感"）。

    Returns:
        [{"text": 卖点内容, "time": 出现时间, "strategy": 卖点策略, "beat_id": beat编号}, ...]
    """
    points = []
    for beat in beat_results:
        sp = beat.get("selling_point", "")
        if sp and sp.strip():
            points.append({
                "text": sp.strip(),
                "time": beat.get("start_time", 0),         # 卖点出现时间
                "strategy": beat.get("selling_strategy", ""), # 策略分类
                "beat_id": beat.get("beat_id", 0),         # 所在beat
            })

    points.sort(key=lambda p: p["time"])  # 按时间排序
    return points


# ═══════════════════════════════════════════════════════════════════
# AS2: 转场类型分布 — 统计各类型转场的出现次数
# ═══════════════════════════════════════════════════════════════════


def compute_transition_distribution(beat_results: list[dict]) -> dict:
    """统计所有beat中转场类型的分布

    每个beat的 transition_out.type 表示该beat结束时使用的转场。
    硬切(hard_cut)通常最多，特效转场(glitch/wipe)更能体现包装水平。

    Returns:
        {"hard_cut": N, "fade": N, "slide": N, "zoom": N, "glitch": N, "wipe": N, "other": N}
    """
    dist = {"hard_cut": 0, "fade": 0, "slide": 0, "zoom": 0, "glitch": 0, "wipe": 0, "other": 0}

    for beat in beat_results:
        to = beat.get("transition_out", {})
        if isinstance(to, dict):
            ttype = to.get("type", "hard_cut")
            if ttype in dist:
                dist[ttype] += 1
            else:
                dist["other"] += 1  # 不在已知类型中的都归入other
    return dist


# ═══════════════════════════════════════════════════════════════════
# AS3: 包装主导类型 — 判断视频的主要视觉支撑类型
# ═══════════════════════════════════════════════════════════════════


def compute_packaging_dominance(beat_results: list[dict]) -> dict:
    """统计每个beat的包装主导类型

    启发式判断逻辑:
      - subtitle_heavy: 有底部字幕（position_y>80）+ 至少2个文字元素
      - title_led: 有大号/超大号标题
      - person_led: 文字中含"人"/"脸"关键词（人物出镜视频）
      - product_centric: 其他情况（默认）

    Returns:
        {"primary": "subtitle_heavy", "distribution": {"subtitle_heavy": 3, ...}}
    """
    dist = {"subtitle_heavy": 0, "title_led": 0, "person_led": 0, "product_centric": 0, "mixed": 0}

    for beat in beat_results:
        tes = beat.get("text_elements", [])
        if not tes:
            dist["mixed"] += 1
            continue

        # 启发式检查
        has_subtitle = any("字幕" in e.get("text", "") or
                          ("position_y" in e and e.get("position_y", 50) > 80)
                          for e in tes)  # 底部文字→字幕
        has_title = any(e.get("font_size", "small") in ("large", "xlarge")
                       for e in tes)  # 大号字→标题
        has_person = any("人" in e.get("text", "") or "脸" in e.get("text", "")
                        for e in tes)  # 文字含人物关键词

        if has_subtitle and len(tes) >= 2:
            dist["subtitle_heavy"] += 1  # 字幕密集型
        elif has_title:
            dist["title_led"] += 1       # 标题主导型
        elif has_person:
            dist["person_led"] += 1      # 人物出镜型
        else:
            dist["product_centric"] += 1 # 产品展示型

    # 取最大值作为主要类型
    primary = max(dist, key=dist.get) if dist else "mixed"

    return {"primary": primary, "distribution": {k: v for k, v in dist.items() if v > 0}}


# ═══════════════════════════════════════════════════════════════════
# AS4: 卡点同步数据 — 构建bgm_features中的beat_alignments字段
# ═══════════════════════════════════════════════════════════════════


def build_beat_alignment(result: PreprocessResult) -> dict:
    """从预处理结果构建卡点对齐JSON

    数据来源: Phase 0 中 compute_beat_sync_ratio() 的计算结果。
    """
    return {
        "match_rate": result.beat_sync_ratio,              # 卡点匹配率
        "typical_offset": result.beat_sync_typical_offset,  # 典型偏移(秒)
        "matched_count": result.beat_sync_matched_count,   # 匹配切点数
        "total_cuts": result.beat_sync_total_cuts,         # 总切点数
    }


# ═══════════════════════════════════════════════════════════════════
# AS5: 节奏结构 — 派生统计（不存原始数据）
# ═══════════════════════════════════════════════════════════════════


def _compute_shot_frequency_curve(result: PreprocessResult) -> list[float]:
    """计算每秒镜头数量曲线

    用途: 可视化节奏变化——快节奏段落每秒有多次切镜，慢节奏段落可能0切。

    Returns:
        [sec0的切镜数, sec1的切镜数, ...]
    """
    if result.duration <= 0:
        return []
    boundaries = result.shot_boundaries
    curve = []
    for sec in range(int(result.duration) + 1):
        count = sum(1 for b in boundaries if sec <= b < sec + 1)  # 落入第sec秒的切点数
        curve.append(round(count, 2))
    return curve


def build_rhythm_structure(result: PreprocessResult, phase1: dict,
                            transition_dist: dict, beat_results: list[dict] | None = None) -> dict:
    """构建节奏结构（纯派生字段，不存原始LLM数据）

    快节奏判定: beat时长 ≤ 2.0秒
    高潮判定: 特效数量 + 情绪强度 最大的beat中点位置
    """
    fast_segments = []        # 快节奏段落列表
    climax_pos = 0.0          # 高潮位置(秒)
    max_excitement = 0        # 最大兴奋度得分

    if beat_results:
        for b in beat_results:
            dur = b.get("end_time", 0) - b.get("start_time", 0)
            if dur <= 2.0:
                fast_segments.append({
                    "start": b.get("start_time", 0),
                    "end": b.get("end_time", 0),
                    "avg_duration": round(dur, 2),
                })
            # 高潮判定 = 特效数 + 情绪强度
            # excited=3分, urgent/suspenseful=2分, curious=1分, 其他=0分
            effects_count = len(b.get("effects", []))
            emotion_score = {"excited": 3, "urgent": 2, "suspenseful": 2, "curious": 1}.get(
                b.get("emotion", ""), 0)
            score = effects_count + emotion_score
            if score > max_excitement:
                max_excitement = score
                climax_pos = (b.get("start_time", 0) + b.get("end_time", 0)) / 2  # beat中点

    return {
        "avg_shot_duration": round(result.avg_shot_duration, 2),
        "shot_frequency_curve": _compute_shot_frequency_curve(result),
        "rhythm_pattern": phase1.get("rhythm_pattern", ""),
        "fast_segments": fast_segments,
        "climax_position": round(climax_pos, 2),
        "transition_type_distribution": transition_dist,
        "beat_timestamps": result.shot_boundaries,
        "cut_timestamps": result.shot_boundaries,
    }


# ═══════════════════════════════════════════════════════════════════
# AS6: 最终组装 — 将所有数据拼接为完整JSON
# ═══════════════════════════════════════════════════════════════════


def _build_video_info(result: PreprocessResult, phase1: dict, pkg_dominance: dict) -> dict:
    """构建 video_info 块 — 视频基础信息+视觉分析汇总"""
    cover_style = phase1.get("global_style", {}).get("cover_style", "")
    if not cover_style:
        # 回退：取第一个beat的描述作为封面风格
        beats_data = phase1.get("beats", [])
        if beats_data:
            first_desc = beats_data[0].get("description", "")
            if first_desc:
                cover_style = first_desc

    return {
        "filename": result.filename,
        "duration": round(result.duration, 2),
        "resolution": result.resolution,
        "fps": result.fps,
        "codec": result.codec,
        "shot_count": result.shot_count,
        "asr_text": result.asr_segments,           # 完整ASR转写（含词级时间戳）
        "asr_summary": phase1.get("asr_summary", ""), # LLM生成的50字摘要
        "cover_style": cover_style,
        "language": phase1.get("language", result.language),
        "visual_style": phase1.get("visual_style", ""),
        "packaging_dominance": pkg_dominance,
        "caption_density_label": _density_label(result), # 字幕密度标签
    }


def _density_label(result: PreprocessResult) -> str:
    """根据字幕密度返回语义化标签"""
    density = result.subtitle_density  # 条/分钟
    if density > 30:
        return "high"     # 高频字幕
    elif density > 15:
        return "medium"   # 中等字幕
    elif density > 0:
        return "low"      # 低频字幕
    return "none"         # 无字幕


def _build_script_structure(phase1: dict, video_duration: float = 0) -> list[dict]:
    """构建脚本结构块 — 从 Phase 1 输出清洗+补全

    如果所有 segment 的时间都是0（LLM漏填），则均匀分配到视频时长。
    """
    segments = phase1.get("script_structure", [])
    cleaned = []
    for seg in segments:
        cleaned.append({
            "label": seg.get("label", "unknown"),
            "start_time": seg.get("start_time", 0),
            "end_time": seg.get("end_time", 0),
            "text": seg.get("text", ""),
            "keywords": seg.get("keywords", []),
            "visual_hint": seg.get("visual_hint", ""),
            "emotion": seg.get("emotion", "neutral"),
            "hook_type": seg.get("hook_type", ""),
            "cta_type": seg.get("cta_type", ""),
        })

    # 时间补全：如果全部时间为0，均匀分配
    if cleaned and all(s["start_time"] == 0 and s["end_time"] == 0 for s in cleaned):
        duration = video_duration
        if duration <= 0:
            beats = phase1.get("beats", [])
            if beats:
                duration = max(b.get("end_time", 0) for b in beats)
        if duration <= 0:
            duration = 20.0  # 兜底：默认20秒

        chunk = duration / len(cleaned)
        for i, s in enumerate(cleaned):
            s["start_time"] = round(i * chunk, 1)
            s["end_time"] = round((i + 1) * chunk, 1)

    return cleaned


def _build_packaging_structure(phase1: dict, beat_results: list[dict]) -> dict:
    """构建包装结构块 — 字幕样式、标题条、贴纸等

    优先从 Phase 2 beat text_elements 读取真实数据，
    Phase 2 为空时从 visual_style 推断 fallback。
    """
    subtitle_style = {}
    cover_style = phase1.get("global_style", {}).get("cover_style", "")

    # 从beat text_elements读取字幕样式
    # 筛选策略: 排除顶部水印(position_y < 15)，取底部元素作为字幕参考
    for beat in beat_results:
        tes = beat.get("text_elements", [])
        if tes:
            non_watermark = [e for e in tes if e.get("position_y", 0) >= 15]  # 过滤顶部水印
            candidates = non_watermark if non_watermark else tes
            # 取 position_y 最大的（最底部的）
            best = max(candidates, key=lambda e: e.get("position_y", 0))
            subtitle_style = {
                "position_x": best.get("position_x", 50),
                "position_y": best.get("position_y", 50),
                "color": best.get("color", "#FFFFFF"),
                "font_size_hint": best.get("font_size", "medium"),
                "animation": "see beats[].effects[] for details",
            }
            break

    # Phase 2为空时的 fallback（从visual_style推断）
    if not subtitle_style:
        visual_style = phase1.get("visual_style", "mixed")
        position_y_map = {
            "subtitle_heavy": 82,  # 字幕密集型 — 底部82%
            "person_led": 82,      # 人物出镜型 — 底部82%
            "product_centric": 75, # 产品展示型 — 偏上75%
            "mixed": 82,           # 混合型 — 底部82%
        }
        subtitle_style = {
            "position_x": 50,
            "position_y": position_y_map.get(visual_style, 50),
            "color": "#FFFFFF",
            "font_size_hint": "large",
            "animation": "fade_in",
        }

    return {
        "subtitle_density": 0,
        "subtitle_style": subtitle_style,
        "title_card_timings": [],
        "sticker_timings": [],
        "cover_style": cover_style,
    }


def _build_bgm_features(result: PreprocessResult) -> dict:
    """构建BGM特征块"""
    beat_times = result.beat_timings[:50] if len(result.beat_timings) > 50 else result.beat_timings
    return {
        "bpm": result.bpm,
        "mood": result.bgm_mood_hint,
        "beat_timings": beat_times,  # 最多50个重拍时间点
        "beat_alignments": build_beat_alignment(result),
    }


def _build_summary(phase1: dict, script_structure: list[dict],
                    beat_results: list[dict], pkg_dominance: dict) -> str:
    """生成中文可读摘要字符串"""
    parts = []
    labels = [s["label"] for s in script_structure]
    parts.append(f"脚本结构: {' → '.join(labels)}。")

    primary = pkg_dominance.get("primary", "?")
    parts.append(f"视觉主导类型: {primary}。")

    rp = phase1.get("rhythm_pattern", "")
    if rp:
        parts.append(f"节奏模式: {rp}。")

    if beat_results:
        parts.append(f"共 {len(beat_results)} 个 beat 详细分析。")

    return "".join(parts)


def assemble_final_output(result: PreprocessResult, phase1: dict,
                           beat_results: list[dict], phase3: dict) -> dict:
    """组装最终 analysis_result.json（Phase 4 主函数）

    将 Phase 0/1/2/3 的所有数据按固定 schema 组装。
    最终JSON包含16个顶层字段。

    Returns:
        完整的 analysis_result dict，写入 analysis_result.json
    """
    print("\n" + "=" * 60)
    print("阶段4: 组装最终输出")
    print("=" * 60)

    # AS1: 卖点
    selling_points = aggregate_selling_points(beat_results)
    # AS2: 转场分布
    transition_dist = compute_transition_distribution(beat_results)
    # AS3: 包装主导类型
    pkg_dominance = compute_packaging_dominance(beat_results)
    # AS8: 缺口分析（纯代码计算）
    slots = phase3.get("slot_template", [])
    gap_analysis = compute_gap_analysis(slots)

    final = {
        "video_info": _build_video_info(result, phase1, pkg_dominance),
        "script_structure": _build_script_structure(phase1, result.duration),
        "rhythm_structure": build_rhythm_structure(result, phase1, transition_dist, beat_results),
        "packaging_structure": _build_packaging_structure(phase1, beat_results),
        "bgm_features": _build_bgm_features(result),
        "beats": beat_results,               # Phase 2 完整输出
        "selling_points": selling_points,     # AS1 汇总
        "selling_point_analysis": phase3.get("selling_point_analysis", {}),  # Phase 3 策略分析
        "slot_template": slots,               # Phase 3 槽位模板
        "material_requirements": phase3.get("material_requirements", []),    # Phase 3 素材需求
        "gap_analysis": gap_analysis,         # AS8 缺口分析
        "_summary": _build_summary(phase1, _build_script_structure(phase1, result.duration), beat_results, pkg_dominance),
    }

    print(f"  最终输出: {len(_build_script_structure(phase1, result.duration))}段脚本, "
          f"{len(beat_results)}个beat, {len(slots)}个槽位, "
          f"{len(selling_points)}个卖点, {len(gap_analysis)}个缺口")
    return final


# ═══════════════════════════════════════════════════════════════════
# AS7: 槽位规则兜底 — LLM槽位模板为空时的后备方案
# ═══════════════════════════════════════════════════════════════════


def _derive_slots_from_script(segments: list[dict]) -> list[dict]:
    """从脚本结构用规则推导槽位模板

    当 Phase 3 LLM 的 slot_template 不完整/为空时，
    用预定义的策略映射表从 script_structure 生成槽位。

    每个label有对应的:
      - mat: 所需素材类型
      - elems: 关键视觉元素
      - alt: 缺失时的补全方案
      - mig: 迁移建议
    """
    strategies = {
        "hook":       {"mat": "video", "elems": ["视觉冲击画面"], "alt": "用大字报标题图+音效代替", "mig": "新钩子可用竞品对比、反常识数据或痛点提问替代"},
        "pain_point": {"mat": "video", "elems": ["情景再现"], "alt": "用文字列表+配音列举痛点", "mig": "挖掘新主题的1-3个核心痛点"},
        "solution":   {"mat": "video", "elems": ["产品/方案展示"], "alt": "用产品图+功能卡片代替", "mig": "突出新方案的独特卖点"},
        "product_show":{"mat": "video", "elems": ["产品特写/演示"], "alt": "用产品图+卖点标签+转场动画代替", "mig": "展示新产品的核心功能"},
        "usage_scene":{"mat": "video", "elems": ["使用场景"], "alt": "用分步示意图+文字代替", "mig": "展示新产品在真实场景中的使用"},
        "comparison": {"mat": "image", "elems": ["对比图"], "alt": "用数据图表+文字卡片代替", "mig": "准备前后对比或数据对比"},
        "testimonial":{"mat": "text",  "elems": ["用户评价"], "alt": "用评分数据+用户头像代替", "mig": "收集真实评价或数据证明"},
        "offer":      {"mat": "text",  "elems": ["优惠信息"], "alt": "用大字报展示优惠信息", "mig": "填写新产品的优惠方案"},
        "cta":        {"mat": "text",  "elems": ["引导语+按钮"], "alt": "用动态文字+箭头引导代替", "mig": "根据转化目标设计CTA话术"},
        "outro":      {"mat": "text",  "elems": ["品牌logo"], "alt": "用品牌色背景+logo代替", "mig": "加入新品牌logo和期待话术"},
    }

    slots = []
    for i, seg in enumerate(segments):
        label = seg.get("label", "unknown")
        s = strategies.get(label, {"mat": "video", "elems": ["对应画面"], "alt": "用文字+图片组合代替", "mig": "根据新内容调整"})
        text = seg.get("text", "")
        # 文本模板：取前15字 + 可替换标记
        template = text[:15] + "...{可替换}" if len(text) > 15 else "{可替换内容}"

        slots.append({
            "slot_id": i + 1,
            "label": label,
            "duration": round(seg.get("end_time", 3) - seg.get("start_time", 0), 1),
            "required_material_type": s["mat"],
            "visual_content_desc": seg.get("visual_hint", text[:80]),
            "text_template": template,
            "required_elements": s["elems"],
            "alternative_if_missing": s["alt"],
            "migration_hint": s["mig"],
        })

    return slots


# ═══════════════════════════════════════════════════════════════════
# AS8: 素材缺口分析 — 纯代码集合差集运算
# ═══════════════════════════════════════════════════════════════════


def compute_gap_analysis(slots: list[dict],
                          user_materials: list[str] | None = None) -> list[dict]:
    """计算素材缺口 — 比对槽位需求 vs 用户素材（纯集合运算）

    逻辑:
      1. 对每个 slot，检查 required_material_type 是否在 user_materials 中
      2. 不在 → 记录为缺口
      3. impact 影响级别 = max(label 位置权重, 素材类型权重)
         - hook/cta/pain_point 的缺口一定是 high
      4. 按影响级别排序返回

    Args:
        slots:         从LLM或规则生成的槽位模板
        user_materials: 用户提供的素材类型列表，如 ["text","voiceover"]，None表示仅有text

    Returns:
        缺口列表，按 impact 排序（high > medium > low）
    """
    if user_materials is None:
        user_materials = ["text"]  # 默认：用户只有文字

    user_set = set(user_materials)
    impact_order = {"video": "high", "image": "medium", "voiceover": "medium", "text": "low"}

    gaps = []
    for slot in slots:
        required = slot.get("required_material_type", "text")
        if required not in user_set:
            # 基础影响级别：由素材类型决定
            impact = impact_order.get(required, "medium")
            # hook/cta 缺口强制提升为 high
            if slot.get("label") in ("hook", "cta") and impact != "high":
                impact = "high"
            gaps.append({
                "slot_id": slot.get("slot_id", 0),
                "label": slot.get("label", "unknown"),
                "missing_type": required,
                "impact": impact,
                "alternative_if_missing": slot.get("alternative_if_missing", ""),
            })

    # 按影响级别排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: priority_order.get(g["impact"], 1))

    return gaps


# ═══════════════════════════════════════════════════════════════════
# 文件保存
# ═══════════════════════════════════════════════════════════════════


def save_final_output(output: dict, run_dir: str | Path) -> str:
    """保存最终的 analysis_result.json 到 run_dir"""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / "analysis_result.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n最终结果已保存: {output_path}")
    return str(output_path)
