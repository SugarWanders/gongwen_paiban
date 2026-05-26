from __future__ import annotations

from app.models.settings import normalize_config_font_family


BUNDLED_FONT_SUFFIX = "（软件自带）"


def normalize_font_family(font_name: str) -> str:
    normalized = str(font_name).strip()
    if normalized.endswith(BUNDLED_FONT_SUFFIX):
        normalized = normalized[: -len(BUNDLED_FONT_SUFFIX)].strip()
    return normalize_config_font_family(normalized)


def display_font_name(font_name: str) -> str:
    return normalize_font_family(font_name)
