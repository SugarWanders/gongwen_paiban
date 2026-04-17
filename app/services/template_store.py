from __future__ import annotations

import json
import sys
from pathlib import Path

from app.models.settings import DEFAULT_TEMPLATE, TemplateConfig, template_from_dict, template_to_dict


CONFIG_DIR_NAME = "config"
CONFIG_FILE_NAME = "default_template.json"


def load_default_template() -> TemplateConfig:
    config_path = _get_config_path()
    if not config_path.exists():
        return DEFAULT_TEMPLATE

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_TEMPLATE

    try:
        return template_from_dict(data)
    except (TypeError, ValueError):
        return DEFAULT_TEMPLATE


def save_default_template(template: TemplateConfig) -> Path:
    config_path = _get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(template_to_dict(template), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path


def _get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parents[2]

    return base_dir / CONFIG_DIR_NAME / CONFIG_FILE_NAME
