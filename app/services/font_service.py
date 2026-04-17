from __future__ import annotations

from app.models.settings import COMMON_FONTS


def get_common_fonts() -> list[str]:
    return list(COMMON_FONTS)


def get_system_fonts() -> list[str]:
    from PySide6.QtGui import QFontDatabase

    database = QFontDatabase()
    return sorted(set(database.families()))
