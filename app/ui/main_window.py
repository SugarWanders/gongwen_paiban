from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
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
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    QSplitter,
    QSpinBox,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import HAO_TO_PT, MarginConfig, TemplateConfig, TextStyleConfig
from app.services.document_importer import import_text_document
from app.services.export_service import export_docx_document
from app.services.font_service import get_common_fonts, get_installed_font_candidates
from app.services.font_store import load_font_preferences, save_font_preferences
from app.services.save_path_store import clear_default_save_path, load_default_save_path, save_default_save_path
from app.services.template_store import load_default_template, save_default_template
from app.services.title_classifier import classify_paragraphs
from app.ui.styles import _asset_uri


class AlignedSpinBox(QWidget):
    def __init__(self, minimum: int, maximum: int, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._value = minimum

        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(45, 22)

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
        button_box.setFixedWidth(13)

        up_icon = QIcon(_asset_uri("up-arrow.svg"))
        down_icon = QIcon(_asset_uri("down-arrow.svg"))

        button_layout = QVBoxLayout(button_box)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.up_button = QToolButton()
        self.up_button.setObjectName("spinUpButton")
        self.up_button.setIcon(up_icon)
        self.up_button.setIconSize(QSize(9, 5))
        self.up_button.setAutoRaise(True)
        self.up_button.setFixedSize(13, 10)
        self.up_button.clicked.connect(self.step_up)

        self.down_button = QToolButton()
        self.down_button.setObjectName("spinDownButton")
        self.down_button.setIcon(down_icon)
        self.down_button.setIconSize(QSize(9, 5))
        self.down_button.setAutoRaise(True)
        self.down_button.setFixedSize(13, 10)
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
        self._value = bounded
        self.line_edit.setText(str(bounded))

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
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if multi_select
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.addItems(options)

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
        return [item.text().strip() for item in self.list_widget.selectedItems() if item.text().strip()]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("公文排版助手 V1.2")
        self.resize(830, 500)
        self.setMinimumSize(780, 500)

        self.current_file_name = "未导入文件"
        self.default_template = load_default_template()
        self.default_save_path = self._normalize_save_directory(load_default_save_path())
        self.last_declined_default_save_path: str | None = None
        self.custom_fonts, removed_fonts = load_font_preferences()
        self.removed_fonts = set(removed_fonts)
        self.available_fonts = self._build_available_fonts()
        self.default_editor_text = self._build_default_editor_text()

        self._build_ui()
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
                normalized = font_name.strip()
                if normalized and normalized not in merged:
                    merged.append(normalized)
        return merged

    def _save_font_preferences(self) -> None:
        save_font_preferences(self.custom_fonts, sorted(self.removed_fonts))

    def _get_style_font_combos(self) -> list[QComboBox]:
        return [self.title_font_combo, self.h1_font_combo, self.h2_font_combo, self.body_font_combo]

    def _build_default_editor_text(self) -> str:
        return (
            "可直接在这里粘贴或输入文字，并可进行简单编辑。\n\n"
            "导入文档后会自动清除原有格式，仅保留文字和段落结构。\n\n"
            "自动识别规则：\n"
            "第一段识别为文档标题；\n"
            "以“一、二、三”开头识别为一级标题；\n"
            "以“（一）（二）（三）”开头识别为二级标题；\n"
            "其他段落识别为正文。\n\n"
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
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(6)

        editor_panel = self._build_editor_panel()
        settings_panel = self._build_settings_panel()
        aligned_height = max(editor_panel.sizeHint().height(), settings_panel.sizeHint().height())
        editor_panel.setFixedHeight(aligned_height)
        settings_panel.setFixedHeight(aligned_height)

        content_row.addWidget(editor_panel, 1, Qt.AlignmentFlag.AlignTop)
        content_row.addWidget(settings_panel, 0, Qt.AlignmentFlag.AlignTop)
        root_layout.addLayout(content_row)

        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        if status_bar.layout() is not None:
            status_bar.layout().setContentsMargins(0, 0, 0, 0)
            status_bar.layout().setSpacing(0)

        self.status_message_label = QLabel("公文排版助手已就绪。")
        self.status_message_label.setObjectName("statusMessage")
        self.status_message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_bar.addWidget(self.status_message_label, 1)

        self.contact_label = QLabel("如有问题或建议请联系sugarwanders@163.com")
        self.contact_label.setObjectName("statusContact")
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.contact_container = QWidget()
        self.contact_container.setObjectName("statusContactContainer")
        contact_layout = QHBoxLayout(self.contact_container)
        contact_layout.setContentsMargins(0, 0, 7, 0)
        contact_layout.setSpacing(0)
        contact_layout.addWidget(self.contact_label)

        status_bar.addPermanentWidget(self.contact_container)
        status_bar.addPermanentWidget(self.contact_container)
        self.setStatusBar(status_bar)
        self._set_status_message("公文排版助手已就绪。")

    def _set_status_message(self, text: str) -> None:
        self.status_message_label.setText(text)

    def _build_editor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("card")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        self.import_button = QPushButton("导入文件")
        self.import_button.setObjectName("toolButton")
        self.import_button.setFixedSize(52, 20)
        self.clear_button = QPushButton("清空内容")
        self.clear_button.setObjectName("toolButton")
        self.clear_button.setFixedSize(52, 20)

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.clear_button)
        header_layout.addStretch(1)

        self.editor = QPlainTextEdit()
        self.editor.setFrameShape(QFrame.Shape.NoFrame)

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        self.paragraph_count_label = QLabel("段落数：0")
        self.char_count_label = QLabel("字数：0")
        self.classifier_status_label = QLabel("识别状态：等待内容")

        for label in (self.paragraph_count_label, self.char_count_label, self.classifier_status_label):
            label.setObjectName("mutedText")
            footer_layout.addWidget(label)

        footer_layout.addStretch(1)

        layout.addLayout(header_layout)
        layout.addWidget(self.editor, 1)
        layout.addLayout(footer_layout)
        return panel

    def _build_settings_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("settingsPanelCard")
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(4)
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(280)

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
            button.setFixedHeight(20)
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
        self.export_button.setFixedHeight(20)
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
        grid.setVerticalSpacing(4)

        self._add_margin_row(grid, 0, "上边距", self.top_margin_spin, "下边距", self.bottom_margin_spin)
        self._add_margin_row(grid, 1, "左边距", self.left_margin_spin, "右边距", self.right_margin_spin)

        layout.addWidget(title)
        layout.addLayout(grid)
        return section

    def _add_margin_row(self, grid: QGridLayout, row: int, left_label: str, left_spin: QSpinBox, right_label: str, right_spin: QSpinBox) -> None:
        left_label_widget = QLabel(left_label)
        left_label_widget.setFixedWidth(40)
        left_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_unit_widget = QLabel("毫米")
        left_unit_widget.setFixedWidth(18)
        left_unit_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_label_widget = QLabel(right_label)
        right_label_widget.setFixedWidth(38)
        right_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_unit_widget = QLabel("毫米")
        right_unit_widget.setFixedWidth(18)
        right_unit_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid.setColumnMinimumWidth(1, 45)
        grid.setColumnMinimumWidth(2, 18)
        grid.setColumnMinimumWidth(5, 45)
        grid.setColumnMinimumWidth(6, 18)
        grid.addWidget(left_label_widget, row, 0)
        grid.addWidget(left_spin, row, 1)
        grid.addWidget(left_unit_widget, row, 2)
        grid.setColumnMinimumWidth(3, 12)
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
        line_label.setFixedWidth(40)
        line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_label = QLabel("pt")
        unit_label.setFixedWidth(18)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        row.setColumnMinimumWidth(0, 40)
        row.setColumnMinimumWidth(1, 45)
        row.setColumnMinimumWidth(2, 18)
        row.setColumnMinimumWidth(3, 12)
        row.addItem(QSpacerItem(38, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), 0, 4)
        row.addItem(QSpacerItem(45, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), 0, 5)
        row.addItem(QSpacerItem(18, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), 0, 6)
        row.setColumnStretch(7, 1)
        row.addWidget(line_label, 0, 0)
        row.addWidget(self.line_spacing_spin, 0, 1)
        row.addWidget(unit_label, 0, 2)

        layout.addWidget(title)
        layout.addLayout(row)
        return section

    def _build_text_style_section(self) -> QFrame:
        section = QFrame()
        section.setObjectName("styleGroup")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

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
        layout.setSpacing(3)

        title = QLabel("导出文档")
        title.setObjectName("subSectionTitle")

        self.save_path_edit = QLineEdit()
        self.save_path_edit.setObjectName("pathField")
        self.save_path_edit.setPlaceholderText("请选择保存文件夹")
        self.save_path_edit.setFixedHeight(20)
        self.save_path_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.select_path_button = QPushButton("选择保存位置")
        self.select_path_button.setObjectName("pathButton")
        self.select_path_button.setFixedHeight(20)
        self.select_path_button.setFixedWidth(60)

        row = QGridLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setHorizontalSpacing(4)
        row.setVerticalSpacing(0)
        row.setColumnMinimumWidth(0, 24)
        row.setColumnMinimumWidth(1, 98)
        row.setColumnMinimumWidth(2, 12)
        row.setColumnMinimumWidth(3, 20)
        row.setColumnMinimumWidth(4, 60)
        row.addWidget(self.save_path_edit, 0, 1, 1, 3)
        row.addWidget(self.select_path_button, 0, 4, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)
        layout.addLayout(row)
        return section

    def _create_style_editor(self, parent_layout: QVBoxLayout, label_text: str) -> tuple[QComboBox, QComboBox]:
        wrapper = QFrame()
        wrapper.setObjectName("styleBlock")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        section_label = QLabel(label_text)
        section_label.setObjectName("subSectionTitle")

        row = QGridLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setHorizontalSpacing(4)
        row.setVerticalSpacing(0)

        font_label = QLabel("字体")
        font_label.setFixedWidth(24)
        font_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(font_label, 0, 0)

        font_combo = ClickableComboBox()
        font_combo.setObjectName("fontField")
        font_combo.setFixedSize(78, 20)
        self._configure_centered_combo(font_combo)
        row.addWidget(font_combo, 0, 1)
        row.setColumnMinimumWidth(2, 16)

        size_label = QLabel("字号")
        size_label.setFixedWidth(18)
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(size_label, 0, 3)

        size_combo = ClickableComboBox()
        size_combo.setObjectName("sizeField")
        size_combo.setFixedSize(30, 20)
        self._configure_centered_combo(size_combo)
        size_combo.addItems(list(HAO_TO_PT.keys()))
        for index in range(size_combo.count()):
            size_combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)
        row.addWidget(size_combo, 0, 4)
        row.setColumnMinimumWidth(4, 30)
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
        self.restore_defaults_button.clicked.connect(self._restore_default_parameters)
        self.set_default_button.clicked.connect(self._set_current_as_default)
        self.load_local_fonts_button.clicked.connect(self._load_local_fonts)
        self.remove_fonts_button.clicked.connect(self._delete_fonts)
        self.select_path_button.clicked.connect(self._select_save_path)
        self.export_button.clicked.connect(self._export_document)
        self.editor.textChanged.connect(self._refresh_statistics)

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
            combo.addItems(fonts)
            for index in range(combo.count()):
                combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)
            if default_value in fonts:
                combo.setCurrentText(default_value)
            elif fonts:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def _refresh_font_combos(self, preferred_values: list[str] | None = None) -> None:
        if preferred_values is None:
            preferred_values = [combo.currentText().strip() for combo in self._get_style_font_combos()]

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
            combo.addItems(self.available_fonts)
            for index in range(combo.count()):
                combo.setItemData(index, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

            selected_value = None
            if preferred_value in self.available_fonts:
                selected_value = preferred_value
            elif fallback_value in self.available_fonts:
                selected_value = fallback_value
            elif self.available_fonts:
                selected_value = self.available_fonts[0]

            if selected_value:
                combo.setCurrentText(selected_value)
            combo.blockSignals(False)

    def _load_template_into_form(self, template: TemplateConfig) -> None:
        self.top_margin_spin.setValue(template.margins_mm.top)
        self.bottom_margin_spin.setValue(template.margins_mm.bottom)
        self.left_margin_spin.setValue(template.margins_mm.left)
        self.right_margin_spin.setValue(template.margins_mm.right)
        self.line_spacing_spin.setValue(template.line_spacing_pt)
        if template.title.font_family in self.available_fonts:
            self.title_font_combo.setCurrentText(template.title.font_family)
        if template.h1.font_family in self.available_fonts:
            self.h1_font_combo.setCurrentText(template.h1.font_family)
        if template.h2.font_family in self.available_fonts:
            self.h2_font_combo.setCurrentText(template.h2.font_family)
        if template.body.font_family in self.available_fonts:
            self.body_font_combo.setCurrentText(template.body.font_family)
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
        self.default_template = load_default_template()
        self._refresh_font_combos([
            self.default_template.title.font_family,
            self.default_template.h1.font_family,
            self.default_template.h2.font_family,
            self.default_template.body.font_family,
        ])
        self._load_template_into_form(self.default_template)

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
            config_path = save_default_template(self.default_template)
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"默认参数保存失败：{exc}")
            return
        self._refresh_font_combos()
        self._set_status_message(f"默认参数已保存：{config_path}")
        QMessageBox.information(self, "保存成功", "当前参数已设为默认值，下次打开软件会自动加载。")

    def _load_local_fonts(self) -> None:
        options = get_installed_font_candidates()
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
            title=TextStyleConfig(font_family=self.title_font_combo.currentText(), font_size_hao=self.title_size_combo.currentText()),
            h1=TextStyleConfig(font_family=self.h1_font_combo.currentText(), font_size_hao=self.h1_size_combo.currentText()),
            h2=TextStyleConfig(font_family=self.h2_font_combo.currentText(), font_size_hao=self.h2_size_combo.currentText()),
            body=TextStyleConfig(font_family=self.body_font_combo.currentText(), font_size_hao=self.body_size_combo.currentText()),
        )

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
            exported_path = export_docx_document(text, self._build_template_from_form(), save_directory)
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






