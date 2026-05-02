from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gestion_camiones.data.models import ViajeCreate
from gestion_camiones.data.repositories import ViajeRepository
from gestion_camiones.data.schema import initialize_database


class ViajeRepositoryTests(unittest.TestCase):
    def test_update_full_replaces_trip_fields_and_peajes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=True)
            repository = ViajeRepository(database_path)

            repository.update_full(
                1,
                ViajeCreate(
                    fecha="2026-06-15",
                    cliente_id=2,
                    carta_porte="CP-EDIT",
                    carga_id=2,
                    lugar_carga_id=2,
                    lugar_descarga_id=3,
                    observaciones="Editado",
                    chofer_id=2,
                    tipo_carga="PELIGROSA",
                    camion_id=2,
                    semi_id=1002,
                    tarifa=50000,
                    fecha_descarga_tarifa="2026-06-16",
                    demora=1000,
                    fecha_descarga_demora="2026-06-17",
                    vacio=2000,
                    fecha_descarga_vacio="2026-06-18",
                    gas_oil_lts=150,
                    peaje_ids=(2, 3),
                ),
                estado="Editado",
            )

            data = repository.get_for_edit(1)
            resumen = next(viaje for viaje in repository.list_resumen() if viaje.id == 1)

            self.assertIsNotNone(data)
            assert data is not None
            self.assertEqual(data["cliente_id"], 2)
            self.assertEqual(data["carga_id"], 2)
            self.assertEqual(data["carga_codigo"], "CONT-00000000000000000002")
            self.assertEqual(data["chofer_id"], 2)
            self.assertEqual(data["semi_id"], 1002)
            self.assertEqual(data["peaje_ids"], (2, 3))
            self.assertEqual(data["estado"], "Editado")
            self.assertEqual(resumen.peajes, 31000)


if __name__ == "__main__":
    unittest.main()
