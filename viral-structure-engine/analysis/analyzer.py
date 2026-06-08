"""四阶段 LLM 视频分析编排器 — Phase 1/2/3 的LLM调用和Beat后处理

本模块是分析管线的核心引擎，负责:
  Phase 1: 全视频宏观分析 — 发送完整视频base64+关键帧+ASR+BGM → LLM → beat边界+脚本结构
  Phase 2: 逐beat并发分析 — 线程池并发N个beat，每个发送视频片段+8帧密集关键帧 → LLM → 精细内容
  Phase 3: 跨beat高层汇总 — 纯文本LLM调用 → 卖点策略+槽位模板+素材需求
  Beat后处理: 切点吸附/首尾修正/间隙填充/短beat合并

核心技术:
  - instructor 库: 让LLM输出符合Pydantic模型的JSON（结构化输出）
  - JSON fallback: instructor失败时回退到原始JSON解析
  - ThreadPoolExecutor: 最多5路并发（max_workers参数控制）
  - remocn组件目录注入: 读取remocn_components.json注入Phase 2提示词
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import instructor
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from analysis.models import Phase1Output, Phase2Output, Phase3Output, BeatAnalysis
from analysis.preprocess import PreprocessResult
from analysis.prompts import (
    PHASE1_SYSTEM_PROMPT,
    PHASE1_USER_TEMPLATE,
    PHASE2_SYSTEM_PROMPT,
    PHASE2_USER_TEMPLATE,
    PHASE3_SYSTEM_PROMPT,
    PHASE3_USER_TEMPLATE,
    NO_ASR_HINT,
    REMOCN_COMPONENTS_HINT,
    _format_asr_with_timestamps,
    _format_asr_for_beat,
)
from analysis.video_utils import extract_video_clip, video_to_base64
from analysis.preprocess import extract_beat_keyframes

# 加载 .env 中的 API_KEY, BASE_URL, MODEL
load_dotenv(find_dotenv(), override=True)

# 全局缓存的客户端实例（避免重复创建）
_client: OpenAI | None = None                    # 原始OpenAI客户端（用于JSON fallback）
_instructor_client: instructor.Instructor | None = None  # instructor包装客户端（用于结构化输出）


def _get_clients():
    """懒加载获取OpenAI和instructor客户端实例

    全局缓存避免每次调用都创建新连接。
    """
    global _client, _instructor_client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("API_KEY"),     # 火山方舟Ark API Key
            base_url=os.getenv("BASE_URL"),   # 如 https://ark.cn-beijing.volces.com/api/v3
        )
        _instructor_client = instructor.from_openai(_client)  # 用instructor包装
    return _client, _instructor_client


def _build_image_blocks(base64_list: list[str]) -> list[dict]:
    """将base64图片列表转换为OpenAI Vision API的image_url内容块

    API 格式: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,...", "detail": "low"}}
    detail="low" 表示低分辨率模式（节省token），LLM只需要识别大致内容，不需要高清。
    """
    return [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}}
        for b64 in base64_list if b64
    ]


# 全局缓存的remocn组件目录（只读一次，避免每个beat都读文件）
_remocn_catalog: str | None = None


def _get_remocn_catalog() -> str:
    """加载59个remocn组件目录，缓存为JSON字符串

    从 remocn_components.json 读取所有组件的 name + description，
    转为紧凑JSON注入Phase 2系统提示词，让LLM自动匹配组件名。
    """
    global _remocn_catalog
    if _remocn_catalog is None:
        catalog_path = Path("remotion-video/src/components/remocn_components.json")
        if catalog_path.exists():
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            # 只取name和desc，去掉不必要的字段，减小token消耗
            _remocn_catalog = json.dumps(
                [{"name": c["name"], "desc": c.get("description", "")} for c in data],
                ensure_ascii=False,
            )
        else:
            _remocn_catalog = "[]"
    return _remocn_catalog


# ═══════════════════════════════════════════════════════════════════
# LLM 调用底层 — instructor + JSON fallback
# ═══════════════════════════════════════════════════════════════════


def _call_llm_with_instructor(messages: list[dict], response_model: type, max_tokens: int = 8192) -> dict:
    """使用 instructor 库调用LLM，强制返回符合 Pydantic 模型的结构化JSON

    instructor 在底层做:
      1. 自动在请求中添加 response_format 约束
      2. 校验返回的JSON是否符合 response_model 的字段定义
      3. 自动重试（如果返回格式不对）
      4. 输出转换为 Python dict（通过 model_dump()）

    如果 instructor 失败（通常是模型不支持 function calling），
    回退到 _call_llm_json_fallback() 做原始JSON解析。

    Args:
        messages:       标准 OpenAI 消息列表
        response_model: Pydantic 模型类（如 Phase1Output）
        max_tokens:     最大输出token数

    Returns:
        符合 response_model 结构的 dict
    """
    _, instructor_client = _get_clients()
    model = os.getenv("MODEL", "ep-20260508213828-7ntjl")

    try:
        response = instructor_client.chat.completions.create(
            model=model,
            response_model=response_model,  # Pydantic模型 → instructor自动校验
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.model_dump()  # Pydantic对象 → dict
    except Exception as e:
        print(f"    instructor 失败: {e}, 尝试 JSON 模式...")
        return _call_llm_json_fallback(messages, max_tokens)


def _call_llm_json_fallback(messages: list[dict], max_tokens: int = 8192) -> dict:
    """JSON回退方案 — 原始 completion 调用，手动提取JSON

    当 instructor 的结构化输出失败时使用。
    在最后一条user消息中追加"请只输出JSON"指令。
    解析时处理markdown代码块包裹的情况（```json ... ```）。
    """
    client, _ = _get_clients()
    model = os.getenv("MODEL", "ep-20260508213828-7ntjl")

    # 在最后一条用户消息中注入JSON输出指令
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += "\n\n请只输出JSON，不要加任何解释文字。"

    try:
        response = client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if content:
            content = content.strip()
            # 去除可能的markdown代码块包裹
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]  # 去掉首行 ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]  # 去掉末行 ```
                content = "\n".join(lines)
            return json.loads(content)  # 手动JSON解析
    except Exception as e2:
        print(f"    JSON 模式也失败: {e2}")
    return {}


# ═══════════════════════════════════════════════════════════════════
# A1: 全视频调用 — 发送完整视频 + 关键帧 + 文本
# ═══════════════════════════════════════════════════════════════════


def call_model_video(video_path: str, system_prompt: str, user_text: str,
                     image_base64_list: list[str] | None = None,
                     response_model: type = Phase1Output, max_tokens: int = 8192) -> dict:
    """Phase 1 专用：发送完整视频base64 + 可选关键帧 + 文本给LLM

    消息结构:
      system: PHASE1_SYSTEM_PROMPT
      user: [video, keyframes..., text]

    video_content是OpenAI Vision API的多模态格式:
      含 video_url（完整视频）+ image_url（关键帧）+ text（分析指令）
    """
    video_b64 = video_to_base64(video_path)  # 全视频编码为base64

    # 构建多模态 user content
    user_content: list[dict] = [
        {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}},
    ]

    # 追加关键帧（最多10张，减少token消耗）
    if image_base64_list:
        user_content.extend(_build_image_blocks(image_base64_list[:10]))

    user_content.append({"type": "text", "text": user_text})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    return _call_llm_with_instructor(messages, response_model, max_tokens)


# ═══════════════════════════════════════════════════════════════════
# A2: Beat 级调用 — 发送视频片段 + 8帧密集关键帧 + ASR片段
# ═══════════════════════════════════════════════════════════════════


def call_model_beat(video_path: str, start_s: float, end_s: float,
                    system_prompt: str, user_text: str,
                    output_dir: str | Path,
                    max_tokens: int = 4096) -> dict:
    """Phase 2 专用：发送单个beat的视频片段 + 8帧密集关键帧给LLM

    特殊处理:
      1. 视频片段向前延展0.5s（overlap_before=0.5）— 让LLM看到跨beat的转场
      2. 抽取8帧密集关键帧 — 覆盖beat从头到尾的视觉变化
      3. actual_start 注入结果 — 让LLM知道真实时间基准

    Args:
        video_path: 源视频路径
        start_s:    beat原始开始时间(秒)
        end_s:      beat原始结束时间(秒)
        system_prompt: Phase 2系统提示词（含remocn组件目录）
        user_text:  Phase 2用户模板填充后的文本
        output_dir: 输出目录
        max_tokens: 最大输出token数

    Returns:
        BeatAnalysis 模型的 dict 形式，额外包含 actual_start_s 字段
    """
    # 提取视频片段（向前0.5s overlap看转场）
    clip = extract_video_clip(video_path, start_s, end_s, overlap_before=0.5, overlap_after=0)
    clip_b64 = clip.get("clip_b64", "")          # 片段base64
    actual_start = clip.get("actual_start_s", start_s)  # 片段实际起始时间

    # 抽取8帧密集关键帧
    _, kf_b64s = extract_beat_keyframes(video_path, start_s, end_s, output_dir, num_keyframes=8)

    user_content: list[dict] = []

    if clip_b64:
        user_content.append({
            "type": "video_url",
            "video_url": {"url": f"data:video/mp4;base64,{clip_b64}"},
        })

    if kf_b64s:
        user_content.extend(_build_image_blocks(kf_b64s[:8]))  # 追加关键帧

    if not user_content:
        # 完全没有视觉内容 → 纯文本fallback
        user_content.append({"type": "text", "text": user_text})
    else:
        user_content.append({"type": "text", "text": user_text})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    # 使用 instructor function calling（无8KB限制）
    result = _call_llm_with_instructor(messages, BeatAnalysis, max_tokens)
    # 注入 actual_start（LLM用此字段校准时间基准）
    if isinstance(result, dict):
        result["actual_start_s"] = actual_start
    return result


# ═══════════════════════════════════════════════════════════════════
# Phase 1 — 全视频宏观分析
# ═══════════════════════════════════════════════════════════════════


def analyze_phase1_full_video(video_path: str, result: PreprocessResult) -> dict:
    """阶段1: 全视频宏观分析 — 1次LLM调用

    将完整视频 + ASR文本 + BGM数据 + 切点参考 → 发送给LLM，
    产出: beat边界、全局视觉风格、脚本结构、节奏模式。

    Args:
        video_path: 视频文件路径
        result:     Phase 0预处理的完整结果

    Returns:
        Phase1Output 模型的 dict，包含 beats/global_style/script_structure 等字段
    """
    print("\n" + "=" * 60)
    print("阶段1: 全视频宏观分析")
    print("=" * 60)

    # 格式化ASR词级时间戳
    asr_text = _format_asr_with_timestamps(result.asr_segments)
    no_asr = "" if result.asr_segments else NO_ASR_HINT  # 无语音时的提示

    # cv2切点作为参考锚点（不强制LLM对齐）
    cut_hint = ", ".join([f"{t:.1f}s" for t in result.shot_boundaries[:20]])
    if len(result.shot_boundaries) > 20:
        cut_hint += f"... (共{len(result.shot_boundaries)}个)"

    # BGM重拍采样（只发前15个，节省token）
    bt_sample = ", ".join([f"{t:.1f}s" for t in result.beat_timings[:15]])
    if len(result.beat_timings) > 15:
        bt_sample += f"..."

    # 填充用户模板
    user_text = PHASE1_USER_TEMPLATE.format(
        filename=result.filename,
        duration=result.duration,
        resolution=result.resolution,
        fps=result.fps,
        asr_text_with_timestamps=asr_text,
        no_asr_hint=no_asr,
        cut_points_hint=cut_hint if result.shot_boundaries else "(无切点数据)",
        bpm=result.bpm,
        bgm_mood=result.bgm_mood_hint,
        beat_timings_sample=bt_sample if result.beat_timings else "(无BGM数据)",
    )

    t0 = time.time()
    # 调用LLM（全视频 + 无额外关键帧 — 视频本身已包含所有视觉信息）
    raw = call_model_video(
        video_path, PHASE1_SYSTEM_PROMPT, user_text,
        image_base64_list=None,  # 全视频已足够
        response_model=Phase1Output,
    )

    beats = raw.get("beats", [])      # LLM划定的beat边界
    script = raw.get("script_structure", [])  # LLM识别的脚本结构
    elapsed = time.time() - t0
    print(f"  完成 ({elapsed:.1f}s): {len(beats)} 个beats, {len(script)} 段脚本")
    print(f"  视觉风格: {raw.get('visual_style', '?')} | 节奏模式: {raw.get('rhythm_pattern', '?')}")

    return raw


# ═══════════════════════════════════════════════════════════════════
# Phase 2 — 逐 Beat 精细分析（并发）
# ═══════════════════════════════════════════════════════════════════


def _analyze_single_beat(beat: dict, video_path: str, result: PreprocessResult,
                         run_dir: str | Path, beat_idx: int, total: int) -> dict:
    """分析单个beat — 在线程池中运行

    这是 Phase 2 的单个工作单元，被 ThreadPoolExecutor 并发调用。

    Args:
        beat:       Phase 1产出的beat dict（含start_time/end_time/description）
        video_path: 源视频路径
        result:     预处理结果
        run_dir:    运行目录
        beat_idx:   当前beat在列表中的索引
        total:      总beat数量

    Returns:
        BeatAnalysis dict，额外包含 _elapsed(耗时) 字段
    """
    start_s = beat.get("start_time", 0)
    end_s = beat.get("end_time", beat.get("start_time", 0) + 2)
    beat_desc = beat.get("description", f"Beat #{beat_idx + 1}")
    beat_duration = end_s - start_s  # beat时长

    # 该beat的ASR词级时间戳（LLM用于判断Typewriter特效）
    beat_asr = _format_asr_for_beat(result.asr_segments, start_s, end_s)

    # 填充Phase 2用户模板
    user_text = PHASE2_USER_TEMPLATE.format(
        beat_id=beat_idx + 1,
        start_time=start_s,
        end_time=end_s,
        beat_duration=beat_duration,
        beat_description=beat_desc,
        actual_start_s=max(0, start_s - 0.5),  # 视频片段实际起始时间
        beat_asr_hint=beat_asr,
        bpm=result.bpm,
        bgm_mood=result.bgm_mood_hint,
        resolution=result.resolution,
        fps=result.fps,
    )

    t0 = time.time()
    # 注入 remocn 组件目录到系统提示词
    phase2_prompt = PHASE2_SYSTEM_PROMPT + "\n" + REMOCN_COMPONENTS_HINT.format(
        catalog_json=_get_remocn_catalog()
    )
    raw = call_model_beat(
        video_path, start_s, end_s,
        phase2_prompt, user_text,
        run_dir,
    )

    # ── 补全默认值，防止LLM漏字段导致后续代码报错 ──
    raw.setdefault("text_elements", [])
    raw.setdefault("effects", [])
    raw.setdefault("transition_out", {
        "type": "hard_cut", "direction": "", "duration_frames": 0, "description": ""
    })
    raw.setdefault("editing_technique", "")
    raw.setdefault("selling_point", "")
    raw.setdefault("selling_strategy", "")
    raw.setdefault("emotion", "neutral")
    raw.setdefault("bg_sync_note", "")
    # 注入元数据（覆盖LLM可能的错误输出）
    raw["beat_id"] = beat_idx + 1
    raw["start_time"] = start_s
    raw["end_time"] = end_s
    raw["_elapsed"] = round(time.time() - t0, 1)  # 耗时
    return raw


def analyze_phase2_per_beats(beats: list[dict], video_path: str,
                              result: PreprocessResult, run_dir: str | Path,
                              max_workers: int = 5) -> list[dict]:
    """阶段2: 基于ThreadPoolExecutor的逐beat并发精细分析

    使用线程池并发发送N个LLM请求（每个beat独立分析），
    充分利用LLM API的并发能力（Volcengine Ark允许较高并发）。

    线程安全保证:
      - 每个beat使用独立的视频片段（不同时间范围）
      - 共享的 result 对象只读
      - _get_remocn_catalog() 内部有缓存

    Args:
        beats:       Phase 1产出的beat列表
        video_path:  源视频路径
        result:      预处理结果
        run_dir:     运行目录
        max_workers: 最大并发数(默认5)

    Returns:
        Phase 2分析结果列表（按beat_id排序）
    """
    total = len(beats)
    print("\n" + "=" * 60)
    print(f"阶段2: 逐 Beat 精细分析 (并发 ×{max_workers})")
    print("=" * 60)
    print(f"  共 {total} 个 beats, 并发数={max_workers}")

    beat_results: list[dict] = []
    completed = 0  # 已完成计数

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(_analyze_single_beat, b, video_path, result, run_dir, i, total): i
            for i, b in enumerate(beats)
        }

        # 用 as_completed 实时收集结果
        for future in as_completed(futures):
            try:
                bresult = future.result()
                beat_results.append(bresult)
                completed += 1
                elapsed = bresult.get("_elapsed", 0)
                remaining = (total - completed) * max(0.1, elapsed)  # 预计剩余时间
                print(f"  [{completed}/{total}] Beat #{bresult.get('beat_id', '?')} "
                      f"({bresult.get('start_time', 0):.1f}s-{bresult.get('end_time', 0):.1f}s) "
                      f"完成 ({elapsed:.1f}s) | 预计剩余 {remaining:.0f}s")
            except Exception as e:
                b_idx = futures[future]
                print(f"  [{completed + 1}/{total}] Beat #{b_idx + 1} 失败: {e}")
                # 失败时也记录一个占位结果，不影响整体流程
                beat_results.append({
                    "beat_id": b_idx + 1,
                    "start_time": beats[b_idx].get("start_time", 0),
                    "end_time": beats[b_idx].get("end_time", 0),
                    "error": str(e),
                })
                completed += 1

    # 按 beat_id 排序（并发完成顺序不定）
    beat_results.sort(key=lambda b: b.get("beat_id", 0))
    return beat_results


# ═══════════════════════════════════════════════════════════════════
# Phase 3 — 跨 Beat 高层汇总
# ═══════════════════════════════════════════════════════════════════


def _summarize_beats_for_phase3(beat_results: list[dict]) -> list[dict]:
    """压缩beat结果为Phase 3所需的最小信息

    Phase 3 做的是高层策略综合，不需要像素级的细节。
    只保留: selling_point、text_elements[].text、emotion、transition_out.type、editing_technique。
    去掉: 坐标位置、颜色、特效详情等精细字段，避免token爆炸。
    """
    summary = []
    for beat in beat_results:
        compressed = {
            "beat_id": beat.get("beat_id"),
            "start_time": beat.get("start_time"),
            "end_time": beat.get("end_time"),
            "text_elements": [
                {"text": e.get("text", "")}  # 只传文字内容，不要位置/颜色
                for e in beat.get("text_elements", [])
            ],
            "selling_point": beat.get("selling_point", ""),
            "selling_strategy": beat.get("selling_strategy", ""),
            "emotion": beat.get("emotion", "neutral"),
            "transition_out": {
                "type": beat.get("transition_out", {}).get("type", "hard_cut")
            },
            "editing_technique": beat.get("editing_technique", ""),
        }
        summary.append(compressed)
    return summary


def analyze_phase3_summary(result: PreprocessResult, phase1: dict,
                            beat_results: list[dict]) -> dict:
    """阶段3: 纯文本跨beat高层汇总 — 1次LLM调用（不传视频/图片）

    将所有beat的分析结果压缩后发给LLM，从策略层面总结:
      - 卖点推进逻辑（递进式 vs 并列式）
      - 可复用的结构槽位模板
      - 迁移所需素材需求清单

    Args:
        result:       预处理结果
        phase1:       阶段1的输出（视觉风格、节奏模式等）
        beat_results: 阶段2的输出（所有beat精细分析）

    Returns:
        Phase3Output 模型的 dict
    """
    print("\n" + "=" * 60)
    print("阶段3: 跨 Beat 高层汇总")
    print("=" * 60)

    user_text = PHASE3_USER_TEMPLATE.format(
        filename=result.filename,
        duration=result.duration,
        resolution=result.resolution,
        visual_style=phase1.get("visual_style", ""),
        rhythm_pattern=phase1.get("rhythm_pattern", ""),
        script_structure_json=json.dumps(phase1.get("script_structure", []), ensure_ascii=False, indent=2),
        beats_json=json.dumps(_summarize_beats_for_phase3(beat_results), ensure_ascii=False, indent=2),
        bgm_json=json.dumps({
            "bpm": result.bpm,
            "mood": result.bgm_mood_hint,
            "beat_sync_ratio": result.beat_sync_ratio,  # 卡点匹配率
        }, ensure_ascii=False),
    )

    messages = [
        {"role": "system", "content": PHASE3_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    t0 = time.time()
    raw = _call_llm_with_instructor(messages, Phase3Output, max_tokens=4096)
    elapsed = time.time() - t0

    slots = raw.get("slot_template", [])           # 槽位模板
    sp_analysis = raw.get("selling_point_analysis", {})  # 卖点策略分析
    print(f"  完成 ({elapsed:.1f}s): {len(slots)} 个槽位, "
          f"卖点策略={sp_analysis.get('progression', '?')}")

    return raw


# ═══════════════════════════════════════════════════════════════════
# Beat 边界后处理 — 4个步骤 (A6-A9)
# ═══════════════════════════════════════════════════════════════════


def snap_beats_to_cuts(beats: list[dict], cuts: list[float],
                        fps: float, threshold: float = 0.3) -> list[dict]:
    """A6-切点吸附: 将LLM的beat边界吸附到最近的cv2检测切点

    LLM 对时间的感知不是精确的，但其划定的beat通常对应一个镜头。
    通过将边界吸附到最近的cv2切点（≤0.3s），可以:
      - 消除LLM的时间估计误差
      - 确保beat边界与镜头边界对齐
      - 提高后续卡点分析的准确性

    Args:
        beats:     LLM输出的beat列表
        cuts:      cv2检测的镜头切点列表
        fps:       帧率
        threshold: 吸附距离阈值(秒)，默认0.3

    Returns:
        吸附后的beat列表
    """
    if not beats or not cuts:
        return beats

    cuts_sorted = sorted(set(cuts))  # 去重排序的切点列表
    adjusted = []
    snapped = 0  # 吸附成功的边界计数

    for beat in beats:
        b = dict(beat)
        start_s = b.get("start_time", 0)
        end_s = b.get("end_time", start_s + 2)

        # 找最近的切点
        nearest_start = min(cuts_sorted, key=lambda c: abs(c - start_s))
        nearest_end = min(cuts_sorted, key=lambda c: abs(c - end_s))

        # 如果距离在阈值内（且不是完全相同），吸附
        if abs(nearest_start - start_s) <= threshold and abs(nearest_start - start_s) > 0.01:
            b["start_time"] = round(nearest_start, 2)
            snapped += 1
        if abs(nearest_end - end_s) <= threshold and abs(nearest_end - end_s) > 0.01:
            b["end_time"] = round(nearest_end, 2)
            snapped += 1

        adjusted.append(b)

    if snapped:
        print(f"  [后处理] 切点吸附: {snapped} 处边界已校准 (阈值{threshold}s)")
    return adjusted


def ensure_first_last_beats(beats: list[dict], duration: float) -> list[dict]:
    """A7-首尾修正: 确保首个beat从0开始，末个beat覆盖到视频结尾

    LLM 有时会漏掉视频的最开始和最末尾（如封面的前0.5s），
    这会导致时间线有缺口。
    """
    if not beats:
        return []

    adjusted = list(beats)
    if adjusted[0].get("start_time", 0) > 0.1:
        adjusted[0]["start_time"] = 0.0  # 强制从0开始
        print(f"  [后处理] 首个beat起点修正为 0.0s")
    if adjusted[-1].get("end_time", 0) < duration - 0.5:
        adjusted[-1]["end_time"] = round(duration, 2)  # 强制到视频结尾
        print(f"  [后处理] 末个beat终点修正为 {duration:.1f}s")

    return adjusted


def fill_beat_gaps(beats: list[dict], duration: float) -> list[dict]:
    """A8-间隙填充: 自动填充相邻beat之间的时间空隙

    当两个相邻beat之间存在 >1.5s 的空隙时，插入一个填充beat。
    填充beat标记 _auto_filled=True（后续Phase 2会对其进行独立分析）。
    """
    if not beats:
        return []

    filled = []
    for i, beat in enumerate(beats):
        filled.append(dict(beat))
        if i < len(beats) - 1:
            curr_end = beat.get("end_time", 0)
            next_start = beats[i + 1].get("start_time", 0)
            gap = next_start - curr_end  # 间隙宽度
            if gap > 1.5:
                # 插入填充beat
                filler = {
                    "beat_id": 0,  # 临时ID，后续重新编号
                    "start_time": round(curr_end, 2),
                    "end_time": round(next_start, 2),
                    "description": f"[自动填充] {curr_end:.1f}s-{next_start:.1f}s 间隙",
                    "_auto_filled": True,  # 标记为自动填充
                }
                filled.append(filler)
                print(f"  [后处理] 填充间隙: {curr_end:.1f}s → {next_start:.1f}s ({gap:.1f}s)")

    # 尾部间隙检查
    if filled and filled[-1].get("end_time", 0) < duration - 1.5:
        filled.append({
            "beat_id": 0,
            "start_time": round(filled[-1]["end_time"], 2),
            "end_time": round(duration, 2),
            "description": f"[自动填充] 尾部 {filled[-1]['end_time']:.1f}s-{duration:.1f}s",
            "_auto_filled": True,
        })
        print(f"  [后处理] 填充尾部间隙")

    return filled


def merge_short_beats(beats: list[dict], min_duration: float = 1.0) -> list[dict]:
    """A9-合并短beat: 将时长不足1.0s的短beat合并到相邻beat

    LLM 有时会切出过短的beat（如0.5s的字幕突然弹出），
    这会导致Phase 2的视频片段太短无法分析。
    短beat合并到前一个beat，所有beat重新编号。
    """
    if len(beats) <= 1:
        return beats

    merged = []
    i = 0
    while i < len(beats):
        b = dict(beats[i])
        b_dur = b.get("end_time", 0) - b.get("start_time", 0)
        if b_dur < min_duration and merged:
            # 合并到前一个beat
            merged[-1]["end_time"] = b.get("end_time", merged[-1]["end_time"])
            merged[-1]["description"] += f" + [{b.get('description', '')}]"
            print(f"  [后处理] 合并短beat: {b['start_time']:.1f}s-{b['end_time']:.1f}s ({b_dur:.1f}s)")
        else:
            merged.append(b)
        i += 1

    # 重新编号
    for idx, b in enumerate(merged):
        b["beat_id"] = idx + 1

    return merged


def postprocess_beats(beats: list[dict], cuts: list[float],
                       duration: float, fps: float) -> list[dict]:
    """运行所有beat后处理步骤（A6→A7→A8→A9）

    处理顺序很重要:
      1. 先吸附到切点（精确化边界）
      2. 再修正首尾（保证覆盖完整时长）
      3. 然后填充间隙（消除时间空隙）
      4. 最后合并短beat（优化过碎的划分）
    """
    beats = snap_beats_to_cuts(beats, cuts, fps, threshold=0.3)
    beats = ensure_first_last_beats(beats, duration)
    beats = fill_beat_gaps(beats, duration)
    beats = merge_short_beats(beats, min_duration=1.0)
    return beats


# ═══════════════════════════════════════════════════════════════════
# 中间结果保存
# ═══════════════════════════════════════════════════════════════════


def save_intermediate_result(data: dict, filename: str, run_dir: str | Path) -> None:
    """保存分析中间结果为JSON文件（调试和追踪用）

    将每个阶段的分析结果保存为 intermediates/ 目录下的JSON文件，
    方便后续调试和定位问题。
    """
    intermediates_dir = Path(run_dir) / "intermediates"
    intermediates_dir.mkdir(parents=True, exist_ok=True)
    path = intermediates_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
