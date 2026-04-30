from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QStyleFactory

from gestion_camiones.data.paths import get_database_path
from gestion_camiones.data.repositories import ViajeRepository
from gestion_camiones.data.schema import initialize_database
from gestion_camiones.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gestion Camiones")
    app.setOrganizationName("Jose Romero e hijos SRL")
    app.setStyle(QStyleFactory.create("Fusion"))

    database_path = get_database_path()
    initialize_database(database_path)

    window = MainWindow(ViajeRepository(database_path), database_path)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
