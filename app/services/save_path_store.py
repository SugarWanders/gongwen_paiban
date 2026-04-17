from __future__ import annotations

import json
import sys
from pathlib import Path


CONFIG_DIR_NAME = "config"
CONFIG_FILE_NAME = "default_save_path.json"
DEFAULT_PATH_KEY = "default_save_path"


def load_default_save_path() -> str | None:
    config_path = _get_config_path()
    if not config_path.exists():
        return None

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None

    default_path = data.get(DEFAULT_PATH_KEY)
    if not isinstance(default_path, str):
        return None

    default_path = default_path.strip()
    return default_path or None


def save_default_save_path(default_path: str) -> Path:
    config_path = _get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {DEFAULT_PATH_KEY: default_path.strip()}
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path


def _get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parents[2]

    return base_dir / CONFIG_DIR_NAME / CONFIG_FILE_NAME
