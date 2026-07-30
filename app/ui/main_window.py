from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    QSplitter,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import (
    DEFAULT_FOCUS_FIELDS,
    DEFAULT_TEMPLATE,
    FocusFieldConfig,
    HAO_TO_PT,
    MarginConfig,
    TemplateConfig,
    TextStyleConfig,
)
from app.services.document_importer import import_text_document
from app.services.bundled_fonts import (
    display_font_name,
    normalize_font_family,
)
from app.services.export_service import export_docx_document
from app.services.focus_field_store import load_focus_field_config, save_focus_field_config
from app.services.font_service import get_common_fonts, get_installed_font_candidates
from app.services.font_store import load_font_preferences, save_font_preferences
from app.services.save_path_store import clear_default_save_path, load_default_save_path, save_default_save_path
from app.services.template_store import load_default_template, save_default_template
from app.services.title_classifier import classify_paragraphs
from app.ui.styles import _asset_uri


WINDOW_SIZE = QSize(1030, 613)
PANEL_HEIGHT = 572
SETTINGS_PANEL_WIDTH = 390
STATUS_FOOTER_HEIGHT = 31
STATUS_TEXT_HEIGHT = 16
STATUS_TEXT_TOP = 7
STATUS_TEXT_SIDE_MARGIN = 7
BODY_TITLE_LEFT_PADDING = 6
BODY_TITLE_ZHENG_SHIFT = -4
BODY_TITLE_WEN_SHIFT = -6
LINE_UNIT_SHIFT = -6
STATUS_MESSAGE_SHIFT = 3


class AlignedSpinBox(QWidget):
    valueChanged = Signal(int)

    def __init__(self, minimum: int, maximum: int, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._value = minimum

        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(53, 29)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.line_edit = QLineEdit(str(minimum))
        self.line_edit.setObjectName("spinValue")
        self.line_edit.setValidator(QIntValidator(minimum, maximum, self))
        self.line_edit.setFrame(False)
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_edit.setTextMargins(0, 0, 0, 0)
        self.line_edit.editingFinished.connect(self._commit_text)

        button_box = QWidget()
        button_box.setObjectName("spinButtonBox")
        button_box.setFixedWidth(15)

        up_icon = QIcon(_asset_uri("up-arrow.svg"))
        down_icon = QIcon(_asset_uri("down-arrow.svg"))

        button_layout = QVBoxLayout(button_box)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.up_button = QToolButton()
        self.up_button.setObjectName("spinUpButton")
        self.up_button.setIcon(up_icon)
        self.up_button.setIconSize(QSize(10, 6))
        self.up_button.setAutoRaise(True)
        self.up_button.setFixedSize(15, 13)
        self.up_button.clicked.connect(self.step_up)

        self.down_button = QToolButton()
        self.down_button.setObjectName("spinDownButton")
        self.down_button.setIcon(down_icon)
        self.down_button.setIconSize(QSize(10, 6))
        self.down_button.setAutoRaise(True)
        self.down_button.setFixedSize(15, 13)
        self.down_button.clicked.connect(self.step_down)

        button_layout.addWidget(self.up_button)
        button_layout.addWidget(self.down_button)

        layout.addWidget(self.line_edit, 1)
        layout.addWidget(button_box, 0)

    def setRange(self, minimum: int, maximum: int) -> None:
        self._minimum = minimum
        self._maximum = maximum
        self.line_edit.setValidator(QIntValidator(minimum, maximum, self))
        self.setValue(self._value)

    def setValue(self, value: int) -> None:
        bounded = max(self._minimum, min(self._maximum, int(value)))
        changed = bounded != self._value
        self._value = bounded
        self.line_edit.setText(str(bounded))
        if changed:
            self.valueChanged.emit(bounded)

    def value(self) -> int:
        self._commit_text()
        return self._value

    def setAlignment(self, alignment: Qt.AlignmentFlag) -> None:
        self.line_edit.setAlignment(alignment)

    def step_up(self) -> None:
        self.setValue(self._value + 1)

    def step_down(self) -> None:
        self.setValue(self._value - 1)

    def _commit_text(self) -> None:
        raw = self.line_edit.text().strip()
        try:
            parsed = int(raw)
        except ValueError:
            parsed = self._value
        self.setValue(parsed)


class ClickableComboBox(QComboBox):
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def eventFilter(self, watched, event):
        if watched is self.lineEdit() and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.showPopup()
                event.accept()
                return True
        return super().eventFilter(watched, event)


class FontSelectionDialog(QDialog):
    def __init__(
        self,
        title: str,
        description: str,
        options: list[str],
        parent: QWidget | None = None,
        *,
        multi_select: bool = True,
        mark_bundled_fonts: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(360, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setObjectName("mutedText")

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("dialogList")
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if multi_select
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        for option in options:
            normalized_option = normalize_font_family(option)
            item_text = display_font_name(normalized_option) if mark_bundled_fonts else normalized_option
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, normalized_option)
            self.list_widget.addItem(item)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        if not options:
            self.list_widget.setEnabled(False)
            ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setEnabled(False)

        layout.addWidget(description_label)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(buttons)

    def selected_values(self) -> list[str]:
        selected: list[str] = []
        for item in self.list_widget.selectedItems():
            value = item.data(Qt.ItemDataRole.UserRole)
            font_name = normalize_font_family(value if isinstance(value, str) else item.text())
            if font_name and font_name not in selected:
                selected.append(font_name)
        return selected


class FocusFieldsDialog(QDialog):
    BASE_HEIGHT = 188
    ROW_HEIGHT = 37
    WIDTH = 520
    MIN_HEIGHT = 410
    MAX_HEIGHT = 680
    STYLE_ROW_HEIGHT = 29
    STYLE_COMBO_HEIGHT = 27

    def __init__(self, config: FocusFieldConfig, fonts: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("重点字段")
        self.fonts = self._merge_unique_fonts(fonts, [config.style.font_family])
        self.field_rows: list[tuple[QWidget, QLineEdit]] = []

        self._build_ui(config)
        self._adjust_dialog_height()

    def _build_ui(self, config: FocusFieldConfig) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(10)

        title = QLabel("重点字段")
        title.setObjectName("sectionTitle")

        self.add_field_button = QPushButton("增加重点字段")
        self.add_field_button.setFixedSize(112, 25)
        self.add_field_button.clicked.connect(lambda: self._add_field_row(""))

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)
        toolbar.addWidget(title, 1)
        toolbar.addWidget(self.add_field_button, 0, Qt.AlignmentFlag.AlignRight)

        self.list_frame = QFrame()
        self.list_frame.setObjectName("focusFieldList")
        self.list_frame.setStyleSheet(
            """
            QFrame#focusFieldList {
                background: #F7FAF4;
                border: 1px solid #D7E5D0;
                border-radius: 10px;
            }
            """
        )
        self.list_layout = QVBoxLayout(self.list_frame)
        self.list_layout.setContentsMargins(10, 10, 10, 10)
        self.list_layout.setSpacing(7)

        header_row = QGridLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setHorizontalSpacing(8)
        field_header = QLabel("重点文字")
        action_header = QLabel("操作")
        for header in (field_header, action_header):
            header.setObjectName("mutedText")
        header_row.addWidget(field_header, 0, 0)
        header_row.addWidget(action_header, 0, 1, Qt.AlignmentFlag.AlignCenter)
        header_row.setColumnStretch(0, 1)
        header_row.setColumnMinimumWidth(1, 64)
        self.list_layout.addLayout(header_row)

        fields = config.fields if config.fields else list(DEFAULT_FOCUS_FIELDS)
        for field_text in fields:
            self._add_field_row(field_text, adjust_height=False)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.list_frame)

        style_frame = QFrame()
        style_frame.setObjectName("focusFieldStyle")
        style_frame.setStyleSheet(
            """
            QFrame#focusFieldStyle {
                background: #F7FAF4;
                border: 1px solid #D7E5D0;
                border-radius: 10px;
            }
            """
        )
        style_layout = QVBoxLayout(style_frame)
        style_layout.setContentsMargins(10, 8, 10, 8)
        style_layout.setSpacing(6)

        style_title = QLabel("专用格式")
        style_title.setObjectName("sectionTitle")

        format_row = QWidget()
        format_row.setObjectName("transparentSlot")
        format_layout = QHBoxLayout(format_row)
        format_layout.setContentsMargins(10, 0, 0, 0)
        format_layout.setSpacing(8)
        format_row.setFixedHeight(self.STYLE_ROW_HEIGHT)

        font_label = QLabel("字体")
        font_label.setObjectName("focusStyleLabel")
        font_label.setFixedHeight(self.STYLE_ROW_HEIGHT)
        font_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        size_label = QLabel("字号")
        size_label.setObjectName("focusStyleLabel")
        size_label.setFixedHeight(self.STYLE_ROW_HEIGHT)
        size_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.focus_font_combo = ClickableComboBox()
        self.focus_font_combo.setObjectName("focusFontField")
        self._add_font_items(self.focus_font_combo, self.fonts)
        self._configure_dialog_combo(self.focus_font_combo)
        self.focus_font_combo.setFixedSize(132, self.STYLE_COMBO_HEIGHT)
        self._set_font_combo_value(self.focus_font_combo, config.style.font_family)

        self.focus_size_combo = ClickableComboBox()
        self.focus_size_combo.setObjectName("focusSizeField")
        self.focus_size_combo.addItems(list(HAO_TO_PT.keys()))
        self._configure_dialog_combo(self.focus_size_combo)
        self.focus_size_combo.setFixedSize(79, self.STYLE_COMBO_HEIGHT)
        self.focus_size_combo.lineEdit().setTextMargins(12, 0, 0, 0)
        self.focus_size_combo.setCurrentText(config.style.font_size_hao)

        self.focus_bold_checkbox = QCheckBox("加粗")
        self.focus_bold_checkbox.setObjectName("focusBoldCheckbox")
        self.focus_bold_checkbox.setFixedHeight(self.STYLE_ROW_HEIGHT)
        self.focus_bold_checkbox.setChecked(config.bold)

        format_layout.addWidget(font_label, 0)
        format_layout.addWidget(self.focus_font_combo, 0)
        format_layout.addWidget(size_label, 0)
        format_layout.addWidget(self.focus_size_combo, 0)
        format_layout.addWidget(self.focus_bold_checkbox, 0)
        format_layout.addStretch(1)

        style_layout.addWidget(style_title)
        style_layout.addWidget(format_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button is not None:
            ok_button.setText("保存")
        if cancel_button is not None:
            cancel_button.setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root_layout.addLayout(toolbar)
        root_layout.addWidget(self.scroll_area, 1)
        root_layout.addWidget(style_frame, 0)
        root_layout.addWidget(buttons)

    def _add_field_row(self, text: str, *, adjust_height: bool = True) -> None:
        row = QWidget()
        row.setObjectName("transparentSlot")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        field_edit = QLineEdit(text)
        field_edit.setMinimumHeight(25)
        field_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        delete_button = QPushButton("删除")
        delete_button.setFixedSize(64, 25)
        delete_button.clicked.connect(lambda: self._delete_field_row(row))

        row_layout.addWidget(field_edit, 1)
        row_layout.addWidget(delete_button, 0)
        self.list_layout.addWidget(row)
        self.field_rows.append((row, field_edit))
        if adjust_height:
            self._adjust_dialog_height()

    def _delete_field_row(self, row: QWidget) -> None:
        for index, (row_widget, _) in enumerate(self.field_rows):
            if row_widget is row:
                self.field_rows.pop(index)
                break
        self.list_layout.removeWidget(row)
        row.deleteLater()
        self._adjust_dialog_height()

    def _adjust_dialog_height(self) -> None:
        row_count = max(1, len(self.field_rows))
        desired_height = max(self.MIN_HEIGHT, self.BASE_HEIGHT + row_count * self.ROW_HEIGHT)
        bounded_height = min(self.MAX_HEIGHT, desired_height)
        if hasattr(self, "scroll_area"):
            self.scroll_area.setMaximumHeight(max(120, bounded_height - 162))
        self.setFixedSize(self.WIDTH, bounded_height)

    def focus_field_config(self) -> FocusFieldConfig:
        fields: list[str] = []
        for _, field_edit in self.field_rows:
            field = field_edit.text().strip()
            if field and field not in fields:
                fields.append(field)

        return FocusFieldConfig(
            fields=fields,
            style=TextStyleConfig(
                font_family=self._current_font_combo_value(self.focus_font_combo),
                font_size_hao=self.focus_size_combo.currentText().strip(),
            ),
            bold=self.focus_bold_checkbox.isChecked(),
        )

    def _configure_dialog_combo(self, combo: QComboBox) -> None:
        combo.setEditable(True)
        combo.lineEdit().setReadOnly(True)
        combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        combo.lineEdit().setCursor(Qt.CursorShape.ArrowCursor)
        if isinstance(combo, ClickableComboBox):
            combo.lineEdit().installEventFilter(combo)
        for index in range(combo.count()):
            combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

    def _add_font_items(self, combo: QComboBox, fonts: list[str]) -> None:
        for font_name in fonts:
            normalized = normalize_font_family(font_name)
            combo.addItem(display_font_name(normalized), normalized)

    def _set_font_combo_value(self, combo: QComboBox, font_name: str) -> None:
        normalized = normalize_font_family(font_name)
        for index in range(combo.count()):
            if combo.itemData(index, Qt.ItemDataRole.UserRole) == normalized:
                combo.setCurrentIndex(index)
                combo.setToolTip(combo.currentText())
                return
        if combo.count():
            combo.setCurrentIndex(0)
            combo.setToolTip(combo.currentText())

    def _current_font_combo_value(self, combo: QComboBox) -> str:
        value = combo.currentData(Qt.ItemDataRole.UserRole)
        if isinstance(value, str) and value.strip():
            return normalize_font_family(value)
        return normalize_font_family(combo.currentText())

    def _merge_unique_fonts(self, *font_groups: list[str]) -> list[str]:
        merged: list[str] = []
        for group in font_groups:
            for font_name in group:
                normalized = normalize_font_family(font_name)
                if normalized and normalized not in merged:
                    merged.append(normalized)
        return merged


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("公文排版助手 V1.3.1")
        self.resize(WINDOW_SIZE)
        self.setMinimumSize(WINDOW_SIZE)
        self.setMaximumHeight(WINDOW_SIZE.height())

        self.current_file_name = "未导入文件"
        self.default_template = load_default_template()
        self.focus_field_config = load_focus_field_config()
        self.default_save_path = self._normalize_save_directory(load_default_save_path())
        self.last_declined_default_save_path: str | None = None
        self.custom_fonts, removed_fonts = load_font_preferences()
        self.custom_fonts = self._merge_unique_fonts(self.custom_fonts)
        self.removed_fonts = {normalize_font_family(font_name) for font_name in removed_fonts if normalize_font_family(font_name)}
        self.available_fonts = self._build_available_fonts()
        self.default_editor_text = self._build_default_editor_text()
        self.style_section_labels: dict[str, QWidget] = {}

        self._build_ui()
        self._apply_dpi_safe_window_constraints()
        self._populate_style_font_combos(self.available_fonts)
        self._load_template_into_form(self.default_template)
        self._reset_editor_to_default_text()
        self._update_editor_visual_state()
        if self.default_save_path:
            self.save_path_edit.setText(self.default_save_path)
        self._bind_events()
        self._refresh_statistics()

    def _build_available_fonts(self) -> list[str]:
        fonts = self._merge_unique_fonts(get_common_fonts(), self.custom_fonts)
        return [font_name for font_name in fonts if font_name not in self.removed_fonts]

    def _merge_unique_fonts(self, *font_groups: list[str]) -> list[str]:
        merged: list[str] = []
        for group in font_groups:
            for font_name in group:
                normalized = normalize_font_family(font_name)
                if normalized and normalized not in merged:
                    merged.append(normalized)
        return merged

    def _save_font_preferences(self) -> None:
        save_font_preferences(self.custom_fonts, sorted(self.removed_fonts))

    def _get_style_font_combos(self) -> list[QComboBox]:
        return [self.title_font_combo, self.h1_font_combo, self.h2_font_combo, self.body_font_combo]

    def _add_font_combo_items(self, combo: QComboBox, fonts: list[str]) -> None:
        for font_name in fonts:
            normalized = normalize_font_family(font_name)
            combo.addItem(display_font_name(normalized), normalized)

    def _set_font_combo_value(self, combo: QComboBox, font_name: str) -> None:
        normalized = normalize_font_family(font_name)
        for index in range(combo.count()):
            if combo.itemData(index, Qt.ItemDataRole.UserRole) == normalized:
                combo.setCurrentIndex(index)
                combo.setToolTip(combo.currentText())
                return
        if combo.count():
            combo.setCurrentIndex(0)
            combo.setToolTip(combo.currentText())

    def _current_font_combo_value(self, combo: QComboBox) -> str:
        value = combo.currentData(Qt.ItemDataRole.UserRole)
        if isinstance(value, str) and value.strip():
            return normalize_font_family(value)
        return normalize_font_family(combo.currentText())

    def _build_default_editor_text(self) -> str:
        return (
            "可直接在这里粘贴或输入文字，并可进行简单编辑。\n\n"
            "导入文档后会自动清除原有格式，仅保留文字和段落结构。\n\n"
            "自动识别规则：\n"
            "第一段识别为文档标题；\n"
            "以“一、二、三”开头识别为一级标题；\n"
            "以“（一）（二）（三）”开头识别为二级标题；\n"
            "其他段落识别为正文。\n\n"
            "重点字段：默认强调“分析认为”“一是”“二是”“三是”“四是”“五是”，\n"
            "可在右上角“重点字段”中修改、增加或删除，并单独设置字体、字号和是否加粗。\n\n"
            "请确保电脑中有相应字体。"
        )

    def _normalize_save_directory(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized_value = value.strip()
        if not normalized_value:
            return None
        candidate = Path(normalized_value).expanduser()
        if candidate.suffix.lower() == ".docx":
            candidate = candidate.parent
        return str(candidate)

    def _resolve_initial_save_directory(self) -> str:
        for candidate in (self.save_path_edit.text().strip(), self.default_save_path, str(Path.cwd())):
            normalized = self._normalize_save_directory(candidate)
            if normalized:
                return normalized
        return str(Path.cwd())

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setObjectName("transparentSlot")
        content_wrapper.setFixedHeight(PANEL_HEIGHT + 10)

        content_row = QHBoxLayout(content_wrapper)
        content_row.setContentsMargins(10, 10, 10, 0)
        content_row.setSpacing(6)

        self.editor_panel = self._build_editor_panel()
        self.settings_panel = self._build_settings_panel()
        self.editor_panel.setFixedHeight(PANEL_HEIGHT)
        self.settings_panel.setFixedHeight(PANEL_HEIGHT)
        self._layout_body_title()

        content_row.addWidget(self.editor_panel, 1, Qt.AlignmentFlag.AlignTop)
        content_row.addWidget(self.settings_panel, 0, Qt.AlignmentFlag.AlignTop)
        root_layout.addWidget(content_wrapper)

        self.status_footer = QWidget()
        self.status_footer.setObjectName("statusFooter")
        self.status_footer.setFixedHeight(STATUS_FOOTER_HEIGHT)

        self.status_message_label = QLabel("公文排版助手已就绪。", self.status_footer)
        self.status_message_label.setObjectName("statusMessage")
        self.status_message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.contact_label = QLabel("如有问题或建议请联系sugarwanders@163.com", self.status_footer)
        self.contact_label.setObjectName("statusContact")
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.contact_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.status_footer_layout = QHBoxLayout(self.status_footer)
        self.status_footer_layout.setContentsMargins(
            2 + STATUS_MESSAGE_SHIFT,
            STATUS_TEXT_TOP,
            STATUS_TEXT_SIDE_MARGIN,
            STATUS_FOOTER_HEIGHT - STATUS_TEXT_TOP - STATUS_TEXT_HEIGHT,
        )
        self.status_footer_layout.setSpacing(6)
        self.status_footer_layout.addWidget(self.status_message_label, 1, Qt.AlignmentFlag.AlignVCenter)
        self.status_footer_layout.addWidget(self.contact_label, 0, Qt.AlignmentFlag.AlignVCenter)

        root_layout.addWidget(self.status_footer)
        root_layout.addStretch(1)
        self._set_status_message("公文排版助手已就绪。")
        self._layout_status_footer()

    def _set_status_message(self, text: str) -> None:
        self.status_message_label.setText(text)
        self._layout_status_footer()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_precise_layout_offsets()

    def _apply_precise_layout_offsets(self) -> None:
        self._layout_status_footer()
        self._layout_body_title()

    def _apply_dpi_safe_window_constraints(self) -> None:
        if not hasattr(self, "settings_panel"):
            return

        required_settings_width = max(SETTINGS_PANEL_WIDTH, self.settings_panel.sizeHint().width() + 2)
        self.settings_panel.setMinimumWidth(required_settings_width)
        self.settings_panel.setMaximumWidth(required_settings_width)

        extra_width = max(0, required_settings_width - SETTINGS_PANEL_WIDTH)
        safe_size = QSize(WINDOW_SIZE.width() + extra_width, WINDOW_SIZE.height())
        self.setMinimumSize(safe_size)
        self.setMaximumHeight(safe_size.height())
        if self.width() < safe_size.width() or self.height() < safe_size.height():
            self.resize(max(self.width(), safe_size.width()), max(self.height(), safe_size.height()))

    def _layout_status_footer(self) -> None:
        if not hasattr(self, "status_footer"):
            return
        text_height = max(
            STATUS_TEXT_HEIGHT,
            self.status_message_label.fontMetrics().height() + 2,
            self.contact_label.fontMetrics().height() + 2,
        )
        text_height = min(self.status_footer.height(), text_height)
        text_top = max(0, (self.status_footer.height() - text_height) // 2)
        text_bottom = max(0, self.status_footer.height() - text_height - text_top)
        contact_width = max(282, self.contact_label.sizeHint().width() + 4)
        self.contact_label.setMinimumWidth(contact_width)
        self.status_message_label.setMinimumHeight(text_height)
        self.status_message_label.setMaximumHeight(text_height)
        self.contact_label.setMinimumHeight(text_height)
        self.contact_label.setMaximumHeight(text_height)
        if hasattr(self, "status_footer_layout"):
            self.status_footer_layout.setContentsMargins(
                2 + STATUS_MESSAGE_SHIFT,
                text_top,
                STATUS_TEXT_SIDE_MARGIN,
                text_bottom,
            )

    def _build_body_title_widget(self) -> QWidget:
        title_widget = QWidget()
        title_widget.setObjectName("transparentSlot")
        title_widget.setFixedHeight(18)

        self.body_title_zheng_label = QLabel("正", title_widget)
        self.body_title_wen_label = QLabel("文", title_widget)
        for label in (self.body_title_zheng_label, self.body_title_wen_label):
            label.setObjectName("bodyTitleChar")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return title_widget

    def _layout_body_title(self) -> None:
        h2_label = self.style_section_labels.get("二级标题")
        body_title_widget = self.style_section_labels.get("正文")
        if not h2_label or not body_title_widget:
            return
        if not hasattr(self, "body_title_zheng_label") or not hasattr(self, "body_title_wen_label"):
            return

        h2_top_left = h2_label.mapTo(self.settings_panel, h2_label.rect().topLeft())
        body_top_left = body_title_widget.mapTo(self.settings_panel, body_title_widget.rect().topLeft())
        metrics = h2_label.fontMetrics()
        title_height = max(body_title_widget.height(), metrics.height())
        h2_text_left = h2_top_left.x() + BODY_TITLE_LEFT_PADDING
        zheng_x = h2_text_left + BODY_TITLE_ZHENG_SHIFT - body_top_left.x()
        wen_x = h2_text_left + metrics.horizontalAdvance("二级标") + BODY_TITLE_WEN_SHIFT - body_top_left.x()
        fallback_positions = (2, 45)

        for index, (text, label, x) in enumerate(
            (
                ("正", self.body_title_zheng_label, zheng_x),
                ("文", self.body_title_wen_label, wen_x),
            )
        ):
            label_width = metrics.horizontalAdvance(text) + 8
            safe_x = int(round(x))
            if safe_x < 0 or safe_x + label_width > body_title_widget.width():
                safe_x = fallback_positions[index]
            label.setFixedSize(label_width, title_height)
            label.move(safe_x, 0)
            label.show()
            label.raise_()

    def _build_editor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("card")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 0)
        layout.setSpacing(2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        self.import_button = QPushButton("导入文件")
        self.import_button.setObjectName("toolButton")
        self.import_button.setFixedSize(82, 27)
        self.clear_button = QPushButton("清空内容")
        self.clear_button.setObjectName("toolButton")
        self.clear_button.setFixedSize(82, 27)
        self.focus_fields_button = QPushButton("重点字段")
        self.focus_fields_button.setObjectName("toolButton")
        self.focus_fields_button.setFixedSize(82, 27)

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.clear_button)
        header_layout.addStretch(1)
        header_layout.addWidget(self.focus_fields_button)

        self.editor = QPlainTextEdit()
        self.editor.setFrameShape(QFrame.Shape.NoFrame)

        footer_widget = QWidget()
        footer_widget.setObjectName("transparentSlot")
        footer_widget.setFixedHeight(31)
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 7, 0, 8)
        footer_layout.setSpacing(8)

        self.paragraph_count_label = QLabel("段落数：0")
        self.char_count_label = QLabel("字数：0")
        self.classifier_status_label = QLabel("识别状态：等待内容")

        for label in (self.paragraph_count_label, self.char_count_label, self.classifier_status_label):
            label.setObjectName("mutedText")
            label.setFixedHeight(16)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            footer_layout.addWidget(label)

        footer_layout.addStretch(1)

        layout.addLayout(header_layout)
        layout.addWidget(self.editor, 1)
        layout.addWidget(footer_widget)
        return panel

    def _build_settings_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("settingsPanelCard")
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 5)
        panel_layout.setSpacing(6)
        panel.setMinimumWidth(SETTINGS_PANEL_WIDTH)

        action_grid = QGridLayout()
        action_grid.setContentsMargins(0, 0, 0, 0)
        action_grid.setHorizontalSpacing(6)
        action_grid.setVerticalSpacing(6)

        self.restore_defaults_button = QPushButton("恢复默认参数")
        self.restore_defaults_button.setObjectName("actionButton")
        self.set_default_button = QPushButton("当前参数设为默认值")
        self.set_default_button.setObjectName("actionButton")
        self.load_local_fonts_button = QPushButton("加载本地字体")
        self.load_local_fonts_button.setObjectName("actionButton")
        self.remove_fonts_button = QPushButton("删除字体")
        self.remove_fonts_button.setObjectName("actionButton")

        action_buttons = [
            self.restore_defaults_button,
            self.set_default_button,
            self.load_local_fonts_button,
            self.remove_fonts_button,
        ]
        for index, button in enumerate(action_buttons):
            button.setFixedHeight(27)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            action_grid.addWidget(button, index // 2, index % 2)
        action_grid.setColumnStretch(0, 1)
        action_grid.setColumnStretch(1, 1)

        panel_layout.addLayout(action_grid)
        panel_layout.addWidget(self._build_page_section())
        panel_layout.addWidget(self._build_paragraph_section())
        panel_layout.addWidget(self._build_text_style_section())
        panel_layout.addWidget(self._build_export_section())

        self.export_button = QPushButton("生成 .docx")
        self.export_button.setObjectName("primaryButton")
        self.export_button.setFixedHeight(29)
        panel_layout.addWidget(self.export_button)
        return panel

    def _build_page_section(self) -> QFrame:
        section = QFrame()
        section.setObjectName("styleBlock")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(3)

        title = QLabel("页面设置")
        title.setObjectName("subSectionTitle")

        self.top_margin_spin = self._create_spinbox(0, 100, "marginField")
        self.bottom_margin_spin = self._create_spinbox(0, 100, "marginField")
        self.left_margin_spin = self._create_spinbox(0, 100, "marginField")
        self.right_margin_spin = self._create_spinbox(0, 100, "marginField")

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(9)

        self._add_margin_row(grid, 0, "上边距", self.top_margin_spin, "下边距", self.bottom_margin_spin)
        self._add_margin_row(grid, 1, "左边距", self.left_margin_spin, "右边距", self.right_margin_spin)

        layout.addWidget(title)
        layout.addLayout(grid)
        return section

    def _add_margin_row(self, grid: QGridLayout, row: int, left_label: str, left_spin: QSpinBox, right_label: str, right_spin: QSpinBox) -> None:
        left_label_widget = QLabel(left_label)
        left_label_widget.setFixedWidth(58)
        left_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_unit_widget = QLabel("毫米")
        left_unit_widget.setFixedWidth(52)
        left_unit_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_label_widget = QLabel(right_label)
        right_label_widget.setFixedWidth(58)
        right_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_unit_widget = QLabel("毫米")
        right_unit_widget.setFixedWidth(52)
        right_unit_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid.setColumnMinimumWidth(0, 58)
        grid.setColumnMinimumWidth(1, 53)
        grid.setColumnMinimumWidth(2, 52)
        grid.addWidget(left_label_widget, row, 0)
        grid.addWidget(left_spin, row, 1)
        grid.addWidget(left_unit_widget, row, 2)
        grid.setColumnMinimumWidth(3, 6)
        grid.setColumnMinimumWidth(4, 58)
        grid.setColumnMinimumWidth(5, 53)
        grid.setColumnMinimumWidth(6, 52)
        grid.addWidget(right_label_widget, row, 4)
        grid.addWidget(right_spin, row, 5)
        grid.addWidget(right_unit_widget, row, 6)
        grid.setColumnStretch(7, 1)

    def _build_paragraph_section(self) -> QFrame:
        section = QFrame()
        section.setObjectName("styleBlock")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(3)

        title = QLabel("段落设置")
        title.setObjectName("subSectionTitle")

        self.line_spacing_spin = self._create_spinbox(10, 80, "lineField")
        row = QGridLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setHorizontalSpacing(4)
        row.setVerticalSpacing(0)

        line_label = QLabel("固定行距")
        line_label.setFixedWidth(72)
        line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_slot = QWidget()
        unit_slot.setObjectName("transparentSlot")
        unit_slot.setFixedSize(40, 29)
        unit_label = QLabel("磅", unit_slot)
        unit_label.setFixedSize(40, 29)
        unit_label.move(LINE_UNIT_SHIFT, -2)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_spacing_unit_label = unit_label

        self.clean_body_spaces_checkbox = QCheckBox("检查正文空格")
        self.clean_body_spaces_checkbox.setObjectName("bodySpaceCheckBox")
        self.clean_body_spaces_checkbox.setFixedSize(163, 29)
        self.clean_body_spaces_checkbox.setToolTip("导出时清理正文中的多余空格")

        row.setColumnMinimumWidth(0, 72)
        row.setColumnMinimumWidth(1, 53)
        row.setColumnMinimumWidth(2, 40)
        row.setColumnMinimumWidth(3, 6)
        row.setColumnMinimumWidth(4, 58)
        row.setColumnMinimumWidth(5, 53)
        row.setColumnMinimumWidth(6, 52)
        row.setColumnStretch(7, 1)
        row.addWidget(line_label, 0, 0)
        row.addWidget(self.line_spacing_spin, 0, 1)
        row.addWidget(unit_slot, 0, 2)
        row.addWidget(
            self.clean_body_spaces_checkbox,
            0,
            4,
            1,
            3,
            Qt.AlignmentFlag.AlignCenter,
        )

        layout.addWidget(title)
        layout.addLayout(row)
        return section

    def _build_text_style_section(self) -> QFrame:
        section = QFrame()
        section.setObjectName("styleGroup")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.style_section_labels = {}
        self.title_font_combo, self.title_size_combo = self._create_style_editor(layout, "文档标题")
        self.h1_font_combo, self.h1_size_combo = self._create_style_editor(layout, "一级标题")
        self.h2_font_combo, self.h2_size_combo = self._create_style_editor(layout, "二级标题")
        self.body_font_combo, self.body_size_combo = self._create_style_editor(layout, "正文")
        return section

    def _build_export_section(self) -> QFrame:
        section = QFrame()
        section.setObjectName("styleBlock")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        title = QLabel("导出文档")
        title.setObjectName("subSectionTitle")

        self.save_path_edit = QLineEdit()
        self.save_path_edit.setObjectName("pathField")
        self.save_path_edit.setPlaceholderText("请选择保存文件夹")
        self.save_path_edit.setFixedSize(228, 29)
        self.save_path_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.select_path_button = QPushButton("选择保存位置")
        self.select_path_button.setObjectName("pathButton")
        self.select_path_button.setFixedSize(98, 27)
        select_path_slot = QWidget()
        select_path_slot.setObjectName("transparentSlot")
        select_path_slot.setFixedSize(103, 27)
        self.select_path_button.setParent(select_path_slot)
        self.select_path_button.move(0, 0)

        row = QGridLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setHorizontalSpacing(4)
        row.setVerticalSpacing(0)
        row.setColumnMinimumWidth(0, 6)
        row.setColumnMinimumWidth(1, 220)
        row.setColumnMinimumWidth(2, 8)
        row.setColumnMinimumWidth(3, 0)
        row.setColumnMinimumWidth(4, 103)
        row.addWidget(self.save_path_edit, 0, 1, 1, 3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(select_path_slot, 0, 4)
        layout.addWidget(title)
        layout.addLayout(row)
        return section

    def _create_style_editor(self, parent_layout: QVBoxLayout, label_text: str) -> tuple[QComboBox, QComboBox]:
        wrapper = QFrame()
        wrapper.setObjectName("styleBlock")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        if label_text == "正文":
            section_label = self._build_body_title_widget()
        else:
            section_label = QLabel(label_text)
            section_label.setObjectName("subSectionTitle")
        self.style_section_labels[label_text] = section_label

        row = QGridLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setHorizontalSpacing(4)
        row.setVerticalSpacing(0)

        font_label = QLabel("字体")
        font_label.setFixedWidth(47)
        font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(font_label, 0, 0)

        font_combo = ClickableComboBox()
        font_combo.setObjectName("fontField")
        font_combo.setFixedSize(164, 27)
        self._configure_centered_combo(font_combo)
        row.addWidget(font_combo, 0, 1)
        row.setColumnMinimumWidth(0, 56)
        row.setColumnMinimumWidth(2, 1)

        size_label = QLabel("字号")
        size_label.setFixedWidth(51)
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(size_label, 0, 3)

        size_combo = ClickableComboBox()
        size_combo.setObjectName("sizeField")
        size_combo.setFixedSize(61, 27)
        self._configure_centered_combo(size_combo)
        size_combo.addItems(list(HAO_TO_PT.keys()))
        for index in range(size_combo.count()):
            size_combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)
        row.addWidget(size_combo, 0, 4)
        row.setColumnMinimumWidth(1, 164)
        row.setColumnMinimumWidth(3, 51)
        row.setColumnMinimumWidth(4, 61)
        row.setColumnMinimumWidth(5, 0)

        layout.addWidget(section_label)
        layout.addLayout(row)
        parent_layout.addWidget(wrapper)
        return font_combo, size_combo

    def _create_spinbox(self, minimum: int, maximum: int, object_name: str) -> AlignedSpinBox:
        spinbox = AlignedSpinBox(minimum, maximum, object_name)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return spinbox

    def _configure_centered_combo(self, combo: QComboBox) -> None:
        combo.setEditable(True)
        combo.lineEdit().setReadOnly(True)
        combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        combo.lineEdit().setCursor(Qt.CursorShape.ArrowCursor)
        if isinstance(combo, ClickableComboBox):
            combo.lineEdit().installEventFilter(combo)

    def _bind_events(self) -> None:
        self.import_button.clicked.connect(self._import_file)
        self.clear_button.clicked.connect(self._clear_editor)
        self.focus_fields_button.clicked.connect(self._edit_focus_fields)
        self.restore_defaults_button.clicked.connect(self._restore_default_parameters)
        self.set_default_button.clicked.connect(self._set_current_as_default)
        self.load_local_fonts_button.clicked.connect(self._load_local_fonts)
        self.remove_fonts_button.clicked.connect(self._delete_fonts)
        self.select_path_button.clicked.connect(self._select_save_path)
        self.export_button.clicked.connect(self._export_document)
        self.editor.textChanged.connect(self._refresh_statistics)
        self.clean_body_spaces_checkbox.toggled.connect(self._auto_save_current_template)
        for spin_box in (
            self.top_margin_spin,
            self.bottom_margin_spin,
            self.left_margin_spin,
            self.right_margin_spin,
            self.line_spacing_spin,
        ):
            spin_box.valueChanged.connect(self._auto_save_current_template)
        for combo in (
            self.title_font_combo,
            self.title_size_combo,
            self.h1_font_combo,
            self.h1_size_combo,
            self.h2_font_combo,
            self.h2_size_combo,
            self.body_font_combo,
            self.body_size_combo,
        ):
            combo.currentIndexChanged.connect(self._auto_save_current_template)

    def _populate_style_font_combos(self, fonts: list[str]) -> None:
        defaults = [
            self.default_template.title.font_family,
            self.default_template.h1.font_family,
            self.default_template.h2.font_family,
            self.default_template.body.font_family,
        ]
        for combo, default_value in zip(self._get_style_font_combos(), defaults):
            combo.blockSignals(True)
            combo.clear()
            self._add_font_combo_items(combo, fonts)
            for index in range(combo.count()):
                combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)
            self._set_font_combo_value(combo, default_value)
            combo.blockSignals(False)

    def _refresh_font_combos(self, preferred_values: list[str] | None = None) -> None:
        if preferred_values is None:
            preferred_values = [self._current_font_combo_value(combo) for combo in self._get_style_font_combos()]

        self.available_fonts = self._build_available_fonts()
        fallback_values = [
            self.default_template.title.font_family,
            self.default_template.h1.font_family,
            self.default_template.h2.font_family,
            self.default_template.body.font_family,
        ]

        for combo, preferred_value, fallback_value in zip(self._get_style_font_combos(), preferred_values, fallback_values):
            combo.blockSignals(True)
            combo.clear()
            self._add_font_combo_items(combo, self.available_fonts)
            for index in range(combo.count()):
                combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

            selected_value = None
            preferred_font = normalize_font_family(preferred_value)
            fallback_font = normalize_font_family(fallback_value)
            if preferred_font in self.available_fonts:
                selected_value = preferred_font
            elif fallback_font in self.available_fonts:
                selected_value = fallback_font
            elif self.available_fonts:
                selected_value = self.available_fonts[0]

            if selected_value:
                self._set_font_combo_value(combo, selected_value)
            combo.blockSignals(False)

    def _load_template_into_form(self, template: TemplateConfig) -> None:
        self.top_margin_spin.setValue(template.margins_mm.top)
        self.bottom_margin_spin.setValue(template.margins_mm.bottom)
        self.left_margin_spin.setValue(template.margins_mm.left)
        self.right_margin_spin.setValue(template.margins_mm.right)
        self.line_spacing_spin.setValue(template.line_spacing_pt)
        self.clean_body_spaces_checkbox.setChecked(template.clean_body_spaces)
        if normalize_font_family(template.title.font_family) in self.available_fonts:
            self._set_font_combo_value(self.title_font_combo, template.title.font_family)
        if normalize_font_family(template.h1.font_family) in self.available_fonts:
            self._set_font_combo_value(self.h1_font_combo, template.h1.font_family)
        if normalize_font_family(template.h2.font_family) in self.available_fonts:
            self._set_font_combo_value(self.h2_font_combo, template.h2.font_family)
        if normalize_font_family(template.body.font_family) in self.available_fonts:
            self._set_font_combo_value(self.body_font_combo, template.body.font_family)
        self.title_size_combo.setCurrentText(template.title.font_size_hao)
        self.h1_size_combo.setCurrentText(template.h1.font_size_hao)
        self.h2_size_combo.setCurrentText(template.h2.font_size_hao)
        self.body_size_combo.setCurrentText(template.body.font_size_hao)

    def _reset_editor_to_default_text(self) -> None:
        self.editor.blockSignals(True)
        self.editor.setPlainText(self.default_editor_text)
        self.editor.blockSignals(False)

    def _is_default_editor_content(self, text: str) -> bool:
        return text.strip() == self.default_editor_text.strip()

    def _update_editor_visual_state(self) -> None:
        state = "default" if self._is_default_editor_content(self.editor.toPlainText()) else "normal"
        self.editor.setProperty("editorState", state)
        self.editor.style().unpolish(self.editor)
        self.editor.style().polish(self.editor)
        palette = self.editor.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor("#A8B5C7" if state == "default" else "#163056"))
        self.editor.setPalette(palette)
        self.editor.viewport().update()

    def _import_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文档", "", "支持的文件 (*.docx *.txt)")
        if not file_path:
            return
        try:
            text, file_name = import_text_document(file_path)
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", str(exc))
            return
        self.current_file_name = file_name
        imported_directory = self._normalize_save_directory(str(Path(file_path).resolve().parent))
        if imported_directory:
            self.save_path_edit.setText(imported_directory)
        self.editor.setPlainText(text)
        self._update_editor_visual_state()
        self._set_status_message(f"已导入文件：{file_name}")

    def _clear_editor(self) -> None:
        if self._is_default_editor_content(self.editor.toPlainText()):
            return
        result = QMessageBox.question(self, "清空内容", "确定要清空当前编辑内容吗？")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.current_file_name = "未导入文件"
        self._reset_editor_to_default_text()
        self._update_editor_visual_state()
        self._refresh_statistics()
        self._set_status_message("编辑内容已恢复为默认说明。")

    def _restore_default_parameters(self) -> None:
        self.default_template = DEFAULT_TEMPLATE
        default_fonts = {
            normalize_font_family(self.default_template.title.font_family),
            normalize_font_family(self.default_template.h1.font_family),
            normalize_font_family(self.default_template.h2.font_family),
            normalize_font_family(self.default_template.body.font_family),
        }
        self.removed_fonts.difference_update(default_fonts)
        try:
            self._save_font_preferences()
        except OSError as exc:
            QMessageBox.warning(self, "恢复失败", f"字体列表恢复失败：{exc}")
        self._refresh_font_combos([
            self.default_template.title.font_family,
            self.default_template.h1.font_family,
            self.default_template.h2.font_family,
            self.default_template.body.font_family,
        ])
        self._load_template_into_form(self.default_template)
        try:
            save_default_template(self.default_template)
        except OSError as exc:
            QMessageBox.warning(self, "恢复失败", f"默认参数保存失败：{exc}")

        self.default_save_path = None
        self.last_declined_default_save_path = None
        self.save_path_edit.clear()
        try:
            clear_default_save_path()
        except OSError as exc:
            QMessageBox.warning(self, "清空失败", f"默认保存路径清空失败：{exc}")

        self._set_status_message("已恢复默认参数，并清空保存路径。")

    def _set_current_as_default(self) -> None:
        self.default_template = self._build_template_from_form()
        try:
            config_path = self._save_current_template()
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"默认参数保存失败：{exc}")
            return
        self._refresh_font_combos()
        self._set_status_message(f"默认参数已保存：{config_path}")
        QMessageBox.information(self, "保存成功", "当前参数已设为默认值，下次打开软件会自动加载。")

    def _load_local_fonts(self) -> None:
        options = self._merge_unique_fonts(get_installed_font_candidates())
        dialog = FontSelectionDialog(
            "加载本地字体",
            "\u5b57\u4f53\u6765\u6e90\uff1aC:\\Windows\\Fonts\n\u8bf7\u9009\u62e9\u9700\u8981\u52a0\u8f7d\u7684\u5b57\u4f53\uff0c\u53ef\u591a\u9009\u3002",
            options,
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected_fonts = dialog.selected_values()
        if not selected_fonts:
            return

        common_fonts = get_common_fonts()
        changed = False
        for font_name in selected_fonts:
            if font_name in self.removed_fonts:
                self.removed_fonts.remove(font_name)
                changed = True
            if font_name not in common_fonts and font_name not in self.custom_fonts:
                self.custom_fonts.append(font_name)
                changed = True

        if not changed:
            QMessageBox.information(self, "无需更新", "所选字体已经在本软件的字体列表中。")
            return

        self._save_font_preferences()
        self._refresh_font_combos()
        self._set_status_message(f"已加载 {len(selected_fonts)} 个本地字体。")

    def _delete_fonts(self) -> None:
        dialog = FontSelectionDialog(
            "\u5220\u9664\u5b57\u4f53",
            "\u8bf7\u9009\u62e9\u9700\u8981\u5220\u9664\u7684\u5b57\u4f53\uff0c\u53ef\u591a\u9009\u3002",
            list(self.available_fonts),
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected_fonts = dialog.selected_values()
        if not selected_fonts:
            return

        remaining_fonts = [font_name for font_name in self.available_fonts if font_name not in selected_fonts]
        if not remaining_fonts:
            QMessageBox.warning(self, "无法删除", "至少需要保留一个字体选项。")
            return

        result = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除已选的 {len(selected_fonts)} 个字体选项吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        for font_name in selected_fonts:
            if font_name in self.custom_fonts:
                self.custom_fonts.remove(font_name)
            self.removed_fonts.add(font_name)

        self._save_font_preferences()
        self._refresh_font_combos()
        self._set_status_message(f"已删除 {len(selected_fonts)} 个字体选项。")

    def _edit_focus_fields(self) -> None:
        dialog = FocusFieldsDialog(self.focus_field_config, self.available_fonts, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        updated_config = dialog.focus_field_config()
        if not updated_config.fields:
            QMessageBox.warning(self, "无法保存", "至少需要保留一个重点字段。")
            return

        try:
            config_path = save_focus_field_config(updated_config)
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"重点字段保存失败：{exc}")
            return

        self.focus_field_config = updated_config
        self._set_status_message(f"重点字段已保存：{config_path}")

    def _maybe_ask_set_default_save_path(self, selected_path: str) -> None:
        normalized_path = self._normalize_save_directory(selected_path)
        if not normalized_path:
            return
        if self.default_save_path and normalized_path == self.default_save_path:
            return
        if self.last_declined_default_save_path and normalized_path == self.last_declined_default_save_path:
            return

        result = QMessageBox.question(
            self,
            "设置默认保存路径",
            "是否把当前路径设置为默认保存路径？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if result == QMessageBox.StandardButton.Yes:
            try:
                config_path = save_default_save_path(normalized_path)
            except OSError as exc:
                QMessageBox.critical(self, "保存失败", f"默认保存路径保存失败：{exc}")
                return
            self.default_save_path = normalized_path
            self.last_declined_default_save_path = None
            self._set_status_message(f"默认保存路径已更新：{config_path}")
            return
        self.last_declined_default_save_path = normalized_path

    def _select_save_path(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择保存文件夹", self._resolve_initial_save_directory())
        if not directory:
            return
        normalized_directory = self._normalize_save_directory(directory)
        if not normalized_directory:
            return
        self.save_path_edit.setText(normalized_directory)
        self._maybe_ask_set_default_save_path(normalized_directory)

    def _show_export_success_dialog(self, exported_path: str) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("导出成功")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText(f"文档已生成：\n{exported_path}")
        open_button = dialog.addButton("打开文档", QMessageBox.ButtonRole.ActionRole)
        reveal_button = dialog.addButton("在文件夹中显示", QMessageBox.ButtonRole.ActionRole)
        dialog.exec()
        clicked_button = dialog.clickedButton()
        if clicked_button == open_button:
            self._open_document(exported_path)
        elif clicked_button == reveal_button:
            self._reveal_document_in_folder(exported_path)

    def _open_document(self, exported_path: str) -> None:
        try:
            os.startfile(str(Path(exported_path)))
        except OSError as exc:
            QMessageBox.critical(self, "打开失败", f"无法打开文档：{exc}")

    def _reveal_document_in_folder(self, exported_path: str) -> None:
        exported_file = Path(exported_path)
        try:
            if os.name == "nt":
                target = str(exported_file.resolve()).replace("/", "\\")
                subprocess.Popen(["explorer.exe", f"/select,{target}"])
            else:
                os.startfile(str(exported_file.parent))
        except OSError:
            try:
                os.startfile(str(exported_file.parent))
            except OSError as exc:
                QMessageBox.critical(self, "打开失败", f"无法打开所在文件夹：{exc}")

    def _build_template_from_form(self) -> TemplateConfig:
        return TemplateConfig(
            margins_mm=MarginConfig(
                top=self.top_margin_spin.value(),
                bottom=self.bottom_margin_spin.value(),
                left=self.left_margin_spin.value(),
                right=self.right_margin_spin.value(),
            ),
            line_spacing_pt=self.line_spacing_spin.value(),
            title=TextStyleConfig(
                font_family=self._current_font_combo_value(self.title_font_combo),
                font_size_hao=self.title_size_combo.currentText(),
            ),
            h1=TextStyleConfig(
                font_family=self._current_font_combo_value(self.h1_font_combo),
                font_size_hao=self.h1_size_combo.currentText(),
            ),
            h2=TextStyleConfig(
                font_family=self._current_font_combo_value(self.h2_font_combo),
                font_size_hao=self.h2_size_combo.currentText(),
            ),
            body=TextStyleConfig(
                font_family=self._current_font_combo_value(self.body_font_combo),
                font_size_hao=self.body_size_combo.currentText(),
            ),
            clean_body_spaces=self.clean_body_spaces_checkbox.isChecked(),
        )

    def _save_current_template(self) -> Path:
        self.default_template = self._build_template_from_form()
        return save_default_template(self.default_template)

    def _auto_save_current_template(self, *_args) -> None:
        try:
            self._save_current_template()
        except OSError as exc:
            self._set_status_message(f"排版参数自动保存失败：{exc}")

    def closeEvent(self, event) -> None:
        try:
            self._save_current_template()
        except OSError:
            pass
        super().closeEvent(event)

    def _export_document(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text or self._is_default_editor_content(text):
            QMessageBox.information(self, "缺少内容", "请先导入文档或在编辑区输入正式文字。")
            return
        save_directory = self._normalize_save_directory(self.save_path_edit.text().strip())
        if not save_directory:
            self._select_save_path()
            save_directory = self._normalize_save_directory(self.save_path_edit.text().strip())
            if not save_directory:
                return
        self.save_path_edit.setText(save_directory)
        self._maybe_ask_set_default_save_path(save_directory)
        try:
            self._save_current_template()
        except OSError as exc:
            QMessageBox.warning(self, "保存失败", f"排版参数保存失败：{exc}")
        try:
            exported_path = export_docx_document(
                text,
                self._build_template_from_form(),
                save_directory,
                self.focus_field_config,
            )
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return
        self._set_status_message(f"导出成功：{exported_path}")
        self._show_export_success_dialog(exported_path)

    def _refresh_statistics(self) -> None:
        self._update_editor_visual_state()
        text = self.editor.toPlainText()
        stripped_text = text.strip()
        if not stripped_text or self._is_default_editor_content(stripped_text):
            self.paragraph_count_label.setText("段落数：0")
            self.char_count_label.setText("字数：0")
            self.classifier_status_label.setText("识别状态：等待内容")
            return
        paragraphs = classify_paragraphs(stripped_text)
        self.paragraph_count_label.setText(f"段落数：{len(paragraphs)}")
        self.char_count_label.setText(f"字数：{len(''.join(part for part in text.split()))}")
        counts = {"title": 0, "h1": 0, "h2": 0, "body": 0}
        for item in paragraphs:
            counts[item["type"]] += 1
        self.classifier_status_label.setText(
            f"识别状态：标题 {counts['title']}，一级 {counts['h1']}，二级 {counts['h2']}，正文 {counts['body']}"
        )






