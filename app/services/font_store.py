from __future__ import annotations

import json
import sys
from pathlib import Path


CONFIG_DIR_NAME = "config"
CONFIG_FILE_NAME = "font_preferences.json"
CUSTOM_FONTS_KEY = "custom_fonts"
REMOVED_FONTS_KEY = "removed_fonts"


def load_font_preferences() -> tuple[list[str], list[str]]:
    config_path = _get_config_path()
    if not config_path.exists():
        return [], []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return [], []

    custom_fonts = _normalize_font_list(data.get(CUSTOM_FONTS_KEY, []))
    removed_fonts = _normalize_font_list(data.get(REMOVED_FONTS_KEY, []))
    return custom_fonts, removed_fonts


def save_font_preferences(custom_fonts: list[str], removed_fonts: list[str]) -> Path:
    config_path = _get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        CUSTOM_FONTS_KEY: _normalize_font_list(custom_fonts),
        REMOVED_FONTS_KEY: _normalize_font_list(removed_fonts),
    }
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path


def _normalize_font_list(values: list[str] | tuple[str, ...] | object) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []

    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        font_name = value.strip()
        if font_name and font_name not in normalized:
            normalized.append(font_name)
    return normalized


def _get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parents[2]

    return base_dir / CONFIG_DIR_NAME / CONFIG_FILE_NAME
