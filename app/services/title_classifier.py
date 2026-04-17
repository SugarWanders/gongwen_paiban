from __future__ import annotations

import re


H1_PATTERN = re.compile(r"^[一二三四五六七八九十百千万]+、")
H2_PATTERN = re.compile(r"^（[一二三四五六七八九十百千万]+）")


def split_paragraphs(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def classify_paragraphs(text: str) -> list[dict[str, str]]:
    paragraphs = split_paragraphs(text)
    classified: list[dict[str, str]] = []

    for index, paragraph in enumerate(paragraphs):
        if index == 0:
            paragraph_type = "title"
        elif H1_PATTERN.match(paragraph):
            paragraph_type = "h1"
        elif H2_PATTERN.match(paragraph):
            paragraph_type = "h2"
        else:
            paragraph_type = "body"

        classified.append({"text": paragraph, "type": paragraph_type})

    return classified
