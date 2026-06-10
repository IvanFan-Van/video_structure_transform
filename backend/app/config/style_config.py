from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "styles.yaml"

_STYLES_CACHE: dict | None = None


def _load_styles() -> dict:
    global _STYLES_CACHE
    if _STYLES_CACHE is None:
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                data: dict = yaml.safe_load(f)
        except Exception:
            data = {}
        _STYLES_CACHE = data or {}
    return _STYLES_CACHE


def get_available_styles() -> list[dict]:
    raw = _load_styles().get("styles", {})
    return [
        {
            "name": name,
            "label": cfg.get("label", name),
            "description": cfg.get("description", ""),
        }
        for name, cfg in raw.items()
    ]


def get_style_config(name: str) -> dict | None:
    return _load_styles().get("styles", {}).get(name)


__all__ = ["get_available_styles", "get_style_config"]
