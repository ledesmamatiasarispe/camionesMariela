from __future__ import annotations

import os
import platform
from pathlib import Path

from gestion_camiones.config import APP_NAME


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
    return get_app_data_dir() / "gestion_camiones.sqlite3"


def get_theme_path() -> Path:
    return get_app_data_dir() / "theme.json"


def _safe_app_dir_name(name: str) -> str:
    return name.replace(" ", "_").lower()
