from __future__ import annotations

from dataclasses import asdict, dataclass


HAO_TO_PT = {
    "初号": 42.0,
    "小初": 36.0,
    "一号": 26.0,
    "小一": 24.0,
    "二号": 22.0,
    "小二": 18.0,
    "三号": 16.0,
    "小三": 15.0,
    "四号": 14.0,
    "小四": 12.0,
    "五号": 10.5,
    "小五": 9.0,
}

COMMON_FONTS = [
    "黑体",
    "仿宋",
]

FONT_FAMILY_ALIASES = {}

DEFAULT_FOCUS_FIELDS = [
    "分析认为",
    "一是",
    "二是",
    "三是",
    "四是",
    "五是",
]


@dataclass(slots=True)
class TextStyleConfig:
    font_family: str
    font_size_hao: str


@dataclass(slots=True)
class FocusFieldConfig:
    fields: list[str]
    style: TextStyleConfig
    bold: bool = True


@dataclass(slots=True)
class MarginConfig:
    top: int = 36
    bottom: int = 36
    left: int = 27
    right: int = 27


@dataclass(slots=True)
class TemplateConfig:
    margins_mm: MarginConfig
    line_spacing_pt: int
    title: TextStyleConfig
    h1: TextStyleConfig
    h2: TextStyleConfig
    body: TextStyleConfig
    clean_body_spaces: bool = True


DEFAULT_TEMPLATE = TemplateConfig(
    margins_mm=MarginConfig(),
    line_spacing_pt=30,
    title=TextStyleConfig(font_family="黑体", font_size_hao="二号"),
    h1=TextStyleConfig(font_family="黑体", font_size_hao="小二"),
    h2=TextStyleConfig(font_family="黑体", font_size_hao="小二"),
    body=TextStyleConfig(font_family="仿宋", font_size_hao="小二"),
    clean_body_spaces=True,
)

DEFAULT_FOCUS_FIELD_CONFIG = FocusFieldConfig(
    fields=list(DEFAULT_FOCUS_FIELDS),
    style=TextStyleConfig(font_family="仿宋", font_size_hao="小二"),
    bold=True,
)


def hao_to_pt(size_label: str) -> float:
    return HAO_TO_PT.get(size_label, HAO_TO_PT["小四"])


def template_to_dict(template: TemplateConfig) -> dict:
    data = asdict(template)
    for key in ("title", "h1", "h2", "body"):
        data[key]["font_family"] = normalize_config_font_family(data[key]["font_family"])
    return data


def template_from_dict(data: dict) -> TemplateConfig:
    if not isinstance(data, dict):
        return DEFAULT_TEMPLATE

    margins = _dict_value(data, "margins_mm")
    title = _dict_value(data, "title")
    h1 = _dict_value(data, "h1")
    h2 = _dict_value(data, "h2")
    body = _dict_value(data, "body")
    clean_body_spaces = data.get("clean_body_spaces", DEFAULT_TEMPLATE.clean_body_spaces)
    if not isinstance(clean_body_spaces, bool):
        clean_body_spaces = DEFAULT_TEMPLATE.clean_body_spaces

    return TemplateConfig(
        margins_mm=MarginConfig(
            top=int(margins.get("top", DEFAULT_TEMPLATE.margins_mm.top)),
            bottom=int(margins.get("bottom", DEFAULT_TEMPLATE.margins_mm.bottom)),
            left=int(margins.get("left", DEFAULT_TEMPLATE.margins_mm.left)),
            right=int(margins.get("right", DEFAULT_TEMPLATE.margins_mm.right)),
        ),
        line_spacing_pt=int(data.get("line_spacing_pt", DEFAULT_TEMPLATE.line_spacing_pt)),
        title=TextStyleConfig(
            font_family=normalize_config_font_family(title.get("font_family", DEFAULT_TEMPLATE.title.font_family)),
            font_size_hao=str(title.get("font_size_hao", DEFAULT_TEMPLATE.title.font_size_hao)),
        ),
        h1=TextStyleConfig(
            font_family=normalize_config_font_family(h1.get("font_family", DEFAULT_TEMPLATE.h1.font_family)),
            font_size_hao=str(h1.get("font_size_hao", DEFAULT_TEMPLATE.h1.font_size_hao)),
        ),
        h2=TextStyleConfig(
            font_family=normalize_config_font_family(h2.get("font_family", DEFAULT_TEMPLATE.h2.font_family)),
            font_size_hao=str(h2.get("font_size_hao", DEFAULT_TEMPLATE.h2.font_size_hao)),
        ),
        body=TextStyleConfig(
            font_family=normalize_config_font_family(body.get("font_family", DEFAULT_TEMPLATE.body.font_family)),
            font_size_hao=str(body.get("font_size_hao", DEFAULT_TEMPLATE.body.font_size_hao)),
        ),
        clean_body_spaces=clean_body_spaces,
    )


def _dict_value(data: dict, key: str) -> dict:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def focus_field_config_to_dict(config: FocusFieldConfig) -> dict:
    return {
        "fields": _normalize_focus_fields(config.fields),
        "style": {
            "font_family": normalize_config_font_family(config.style.font_family),
            "font_size_hao": config.style.font_size_hao,
        },
        "bold": bool(config.bold),
    }


def focus_field_config_from_dict(data: dict) -> FocusFieldConfig:
    style = data.get("style", {})

    return FocusFieldConfig(
        fields=_normalize_focus_fields(data.get("fields", DEFAULT_FOCUS_FIELDS)),
        style=TextStyleConfig(
            font_family=normalize_config_font_family(
                style.get("font_family", DEFAULT_FOCUS_FIELD_CONFIG.style.font_family)
            ),
            font_size_hao=str(style.get("font_size_hao", DEFAULT_FOCUS_FIELD_CONFIG.style.font_size_hao)),
        ),
        bold=bool(data.get("bold", DEFAULT_FOCUS_FIELD_CONFIG.bold)),
    )


def _normalize_focus_fields(values: list[str] | tuple[str, ...] | object) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return list(DEFAULT_FOCUS_FIELDS)

    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        field = value.strip()
        if field and field not in normalized:
            normalized.append(field)
    return normalized


def normalize_config_font_family(font_name: object) -> str:
    normalized = str(font_name).strip()
    return FONT_FAMILY_ALIASES.get(normalized, normalized)
