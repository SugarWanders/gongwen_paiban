import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.styles import build_stylesheet


WINDOW_BLUE = "#D7F95A"
WINDOW_TEXT = "#121712"

WINDOW_APP_ID = "gongwen.paiban.zhushou.v1_3_1.icon20260525r1"


def _apply_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    try:
        import ctypes

        # Keep the window correctly sized when it is opened on, or moved to,
        # monitors with different display scaling.
        per_monitor_v2 = ctypes.c_void_p(-4)
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(per_monitor_v2):
            return
    except Exception:
        pass

    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        return


def _apply_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOW_APP_ID)
    except Exception:
        return




def _apply_windows_title_bar_color(window) -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        DWMWA_BORDER_COLOR = 34
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020

        def _hex_to_colorref(hex_color: str) -> int:
            value = hex_color.lstrip("#")
            red = int(value[0:2], 16)
            green = int(value[2:4], 16)
            blue = int(value[4:6], 16)
            return blue << 16 | green << 8 | red

        hwnd = int(window.winId())
        border_color = ctypes.c_uint(_hex_to_colorref(WINDOW_BLUE))
        caption_color = ctypes.c_uint(_hex_to_colorref(WINDOW_BLUE))
        text_color = ctypes.c_uint(_hex_to_colorref(WINDOW_TEXT))

        dwmapi = ctypes.windll.dwmapi
        user32 = ctypes.windll.user32

        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR, ctypes.byref(border_color), ctypes.sizeof(border_color))
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_color), ctypes.sizeof(caption_color))
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_color), ctypes.sizeof(text_color))
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
    except Exception:
        return


def resource_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / name
    return Path(__file__).resolve().parents[1] / name


def main() -> int:
    _apply_windows_dpi_awareness()
    _apply_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("公文排版助手")
    app.setApplicationVersion("V1.3.1")
    app.setStyle("Fusion")
    app.setFont(QFont("\u65b9\u6b63\u5c0f\u6807\u5b8b\u7b80\u4f53", 10))
    app.setStyleSheet(build_stylesheet())

    icon_path = resource_path("icon.png")
    if not icon_path.exists():
        icon_path = resource_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    QTimer.singleShot(0, lambda: _apply_windows_title_bar_color(window))
    QTimer.singleShot(120, lambda: _apply_windows_title_bar_color(window))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
