from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


BUNDLED_FONT_SUFFIX = "（软件自带）"


@dataclass(frozen=True, slots=True)
class BundledFont:
    family: str
    file_name: str


BUNDLED_FONTS = (
    BundledFont("方正小标宋简体", "fangzheng_xiaobiaosong_jianti.ttf"),
    BundledFont("黑体", "simhei.ttf"),
    BundledFont("楷体_GB2312", "kaiti_gb2312.ttf"),
    BundledFont("仿宋_GB2312", "fangsong_gb2312.ttf"),
)

BUNDLED_FONT_FAMILIES = tuple(font.family for font in BUNDLED_FONTS)


def normalize_font_family(font_name: str) -> str:
    normalized = str(font_name).strip()
    if normalized.endswith(BUNDLED_FONT_SUFFIX):
        normalized = normalized[: -len(BUNDLED_FONT_SUFFIX)].strip()
    return normalized


def is_bundled_font(font_name: str) -> bool:
    return normalize_font_family(font_name) in BUNDLED_FONT_FAMILIES


def display_font_name(font_name: str) -> str:
    return normalize_font_family(font_name)


def bundled_font_paths() -> list[Path]:
    return [path for path in (_fonts_dir() / font.file_name for font in BUNDLED_FONTS) if path.exists()]


def register_bundled_fonts() -> list[str]:
    registered: list[str] = []
    for font_path in bundled_font_paths():
        registered.extend(_register_qt_font(font_path))
        _register_windows_session_font(font_path)
    _broadcast_windows_font_change()
    return registered


def _fonts_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "app" / "fonts"
    return Path(__file__).resolve().parents[1] / "fonts"


def _register_qt_font(font_path: Path) -> list[str]:
    try:
        from PySide6.QtGui import QFontDatabase
    except Exception:
        return []

    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id < 0:
        return []
    return list(QFontDatabase.applicationFontFamilies(font_id))


def _register_windows_session_font(font_path: Path) -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.gdi32.AddFontResourceExW(str(_session_font_path(font_path)), 0, None)
    except Exception:
        return


def _session_font_path(font_path: Path) -> Path:
    session_dir = Path(tempfile.gettempdir()) / "gongwen_paiban_fonts"
    session_dir.mkdir(parents=True, exist_ok=True)
    session_path = session_dir / font_path.name

    try:
        if not session_path.exists() or session_path.stat().st_size != font_path.stat().st_size:
            session_path.write_bytes(font_path.read_bytes())
    except OSError:
        return font_path

    return session_path


def _broadcast_windows_font_change() -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        hwnd_broadcast = 0xFFFF
        wm_fontchange = 0x001D
        send_abort_if_hung = 0x0002
        timeout_ms = 100
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            hwnd_broadcast,
            wm_fontchange,
            0,
            0,
            send_abort_if_hung,
            timeout_ms,
            ctypes.byref(result),
        )
    except Exception:
        return
