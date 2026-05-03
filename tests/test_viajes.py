from __future__ import annotations

import sqlite3
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
                    lugar_descarga_vacio_id=3,
                    observaciones="Editado",
                    chofer_id=2,
                    tipo_carga="PELIGROSA",
                    camion_id=2,
                    semi_id=1002,
                    tarifa=50000,
                    fecha_descarga_tarifa="2026-06-16",
                    hay_demora=True,
                    demora=1000,
                    fecha_descarga_demora="2026-06-17",
                    descarga_vacio=True,
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
            self.assertEqual(data["lugar_descarga_vacio_id"], 3)
            self.assertEqual(data["hay_demora"], 1)
            self.assertEqual(data["descarga_vacio"], 1)
            self.assertEqual(data["chofer_id"], 2)
            self.assertEqual(data["semi_id"], 1002)
            self.assertEqual(data["peaje_ids"], (2, 3))
            self.assertEqual(data["estado"], "Editado")
            self.assertEqual(resumen.peajes, 31000)

    def test_create_stores_nulls_when_demora_and_vacio_are_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=True)
            repository = ViajeRepository(database_path)

            viaje_id = repository.create(
                ViajeCreate(
                    fecha="2026-06-20",
                    cliente_id=1,
                    carta_porte="CP-NULL",
                    carga_id=1,
                    lugar_carga_id=1,
                    lugar_descarga_id=2,
                    lugar_descarga_vacio_id=None,
                    observaciones="",
                    chofer_id=1,
                    tipo_carga="GENERAL",
                    camion_id=1,
                    semi_id=None,
                    tarifa=10000,
                    fecha_descarga_tarifa="2026-06-21",
                    hay_demora=False,
                    demora=None,
                    fecha_descarga_demora=None,
                    descarga_vacio=False,
                    vacio=None,
                    fecha_descarga_vacio=None,
                    gas_oil_lts=0,
                    peaje_ids=(),
                )
            )

            connection = sqlite3.connect(database_path)
            try:
                row = connection.execute(
                    """
                    SELECT
                        hay_demora,
                        demora,
                        fecha_descarga_demora,
                        descarga_vacio,
                        vacio,
                        fecha_descarga_vacio
                    FROM viajes
                    WHERE id = ?
                    """,
                    (viaje_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], 0)
            self.assertIsNone(row[1])
            self.assertIsNone(row[2])
            self.assertEqual(row[3], 0)
            self.assertIsNone(row[4])
            self.assertIsNone(row[5])

    def test_update_full_stores_nulls_when_demora_and_vacio_are_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=True)
            repository = ViajeRepository(database_path)

            repository.update_full(
                2,
                ViajeCreate(
                    fecha="2026-06-20",
                    cliente_id=1,
                    carta_porte="CP-NULL",
                    carga_id=1,
                    lugar_carga_id=1,
                    lugar_descarga_id=2,
                    lugar_descarga_vacio_id=None,
                    observaciones="",
                    chofer_id=1,
                    tipo_carga="GENERAL",
                    camion_id=1,
                    semi_id=None,
                    tarifa=10000,
                    fecha_descarga_tarifa="2026-06-21",
                    hay_demora=False,
                    demora=None,
                    fecha_descarga_demora=None,
                    descarga_vacio=False,
                    vacio=None,
                    fecha_descarga_vacio=None,
                    gas_oil_lts=0,
                    peaje_ids=(),
                ),
                estado="Editado",
            )

            connection = sqlite3.connect(database_path)
            try:
                row = connection.execute(
                    """
                    SELECT
                        hay_demora,
                        demora,
                        fecha_descarga_demora,
                        descarga_vacio,
                        vacio,
                        fecha_descarga_vacio,
                        lugar_descarga_vacio_id
                    FROM viajes
                    WHERE id = 2
                    """
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], 0)
            self.assertIsNone(row[1])
            self.assertIsNone(row[2])
            self.assertEqual(row[3], 0)
            self.assertIsNone(row[4])
            self.assertIsNone(row[5])
            self.assertIsNone(row[6])


if __name__ == "__main__":
    unittest.main()
