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
        background: #A6B1A3;
        color: #151A15;
        font-family: "\u65b9\u6b63\u5c0f\u6807\u5b8b\u7b80\u4f53", "\u65b9\u6b63\u5c0f\u6807\u5b8b_GBK", "FZYaSong", "Microsoft YaHei UI", "Segoe UI";
        font-size: 8pt;
    }}

    QLabel {{
        background: transparent;
    }}

    QMainWindow, #root {{
        background: #A6B1A3;
    }}

    QSplitter::handle {{
        background: #A6B1A3;
    }}

    QAbstractScrollArea::corner {{
        background: #A6B1A3;
        border: none;
    }}

    #card {{
        background: #F4F7F1;
        border: 1px solid #CFD8CA;
        border-radius: 16px;
    }}

    #cardContent {{
        background: transparent;
        border: none;
    }}

    #settingsPanelCard {{
        background: #F4F7F1;
        border: 1px solid #CFD8CA;
        border-radius: 16px;
    }}

    QWidget#settingsContent {{
        background: transparent;
    }}

    QFrame#styleGroup {{
        background: transparent;
    }}

    #settingsContent QLabel,
    #settingsContent QPushButton,
    #settingsContent QLineEdit,
    #settingsContent QComboBox,
    #settingsContent QSpinBox {{
        font-size: 7pt;
    }}

    #settingsContent QLabel#sectionTitle {{
        font-size: 8.5pt;
    }}

    #settingsContent #styleBlock QLabel,
    #settingsContent #styleBlock QLineEdit,
    #settingsContent #styleBlock QComboBox,
    #settingsContent #styleBlock QSpinBox,
    #settingsContent #styleBlock QPushButton {{
        font-size: 6pt;
    }}

    #settingsContent #styleBlock QLabel#subSectionTitle {{
        font-size: 7.5pt;
        padding-left: 26px;
    }}

    #settingsContainer {{
        background: transparent;
        border: none;
    }}

    #styleBlock {{
        background: #CFE89A;
        border: 1px solid #B7D97A;
        border-radius: 10px;
    }}

    #styleBlock QLabel,
    #styleBlock QLineEdit,
    #styleBlock QComboBox,
    #styleBlock QSpinBox,
    #styleBlock QPushButton {{
        font-size: 7pt;
    }}

    #styleBlock QLabel#subSectionTitle {{
        font-size: 8.5pt;
    }}

    #styleDivider {{
        background: transparent;
        border: none;
        min-height: 0px;
        max-height: 0px;
    }}

    QLabel#sectionTitle {{
        font-size: 9.5pt;
        font-weight: 700;
        color: #141914;
        padding: 0 0 1px 0;
    }}

    QLabel#subSectionTitle {{
        font-size: 9.5pt;
        font-weight: 700;
        color: #1B231A;
        padding: 0;
    }}

    QLabel#mutedText {{
        color: #758173;
        font-size: 7.5pt;
    }}

    QPushButton {{
        background: #F8FBF5;
        color: #1A2318;
        border: 1px solid #BECBB7;
        border-radius: 10px;
        padding: 0 10px;
        font-weight: 600;
        min-height: 20px;
        max-height: 20px;
        text-align: center;
    }}

    QPushButton:hover {{
        background: #F1F6EB;
        border-color: #AEBFA4;
    }}

    QPushButton:pressed {{
        background: #E6EEDC;
    }}

    QPushButton#toolButton {{
        min-width: 52px;
        max-width: 52px;
    }}

    QPushButton#actionButton {{
        min-height: 20px;
        max-height: 20px;
        font-size: 8pt;
    }}

    QPushButton#pathButton {{
        min-width: 60px;
        max-width: 60px;
    }}

    QPushButton#toolButton, QPushButton#actionButton, QPushButton#pathButton {{
        background: #F8FBF5;
        color: #1A2318;
        border: 1px solid #BECBB7;
        border-radius: 10px;
        font-weight: 600;
    }}

    QPushButton#toolButton:hover, QPushButton#actionButton:hover, QPushButton#pathButton:hover {{
        background: #F1F6EB;
        border-color: #AEBFA4;
    }}

    QPushButton#primaryButton {{
        background: #000000;
        color: #FFFFFF;
        border: 1px solid #000000;
        font-weight: 700;
    }}

    QPushButton#primaryButton:hover {{
        background: #000000;
        color: #FFFFFF;
        border: 1px solid #000000;
    }}

    QPushButton#primaryButton:pressed {{
        background: #000000;
        color: #FFFFFF;
        border: 1px solid #000000;
    }}

    QMessageBox, QDialog {{
        background: #FFFFFF;
        color: #151A15;
    }}

    QMessageBox QLabel, QDialog QLabel {{
        background: transparent;
        color: #151A15;
    }}

    QMessageBox QPushButton, QDialog QPushButton {{
        background: #FFFFFF;
        color: #151A15;
        border: 1px solid #D7F95A;
        border-radius: 10px;
        padding: 0 10px;
        min-height: 20px;
        max-height: 20px;
        font-weight: 600;
    }}

    QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
        background: #D7F95A;
        color: #151A15;
        border: 1px solid #D7F95A;
    }}

    QMessageBox QPushButton:pressed, QDialog QPushButton:pressed {{
        background: #D7F95A;
        color: #151A15;
        border: 1px solid #D7F95A;
    }}

    QPlainTextEdit, QLineEdit, QComboBox, QSpinBox {{
        background: #FCFDFB;
        border: 1px solid #C5D0BF;
        border-radius: 10px;
        padding: 1px 6px;
        selection-background-color: #D7F95A;
        selection-color: #131713;
        color: #1B2219;
        min-height: 20px;
    }}

    QLineEdit, QSpinBox {{
        qproperty-alignment: AlignCenter;
    }}

    QComboBox {{
        padding: 0 16px 0 6px;
    }}

    QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid #AFC861;
        background: #FFFFFF;
    }}

    QPlainTextEdit {{
        background: #FBFDF9;
        font-size: 9pt;
        line-height: 1.55;
        border-radius: 14px;
        padding: 10px;
    }}

    QPlainTextEdit[editorState="default"] {{
        color: #A6B0A3;
    }}

    QPlainTextEdit[editorState="normal"] {{
        color: #1B2219;
    }}

    QLineEdit#pathField {{
        min-height: 20px;
        max-height: 20px;
    }}

    QComboBox#fontField {{
        min-width: 78px;
        max-width: 78px;
        min-height: 20px;
        max-height: 20px;
        padding: 0 16px 0 16px;
    }}

    QComboBox#sizeField {{
        min-width: 30px;
        max-width: 30px;
        min-height: 20px;
        max-height: 20px;
        padding: 0 0px 0 10px;
        font-size: 6pt;
    }}

    QComboBox#sizeField::drop-down {{
        width: 10px;
    }}

    QWidget#marginField, QWidget#lineField {{
        background: #FCFDFB;
        border: 1px solid #C5D0BF;
        border-radius: 10px;
        min-width: 45px;
        max-width: 45px;
        min-height: 22px;
        max-height: 22px;
    }}

    QLineEdit#spinValue {{
        background: transparent;
        border: none;
        color: #1B2219;
        padding: 0;
        min-height: 20px;
        max-height: 20px;
    }}

    QWidget#spinButtonBox {{
        background: transparent;
        border: none;
    }}

    QToolButton#spinUpButton,
    QToolButton#spinDownButton {{
        background: transparent;
        border: none;
        border-left: 1px solid #C5D0BF;
        padding: 0;
        margin: 0;
        min-width: 13px;
        max-width: 13px;
        min-height: 10px;
        max-height: 10px;
    }}

    QToolButton#spinUpButton {{
        border-bottom: 1px solid #DCE5D7;
        border-top-right-radius: 10px;
    }}

    QToolButton#spinDownButton {{
        border-bottom-right-radius: 10px;
    }}

    QToolButton#spinUpButton:hover,
    QToolButton#spinDownButton:hover {{
        background: #F0F6E9;
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







    QComboBox QAbstractItemView {{
        border: 1px solid #C5D0BF;
        background: #FFFFFF;
        color: #171D16;
        selection-background-color: #D7F95A;
        selection-color: #171D16;
        outline: 0;
    }}

    QComboBox QAbstractItemView::item:selected {{
        color: #171D16;
        background: #D7F95A;
    }}

    QComboBox QAbstractItemView::item:hover {{
        color: #171D16;
        background: #ECF6CC;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    QAbstractScrollArea::corner {{
        background: #A6B1A3;
        border: none;
    }}

    QStatusBar {{
        background: #A6B1A3;
        color: transparent;
        font-size: 7.5pt;
        border: none;
        min-height: 20px;
        max-height: 20px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    QStatusBar QLabel#statusMessage,
    QStatusBar QLabel#statusContact {{
        color: #758173;
        font-size: 7.5pt;
        min-height: 18px;
        max-height: 18px;
    }}

    QStatusBar QLabel#statusMessage {{
        padding: 0 0 0 11px;
        qproperty-alignment: AlignVCenter | AlignLeft;
    }}

    QStatusBar QLabel#statusContact {{
        padding: 0 19px 0 4px;
        qproperty-alignment: AlignVCenter | AlignRight;
    }}
    """




