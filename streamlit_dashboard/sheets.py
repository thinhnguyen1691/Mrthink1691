from __future__ import annotations

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import get_google_private_key, get_setting, require_setting
from .mapper import map_sheet_rows


READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


def read_delivery_sheet() -> dict:
    spreadsheet_id = require_setting("GOOGLE_SHEET_ID")
    sheet_gid = int(get_setting("GOOGLE_SHEET_GID", "0") or "0")
    service = _build_sheets_service()
    sheet_title = _get_sheet_title(service, spreadsheet_id, sheet_gid)
    values = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_title}'",
            majorDimension="ROWS",
            valueRenderOption="FORMATTED_VALUE",
            dateTimeRenderOption="FORMATTED_STRING",
        )
        .execute()
        .get("values", [])
    )

    headers = values[0] if values else []
    body_rows = values[1:] if len(values) > 1 else []

    return {
        "headers": headers,
        "rows": map_sheet_rows(headers, body_rows),
        "sheet_title": sheet_title,
    }


def _build_sheets_service():
    info = {
        "type": "service_account",
        "client_email": require_setting("GOOGLE_CLIENT_EMAIL"),
        "private_key": get_google_private_key(),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    credentials = service_account.Credentials.from_service_account_info(info, scopes=[READONLY_SCOPE])
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _get_sheet_title(service, spreadsheet_id: str, sheet_gid: int) -> str:
    metadata = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties(sheetId,title)")
        .execute()
    )
    sheets = metadata.get("sheets", [])

    for sheet in sheets:
        properties = sheet.get("properties", {})
        if int(properties.get("sheetId", -1)) == sheet_gid:
            return properties.get("title", "GIAO HÀNG")

    if sheets:
        return sheets[0].get("properties", {}).get("title", "GIAO HÀNG")

    return "GIAO HÀNG"
