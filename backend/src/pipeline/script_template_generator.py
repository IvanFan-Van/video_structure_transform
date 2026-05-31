import json


def build_script_template(structure: dict):

    placeholders = structure["global_placeholders"]

    template = {
        "hook": "什么东西比{{核心变量}}更值钱？",
        "answer_list": "{{常规答案列表}}",
        "twist": "{{反差爆点数字}}",
        "full_template": ["hook", "answers", "twist", "reinforce"],
        "placeholders": placeholders,
    }

    return template


def save_script_template(structure_path, output_path):

    with open(structure_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    template = build_script_template(structure)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=4)
