from __future__ import annotations

import re

from .text_utils import normalize_text, safe_str


COMPLETED_STATUS = "hoan tat"


STATUS_COLORS = {
    "cho xac nhan": ("#64748b", "#f1f5f9"),
    "dang lay hang": ("#1d4ed8", "#dbeafe"),
    "dang giao hang": ("#c2410c", "#ffedd5"),
    "da giao nha xe": ("#6d28d9", "#ede9fe"),
    "da giao chanh xe": ("#6d28d9", "#ede9fe"),
    "hoan tat": ("#047857", "#d1fae5"),
}


def normalize_status(status: object) -> str:
    text = normalize_text(status)
    return re.sub(r"^\d+\s*[.)-]?\s*", "", text).strip()


def is_completed_status(status: object) -> bool:
    return normalize_status(status) == COMPLETED_STATUS


def status_badge_html(status: object) -> str:
    label = safe_str(status) or "Chưa có trạng thái"
    color, background = STATUS_COLORS.get(normalize_status(label), ("#475569", "#f1f5f9"))
    return (
        f"<span style='display:inline-flex;align-items:center;border-radius:999px;"
        f"padding:4px 10px;background:{background};color:{color};"
        f"font-size:12px;font-weight:700;white-space:nowrap'>{label}</span>"
    )


def status_style(status: object) -> tuple[str, str]:
    return STATUS_COLORS.get(normalize_status(status), ("#475569", "#f1f5f9"))
