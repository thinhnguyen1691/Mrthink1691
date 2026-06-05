from __future__ import annotations

import re
import unicodedata


def safe_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_text(value: object) -> str:
    text = safe_str(value).lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def compact_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(value))
