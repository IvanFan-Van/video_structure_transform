"""从 analysis_result.json 生成用户素材填写模板

本模块是 Phase 4 的最后一个步骤：分析完成后，自动生成一份
material_template.json 文件，用户填写后即可用于结构迁移。

模板包含:
  - 每个槽位的文案模板（含 {变量} 占位符）
  - 素材需求清单（哪些需要用户提供、哪些可以自动生成）
  - 填写说明（指导用户完成）

用户填写完后，直接将此文件另存为 transfer/new_content.json 即可进入迁移阶段。
"""

import json
import re
from pathlib import Path


def generate(analysis_path: str, output_dir: str | Path) -> str:
    """读取 analysis_result.json，生成素材清单模板 JSON 文件

    处理逻辑:
      1. 从 analysis_result.json 读取 slot_template（槽位列表）
      2. 从每个 slot 的 text_template 中提取 {变量名} 作为待填写字段
      3. 从 material_requirements 提取素材需求（标注哪些可AIGC生成）
      4. 组装为带填写指南的 JSON 模板

    Args:
        analysis_path: analysis_result.json 的完整路径
        output_dir:   输出目录（通常是 run_dir，如 output/20260607_134912/）

    Returns:
        生成的 material_template.json 路径
    """
    with open(analysis_path, encoding="utf-8") as f:
        analysis = json.load(f)

    slot_template = analysis.get("slot_template", [])        # LLM产出的槽位模板
    material_reqs = analysis.get("material_requirements", []) # LLM产出的素材需求
    video_info = analysis.get("video_info", {})               # 视频元数据

    # ── 为每个 slot 构建填写结构 ──
    # slots 字典的 key 是 label（如 "hook"），value 是包含 text/variables/素材路径的 dict
    slots = {}
    for slot in slot_template:
        label = slot.get("label", "")              # 槽位标签
        text_tmpl = slot.get("text_template", "")  # 文案模板

        # 从 text_template 中提取 {变量名} 占位符
        # 例如 "打开包装就能闻到{核心香气}" → ["核心香气"]
        var_names = re.findall(r"\{([^}]+)\}", text_tmpl)
        # 初始化为空字典，用户需填入实际值
        variables = {name: "" for name in var_names}

        # 每个 slot 的结构（用户需要填写的内容）
        slots[label] = {
            "text": "",           # 覆盖默认text_template的文案（可选，留空则用模板）
            "user_video": None,   # 用户视频素材路径（绝对路径，可选）
            "user_image": None,   # 用户图片素材路径（绝对路径，可选）
            "variables": variables, # 模板变量值（必须填写）
        }

    # ── 素材需求摘要（供用户参考哪些需要自己拍、哪些自动生成）──
    materials_needed = []
    for mr in material_reqs:
        materials_needed.append({
            "type": mr.get("type", "?"),                    # 素材类型
            "description": mr.get("description", ""),       # 素材描述
            "can_generate": mr.get("can_generate", False), # 是否可AIGC生成
        })

    # ── 组装最终模板 ──
    template = {
        "_source_analysis": str(Path(analysis_path).name),  # 来源分析文件名
        "_instructions": (
            "请编辑此文件，填写每个槽位的文案(text)、变量(variables)和素材路径(user_video/user_image)。\n"
            "素材路径请填写**绝对路径**（如 C:\\videos\\unboxing.mp4），运行 transfer 时会自动拷贝。\n"
            "填完后将此文件另存为 transfer/new_content.json 即可使用。"
        ),
        "theme": "替换为你的产品名",          # 新视频主题
        "target_audience": "替换为你的目标人群", # 目标受众
        "output_ratio": "9:16",              # 输出比例（默认9:16竖屏）
        "user_materials": ["text", "voiceover"], # 用户提供的素材类型（默认只有文字+语音）
        "voiceover_text": "",                # TTS旁白文案（留空则从slots自动拼接）
        "slots": slots,                      # 槽位填写区
        "material_requirements": materials_needed, # 素材需求参考
    }

    # ── 写入文件 ──
    output_dir = Path(output_dir)
    output_path = output_dir / "material_template.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    return str(output_path)
