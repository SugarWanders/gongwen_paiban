from __future__ import annotations

import re
from pathlib import Path

from app.models.settings import TemplateConfig, hao_to_pt
from app.services.title_classifier import classify_paragraphs


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]+')


def export_docx_document(text: str, template: TemplateConfig, save_directory: str) -> str:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.shared import Mm, Pt
    except ImportError as exc:
        raise RuntimeError("缺少 python-docx 依赖，暂时无法导出 .docx 文件。") from exc

    paragraphs = classify_paragraphs(text)
    if not paragraphs:
        raise ValueError("没有可导出的正文内容。")

    target_path = _build_export_path(paragraphs, save_directory)

    document = Document()
    section = document.sections[0]
    section.top_margin = Mm(template.margins_mm.top)
    section.bottom_margin = Mm(template.margins_mm.bottom)
    section.left_margin = Mm(template.margins_mm.left)
    section.right_margin = Mm(template.margins_mm.right)

    style_map = {
        "title": template.title,
        "h1": template.h1,
        "h2": template.h2,
        "body": template.body,
    }

    body_indent = Pt(hao_to_pt(template.body.font_size_hao) * 2)
    h1_indent = Pt(hao_to_pt(template.h1.font_size_hao) * 2)
    h2_indent = Pt(hao_to_pt(template.h2.font_size_hao) * 2)

    for paragraph_data in paragraphs:
        paragraph = document.add_paragraph()
        paragraph_type = paragraph_data["type"]
        config = style_map[paragraph_type]

        paragraph.paragraph_format.line_spacing = Pt(template.line_spacing_pt)
        paragraph.paragraph_format.first_line_indent = None
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)

        if paragraph_type == "title":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

        if paragraph_type == "body":
            paragraph.paragraph_format.first_line_indent = body_indent
        elif paragraph_type == "h1":
            paragraph.paragraph_format.first_line_indent = h1_indent
        elif paragraph_type == "h2":
            paragraph.paragraph_format.first_line_indent = h2_indent

        run = paragraph.add_run(paragraph_data["text"])
        run.font.name = config.font_family
        run.font.size = Pt(hao_to_pt(config.font_size_hao))

        r_pr = run._element.get_or_add_rPr()
        r_fonts = r_pr.rFonts
        r_fonts.set(qn("w:eastAsia"), config.font_family)

    document.save(str(target_path))
    return str(target_path)


def _build_export_path(paragraphs: list[dict[str, str]], save_directory: str) -> Path:
    directory = Path(save_directory).expanduser()
    if directory.suffix.lower() == ".docx":
        directory = directory.parent
    directory.mkdir(parents=True, exist_ok=True)

    original_title = paragraphs[0]["text"].strip() if paragraphs else ""
    safe_title = _sanitize_filename(original_title) or "排版结果"
    base_name = f"{safe_title}_排版结果"

    target_path = directory / f"{base_name}.docx"
    suffix_index = 1
    while target_path.exists():
        target_path = directory / f"{base_name}{suffix_index}.docx"
        suffix_index += 1

    return target_path


def _sanitize_filename(value: str) -> str:
    return INVALID_FILENAME_CHARS.sub("_", value).strip().strip(".")
