from __future__ import annotations

import os
import re
from pathlib import Path

from app.models.settings import COMMON_FONTS


FONT_REGISTRY_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
FONT_FILE_EXTENSIONS = {".ttf", ".ttc", ".otf", ".fon", ".fnt"}
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")
REGISTRY_SUFFIX_PATTERN = re.compile(r"\s*\((?:TrueType|OpenType|All Resolutions)\)$", re.IGNORECASE)


def get_common_fonts() -> list[str]:
    return list(COMMON_FONTS)


def get_system_fonts() -> list[str]:
    from PySide6.QtGui import QFontDatabase

    database = QFontDatabase()
    return sorted(set(database.families()), key=_font_sort_key)


def get_installed_font_candidates() -> list[str]:
    candidates = _read_windows_font_registry()
    if candidates:
        return candidates

    return _read_fonts_directory_fallback()


def _read_windows_font_registry() -> list[str]:
    if os.name != "nt":
        return []

    try:
        import winreg
    except ImportError:
        return []

    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    font_map: dict[str, str] = {}

    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            registry_key = winreg.OpenKey(hive, FONT_REGISTRY_KEY)
        except OSError:
            continue

        try:
            value_count = winreg.QueryInfoKey(registry_key)[1]
            for index in range(value_count):
                try:
                    value_name, value_data, _ = winreg.EnumValue(registry_key, index)
                except OSError:
                    continue

                if not isinstance(value_data, str):
                    continue

                normalized_name = _normalize_font_name(value_name)
                if not normalized_name or normalized_name.startswith("@"):
                    continue

                font_path = Path(value_data)
                if not font_path.is_absolute():
                    font_path = fonts_dir / value_data

                if font_path.suffix.lower() not in FONT_FILE_EXTENSIONS:
                    continue

                if normalized_name not in font_map:
                    font_map[normalized_name] = str(font_path)
        finally:
            winreg.CloseKey(registry_key)

    return sorted(font_map.keys(), key=_font_sort_key)


def _read_fonts_directory_fallback() -> list[str]:
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if not fonts_dir.exists():
        return []

    names: list[str] = []
    for font_file in fonts_dir.iterdir():
        if font_file.suffix.lower() not in FONT_FILE_EXTENSIONS:
            continue
        font_name = font_file.stem.strip()
        if font_name and font_name not in names:
            names.append(font_name)

    return sorted(names, key=_font_sort_key)


def _normalize_font_name(value: str) -> str:
    return REGISTRY_SUFFIX_PATTERN.sub("", value).strip()


def _font_sort_key(name: str) -> tuple[int, str]:
    return (0 if CHINESE_PATTERN.search(name) else 1, name.lower())
