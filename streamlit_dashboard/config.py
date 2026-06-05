from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for path in (PROJECT_ROOT / ".env.local", PROJECT_ROOT / ".env"):
        if not path.exists():
            continue

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = _clean_env_value(value.strip())
            os.environ.setdefault(key, value)


def get_setting(name: str, default: str = "") -> str:
    value = os.environ.get(name, default)
    return value if value is not None else default


def require_setting(name: str) -> str:
    value = get_setting(name)
    if not value:
        raise RuntimeError(f"Thiếu biến môi trường {name}.")
    return value


def get_google_private_key() -> str:
    return require_setting("GOOGLE_PRIVATE_KEY").replace("\\n", "\n")


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    return value.replace("\\n", "\n").replace("\\r", "\r")
