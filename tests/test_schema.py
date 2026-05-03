from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from gestion_camiones.data.repositories import VehiculoRepository
from gestion_camiones.data.schema import initialize_database
from gestion_camiones.ui.main_window import (
    _format_codigo_contenedor,
    _format_codigo_contenedor_partial,
)


class SchemaInitializationTests(unittest.TestCase):
    def test_default_initialization_does_not_seed_demo_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"

            initialize_database(database_path)

            with closing(sqlite3.connect(database_path)) as connection:
                cliente_count = connection.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
                viaje_count = connection.execute("SELECT COUNT(*) FROM viajes").fetchone()[0]

            self.assertEqual(cliente_count, 0)
            self.assertEqual(viaje_count, 0)

    def test_camion_can_store_default_semi(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"

            initialize_database(database_path)
            repository = VehiculoRepository(database_path)
            semi_id = repository.create(
                tipo="SEMI",
                nombre_identificatorio="Semi prueba",
                patente="SEM123",
                observaciones="",
            )
            camion_id = repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion prueba",
                patente="CAM123",
                observaciones="",
                semi_predeterminado_id=semi_id,
            )

            camion = next(item for item in repository.list_all("CAMION") if item.id == camion_id)

            self.assertEqual(camion.semi_predeterminado_id, semi_id)
            self.assertEqual(camion.semi_predeterminado_nombre, "Semi prueba - SEM123")

    def test_codigo_contenedor_is_normalized_to_user_format(self) -> None:
        self.assertEqual(_format_codigo_contenedor_partial("abcd"), "ABCD")
        self.assertEqual(_format_codigo_contenedor_partial("abcd1"), "ABCD 1")
        self.assertEqual(
            _format_codigo_contenedor_partial("abcd1234567"),
            "ABCD 123456 - 7",
        )
        self.assertEqual(
            _format_codigo_contenedor("abcd1234567"),
            "ABCD 123456 - 7",
        )
        self.assertEqual(
            _format_codigo_contenedor("ABCD 123456-7"),
            "ABCD 123456 - 7",
        )

        with self.assertRaises(ValueError):
            _format_codigo_contenedor("AB123")


if __name__ == "__main__":
    unittest.main()
