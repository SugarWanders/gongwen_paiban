from pathlib import Path
import sys


def _asset_uri(name: str) -> str:
    if getattr(sys, "frozen", False):
        asset_path = Path(getattr(sys, "_MEIPASS")) / "app" / "ui" / "assets" / name
    else:
        asset_path = Path(__file__).resolve().parent / "assets" / name
    return asset_path.as_posix()


def build_stylesheet() -> str:
    arrow_uri = _asset_uri("down-arrow.svg")
    spin_up_arrow_uri = _asset_uri("up-arrow.svg")
    spin_down_arrow_uri = _asset_uri("down-arrow.svg")
    return f"""
    QWidget {{
        background: #EFF5FF;
        color: #18304F;
        font-family: "SF Pro Display", "Segoe UI", "Microsoft YaHei UI";
        font-size: 8pt;
    }}

    QLabel {{
        background: transparent;
    }}

    QMainWindow, #root {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #F8FBFF,
            stop: 0.56 #EEF5FF,
            stop: 1 #E4F0FF
        );
    }}

    #card {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #FFFFFF,
            stop: 1 #F4F9FF
        );
        border: 1px solid #D5E3F6;
        border-radius: 16px;
    }}

    #softCard {{
        background: #F7FBFF;
        border: 1px solid #DCE9F8;
        border-radius: 14px;
    }}

    #styleBlock {{
        background: transparent;
        border: none;
        border-radius: 0;
    }}

    QLabel#sectionTitle {{
        font-size: 9.5pt;
        font-weight: 700;
        color: #143257;
        padding: 0 0 1px 0;
    }}

    QLabel#subSectionTitle {{
        font-size: 9.5pt;
        font-weight: 700;
        color: #16355B;
        padding: 0;
    }}

    QLabel#mutedText {{
        color: #7E91AA;
        font-size: 7.5pt;
    }}

    QLabel#footerHint {{
        color: #A8B5C7;
        font-size: 7.5pt;
        padding: 0 4px 0 4px;
        min-height: 12px;
    }}

    QPushButton {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #FFFFFF,
            stop: 1 #F2F8FF
        );
        color: #153254;
        border: 1px solid #C8DBF1;
        border-radius: 10px;
        padding: 1px 6px;
        font-weight: 600;
        min-height: 12px;
        text-align: center;
    }}

    QPushButton:hover {{
        background: #F7FBFF;
        border-color: #9DBDE6;
    }}

    QPushButton:pressed {{
        background: #E8F2FF;
    }}

    QPushButton#primaryButton:pressed {{
        background: #5AA7FF;
        border: 1px solid #5AA7FF;
    }}

    QPushButton#toolButton {{
        min-width: 52px;
        max-width: 52px;
        min-height: 20px;
        max-height: 20px;
    }}

    QPushButton#actionButton {{
        min-height: 20px;
        max-height: 20px;
    }}

    QPushButton#pathButton {{
        min-width: 76px;
        max-width: 76px;
        min-height: 20px;
        max-height: 20px;
    }}

    QPushButton#primaryButton {{
        background: #5AA7FF;
        color: #FFFFFF;
        border: 1px solid #5AA7FF;
        min-height: 20px;
        max-height: 20px;
    }}

    QPushButton#primaryButton:hover {{
        background: #5AA7FF;
        border: 1px solid #5AA7FF;
    }}

    QPlainTextEdit, QLineEdit, QComboBox, QSpinBox {{
        background: #FFFFFF;
        border: 1px solid #D1E0F3;
        border-radius: 10px;
        padding: 1px 6px;
        selection-background-color: #C7E0FF;
        selection-color: #173252;
        color: #18304F;
        min-height: 12px;
    }}

    QLineEdit, QSpinBox {{
        qproperty-alignment: AlignCenter;
    }}

    QComboBox {{
        padding: 0 16px 0 6px;
    }}

    QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid #6EAFFF;
        background: #FFFFFF;
    }}

    QPlainTextEdit {{
        background: #FCFEFF;
        font-size: 9pt;
        line-height: 1.55;
        border-radius: 14px;
        padding: 10px;
    }}

    QPlainTextEdit[editorState="default"] {{
        color: #A8B5C7;
    }}

    QPlainTextEdit[editorState="normal"] {{
        color: #163056;
    }}

    QLineEdit#pathField {{
        min-height: 20px;
        max-height: 20px;
    }}

    QComboBox#fontField {{
        min-width: 92px;
        max-width: 92px;
        min-height: 20px;
        max-height: 20px;
    }}

    QComboBox#sizeField {{
        min-width: 40px;
        max-width: 40px;
        min-height: 20px;
        max-height: 20px;
    }}

    QSpinBox#marginField, QSpinBox#lineField {{
        min-width: 36px;
        max-width: 36px;
        min-height: 20px;
        max-height: 20px;
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 13px;
        border: none;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: url("{arrow_uri}");
        width: 9px;
        height: 5px;
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border;
        width: 13px;
        background: transparent;
        border: none;
    }}

    QSpinBox::up-button {{
        subcontrol-position: top right;
        border-left: 1px solid #D1E0F3;
        border-bottom: 1px solid #E2ECF8;
        border-top-right-radius: 10px;
    }}

    QSpinBox::down-button {{
        subcontrol-position: bottom right;
        border-left: 1px solid #D1E0F3;
        border-bottom-right-radius: 10px;
    }}

    QSpinBox::up-arrow {{
        image: url("{spin_up_arrow_uri}");
        width: 9px;
        height: 5px;
    }}

    QSpinBox::down-arrow {{
        image: url("{spin_down_arrow_uri}");
        width: 9px;
        height: 5px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background: #F5FAFF;
    }}

    QComboBox QAbstractItemView {{
        border: 1px solid #D1E0F3;
        background: #FFFFFF;
        color: #18304F;
        selection-background-color: #E8F2FF;
        selection-color: #18304F;
        outline: 0;
    }}

    QComboBox QAbstractItemView::item:selected {{
        color: #18304F;
        background: #E8F2FF;
    }}

    QComboBox QAbstractItemView::item:hover {{
        color: #18304F;
        background: #F2F8FF;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QStatusBar {{
        background: transparent;
        color: #7289A6;
        font-size: 7.5pt;
    }}
    """
