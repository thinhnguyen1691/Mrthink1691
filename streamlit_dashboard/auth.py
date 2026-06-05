from __future__ import annotations

import hmac
import json
import os
from dataclasses import dataclass

from .text_utils import normalize_text, safe_str


@dataclass(frozen=True)
class AppUser:
    email: str
    password: str
    role: str = "viewer"
    name: str = ""
    driver_name: str = ""


def get_configured_users() -> list[AppUser]:
    return parse_auth_users(os.environ.get("AUTH_USERS", ""))


def parse_auth_users(value: str) -> list[AppUser]:
    if not value.strip():
        return []

    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [_normalize_user(item) for item in parsed if isinstance(item, dict) and item.get("email")]
    except json.JSONDecodeError:
        pass

    users: list[AppUser] = []
    for entry in value.split(";"):
        parts = [part.strip() for part in entry.split(",")]
        if not parts or not parts[0]:
            continue

        email = parts[0]
        password = parts[1] if len(parts) > 1 else ""
        role = parts[2] if len(parts) > 2 else "viewer"
        name = parts[3] if len(parts) > 3 else ""
        driver_name = parts[4] if len(parts) > 4 else ""
        users.append(_normalize_user({"email": email, "password": password, "role": role, "name": name, "driverName": driver_name}))

    return users


def find_user(email: str) -> AppUser | None:
    normalized_email = safe_str(email).lower()
    for user in get_configured_users():
        if user.email == normalized_email:
            return user
    return None


def authenticate(email: str, password: str) -> AppUser | None:
    user = find_user(email)
    if not user or not user.password:
        return None

    if hmac.compare_digest(password, user.password):
        return user

    return None


def can_user_view_all(user: AppUser) -> bool:
    return user.role in {"admin", "viewer"}


def apply_row_security(rows: list[dict], user: AppUser) -> list[dict]:
    if can_user_view_all(user):
        return rows

    if user.role != "driver":
        return rows

    email = safe_str(user.email).lower()
    driver_name = normalize_text(user.driver_name or user.name)
    has_driver_email = any(safe_str(row.get("driver_email")) for row in rows)
    has_driver_name = any(safe_str(row.get("driver")) or safe_str(row.get("actual_driver")) for row in rows)

    if has_driver_email:
        return [row for row in rows if safe_str(row.get("driver_email")).lower() == email]

    if driver_name and has_driver_name:
        return [
            row
            for row in rows
            if driver_name in {
                normalize_text(row.get("driver")),
                normalize_text(row.get("actual_driver")),
                normalize_text(row.get("suggested_driver")),
            }
        ]

    return rows


def _normalize_user(raw: dict) -> AppUser:
    role = safe_str(raw.get("role") or "viewer").lower()
    if role not in {"admin", "viewer", "driver"}:
        role = "viewer"

    return AppUser(
        email=safe_str(raw.get("email")).lower(),
        password=safe_str(raw.get("password")),
        role=role,
        name=safe_str(raw.get("name")),
        driver_name=safe_str(raw.get("driverName") or raw.get("driver_name")),
    )
