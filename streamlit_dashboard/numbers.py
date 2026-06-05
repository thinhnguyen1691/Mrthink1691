from __future__ import annotations

import re

from .text_utils import safe_str


def parse_sheet_number(value: object) -> float:
    raw = safe_str(value)
    if not raw:
        return 0.0

    cleaned = re.sub(r"[^\d,.-]", "", raw)
    comma_count = cleaned.count(",")
    dot_count = cleaned.count(".")
    last_comma = cleaned.rfind(",")
    last_dot = cleaned.rfind(".")
    normalized = cleaned

    if comma_count and dot_count:
        decimal_separator = "," if last_comma > last_dot else "."
        thousand_separator = "." if decimal_separator == "," else ","
        normalized = cleaned.replace(thousand_separator, "").replace(decimal_separator, ".")
    elif comma_count:
        normalized = _normalize_single_separator(cleaned, ",", comma_count)
    elif dot_count:
        normalized = _normalize_single_separator(cleaned, ".", dot_count)

    try:
        return float(normalized)
    except ValueError:
        return 0.0


def format_number(value: float, digits: int = 2) -> str:
    text = f"{value:,.{digits}f}"
    if digits:
        text = text.rstrip("0").rstrip(".")
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def format_currency(value: float) -> str:
    return f"{format_number(round(value), 0)} đ"


def _normalize_single_separator(value: str, separator: str, count: int) -> str:
    if count > 1:
        return value.replace(separator, "")

    fraction = value.split(separator, 1)[1] if separator in value else ""
    if len(fraction) == 3:
        return value.replace(separator, "")

    return value.replace(separator, ".")
