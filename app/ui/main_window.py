from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QSpinBox,
)

from app.models.settings import HAO_TO_PT, MarginConfig, TemplateConfig, TextStyleConfig
from app.services.document_importer import import_text_document
from app.services.export_service import export_docx_document
from app.services.font_service import get_common_fonts
from app.services.template_store import load_default_template, save_default_template
from app.services.save_path_store import load_default_save_path, save_default_save_path
from app.services.title_classifier import classify_paragraphs


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("公文排版助手 V1.0")
        self.resize(880, 560)
        self.setMinimumSize(820, 520)

        self.current_file_name = "未导入文件"
        self.default_template = load_default_template()
        self.default_save_path = self._normalize_save_directory(load_default_save_path())
        self.last_declined_default_save_path: str | None = None
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
        fonts = list(get_common_fonts())
        for font_name in (
            self.default_template.title.font_family,
            self.default_template.h1.font_family,
            self.default_template.h2.font_family,
            self.default_template.body.font_family,
        ):
            if font_name not in fonts:
                fonts.append(font_name)
        return fonts

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

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.addWidget(self._build_editor_panel())
        splitter.addWidget(self._build_settings_panel())
        splitter.setSizes([430, 330])
        root_layout.addWidget(splitter)

        status_bar = QStatusBar()
        status_bar.showMessage("公文排版助手已就绪。")
        self.setStatusBar(status_bar)

    def _build_editor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("card")

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
        self.editor.setFrameShape(QFrame.NoFrame)

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
        panel.setObjectName("card")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(340)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(2)

        title = QLabel("参数设置")
        title.setObjectName("sectionTitle")

        action_row = QHBoxLayout()
        action_row.setSpacing(5)
        self.restore_defaults_button = QPushButton("恢复默认参数")
        self.restore_defaults_button.setObjectName("actionButton")
        self.restore_defaults_button.setFixedSize(84, 20)
        self.set_default_button = QPushButton("当前参数设为默认值")
        self.set_default_button.setObjectName("actionButton")
        self.set_default_button.setFixedSize(114, 20)
        action_row.addWidget(self.restore_defaults_button)
        action_row.addWidget(self.set_default_button)
        action_row.addStretch(1)

        settings_card = QFrame()
        settings_card.setObjectName("softCard")
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(2)

        settings_layout.addWidget(self._build_page_section())
        settings_layout.addWidget(self._build_paragraph_section())
        settings_layout.addWidget(self._build_text_style_section())
        settings_layout.addWidget(self._build_export_section())

        self.contact_label = QLabel("\u5982\u6709\u95ee\u9898\u6216\u5efa\u8bae\u8bf7\u8054\u7cfbwoomytown@163.com")
        self.contact_label.setObjectName("footerHint")
        self.contact_label.setWordWrap(False)
        self.contact_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        content_layout.addWidget(title)
        content_layout.addLayout(action_row)
        content_layout.addWidget(settings_card)
        content_layout.addStretch(1)
        content_layout.addWidget(self.contact_label, 0, Qt.AlignRight | Qt.AlignBottom)

        scroll_area.setWidget(content)
        panel_layout.addWidget(scroll_area)
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

    def _add_margin_row(
        self,
        grid: QGridLayout,
        row: int,
        left_label: str,
        left_spin: QSpinBox,
        right_label: str,
        right_spin: QSpinBox,
    ) -> None:
        left_label_widget = QLabel(left_label)
        left_label_widget.setFixedWidth(40)
        left_label_widget.setAlignment(Qt.AlignCenter)
        left_unit_widget = QLabel("毫米")
        left_unit_widget.setFixedWidth(20)
        left_unit_widget.setAlignment(Qt.AlignCenter)
        right_label_widget = QLabel(right_label)
        right_label_widget.setFixedWidth(40)
        right_label_widget.setAlignment(Qt.AlignCenter)
        right_unit_widget = QLabel("毫米")
        right_unit_widget.setFixedWidth(20)
        right_unit_widget.setAlignment(Qt.AlignCenter)

        spacer = QWidget()
        spacer.setFixedWidth(18)
        grid.addWidget(left_label_widget, row, 0)
        grid.addWidget(left_spin, row, 1)
        grid.addWidget(left_unit_widget, row, 2)
        grid.addWidget(spacer, row, 3)
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

        row = QHBoxLayout()
        row.setSpacing(4)
        self.line_spacing_spin = self._create_spinbox(10, 80, "lineField")
        line_label = QLabel("固定行距")
        line_label.setFixedWidth(48)
        line_label.setAlignment(Qt.AlignCenter)
        unit_label = QLabel("pt")
        unit_label.setFixedWidth(16)
        unit_label.setAlignment(Qt.AlignCenter)
        row.addWidget(line_label)
        row.addWidget(self.line_spacing_spin)
        row.addWidget(unit_label)
        row.addStretch(1)

        layout.addWidget(title)
        layout.addLayout(row)
        return section

    def _build_text_style_section(self) -> QFrame:
        section = QFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

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
        self.save_path_edit.setMaximumWidth(188)
        self.save_path_edit.setAlignment(Qt.AlignCenter)

        self.select_path_button = QPushButton("选择保存位置")
        self.select_path_button.setObjectName("pathButton")
        self.select_path_button.setFixedSize(76, 20)
        self.export_button = QPushButton("生成 .docx")
        self.export_button.setObjectName("primaryButton")
        self.export_button.setFixedHeight(20)

        path_row = QHBoxLayout()
        path_row.setSpacing(4)
        path_row.addWidget(self.save_path_edit, 1)
        path_row.addWidget(self.select_path_button)

        layout.addWidget(title)
        layout.addLayout(path_row)
        layout.addWidget(self.export_button)
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
        font_label.setAlignment(Qt.AlignCenter)
        row.addWidget(font_label, 0, 0)

        font_combo = QComboBox()
        font_combo.setObjectName("fontField")
        font_combo.setFixedSize(78, 20)
        self._configure_centered_combo(font_combo)
        row.addWidget(font_combo, 0, 1)

        size_label = QLabel("字号")
        size_label.setFixedWidth(24)
        size_label.setAlignment(Qt.AlignCenter)
        row.addWidget(size_label, 0, 2)

        size_combo = QComboBox()
        size_combo.setObjectName("sizeField")
        size_combo.setFixedSize(36, 20)
        self._configure_centered_combo(size_combo)
        size_combo.addItems(list(HAO_TO_PT.keys()))
        for index in range(size_combo.count()):
            size_combo.setItemData(index, Qt.AlignCenter, Qt.TextAlignmentRole)
        row.addWidget(size_combo, 0, 3)
        row.setColumnStretch(4, 1)

        layout.addWidget(section_label)
        layout.addLayout(row)
        parent_layout.addWidget(wrapper)
        return font_combo, size_combo

    def _create_spinbox(self, minimum: int, maximum: int, object_name: str) -> QSpinBox:
        spinbox = QSpinBox()
        spinbox.setObjectName(object_name)
        spinbox.setRange(minimum, maximum)
        spinbox.setFixedSize(36, 20)
        spinbox.setAlignment(Qt.AlignCenter)
        spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        return spinbox

    def _configure_centered_combo(self, combo: QComboBox) -> None:
        combo.setEditable(True)
        combo.lineEdit().setReadOnly(True)
        combo.lineEdit().setAlignment(Qt.AlignCenter)
        combo.lineEdit().setCursor(Qt.ArrowCursor)

    def _bind_events(self) -> None:
        self.import_button.clicked.connect(self._import_file)
        self.clear_button.clicked.connect(self._clear_editor)
        self.restore_defaults_button.clicked.connect(self._restore_default_parameters)
        self.set_default_button.clicked.connect(self._set_current_as_default)
        self.select_path_button.clicked.connect(self._select_save_path)
        self.export_button.clicked.connect(self._export_document)
        self.editor.textChanged.connect(self._refresh_statistics)

    def _populate_style_font_combos(self, fonts: list[str]) -> None:
        combos = [
            self.title_font_combo,
            self.h1_font_combo,
            self.h2_font_combo,
            self.body_font_combo,
        ]
        defaults = [
            self.default_template.title.font_family,
            self.default_template.h1.font_family,
            self.default_template.h2.font_family,
            self.default_template.body.font_family,
        ]

        for combo, default_value in zip(combos, defaults):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(fonts)
            for index in range(combo.count()):
                combo.setItemData(index, Qt.AlignCenter, Qt.TextAlignmentRole)
            if default_value in fonts:
                combo.setCurrentText(default_value)
            elif fonts:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def _load_template_into_form(self, template: TemplateConfig) -> None:
        self.top_margin_spin.setValue(template.margins_mm.top)
        self.bottom_margin_spin.setValue(template.margins_mm.bottom)
        self.left_margin_spin.setValue(template.margins_mm.left)
        self.right_margin_spin.setValue(template.margins_mm.right)
        self.line_spacing_spin.setValue(template.line_spacing_pt)

        self.title_font_combo.setCurrentText(template.title.font_family)
        self.h1_font_combo.setCurrentText(template.h1.font_family)
        self.h2_font_combo.setCurrentText(template.h2.font_family)
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
        if state == "default":
            palette.setColor(QPalette.ColorRole.Text, QColor("#A8B5C7"))
        else:
            palette.setColor(QPalette.ColorRole.Text, QColor("#163056"))
        self.editor.setPalette(palette)
        self.editor.viewport().update()

    def _import_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文档",
            "",
            "支持的文件 (*.docx *.txt)",
        )
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
        self.statusBar().showMessage(f"已导入文件：{file_name}")

    def _clear_editor(self) -> None:
        if self._is_default_editor_content(self.editor.toPlainText()):
            return

        result = QMessageBox.question(
            self,
            "清空内容",
            "确定要清空当前编辑内容吗？",
        )
        if result != QMessageBox.Yes:
            return

        self.current_file_name = "未导入文件"
        self._reset_editor_to_default_text()
        self._update_editor_visual_state()
        self._refresh_statistics()
        self.statusBar().showMessage("编辑内容已恢复为默认说明。")

    def _restore_default_parameters(self) -> None:
        self.default_template = load_default_template()
        self.available_fonts = self._build_available_fonts()
        self._populate_style_font_combos(self.available_fonts)
        self._load_template_into_form(self.default_template)
        self.statusBar().showMessage("已恢复默认参数。")

    def _set_current_as_default(self) -> None:
        self.default_template = self._build_template_from_form()
        try:
            config_path = save_default_template(self.default_template)
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"默认参数保存失败：{exc}")
            return

        self.available_fonts = self._build_available_fonts()
        self._populate_style_font_combos(self.available_fonts)
        self.statusBar().showMessage(f"默认参数已保存：{config_path}")
        QMessageBox.information(self, "保存成功", "当前参数已设为默认值，下次打开软件会自动加载。")

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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if result == QMessageBox.Yes:
            try:
                config_path = save_default_save_path(normalized_path)
            except OSError as exc:
                QMessageBox.critical(self, "保存失败", f"默认保存路径保存失败：{exc}")
                return

            self.default_save_path = normalized_path
            self.last_declined_default_save_path = None
            self.statusBar().showMessage(f"默认保存路径已更新：{config_path}")
            return

        self.last_declined_default_save_path = normalized_path

    def _select_save_path(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择保存文件夹",
            self._resolve_initial_save_directory(),
        )
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
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(f"文档已生成：\n{exported_path}")
        open_button = dialog.addButton("打开文档", QMessageBox.ActionRole)
        reveal_button = dialog.addButton("在文件夹中显示", QMessageBox.ActionRole)
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
                font_family=self.title_font_combo.currentText(),
                font_size_hao=self.title_size_combo.currentText(),
            ),
            h1=TextStyleConfig(
                font_family=self.h1_font_combo.currentText(),
                font_size_hao=self.h1_size_combo.currentText(),
            ),
            h2=TextStyleConfig(
                font_family=self.h2_font_combo.currentText(),
                font_size_hao=self.h2_size_combo.currentText(),
            ),
            body=TextStyleConfig(
                font_family=self.body_font_combo.currentText(),
                font_size_hao=self.body_size_combo.currentText(),
            ),
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

        self.statusBar().showMessage(f"导出成功：{exported_path}")
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
