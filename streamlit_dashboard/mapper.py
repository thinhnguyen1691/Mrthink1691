from __future__ import annotations

from .text_utils import compact_text, safe_str


FIELD_ALIASES: dict[str, list[str]] = {
    "order_number": ["so don hang", "số đơn hàng", "ma don hang", "mã đơn hàng", "don hang", "đơn hàng", "order", "order number", "order id"],
    "delivery_date": ["ngay giao hang", "ngày giao hàng", "ngay giao", "ngày giao", "delivery date", "date"],
    "customer_receive_date": ["ngay khach nhan", "ngày khách nhận", "ngay khach nhan hang", "ngày khách nhận hàng", "customer receive date", "received date"],
    "customer_code": ["ma khach hang", "mã khách hàng", "ma kh", "mã kh", "customer code", "customer id"],
    "customer_name": ["ten khach hang", "tên khách hàng", "ten kh", "tên kh", "khach hang", "khách hàng", "customer name", "customer"],
    "address": ["dia chi", "địa chỉ", "address", "delivery address"],
    "phone": ["so dien thoai", "số điện thoại", "dien thoai", "điện thoại", "sdt", "phone", "phone number"],
    "driver": ["nhan vien giao hang", "nhân viên giao hàng", "nvgh", "shipper", "tai xe", "tài xế", "driver", "delivery staff"],
    "driver_email": ["email nhan vien giao hang", "email nhân viên giao hàng", "email nvgh", "driver email", "shipper email", "email tai xe", "email tài xế"],
    "suggested_driver": ["nvgh goi y", "nvgh gợi ý", "nhan vien giao hang goi y", "nhân viên giao hàng gợi ý", "suggested driver"],
    "actual_driver": ["nvgh thuc hien", "nvgh thực hiện", "nhan vien giao hang thuc hien", "nhân viên giao hàng thực hiện", "actual driver", "driver done"],
    "route": ["tuyen", "tuyến", "route", "delivery route"],
    "zone": ["zone", "vung", "vùng"],
    "area": ["khu vuc", "khu vực", "area", "region"],
    "transport_company": ["nha xe", "nhà xe", "chanh xe", "chành xe", "transport company", "carrier"],
    "package_count": ["so kien", "số kiện", "packages", "package count", "kien", "kiện"],
    "shipping_cost": ["chi phi van chuyen", "chi phí vận chuyển", "phi van chuyen", "phí vận chuyển", "shipping cost", "freight cost"],
    "order_value": ["gia tri don hang", "giá trị đơn hàng", "gia tri", "giá trị", "order value", "total value"],
    "volume": ["so khoi", "số khối", "khoi", "khối", "volume", "cbm"],
    "status": ["trang thai", "trạng thái", "status", "tinh trang", "tình trạng"],
    "note": ["ghi chu", "ghi chú", "note", "notes", "remark", "remarks", "su co", "sự cố"],
}


def map_sheet_rows(headers: list[str], rows: list[list[str]]) -> list[dict]:
    normalized_headers = [safe_str(header) or f"Column {index + 1}" for index, header in enumerate(headers)]
    index_map = create_index_map(normalized_headers)
    records: list[dict] = []

    for row_index, row in enumerate(rows):
        fields = {header: safe_str(row[index]) if index < len(row) else "" for index, header in enumerate(normalized_headers)}
        if not any(fields.values()):
            continue

        suggested_driver = get_mapped_value(row, index_map, "suggested_driver")
        actual_driver = get_mapped_value(row, index_map, "actual_driver")
        legacy_driver = get_mapped_value(row, index_map, "driver")
        driver = actual_driver or legacy_driver or suggested_driver
        order_number = get_mapped_value(row, index_map, "order_number")

        records.append(
            {
                "id": f"order-{order_number}-{row_index + 2}" if order_number else f"row-{row_index + 2}",
                "row_number": row_index + 2,
                "fields": fields,
                "order_number": order_number,
                "delivery_date": get_mapped_value(row, index_map, "delivery_date"),
                "customer_receive_date": get_mapped_value(row, index_map, "customer_receive_date"),
                "customer_code": get_mapped_value(row, index_map, "customer_code"),
                "customer_name": get_mapped_value(row, index_map, "customer_name"),
                "address": get_mapped_value(row, index_map, "address"),
                "phone": get_mapped_value(row, index_map, "phone"),
                "driver": driver,
                "driver_email": get_mapped_value(row, index_map, "driver_email"),
                "suggested_driver": suggested_driver,
                "actual_driver": actual_driver,
                "route": get_mapped_value(row, index_map, "route"),
                "zone": get_mapped_value(row, index_map, "zone"),
                "area": get_mapped_value(row, index_map, "area"),
                "transport_company": get_mapped_value(row, index_map, "transport_company"),
                "package_count": get_mapped_value(row, index_map, "package_count"),
                "shipping_cost": get_mapped_value(row, index_map, "shipping_cost"),
                "order_value": get_mapped_value(row, index_map, "order_value"),
                "volume": get_mapped_value(row, index_map, "volume"),
                "status": get_mapped_value(row, index_map, "status"),
                "note": get_mapped_value(row, index_map, "note"),
            }
        )

    return records


def create_index_map(headers: list[str]) -> dict[str, int]:
    index_map: dict[str, int] = {}
    compact_headers = [compact_text(header) for header in headers]

    for field, aliases in FIELD_ALIASES.items():
        alias_keys = {compact_text(alias) for alias in aliases}
        for index, compact_header in enumerate(compact_headers):
            if compact_header in alias_keys:
                index_map[field] = index
                break

    return index_map


def get_mapped_value(row: list[str], index_map: dict[str, int], field: str) -> str:
    index = index_map.get(field)
    if index is None or index >= len(row):
        return ""
    return safe_str(row[index])
