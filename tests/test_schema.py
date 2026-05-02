from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from gestion_camiones.data.schema import initialize_database


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


if __name__ == "__main__":
    unittest.main()
