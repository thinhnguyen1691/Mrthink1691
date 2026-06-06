from __future__ import annotations

from datetime import datetime
from html import escape

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from streamlit_dashboard.auth import AppUser, apply_row_security, authenticate, get_configured_users
from streamlit_dashboard.config import load_env
from streamlit_dashboard.dates import date_input_to_key, format_date_key, to_date_key
from streamlit_dashboard.filters import filter_rows, get_filter_options, sort_default
from streamlit_dashboard.numbers import format_currency, format_number, parse_sheet_number
from streamlit_dashboard.sheets import read_delivery_sheet
from streamlit_dashboard.status import is_completed_status, status_badge_html, status_style
from streamlit_dashboard.text_utils import normalize_text, safe_str


load_env()

st.set_page_config(
    page_title="Theo dõi giao hàng",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
  .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
  [data-testid="stMetricValue"] { font-size: 1.55rem; line-height: 1.15; }
  [data-testid="stMetricLabel"] { color: #475569; }
  .ops-card {
    border: 1px solid #dbe3ef;
    background: #fff;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  }
  .muted { color: #64748b; font-size: 13px; }
  .card-title { font-weight: 750; color: #0f172a; margin-bottom: 4px; }
  .card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; font-size: 13px; color: #334155; }
  .detail-table td { padding: 6px 8px; border-bottom: 1px solid #edf2f7; vertical-align: top; }
  .detail-table td:first-child { width: 220px; color: #64748b; font-weight: 700; }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 8px 0 20px;
  }
  .kpi-card {
    position: relative;
    overflow: hidden;
    min-height: 118px;
    border: 1px solid rgba(148, 163, 184, 0.32);
    border-radius: 14px;
    padding: 16px 16px 14px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    box-shadow: 0 14px 28px rgba(15, 23, 42, 0.10), 0 2px 6px rgba(15, 23, 42, 0.05);
  }
  .kpi-card::after {
    content: "";
    position: absolute;
    right: -30px;
    top: -30px;
    width: 88px;
    height: 88px;
    border-radius: 50%;
    background: var(--accent-soft);
  }
  .kpi-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    position: relative;
    z-index: 1;
  }
  .kpi-label {
    color: #64748b;
    font-size: 12.5px;
    line-height: 1.25;
    font-weight: 800;
    letter-spacing: 0;
  }
  .kpi-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 10px;
    color: var(--accent);
    background: var(--accent-soft);
    font-size: 12px;
    font-weight: 850;
    flex: 0 0 auto;
  }
  .kpi-value {
    position: relative;
    z-index: 1;
    margin-top: 14px;
    color: #0f172a;
    font-size: clamp(22px, 1.7vw, 30px);
    line-height: 1.12;
    font-weight: 850;
    overflow-wrap: anywhere;
  }
  .kpi-sub {
    position: relative;
    z-index: 1;
    margin-top: 7px;
    color: #64748b;
    font-size: 12px;
    line-height: 1.3;
  }
  .ops-table-wrap {
    width: 100%;
    max-height: 660px;
    overflow: auto;
    border: 1px solid #dbe3ef;
    border-radius: 12px;
    background: #fff;
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.07);
  }
  .ops-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    table-layout: fixed;
    font-size: 13px;
  }
  .ops-table th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: #f8fafc;
    color: #475569;
    padding: 11px 10px;
    border-bottom: 1px solid #dbe3ef;
    text-align: left;
    font-size: 11px;
    text-transform: uppercase;
  }
  .ops-table td {
    padding: 11px 10px;
    border-bottom: 1px solid #edf2f7;
    color: #0f172a;
    vertical-align: middle;
    word-break: break-word;
  }
  .ops-table tr:hover td { background: #f8fafc; }
  .ops-table .num { width: 74px; font-weight: 800; }
  .ops-table .date { width: 86px; }
  .ops-table .route { width: 118px; }
  .ops-table .zone { width: 92px; }
  .ops-table .customer { width: 220px; }
  .ops-table .driver { width: 132px; }
  .ops-table .status { width: 128px; }
  .ops-table .money { width: 138px; text-align: right; }
  .cell-main { font-weight: 750; }
  .cell-sub { color: #64748b; font-size: 12px; margin-top: 2px; }
  .status-pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 11.5px;
    font-weight: 800;
    line-height: 1.2;
    white-space: normal;
  }
  @media (max-width: 1100px) {
    .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .ops-table { min-width: 980px; }
  }
  @media (max-width: 700px) {
    .kpi-grid { grid-template-columns: 1fr; }
    .kpi-value { font-size: 25px; }
  }
</style>
"""


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not require_login():
        return

    user: AppUser = st.session_state["user"]
    render_sidebar_user(user)

    try:
        data = get_sheet_data(st.session_state.get("refresh_token", 0))
    except Exception as exc:
        st.error(f"Lỗi kết nối Google Sheet: {exc}")
        st.stop()

    all_rows = apply_row_security(data["rows"], user)
    options = get_filter_options(all_rows)
    filters = render_filters(options)
    filtered_rows = sort_default(filter_rows(all_rows, **filters))

    render_header(data, len(all_rows), len(filtered_rows))

    tab_dashboard, tab_report, tab_list = st.tabs(["Dashboard", "Báo cáo", "Danh sách giao hàng"])
    with tab_dashboard:
        render_dashboard(filtered_rows, filters)
    with tab_report:
        render_report(filtered_rows, filters)
    with tab_list:
        render_delivery_list(filtered_rows)


def require_login() -> bool:
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        return True

    users = get_configured_users()
    left, center, right = st.columns([1, 1.1, 1])
    with center:
        st.title("Theo dõi giao hàng")
        st.caption("Dashboard nội bộ, chỉ đọc dữ liệu từ Google Sheet.")

        if not users:
            st.error("Chưa cấu hình AUTH_USERS trong .env.local.")
            return False

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", value="admin@example.com")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

        if submitted:
            user = authenticate(email, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user"] = user
                st.rerun()
            st.error("Email hoặc mật khẩu không đúng.")

    return False


def render_sidebar_user(user: AppUser) -> None:
    with st.sidebar:
        st.subheader("Người dùng")
        st.write(user.name or user.email)
        st.caption(f"{user.email} · {user.role.upper()}")
        if st.button("Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def render_filters(options: dict[str, list[str]]) -> dict[str, str]:
    with st.sidebar:
        st.divider()
        st.subheader("Bộ lọc")
        search = st.text_input("Tìm kiếm", placeholder="Số đơn, khách hàng, tuyến, zone...", key="filter_search")
        status = st.selectbox(
            "Trạng thái",
            [""] + options["statuses"],
            format_func=lambda value: value or "Tất cả trạng thái",
            key="filter_status",
        )
        driver = st.selectbox(
            "NVGH thực hiện",
            [""] + options["drivers"],
            format_func=lambda value: value or "Tất cả NVGH",
            key="filter_driver",
        )

        date_from_raw = st.date_input("Từ ngày giao", value=None, format="DD/MM/YYYY", key="filter_date_from")
        date_to_raw = st.date_input("Đến ngày giao", value=None, format="DD/MM/YYYY", key="filter_date_to")
        date_from = date_input_to_key(date_from_raw)
        date_to = date_input_to_key(date_to_raw)

        if date_from and date_to and date_from > date_to:
            st.warning("Khoảng ngày chưa hợp lệ: Từ ngày đang lớn hơn Đến ngày.")

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Refresh", use_container_width=True):
                get_sheet_data.clear()
                st.session_state["refresh_token"] = st.session_state.get("refresh_token", 0) + 1
                st.rerun()
        with col_b:
            if st.button("Reset", use_container_width=True):
                for key in ("filter_search", "filter_status", "filter_driver", "filter_date_from", "filter_date_to"):
                    st.session_state.pop(key, None)
                st.rerun()

        auto_refresh = st.selectbox("Tự động refresh", [0, 60, 180, 300], format_func=lambda value: "Tắt" if value == 0 else f"{value // 60} phút")
        if auto_refresh:
            st.markdown(f"<meta http-equiv='refresh' content='{auto_refresh}'>", unsafe_allow_html=True)

    return {
        "search": search,
        "status": status,
        "driver": driver,
        "date_from": date_from,
        "date_to": date_to,
    }


def render_header(data: dict, total_rows: int, filtered_count: int) -> None:
    title_col, action_col = st.columns([1, 0.35])
    with title_col:
        st.title("Theo dõi giao hàng")
        st.caption(f"Sheet: {data['sheet_title']} · Dữ liệu read-only qua Google Sheets API")
    with action_col:
        st.caption(f"Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
        st.metric("Đang hiển thị", f"{filtered_count:,}".replace(",", "."), delta=f"Tổng {total_rows:,}".replace(",", "."))


def render_dashboard(rows: list[dict], filters: dict[str, str]) -> None:
    if not rows:
        st.info("Chưa có dữ liệu phù hợp bộ lọc.")
        return

    summary = build_summary(rows)
    date_label = format_range_label(filters["date_from"], filters["date_to"])

    render_kpi_grid(summary, date_label)

    left, right = st.columns([1, 1])
    with left:
        status_df = pd.DataFrame(summary["status_counts"], columns=["Trạng thái", "Số đơn"])
        render_pie_panel("Số đơn theo trạng thái", status_df, "Trạng thái", use_status_colors=True)

    with right:
        driver_df = pd.DataFrame(summary["driver_counts"], columns=["NVGH", "Số đơn"])
        render_pie_panel("Số đơn theo NVGH thực hiện", driver_df, "NVGH", use_status_colors=False)


def render_pie_panel(title: str, df: pd.DataFrame, label_column: str, use_status_colors: bool) -> None:
    with st.container(border=True):
        st.subheader(title)
        if df.empty:
            st.info("Chưa có dữ liệu.")
            return

        chart_df = compact_pie_dataframe(df, label_column)
        total = chart_df["Số đơn"].sum()
        chart_df["Tỉ lệ"] = chart_df["Số đơn"] / total * 100 if total else 0

        color = build_pie_color_encoding(chart_df, label_column, use_status_colors)
        chart = (
            alt.Chart(chart_df)
            .mark_arc(innerRadius=64, outerRadius=118, cornerRadius=4, padAngle=0.012)
            .encode(
                theta=alt.Theta("Số đơn:Q", title="Số đơn"),
                color=color,
                tooltip=[
                    alt.Tooltip(f"{label_column}:N", title=label_column),
                    alt.Tooltip("Số đơn:Q", title="Số đơn", format=","),
                    alt.Tooltip("Tỉ lệ:Q", title="Tỉ lệ", format=".1f"),
                ],
            )
            .properties(height=330)
        )
        st.altair_chart(chart, use_container_width=True)


def compact_pie_dataframe(df: pd.DataFrame, label_column: str, max_items: int = 8) -> pd.DataFrame:
    if len(df) <= max_items:
        return df.copy()

    top = df.head(max_items - 1).copy()
    other_count = df.iloc[max_items - 1 :]["Số đơn"].sum()
    other = pd.DataFrame([{label_column: "Khác", "Số đơn": other_count}])
    return pd.concat([top, other], ignore_index=True)


def build_pie_color_encoding(df: pd.DataFrame, label_column: str, use_status_colors: bool):
    if not use_status_colors:
        palette = ["#2563eb", "#0f766e", "#ea580c", "#7c3aed", "#0891b2", "#d97706", "#475569", "#be123c", "#16a34a"]
        return alt.Color(
            f"{label_column}:N",
            legend=alt.Legend(orient="bottom", columns=2),
            scale=alt.Scale(range=palette),
        )

    domain = df[label_column].tolist()
    color_range = [status_style(status)[0] for status in domain]
    return alt.Color(
        f"{label_column}:N",
        legend=alt.Legend(orient="bottom", columns=2),
        scale=alt.Scale(domain=domain, range=color_range),
    )


def render_kpi_grid(summary: dict, date_label: str) -> None:
    cards = [
        {
            "label": "Tổng số đơn",
            "value": format_number(summary["total"], 0),
            "sub": "Số đơn trong phạm vi đang lọc",
            "icon": "ĐH",
            "accent": "#2563eb",
            "soft": "#dbeafe",
        },
        {
            "label": "Chưa hoàn tất",
            "value": format_number(summary["unfinished"], 0),
            "sub": "Các đơn chưa ở trạng thái Hoàn Tất",
            "icon": "CH",
            "accent": "#d97706",
            "soft": "#fef3c7",
        },
        {
            "label": "Hoàn tất",
            "value": format_number(summary["completed"], 0),
            "sub": "Trạng thái 4. Hoàn Tất",
            "icon": "HT",
            "accent": "#059669",
            "soft": "#d1fae5",
        },
        {
            "label": "NVGH thực hiện",
            "value": format_number(summary["driver_count"], 0),
            "sub": "Số nhân viên đang có đơn",
            "icon": "NV",
            "accent": "#0f766e",
            "soft": "#ccfbf1",
        },
        {
            "label": "Giá trị đơn hàng",
            "value": format_currency(summary["order_value"]),
            "sub": "Tổng giá trị theo bộ lọc",
            "icon": "₫",
            "accent": "#334155",
            "soft": "#e2e8f0",
        },
        {
            "label": "Số khối",
            "value": format_number(summary["volume"]),
            "sub": "Tổng số khối giao hàng",
            "icon": "M3",
            "accent": "#7c3aed",
            "soft": "#ede9fe",
        },
        {
            "label": "Chi phí vận chuyển",
            "value": format_currency(summary["shipping_cost"]),
            "sub": "Tổng chi phí vận chuyển",
            "icon": "VC",
            "accent": "#ea580c",
            "soft": "#ffedd5",
        },
        {
            "label": "Khoảng ngày",
            "value": date_label,
            "sub": "Theo Ngày Giao Hàng",
            "icon": "TG",
            "accent": "#0891b2",
            "soft": "#cffafe",
        },
    ]
    html = ["<div class='kpi-grid'>"]
    for card in cards:
        html.append(
            "<div class='kpi-card' style='--accent:{accent};--accent-soft:{soft}'>"
            "<div class='kpi-top'>"
            "<div class='kpi-label'>{label}</div>"
            "<div class='kpi-icon'>{icon}</div>"
            "</div>"
            "<div class='kpi-value'>{value}</div>"
            "<div class='kpi-sub'>{sub}</div>"
            "</div>".format(
                accent=card["accent"],
                soft=card["soft"],
                label=escape(card["label"]),
                icon=escape(card["icon"]),
                value=escape(str(card["value"])),
                sub=escape(card["sub"]),
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_report(rows: list[dict], filters: dict[str, str]) -> None:
    if not rows:
        st.info("Chưa có dữ liệu phù hợp bộ lọc.")
        return

    date_label = format_range_label(filters["date_from"], filters["date_to"])
    report_summary = build_report_summary(rows)
    driver_report = build_report_by_driver(rows)
    province_report = build_report_by_province(rows)

    st.subheader("Báo cáo đơn hàng tỉnh")
    st.caption("Đơn hàng tỉnh được tính theo `Zone = Ngoại thành`. Tỉ lệ tiền gửi tỉnh = Chi phí vận chuyển tỉnh / Giá trị đơn hàng tỉnh.")
    render_report_kpi_grid(report_summary, date_label)

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Theo nhân viên giao hàng")
        if driver_report.empty:
            st.info("Chưa có dữ liệu NVGH phù hợp.")
        else:
            st.dataframe(
                driver_report,
                hide_index=True,
                use_container_width=True,
                height=430,
                column_config=get_report_column_config(),
            )
            chart_df = driver_report[["NVGH", "Giá trị đơn hàng tỉnh"]].head(12).set_index("NVGH")
            st.bar_chart(chart_df)

    with right:
        st.markdown("#### Theo tỉnh / tuyến")
        if province_report.empty:
            st.info("Chưa có đơn hàng tỉnh trong phạm vi lọc.")
        else:
            st.dataframe(
                province_report,
                hide_index=True,
                use_container_width=True,
                height=430,
                column_config=get_report_column_config(),
            )
            chart_df = province_report[["Tỉnh / Tuyến", "Chi phí vận chuyển đơn hàng tỉnh"]].head(12).set_index("Tỉnh / Tuyến")
            st.bar_chart(chart_df)


def render_report_kpi_grid(summary: dict, date_label: str) -> None:
    cards = [
        {
            "label": "Số đơn hàng tỉnh",
            "value": format_number(summary["province_orders"], 0),
            "sub": "Zone = Ngoại thành",
            "icon": "TỈ",
            "accent": "#2563eb",
            "soft": "#dbeafe",
        },
        {
            "label": "Giá trị đơn tỉnh",
            "value": format_currency(summary["province_order_value"]),
            "sub": "Tổng giá trị đơn ngoại thành",
            "icon": "GT",
            "accent": "#059669",
            "soft": "#d1fae5",
        },
        {
            "label": "Chi phí vận chuyển tỉnh",
            "value": format_currency(summary["province_shipping_cost"]),
            "sub": "Tổng tiền gửi nhà xe",
            "icon": "VC",
            "accent": "#ea580c",
            "soft": "#ffedd5",
        },
        {
            "label": "Tỉ lệ tiền gửi tỉnh",
            "value": format_percent(summary["province_shipping_ratio"]),
            "sub": "Phí vận chuyển / Giá trị đơn",
            "icon": "%",
            "accent": "#7c3aed",
            "soft": "#ede9fe",
        },
        {
            "label": "Tổng số đơn",
            "value": format_number(summary["total_orders"], 0),
            "sub": "Tất cả zone trong bộ lọc",
            "icon": "ĐH",
            "accent": "#334155",
            "soft": "#e2e8f0",
        },
        {
            "label": "Giá trị đơn hàng",
            "value": format_currency(summary["order_value"]),
            "sub": "Tất cả đơn trong bộ lọc",
            "icon": "₫",
            "accent": "#0f766e",
            "soft": "#ccfbf1",
        },
        {
            "label": "Số khối",
            "value": format_number(summary["volume"]),
            "sub": "Tất cả đơn trong bộ lọc",
            "icon": "M3",
            "accent": "#0891b2",
            "soft": "#cffafe",
        },
        {
            "label": "Khoảng ngày",
            "value": date_label,
            "sub": "Theo Ngày Giao Hàng",
            "icon": "TG",
            "accent": "#475569",
            "soft": "#f1f5f9",
        },
    ]
    html = ["<div class='kpi-grid'>"]
    for card in cards:
        html.append(
            "<div class='kpi-card' style='--accent:{accent};--accent-soft:{soft}'>"
            "<div class='kpi-top'>"
            "<div class='kpi-label'>{label}</div>"
            "<div class='kpi-icon'>{icon}</div>"
            "</div>"
            "<div class='kpi-value'>{value}</div>"
            "<div class='kpi-sub'>{sub}</div>"
            "</div>".format(
                accent=card["accent"],
                soft=card["soft"],
                label=escape(card["label"]),
                icon=escape(card["icon"]),
                value=escape(str(card["value"])),
                sub=escape(card["sub"]),
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_delivery_list(rows: list[dict]) -> None:
    if not rows:
        st.info("Không có đơn phù hợp bộ lọc.")
        return

    view_mode = st.radio("Kiểu hiển thị", ["Bảng", "Card mobile"], horizontal=True)
    if view_mode == "Card mobile":
        render_cards(rows)
        return

    st.caption("Bấm header `Số đơn`, `Ngày`, `Giá trị` để sắp xếp tăng/giảm. Bảng vẫn dùng layout compact để nhìn đủ thông tin trên một màn hình.")
    render_sortable_compact_delivery_table(rows)
    selected_row = None

    labels = [""] + [make_order_label(row) for row in rows]
    selected_label = st.selectbox("Xem chi tiết đơn", labels, format_func=lambda value: value or "Chọn đơn để xem toàn bộ thông tin")
    if selected_label:
        selected_row = rows[labels.index(selected_label) - 1]

    if selected_row:
        render_detail(selected_row)


def render_sortable_compact_delivery_table(rows: list[dict]) -> None:
    table_rows = []
    for row in rows:
        status_color, status_background = status_style(row.get("status"))
        order_number = safe_str(row.get("order_number"))
        order_sort = parse_order_number(order_number) or 0
        delivery_date_key = to_date_key(row.get("delivery_date"))
        order_value = parse_sheet_number(row.get("order_value"))
        volume = parse_sheet_number(row.get("volume"))
        shipping_cost = parse_sheet_number(row.get("shipping_cost"))
        route = safe_str(row.get("route")) or "-"
        zone = safe_str(row.get("zone")) or "-"
        customer_name = safe_str(row.get("customer_name")) or "-"
        customer_code = safe_str(row.get("customer_code"))
        driver = safe_str(row.get("driver")) or "-"
        status = safe_str(row.get("status")) or "Chưa có trạng thái"

        table_rows.append(
            "<tr "
            f"data-order='{order_sort}' "
            f"data-date='{escape(delivery_date_key)}' "
            f"data-route='{escape(route)} {escape(zone)}' "
            f"data-customer='{escape(customer_name)} {escape(customer_code)}' "
            f"data-driver='{escape(driver)}' "
            f"data-status='{escape(status)}' "
            f"data-value='{order_value}'>"
            f"<td class='num'>{escape(order_number or '-')}</td>"
            "<td class='date'>"
            f"<div class='cell-main'>{escape(safe_str(row.get('delivery_date')) or '-')}</div>"
            f"<div class='cell-sub'>Nhận: {escape(safe_str(row.get('customer_receive_date')) or '-')}</div>"
            "</td>"
            "<td class='route'>"
            f"<div class='cell-main'>{escape(route)}</div>"
            f"<div class='cell-sub'>Zone: {escape(zone)}</div>"
            "</td>"
            "<td class='customer'>"
            f"<div class='cell-main'>{escape(customer_name)}</div>"
            f"<div class='cell-sub'>{escape(customer_code or '-')}</div>"
            "</td>"
            f"<td class='driver'>{escape(driver)}</td>"
            "<td class='status'>"
            f"<span class='status-pill' style='color:{status_color};background:{status_background}'>{escape(status)}</span>"
            "</td>"
            "<td class='money'>"
            f"<div class='cell-main'>{escape(format_currency(order_value))}</div>"
            f"<div class='cell-sub'>Khối: {escape(format_number(volume))}</div>"
            f"<div class='cell-sub'>Phí: {escape(format_currency(shipping_cost))}</div>"
            "</td>"
            "</tr>"
        )

    html = f"""
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0;
      color: #0f172a;
      background: transparent;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .table-shell {{
      width: 100%;
      height: 680px;
      overflow: auto;
      border: 1px solid #dbe3ef;
      border-radius: 12px;
      background: #fff;
      box-shadow: 0 12px 24px rgba(15, 23, 42, 0.07);
    }}
    table {{
      width: 100%;
      min-width: 980px;
      border-collapse: separate;
      border-spacing: 0;
      table-layout: fixed;
      font-size: 13px;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #f8fafc;
      color: #475569;
      padding: 11px 10px;
      border-bottom: 1px solid #dbe3ef;
      text-align: left;
      font-size: 11px;
      text-transform: uppercase;
      line-height: 1.25;
      user-select: none;
    }}
    th.sortable {{ cursor: pointer; }}
    th.sortable:hover {{ color: #0f172a; background: #eef4ff; }}
    th .sort-mark {{ margin-left: 5px; color: #94a3b8; font-size: 10px; }}
    th.active .sort-mark {{ color: #2563eb; }}
    td {{
      padding: 11px 10px;
      border-bottom: 1px solid #edf2f7;
      color: #0f172a;
      vertical-align: middle;
      word-break: break-word;
    }}
    tr:hover td {{ background: #f8fafc; }}
    .num {{ width: 78px; font-weight: 800; }}
    .date {{ width: 92px; }}
    .route {{ width: 126px; }}
    .customer {{ width: 240px; }}
    .driver {{ width: 138px; }}
    .status {{ width: 134px; }}
    .money {{ width: 142px; text-align: right; }}
    .cell-main {{ font-weight: 750; }}
    .cell-sub {{ color: #64748b; font-size: 12px; margin-top: 2px; }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 11.5px;
      font-weight: 800;
      line-height: 1.2;
      white-space: normal;
    }}
    @media (max-width: 1200px) {{
      .table-shell {{ height: 660px; }}
      table {{ min-width: 960px; }}
      .customer {{ width: 220px; }}
      .driver {{ width: 128px; }}
      .money {{ width: 136px; }}
    }}
  </style>
</head>
<body>
  <div class="table-shell">
    <table id="delivery-table">
      <thead>
        <tr>
          <th class="sortable num" data-key="order" data-type="number">Số đơn <span class="sort-mark">↕</span></th>
          <th class="sortable date" data-key="date" data-type="date">Ngày <span class="sort-mark">↕</span></th>
          <th class="sortable route" data-key="route" data-type="text">Tuyến / Zone <span class="sort-mark">↕</span></th>
          <th class="sortable customer" data-key="customer" data-type="text">Khách hàng <span class="sort-mark">↕</span></th>
          <th class="sortable driver" data-key="driver" data-type="text">NVGH <span class="sort-mark">↕</span></th>
          <th class="sortable status" data-key="status" data-type="text">Trạng thái <span class="sort-mark">↕</span></th>
          <th class="sortable money" data-key="value" data-type="number">Giá trị / Khối / Phí <span class="sort-mark">↕</span></th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>
  </div>
  <script>
    const table = document.getElementById("delivery-table");
    const tbody = table.querySelector("tbody");
    const collator = new Intl.Collator("vi", {{ numeric: true, sensitivity: "base" }});

    function parseValue(row, key, type) {{
      const value = row.dataset[key] || "";
      if (type === "number") {{
        const number = Number(value);
        return Number.isFinite(number) ? number : -Infinity;
      }}
      if (type === "date") {{
        return value ? Date.parse(value) : -Infinity;
      }}
      return value;
    }}

    function updateMarks(activeHeader, direction) {{
      table.querySelectorAll("th.sortable").forEach((header) => {{
        header.classList.remove("active");
        header.querySelector(".sort-mark").textContent = "↕";
      }});
      activeHeader.classList.add("active");
      activeHeader.querySelector(".sort-mark").textContent = direction === "asc" ? "↑" : "↓";
    }}

    table.querySelectorAll("th.sortable").forEach((header) => {{
      header.addEventListener("click", () => {{
        const key = header.dataset.key;
        const type = header.dataset.type;
        const direction = header.dataset.direction === "asc" ? "desc" : "asc";
        table.querySelectorAll("th.sortable").forEach((item) => delete item.dataset.direction);
        header.dataset.direction = direction;

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((left, right) => {{
          const leftValue = parseValue(left, key, type);
          const rightValue = parseValue(right, key, type);
          let result = 0;
          if (type === "text") {{
            result = collator.compare(String(leftValue), String(rightValue));
          }} else {{
            result = leftValue === rightValue ? 0 : leftValue > rightValue ? 1 : -1;
          }}
          return direction === "asc" ? result : -result;
        }});
        rows.forEach((row) => tbody.appendChild(row));
        updateMarks(header, direction);
      }});
    }});
  </script>
</body>
</html>
"""
    components.html(html, height=700, scrolling=False)


def render_cards(rows: list[dict]) -> None:
    for row in rows:
        with st.container(border=True):
            top_left, top_right = st.columns([1, 0.35])
            with top_left:
                st.markdown(f"**{safe_str(row.get('order_number')) or f'Dòng {row.get('row_number')}'}**")
                st.caption(f"{safe_str(row.get('customer_name')) or '-'} · {safe_str(row.get('customer_code'))}")
            with top_right:
                st.markdown(status_badge_html(row.get("status")), unsafe_allow_html=True)

            st.markdown(
                "<div class='card-grid'>"
                f"<div><b>Ngày giao</b><br>{safe_str(row.get('delivery_date')) or '-'}</div>"
                f"<div><b>Ngày khách nhận</b><br>{safe_str(row.get('customer_receive_date')) or '-'}</div>"
                f"<div><b>Tuyến</b><br>{safe_str(row.get('route')) or '-'}</div>"
                f"<div><b>Zone</b><br>{safe_str(row.get('zone')) or '-'}</div>"
                f"<div><b>NVGH</b><br>{safe_str(row.get('driver')) or '-'}</div>"
                f"<div><b>Số khối</b><br>{safe_str(row.get('volume')) or '-'}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if safe_str(row.get("note")):
                st.caption(f"Ghi chú: {row.get('note')}")
            with st.expander("Chi tiết đơn"):
                render_detail(row)


def render_detail(row: dict) -> None:
    st.subheader(f"Chi tiết đơn {safe_str(row.get('order_number')) or f'Dòng {row.get('row_number')}'}")
    st.markdown(status_badge_html(row.get("status")), unsafe_allow_html=True)
    table_rows = "".join(
        f"<tr><td>{key}</td><td>{safe_str(value) or '-'}</td></tr>"
        for key, value in row.get("fields", {}).items()
    )
    st.markdown(f"<table class='detail-table'>{table_rows}</table>", unsafe_allow_html=True)


def build_report_summary(rows: list[dict]) -> dict:
    summary = new_report_bucket()
    for row in rows:
        add_to_report_bucket(summary, row)
    finalize_report_bucket(summary)
    return summary


def build_report_by_driver(rows: list[dict]) -> pd.DataFrame:
    buckets: dict[str, dict] = {}
    for row in rows:
        key = safe_str(row.get("driver")) or "Chưa có NVGH"
        bucket = buckets.setdefault(key, new_report_bucket())
        bucket["group"] = key
        add_to_report_bucket(bucket, row)

    records = []
    for bucket in buckets.values():
        finalize_report_bucket(bucket)
        records.append(
            {
                "NVGH": bucket["group"],
                "Số đơn hàng": bucket["total_orders"],
                "Giá trị đơn hàng": bucket["order_value"],
                "Số khối": bucket["volume"],
                "Số đơn hàng tỉnh": bucket["province_orders"],
                "Giá trị đơn hàng tỉnh": bucket["province_order_value"],
                "Chi phí vận chuyển đơn hàng tỉnh": bucket["province_shipping_cost"],
                "Số kiện đơn hàng tỉnh": bucket["province_package_count"],
                "Tỉ lệ tiền gửi đơn hàng tỉnh": bucket["province_shipping_ratio"],
            }
        )

    return pd.DataFrame(records).sort_values(
        by=["Giá trị đơn hàng tỉnh", "Số đơn hàng tỉnh", "Giá trị đơn hàng"],
        ascending=[False, False, False],
        ignore_index=True,
    )


def build_report_by_province(rows: list[dict]) -> pd.DataFrame:
    buckets: dict[str, dict] = {}
    for row in rows:
        if not is_province_order(row):
            continue

        key = safe_str(row.get("route")) or "Chưa có tỉnh / tuyến"
        bucket = buckets.setdefault(key, new_report_bucket())
        bucket["group"] = key
        bucket.setdefault("transport_counts", {})
        transport_company = safe_str(row.get("transport_company")) or "Chưa có nhà xe"
        bucket["transport_counts"][transport_company] = bucket["transport_counts"].get(transport_company, 0) + 1
        add_to_report_bucket(bucket, row)

    records = []
    for bucket in buckets.values():
        finalize_report_bucket(bucket)
        records.append(
            {
                "Tỉnh / Tuyến": bucket["group"],
                "Nhà xe": format_transport_companies(bucket.get("transport_counts", {})),
                "Số đơn hàng": bucket["total_orders"],
                "Giá trị đơn hàng": bucket["order_value"],
                "Số khối": bucket["volume"],
                "Số đơn hàng tỉnh": bucket["province_orders"],
                "Giá trị đơn hàng tỉnh": bucket["province_order_value"],
                "Chi phí vận chuyển đơn hàng tỉnh": bucket["province_shipping_cost"],
                "Số kiện đơn hàng tỉnh": bucket["province_package_count"],
                "Tỉ lệ tiền gửi đơn hàng tỉnh": bucket["province_shipping_ratio"],
            }
        )

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records).sort_values(
        by=["Giá trị đơn hàng tỉnh", "Số đơn hàng tỉnh"],
        ascending=[False, False],
        ignore_index=True,
    )


def new_report_bucket() -> dict:
    return {
        "group": "",
        "total_orders": 0,
        "order_value": 0.0,
        "volume": 0.0,
        "province_orders": 0,
        "province_order_value": 0.0,
        "province_shipping_cost": 0.0,
        "province_package_count": 0.0,
        "province_shipping_ratio": 0.0,
    }


def add_to_report_bucket(bucket: dict, row: dict) -> None:
    bucket["total_orders"] += 1
    bucket["order_value"] += parse_sheet_number(row.get("order_value"))
    bucket["volume"] += parse_sheet_number(row.get("volume"))

    if not is_province_order(row):
        return

    bucket["province_orders"] += 1
    bucket["province_order_value"] += parse_sheet_number(row.get("order_value"))
    bucket["province_shipping_cost"] += parse_sheet_number(row.get("shipping_cost"))
    bucket["province_package_count"] += parse_sheet_number(row.get("package_count"))


def finalize_report_bucket(bucket: dict) -> None:
    province_order_value = bucket["province_order_value"]
    bucket["province_shipping_ratio"] = (bucket["province_shipping_cost"] / province_order_value * 100) if province_order_value else 0.0


def is_province_order(row: dict) -> bool:
    return normalize_text(row.get("zone")) == "ngoai thanh"


def format_transport_companies(counts: dict[str, int]) -> str:
    if not counts:
        return "-"

    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    parts = [f"{name} ({count})" for name, count in ordered[:3]]
    if len(ordered) > 3:
        parts.append(f"+{len(ordered) - 3}")
    return ", ".join(parts)


def get_report_column_config() -> dict:
    return {
        "Số đơn hàng": st.column_config.NumberColumn(format="%d"),
        "Giá trị đơn hàng": st.column_config.NumberColumn(format="%d đ"),
        "Số khối": st.column_config.NumberColumn(format="%.2f"),
        "Số đơn hàng tỉnh": st.column_config.NumberColumn(format="%d"),
        "Giá trị đơn hàng tỉnh": st.column_config.NumberColumn(format="%d đ"),
        "Chi phí vận chuyển đơn hàng tỉnh": st.column_config.NumberColumn(format="%d đ"),
        "Số kiện đơn hàng tỉnh": st.column_config.NumberColumn(format="%d"),
        "Tỉ lệ tiền gửi đơn hàng tỉnh": st.column_config.NumberColumn(format="%.2f%%"),
    }


def build_summary(rows: list[dict]) -> dict:
    status_counts: dict[str, int] = {}
    driver_counts: dict[str, int] = {}
    completed = 0
    order_value = 0.0
    volume = 0.0
    shipping_cost = 0.0

    for row in rows:
        status = safe_str(row.get("status")) or "Chưa có trạng thái"
        status_counts[status] = status_counts.get(status, 0) + 1

        driver = safe_str(row.get("driver"))
        if driver:
            driver_counts[driver] = driver_counts.get(driver, 0) + 1

        order_value += parse_sheet_number(row.get("order_value"))
        volume += parse_sheet_number(row.get("volume"))
        shipping_cost += parse_sheet_number(row.get("shipping_cost"))
        completed += 1 if is_completed_status(row.get("status")) else 0

    return {
        "total": len(rows),
        "completed": completed,
        "unfinished": len(rows) - completed,
        "driver_count": len(driver_counts),
        "order_value": order_value,
        "volume": volume,
        "shipping_cost": shipping_cost,
        "status_counts": sorted(status_counts.items(), key=lambda item: item[1], reverse=True),
        "driver_counts": sorted(driver_counts.items(), key=lambda item: item[1], reverse=True),
    }


def build_display_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Số đơn hàng": parse_order_number(row.get("order_number")),
                "Ngày giao": parse_table_date(row.get("delivery_date")),
                "Giá trị đơn hàng": parse_sheet_number(row.get("order_value")),
                "Ngày khách nhận": safe_str(row.get("customer_receive_date")) or "-",
                "Tuyến": safe_str(row.get("route")) or "-",
                "Zone": safe_str(row.get("zone")) or "-",
                "Khách hàng": format_customer_cell(row),
                "NVGH": safe_str(row.get("driver")) or "-",
                "Trạng thái": safe_str(row.get("status")) or "Chưa có trạng thái",
                "Số khối": parse_sheet_number(row.get("volume")),
                "Phí VC": parse_sheet_number(row.get("shipping_cost")),
            }
            for row in rows
        ]
    )


def parse_order_number(value: object) -> int | None:
    text = safe_str(value)
    if not text:
        return None

    digits = "".join(char for char in text if char.isdigit())
    return int(digits) if digits else None


def parse_table_date(value: object):
    date_key = to_date_key(value)
    if not date_key:
        return pd.NaT

    return pd.to_datetime(date_key, errors="coerce")


def format_customer_cell(row: dict) -> str:
    customer_name = safe_str(row.get("customer_name")) or "-"
    customer_code = safe_str(row.get("customer_code"))
    return f"{customer_name} · {customer_code}" if customer_code else customer_name


def make_order_label(row: dict) -> str:
    order_number = safe_str(row.get("order_number")) or f"Dòng {row.get('row_number')}"
    customer = safe_str(row.get("customer_name")) or "-"
    return f"{order_number} · {customer}"


def format_range_label(date_from: str, date_to: str) -> str:
    if date_from and date_to:
        return f"{format_date_key(date_from)} - {format_date_key(date_to)}"
    if date_from:
        return f"Từ {format_date_key(date_from)}"
    if date_to:
        return f"Đến {format_date_key(date_to)}"
    return "Tất cả"


def format_percent(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


@st.cache_data(ttl=60, show_spinner=False)
def get_sheet_data(refresh_token: int = 0) -> dict:
    _ = refresh_token
    return read_delivery_sheet()


if __name__ == "__main__":
    main()
