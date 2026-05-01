from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gestion_camiones.data.repositories import ClienteRepository
from gestion_camiones.data.schema import initialize_database


class ClienteRepositoryTests(unittest.TestCase):
    def test_stores_cuit_and_selected_intermediario(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            repository = ClienteRepository(database_path)

            intermediario_id = repository.create(
                nombre="Intermediario SA",
                cuit="30-11111111-1",
                email="",
                numero_contacto="",
                es_cliente_directo=True,
                cliente_padre_id=None,
            )
            cliente_id = repository.create(
                nombre="Cliente Final",
                cuit="30-22222222-2",
                email="cliente@example.com",
                numero_contacto="",
                es_cliente_directo=False,
                cliente_padre_id=intermediario_id,
            )

            cliente = next(item for item in repository.list_all() if item.id == cliente_id)

            self.assertEqual(cliente.cuit, "30-22222222-2")
            self.assertFalse(cliente.es_cliente_directo)
            self.assertEqual(cliente.cliente_padre_id, intermediario_id)
            self.assertEqual(cliente.cliente_padre_nombre, "Intermediario SA")


if __name__ == "__main__":
    unittest.main()
