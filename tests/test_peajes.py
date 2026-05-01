from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from gestion_camiones.data.repositories import PeajeRepository
from gestion_camiones.data.schema import initialize_database


class PeajeRepositoryTests(unittest.TestCase):
    def test_groups_peajes_by_empresa(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            repository = PeajeRepository(database_path)

            empresa_id = repository.create_empresa(nombre="Autopistas Centro")
            peaje_id = repository.create(
                empresa_id=empresa_id,
                nombre="Cabina Norte",
                direccion="Ruta 1",
                costo=1200,
            )

            empresas = repository.list_empresas()
            peajes = repository.list_all(empresa_id=empresa_id)

            self.assertIn("Autopistas Centro", [empresa.nombre for empresa in empresas])
            self.assertEqual(len(peajes), 1)
            self.assertEqual(peajes[0].id, peaje_id)
            self.assertEqual(peajes[0].empresa_id, empresa_id)
            self.assertEqual(peajes[0].empresa_nombre, "Autopistas Centro")

    def test_migrates_existing_peajes_to_default_empresa(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "legacy.sqlite3"
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    """
                    CREATE TABLE peajes (
                        id INTEGER PRIMARY KEY,
                        nombre TEXT NOT NULL UNIQUE,
                        direccion TEXT NOT NULL DEFAULT '',
                        costo NUMERIC NOT NULL DEFAULT 0,
                        activo INTEGER NOT NULL DEFAULT 1
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO peajes (id, nombre, direccion, costo)
                    VALUES (1, 'Peaje legado', 'Ruta vieja', 500)
                    """
                )
                connection.commit()

            initialize_database(database_path, seed=False)
            repository = PeajeRepository(database_path)

            peajes = repository.list_all()

            self.assertEqual(len(peajes), 1)
            self.assertEqual(peajes[0].empresa_id, 1)
            self.assertEqual(peajes[0].empresa_nombre, "Sin empresa")

    def test_updates_cost_for_many_peajes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            repository = PeajeRepository(database_path)
            empresa_id = repository.create_empresa(nombre="Autopistas Centro")
            first_id = repository.create(
                empresa_id=empresa_id,
                nombre="Cabina Norte",
                direccion="Ruta 1",
                costo=1200,
            )
            second_id = repository.create(
                empresa_id=empresa_id,
                nombre="Cabina Sur",
                direccion="Ruta 2",
                costo=1500,
            )

            repository.update_cost_many((first_id, second_id), costo=2100)

            costs = {
                peaje.nombre: peaje.costo
                for peaje in repository.list_all(empresa_id=empresa_id)
            }
            self.assertEqual(costs, {"Cabina Norte": 2100, "Cabina Sur": 2100})


if __name__ == "__main__":
    unittest.main()
