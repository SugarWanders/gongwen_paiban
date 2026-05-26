from __future__ import annotations

import json
import sys
from pathlib import Path

from app.models.settings import (
    DEFAULT_FOCUS_FIELD_CONFIG,
    FocusFieldConfig,
    focus_field_config_from_dict,
    focus_field_config_to_dict,
)


CONFIG_DIR_NAME = "config"
CONFIG_FILE_NAME = "focus_fields.json"


def load_focus_field_config() -> FocusFieldConfig:
    config_path = _get_config_path()
    if not config_path.exists():
        return DEFAULT_FOCUS_FIELD_CONFIG

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_FOCUS_FIELD_CONFIG

    try:
        return focus_field_config_from_dict(data)
    except (AttributeError, TypeError, ValueError):
        return DEFAULT_FOCUS_FIELD_CONFIG


def save_focus_field_config(config: FocusFieldConfig) -> Path:
    config_path = _get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(focus_field_config_to_dict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path


def _get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parents[2]

    return base_dir / CONFIG_DIR_NAME / CONFIG_FILE_NAME
