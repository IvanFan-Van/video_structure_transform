import json


def build_design(structure: dict):

    prompt_data = structure["global_config"]

    design = {
        "visual_style": prompt_data["visual_style"],
        "audio_bgm_vibe": prompt_data["audio_bgm_vibe"],
        "design_system": {
            "primary_color": "auto_detected_or_black",
            "accent_color": "auto_detected_or_red",
            "font_family": "auto_detected_gothic",
            "transition_style": "glitch_flash",
            "animation_style": "fade_scale",
            "camera_style": "static",
        },
    }

    return design


def save_design(structure_path, output_path):

    with open(structure_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    design = build_design(structure)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(design, f, ensure_ascii=False, indent=4)
