from __future__ import annotations

from .dates import to_date_key
from .text_utils import normalize_text, safe_str


def filter_rows(
    rows: list[dict],
    search: str = "",
    status: str = "",
    driver: str = "",
    date_from: str = "",
    date_to: str = "",
) -> list[dict]:
    search_key = normalize_text(search)

    return [
        row
        for row in rows
        if _matches_search(row, search_key)
        and (not status or row.get("status") == status)
        and (not driver or row.get("driver") == driver)
        and is_delivery_date_in_range(row.get("delivery_date", ""), date_from, date_to)
    ]


def is_delivery_date_in_range(delivery_date: object, date_from: str, date_to: str) -> bool:
    if not date_from and not date_to:
        return True

    date_key = to_date_key(delivery_date)
    if not date_key:
        return False

    if date_from and date_key < date_from:
        return False

    if date_to and date_key > date_to:
        return False

    return True


def get_filter_options(rows: list[dict]) -> dict[str, list[str]]:
    return {
        "statuses": sorted({safe_str(row.get("status")) for row in rows if safe_str(row.get("status"))}, key=normalize_text),
        "drivers": sorted({safe_str(row.get("driver")) for row in rows if safe_str(row.get("driver"))}, key=normalize_text),
    }


def sort_default(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            _month_desc(row.get("delivery_date")),
            normalize_text(row.get("route")),
            normalize_text(row.get("zone")),
            _desc(row.get("delivery_date")),
            safe_str(row.get("order_number")),
        ),
    )


def _matches_search(row: dict, search_key: str) -> bool:
    if not search_key:
        return True

    haystack = " ".join(
        [
            safe_str(row.get("order_number")),
            safe_str(row.get("delivery_date")),
            safe_str(row.get("customer_receive_date")),
            safe_str(row.get("customer_code")),
            safe_str(row.get("customer_name")),
            safe_str(row.get("driver")),
            safe_str(row.get("actual_driver")),
            safe_str(row.get("suggested_driver")),
            safe_str(row.get("route")),
            safe_str(row.get("zone")),
            safe_str(row.get("area")),
            safe_str(row.get("transport_company")),
            safe_str(row.get("order_value")),
            safe_str(row.get("volume")),
            safe_str(row.get("shipping_cost")),
            safe_str(row.get("status")),
            safe_str(row.get("note")),
            *[safe_str(value) for value in row.get("fields", {}).values()],
        ]
    )
    return search_key in normalize_text(haystack)


def _desc(value: object) -> str:
    date_key = to_date_key(value)
    return "".join(chr(255 - ord(char)) for char in date_key)


def _month_desc(value: object) -> str:
    date_key = to_date_key(value)
    month_key = date_key[:7] if date_key else ""
    return "".join(chr(255 - ord(char)) for char in month_key)
