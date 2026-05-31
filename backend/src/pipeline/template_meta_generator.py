import json


def build_meta(structure: dict):

    strategy = structure["production_strategy"]

    meta = {
        "template_type": strategy["video_category"],
        "requires_physical_shooting": strategy["requires_physical_shooting"],
        "asset_requirement": strategy["user_action_required"],
        "input_mode": "text_only"
        if not strategy["requires_physical_shooting"]
        else "hybrid",
    }

    return meta


def save_meta(structure_path, output_path):

    with open(structure_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    meta = build_meta(structure)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)
