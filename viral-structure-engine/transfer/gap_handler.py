"""素材缺口检测与补全策略

本模块负责:
  1. detect_gaps()  — 比对槽位所需素材类型 vs 用户拥有的素材类型，找出缺口
  2. apply_gap_fill() — 为有缺口的scene应用补全策略（纯色背景/AIGC生图/纯文字）

缺口类型和补全方案:
  - video缺失 → 降级为纯文字渲染 + 纯色背景（最可靠）
  - image缺失 → 优先尝试Agnes AIGC生图 → 失败则纯色背景
  - voiceover缺失 → 保留文字字幕（静音模式）

影响等级(impact)由槽位标签决定:
  - high:   hook, cta, pain_point, testimonial, product_show（核心转化段落）
  - medium: solution, usage_scene, comparison（辅助说明段落）
  - low:    offer, outro（非核心段落）
"""

import os
import time
from pathlib import Path

import requests

from .schema import GapItem, SceneProps
from .constants import LABEL_BG_COLORS


# 缺口影响级别：label 位置权重（优于素材类型权重）
# hook/cta的缺口影响视频点击率和转化率，必须标记为high
_LABEL_PRIORITY = {
    "hook":                 "high",
    "cta":                  "high",
    "pain_point":           "high",
    "testimonial":          "high",
    "product_show":         "high",   # 产品展示段落缺素材影响很大
    "solution":             "medium",
    "usage_scene":          "medium",
    "comparison":           "medium",
    "offer":                "low",
    "outro":                "low",
    "outro_platform_guide": "low",
}


def detect_gaps(slot_template: list[dict], user_materials: list[str]) -> list[GapItem]:
    """检测素材缺口

    遍历每个槽位，检查 required_material_type 是否在 user_materials 中。
    text 始终算作可用（所有槽位都可以用纯文字渲染兜底）。

    Args:
        slot_template:   analysis_result.json 中的 slot_template 列表
        user_materials:  用户声明的素材类型如 ["text","voiceover"]

    Returns:
        GapItem 列表，按影响等级排序（high > medium > low）
    """
    user_set = set(user_materials)
    user_set.add("text")  # 文字始终可用（兜底）

    type_impact = {"video": "high", "image": "medium", "voiceover": "medium", "text": "low"}

    gaps = []
    for slot in slot_template:
        required = slot.get("required_material_type", "text")
        if required in user_set:
            continue  # 用户有这种素材，跳过

        label = slot.get("label", "")
        # label 位置权重优先于素材类型权重
        impact = _LABEL_PRIORITY.get(label) or type_impact.get(required, "medium")

        gaps.append(GapItem(
            slot_id=slot["slot_id"],
            label=label,
            missing_type=required,
            impact=impact,
            strategy=slot.get("alternative_if_missing", ""),  # LLM推荐的补全策略
            filled=False,
            fill_method="",
        ))

    # 按影响等级排序: high(0) > medium(1) > low(2)
    order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: order.get(g.impact, 1))
    return gaps


def _try_generate_image(prompt: str, output_dir: str) -> str | None:
    """调用 Agnes AI 图像生成API，生成产品背景图

    这是 image 缺口的"锦上添花"方案。若成功，pic直接用作背景；
    若失败（API不可用/配额不足/网络问题），回退到纯色背景。

    Args:
        prompt:     生图提示词（中英文均可）
        output_dir: 保存目录（remotion-video/public/）

    Returns:
        成功→生成的文件名，失败→None
    """
    api_key = os.getenv("AGNES_API_KEY")
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
    model = os.getenv("AGNES_IMAGE_MODEL", "agnes-image-2.0-flash")

    if not api_key:
        print("  [AIGC] AGNES_API_KEY 未配置，跳过生图")
        return None

    safe_prompt = prompt[:500]  # 截断过长prompt
    if not safe_prompt.strip():
        return None

    try:
        # 调用Agnes图片生成API
        resp = requests.post(
            f"{base_url}/images/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "prompt": f"{safe_prompt}，竖版构图",  # 追加竖版构图指令
                "size": "1024x1792",                    # 9:16竖版尺寸
                "n": 1,                                 # 只生成1张
            },
            timeout=120,  # 生图通常需要较长时间
        )
        if resp.status_code != 200:
            print(f"  [AIGC] 图片生成失败 (HTTP {resp.status_code}): {resp.text[:200]}")
            return None

        data = resp.json()
        img_url = (data.get("data") or [{}])[0].get("url")  # 获取图片URL
        if not img_url:
            print("  [AIGC] 响应中无图片 URL")
            return None

        # 下载生成的图片
        img_resp = requests.get(img_url, timeout=60)
        img_resp.raise_for_status()

        filename = f"aigc_{int(time.time())}.png"  # 时间戳命名，避免冲突
        save_path = Path(output_dir) / filename
        save_path.write_bytes(img_resp.content)

        print(f"  [AIGC] 图片生成完成: {filename} ({len(img_resp.content)} bytes)")
        return filename

    except Exception as e:
        print(f"  [AIGC] 图片生成异常: {e}")
        return None


def apply_gap_fill(
    scene: SceneProps,
    gap: GapItem,
    slot: dict,
    theme: str = "",
    filled_text: str = "",
) -> SceneProps:
    """将缺口补全策略写入scene（in-place修改并返回）

    补全优先级（按可行性排序）:
      1. 纯文字渲染（text_only）— 无需任何素材，Remotion直接渲染
      2. 纯色背景 + 文字（color_bg）— 使用LABEL_BG_COLORS映射的背景色
      3. AIGC图片（aigc_image）— 仅当missing_type=image且Agnes API可用
      4. 结构重排建议（reorder）— 仅标记，由前端提示用户

    Args:
        scene:       当前场景对象
        gap:         对应的缺口项
        slot:        原始槽位数据（含visual_content_desc等）
        theme:       新视频主题（用于AIGC prompt）
        filled_text: 填充后的文案

    Returns:
        修改后的scene对象
    """
    label = gap.label
    scene.gapFilled = True  # 标记已触发补全
    scene.backgroundColorFallback = LABEL_BG_COLORS.get(label, "#0D0D0D")

    if gap.missing_type == "video":
        # 视频缺失 → 降级为纯文字渲染 + 纯色背景（最可靠的兜底）
        scene.gapStrategy = "color_bg+text"
        scene.fill_method = "color_bg"
        scene.type = _downgrade_scene_type(scene.type)  # 场景类型降级

    elif gap.missing_type == "image":
        # 图片缺失 → 优先尝试AIGC生图
        base_desc = slot.get("visual_content_desc", "") or slot.get("text_template", "")
        prompt_parts = [p for p in [base_desc, f"产品：{theme}" if theme else "", filled_text[:40]] if p.strip()]
        prompt = "，".join(prompt_parts) + "，竖版构图，高质量"

        public_dir = str(Path(__file__).resolve().parent.parent / "remotion-video" / "public")
        generated = _try_generate_image(prompt, public_dir)
        if generated:
            # AIGC成功
            scene.backgroundImage = generated
            scene.gapStrategy = "aigc_image"
            scene.fill_method = "aigc_image"
            gap.filled = True
            gap.fill_method = "aigc_image"
            return scene

        # AIGC失败 → 回退到纯色背景
        scene.gapStrategy = "color_bg+text"
        scene.fill_method = "color_bg"

    elif gap.missing_type == "voiceover":
        # 语音缺失 → 纯文字字幕模式（用户没提供语音，保留字幕即可）
        scene.gapStrategy = "text_subtitle_only"
        scene.fill_method = "text_only"

    gap.filled = True
    gap.fill_method = scene.fill_method
    return scene


def _downgrade_scene_type(original_type: str) -> str:
    """将需要视频素材的scene type降级为纯文字渲染版本

    remocn_composed 比较特殊——它本身就可以纯文字渲染（组件不依赖背景），
    所以降级时保持不变。
    """
    downgrade_map = {
        "curiosity_text":   "text_overlay",   # 好奇心钩子 → 普通文字叠加
        "contrast_reveal":  "text_overlay",   # 对比揭露 → 普通文字叠加
        "value_list":       "value_list",     # 价值列表 → 保持不变
        "product_centric":  "emphasis_text",  # 产品展示 → KenBurns强调文字
        "usage_scene":      "value_list",     # 使用场景 → 价值列表
        "comparison_card":  "text_overlay",   # 对比卡片 → 普通文字
        "testimonial_card": "text_overlay",   # 证言卡片 → 普通文字
        "offer_card":       "text_overlay",   # 优惠卡片 → 普通文字
        "cta_card":         "text_overlay",   # CTA卡片 → 普通文字
        "emphasis_text":    "emphasis_text",  # 强调文字 → 保持不变
        "remocn_composed":  "remocn_composed", # remocn组合 → 保持不变
    }
    return downgrade_map.get(original_type, "text_overlay")
