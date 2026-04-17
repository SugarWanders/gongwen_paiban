from __future__ import annotations

from pathlib import Path


SUPPORTED_EXTENSIONS = {".docx", ".txt"}
TXT_ENCODINGS = ("utf-8", "utf-8-sig", "gb18030", "gbk")


def import_text_document(path: str) -> tuple[str, str]:
    file_path = Path(path)
    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("只能导入 .docx 或 .txt 文件。")

    if extension == ".txt":
        return _read_txt(file_path), file_path.name

    return _read_docx(file_path), file_path.name


def _read_txt(file_path: Path) -> str:
    for encoding in TXT_ENCODINGS:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("TXT 文件编码无法识别，请尝试另存为 UTF-8 后再导入。")


def _read_docx(file_path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("缺少 python-docx 依赖，暂时无法读取 .docx 文件。") from exc

    document = Document(str(file_path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)
