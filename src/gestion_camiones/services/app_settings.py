from __future__ import annotations

import json
from pathlib import Path

from gestion_camiones.config import APP_NAME

DEFAULT_COMPANY_NAME = APP_NAME


def normalize_company_name(value: str) -> str:
    normalized = " ".join((value or "").split())
    return normalized or DEFAULT_COMPANY_NAME


def load_app_settings(settings_path: Path) -> dict[str, object]:
    data: dict[str, object] = {
        "company_name": DEFAULT_COMPANY_NAME,
        "cliente_viaje_fields": {},
    }
    if not settings_path.exists():
        return data

    try:
        stored = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return data

    company_name = stored.get("company_name")
    if isinstance(company_name, str):
        data["company_name"] = normalize_company_name(company_name)

    cliente_viaje_fields = stored.get("cliente_viaje_fields")
    if isinstance(cliente_viaje_fields, dict):
        data["cliente_viaje_fields"] = {
            str(cliente_id): [
                str(field_key)
                for field_key in field_keys
                if isinstance(field_key, str)
            ]
            for cliente_id, field_keys in cliente_viaje_fields.items()
            if isinstance(field_keys, list)
        }
    return data


def save_app_settings(settings_path: Path, settings: dict[str, object]) -> None:
    cliente_viaje_fields = settings.get("cliente_viaje_fields", {})
    if not isinstance(cliente_viaje_fields, dict):
        cliente_viaje_fields = {}

    payload = {
        "company_name": normalize_company_name(str(settings.get("company_name", ""))),
        "cliente_viaje_fields": cliente_viaje_fields,
    }
    settings_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
