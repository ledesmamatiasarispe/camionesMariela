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
        "dialog_sizes": {},
        "splitter_sizes": {},
        "font_sizes": {},
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
    dialog_sizes = stored.get("dialog_sizes")
    if isinstance(dialog_sizes, dict):
        data["dialog_sizes"] = {
            str(key): [
                int(value)
                for value in values
                if isinstance(value, int | float) and int(value) > 0
            ][:2]
            for key, values in dialog_sizes.items()
            if isinstance(values, list)
        }
    splitter_sizes = stored.get("splitter_sizes")
    if isinstance(splitter_sizes, dict):
        data["splitter_sizes"] = {
            str(key): [
                int(value)
                for value in values
                if isinstance(value, int | float) and int(value) >= 0
            ]
            for key, values in splitter_sizes.items()
            if isinstance(values, list)
        }
    font_sizes = stored.get("font_sizes")
    if isinstance(font_sizes, dict):
        data["font_sizes"] = {
            str(key): int(value)
            for key, value in font_sizes.items()
            if isinstance(value, int | float) and 8 <= int(value) <= 36
        }
    return data


def save_app_settings(settings_path: Path, settings: dict[str, object]) -> None:
    cliente_viaje_fields = settings.get("cliente_viaje_fields", {})
    if not isinstance(cliente_viaje_fields, dict):
        cliente_viaje_fields = {}
    dialog_sizes = settings.get("dialog_sizes", {})
    if not isinstance(dialog_sizes, dict):
        dialog_sizes = {}
    splitter_sizes = settings.get("splitter_sizes", {})
    if not isinstance(splitter_sizes, dict):
        splitter_sizes = {}
    font_sizes = settings.get("font_sizes", {})
    if not isinstance(font_sizes, dict):
        font_sizes = {}

    payload = {
        "company_name": normalize_company_name(str(settings.get("company_name", ""))),
        "cliente_viaje_fields": cliente_viaje_fields,
        "dialog_sizes": dialog_sizes,
        "splitter_sizes": splitter_sizes,
        "font_sizes": font_sizes,
    }
    settings_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
