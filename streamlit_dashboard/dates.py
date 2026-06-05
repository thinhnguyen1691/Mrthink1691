from __future__ import annotations

import re
from datetime import date, datetime

import pandas as pd

from .text_utils import safe_str


def to_date_key(value: object) -> str:
    text = safe_str(value)
    if not text:
        return ""

    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso_match:
        return f"{iso_match.group(1)}-{iso_match.group(2).zfill(2)}-{iso_match.group(3).zfill(2)}"

    vn_match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", text)
    if vn_match:
        year = vn_match.group(3)
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{vn_match.group(2).zfill(2)}-{vn_match.group(1).zfill(2)}"

    parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return ""

    return parsed.strftime("%Y-%m-%d")


def date_input_to_key(value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return to_date_key(value)


def format_date_key(value: str) -> str:
    if not value:
        return ""

    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value
