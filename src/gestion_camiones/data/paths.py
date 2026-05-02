from __future__ import annotations

import json
import os
import platform
from pathlib import Path

from gestion_camiones.config import APP_NAME

DEFAULT_DATABASE_NAME = "gestion_camiones.sqlite3"


def get_app_data_dir() -> Path:
    system = platform.system()

    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    app_dir = base / _safe_app_dir_name(APP_NAME)
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_database_path() -> Path:
    stored_path = _stored_database_path()
    if stored_path is not None:
        return stored_path
    return get_default_database_path()


def get_default_database_path() -> Path:
    return get_app_data_dir() / DEFAULT_DATABASE_NAME


def get_theme_path() -> Path:
    return get_app_data_dir() / "theme.json"


def get_settings_path() -> Path:
    return get_app_data_dir() / "settings.json"


def _stored_database_path() -> Path | None:
    settings_path = get_settings_path()
    if not settings_path.exists():
        return None

    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    database_path = settings.get("database_path")
    if not isinstance(database_path, str) or not database_path.strip():
        return None
    return Path(database_path).expanduser()


def _safe_app_dir_name(name: str) -> str:
    return name.replace(" ", "_").lower()
