from __future__ import annotations

import json
from pathlib import Path

from gestion_camiones.config import APP_NAME

DEFAULT_COMPANY_NAME = APP_NAME


def normalize_company_name(value: str) -> str:
    normalized = " ".join((value or "").split())
    return normalized or DEFAULT_COMPANY_NAME


def load_app_settings(settings_path: Path) -> dict[str, str]:
    data = {"company_name": DEFAULT_COMPANY_NAME}
    if not settings_path.exists():
        return data

    try:
        stored = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return data

    company_name = stored.get("company_name")
    if isinstance(company_name, str):
        data["company_name"] = normalize_company_name(company_name)
    return data


def save_app_settings(settings_path: Path, settings: dict[str, str]) -> None:
    payload = {
        "company_name": normalize_company_name(settings.get("company_name", "")),
    }
    settings_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
