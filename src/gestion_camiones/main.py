from __future__ import annotations

import sys
import traceback
from pathlib import Path

from gestion_camiones import __version__
from gestion_camiones.data.paths import get_app_data_dir


def _write_startup_error(error: BaseException) -> None:
    try:
        log_path = get_app_data_dir() / "startup-error.log"
    except Exception:
        log_path = Path.home() / "gestion-camiones-startup-error.log"

    log_path.write_text(
        "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        encoding="utf-8",
    )


def main() -> int:
    if "--version" in sys.argv:
        print(__version__)
        return 0

    from PySide6.QtWidgets import QApplication, QStyleFactory

    from gestion_camiones.data.paths import get_database_path
    from gestion_camiones.data.repositories import ViajeRepository
    from gestion_camiones.data.schema import initialize_database
    from gestion_camiones.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Gestion Camiones")
    app.setOrganizationName("Jose Romero e hijos SRL")
    app.setStyle(QStyleFactory.create("Fusion"))

    database_path = get_database_path()
    initialize_database(database_path, seed=False)

    window = MainWindow(ViajeRepository(database_path), database_path)
    window.show()

    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        _write_startup_error(exc)
        raise
