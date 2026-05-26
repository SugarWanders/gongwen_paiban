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
    checkmark_uri = _asset_uri("checkmark.svg")
    return f"""
    QWidget {{
        background: #A6B1A3;
        color: #151A15;
        font-family: "\u65b9\u6b63\u5c0f\u6807\u5b8b\u7b80\u4f53", "\u65b9\u6b63\u5c0f\u6807\u5b8b_GBK", "FZYaSong", "Microsoft YaHei UI", "Segoe UI";
        font-size: 10pt;
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
        font-size: 9pt;
    }}

    #settingsContent QLabel#sectionTitle {{
        font-size: 10.5pt;
    }}

    #settingsContent #styleBlock QLabel,
    #settingsContent #styleBlock QLineEdit,
    #settingsContent #styleBlock QComboBox,
    #settingsContent #styleBlock QSpinBox,
    #settingsContent #styleBlock QPushButton {{
        font-size: 8pt;
    }}

    #settingsContent #styleBlock QLabel#subSectionTitle {{
        font-size: 9.5pt;
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
        font-size: 9pt;
    }}

    #styleBlock QLabel#subSectionTitle {{
        font-size: 10.5pt;
    }}

    #styleDivider {{
        background: transparent;
        border: none;
        min-height: 0px;
        max-height: 0px;
    }}

    QLabel#sectionTitle {{
        font-size: 10.5pt;
        font-weight: 700;
        color: #141914;
        padding: 0 0 1px 0;
    }}

    QLabel#subSectionTitle {{
        font-size: 10.5pt;
        font-weight: 700;
        color: #1B231A;
        padding: 0;
    }}

    QLabel#mutedText {{
        color: #758173;
        font-size: 9.5pt;
    }}

    QPushButton {{
        background: #F8FBF5;
        color: #1A2318;
        border: 1px solid #BECBB7;
        border-radius: 10px;
        padding: 0 10px;
        font-weight: 600;
        min-height: 25px;
        max-height: 25px;
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
        min-width: 60px;
        max-width: 60px;
    }}

    QPushButton#actionButton {{
        min-height: 25px;
        max-height: 25px;
        font-size: 10pt;
    }}

    QPushButton#pathButton {{
        min-width: 76px;
        max-width: 76px;
        min-height: 25px;
        max-height: 25px;
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
        background: #5F7450;
        color: #FFFFFF;
        border: 1px solid #4A5D3E;
        font-weight: 700;
        min-height: 27px;
        max-height: 27px;
    }}

    QPushButton#primaryButton:hover {{
        background: #6C835B;
        color: #FFFFFF;
        border: 1px solid #5F7450;
    }}

    QPushButton#primaryButton:pressed {{
        background: #4E6042;
        color: #FFFFFF;
        border: 1px solid #405037;
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
        font-size: 11pt;
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
        min-height: 25px;
        max-height: 25px;
    }}

    QComboBox#fontField {{
        min-width: 122px;
        max-width: 122px;
        min-height: 25px;
        max-height: 25px;
        padding: 0 20px 0 20px;
    }}

    QComboBox#sizeField {{
        min-width: 41px;
        max-width: 41px;
        min-height: 25px;
        max-height: 25px;
        padding: 0 6px 0 12px;
        font-size: 8pt;
    }}

    QComboBox#sizeField::drop-down {{
        width: 14px;
    }}

    QWidget#marginField, QWidget#lineField {{
        background: #FCFDFB;
        border: 1px solid #C5D0BF;
        border-radius: 10px;
        min-width: 51px;
        max-width: 51px;
        min-height: 27px;
        max-height: 27px;
    }}

    QLineEdit#spinValue {{
        background: transparent;
        border: none;
        color: #1B2219;
        padding: 0;
        min-height: 27px;
        max-height: 27px;
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
        min-width: 15px;
        max-width: 15px;
        min-height: 13px;
        max-height: 13px;
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

    QDialog QLabel#focusStyleLabel {{
        color: #111711;
        font-weight: 700;
        padding: 0;
        min-height: 29px;
        max-height: 29px;
    }}

    QComboBox#focusFontField,
    QComboBox#focusSizeField {{
        background: #FCFDFB;
        border: 1px solid #C5D0BF;
        border-radius: 10px;
        color: #111711;
        font-weight: 700;
        min-height: 27px;
        max-height: 27px;
    }}

    QComboBox#focusFontField:focus,
    QComboBox#focusSizeField:focus {{
        border: 1px solid #AFC861;
        background: #FFFFFF;
    }}

    QCheckBox#focusBoldCheckbox {{
        background: transparent;
        border: none;
        color: #111711;
        font-weight: 700;
        padding: 0;
        spacing: 8px;
        min-height: 29px;
        max-height: 29px;
    }}

    QCheckBox#focusBoldCheckbox::indicator {{
        width: 27px;
        height: 27px;
        background: #FCFDFB;
        border: 1px solid #C5D0BF;
        border-radius: 10px;
    }}

    QCheckBox#focusBoldCheckbox::indicator:hover {{
        background: #FFFFFF;
        border: 1px solid #AFC861;
    }}

    QCheckBox#focusBoldCheckbox::indicator:checked {{
        image: url("{checkmark_uri}");
    }}

    QListWidget#dialogList {{
        background: #F7FAF4;
        border: 1px solid #D7E5D0;
        border-radius: 10px;
        color: #151A15;
        font-size: 10pt;
        outline: 0;
        padding: 4px;
        selection-background-color: #D7F95A;
        selection-color: #151A15;
    }}

    QListWidget#dialogList::item {{
        background: transparent;
        color: #151A15;
        min-height: 22px;
        padding: 2px 6px;
    }}

    QListWidget#dialogList::item:selected {{
        background: #D7F95A;
        color: #151A15;
    }}

    QListWidget#dialogList::item:hover {{
        background: #ECF6CC;
        color: #151A15;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    QWidget#transparentSlot {{
        background: transparent;
        border: none;
    }}

    QWidget#statusFooter {{
        background: #A6B1A3;
        border: none;
    }}

    QLabel#statusMessage,
    QLabel#statusContact {{
        background: transparent;
        color: #758173;
        font-size: 9.5pt;
        min-height: 16px;
    }}

    QLabel#statusMessage {{
        padding: 0;
    }}

    QLabel#statusContact {{
        padding: 0;
    }}

    QLabel#bodyTitleChar {{
        background: transparent;
        color: #1B231A;
        font-size: 10.5pt;
        font-weight: 700;
        padding: 0;
    }}

    QAbstractScrollArea::corner {{
        background: #A6B1A3;
        border: none;
    }}

    QStatusBar {{
        background: #A6B1A3;
        color: transparent;
        font-size: 9.5pt;
        border: none;
        min-height: 31px;
        max-height: 31px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    QStatusBar QLabel#statusMessage,
    QStatusBar QLabel#statusContact {{
        color: #758173;
        font-size: 9.5pt;
        min-height: 16px;
    }}

    QStatusBar QLabel#statusMessage {{
        padding: 0 0 0 11px;
        qproperty-alignment: AlignVCenter | AlignLeft;
    }}

    QStatusBar QLabel#statusContact {{
        padding: 0;
        qproperty-alignment: AlignVCenter | AlignRight;
    }}
    """




