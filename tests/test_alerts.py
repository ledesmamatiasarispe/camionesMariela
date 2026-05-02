from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from gestion_camiones.data.repositories import (
    AlertRepository,
    ChoferRepository,
    VehiculoCombustibleRepository,
    VehiculoMantenimientoRepository,
    VehiculoRepository,
)
from gestion_camiones.data.schema import initialize_database


class AlertRepositoryTests(unittest.TestCase):
    def test_fuel_load_updates_truck_km_and_saves_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            vehiculo_repository = VehiculoRepository(database_path)
            combustible_repository = VehiculoCombustibleRepository(database_path)

            vehiculo_id = vehiculo_repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion combustible",
                patente="GHI789",
                km_actual=12000,
                observaciones="",
            )

            combustible_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_carga="2026-05-02",
                litros_cargados=150.5,
                km_actual_camion=12340,
            )

            vehiculo = vehiculo_repository.list_all("CAMION")[0]
            cargas = combustible_repository.list_all(vehiculo_id=vehiculo_id)

            self.assertEqual(vehiculo.km_actual, 12340)
            self.assertEqual(len(cargas), 1)
            self.assertEqual(cargas[0].vehiculo_id, vehiculo_id)
            self.assertEqual(cargas[0].fecha_carga, "2026-05-02")
            self.assertEqual(cargas[0].litros_cargados, 150.5)
            self.assertEqual(cargas[0].km_actual_camion, 12340)

    def test_can_delete_fuel_load_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            vehiculo_repository = VehiculoRepository(database_path)
            combustible_repository = VehiculoCombustibleRepository(database_path)

            vehiculo_id = vehiculo_repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion combustible",
                patente="DEL123",
                km_actual=12000,
                observaciones="",
            )
            carga_id = combustible_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_carga="2026-05-02",
                litros_cargados=150.5,
                km_actual_camion=12340,
            )

            combustible_repository.delete(carga_id)

            self.assertEqual(combustible_repository.list_all(vehiculo_id=vehiculo_id), [])

    def test_fuel_consumption_summary_uses_successive_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            vehiculo_repository = VehiculoRepository(database_path)
            combustible_repository = VehiculoCombustibleRepository(database_path)

            vehiculo_id = vehiculo_repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion consumo",
                patente="JKL012",
                km_actual=10000,
                observaciones="",
            )
            combustible_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_carga="2026-05-01",
                litros_cargados=100,
                km_actual_camion=10000,
            )
            combustible_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_carga="2026-05-10",
                litros_cargados=120,
                km_actual_camion=10600,
            )
            combustible_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_carga="2026-05-20",
                litros_cargados=80,
                km_actual_camion=11000,
            )

            summary = combustible_repository.consumption_summary()[0]

            self.assertEqual(summary.vehiculo_id, vehiculo_id)
            self.assertEqual(summary.cargas, 3)
            self.assertEqual(summary.km_recorridos, 1000)
            self.assertEqual(summary.litros_computados, 200)
            self.assertEqual(summary.consumo_litros_100km, 20)

    def test_driver_license_alert_repeats_weekly_until_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            chofer_repository = ChoferRepository(database_path)
            alert_repository = AlertRepository(database_path)
            today = date(2026, 5, 1)
            due_date = today + timedelta(days=45)

            chofer_id = chofer_repository.create(
                dni="12345678",
                nombre="Juan",
                apellido="Perez",
                numero_telefono="",
                fecha_vencimiento_registro=due_date.isoformat(),
                regularidad_registro_meses=24,
            )

            alerts = alert_repository.list_startup_alerts(today)

            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0].entity_id, chofer_id)

            alert_repository.accept_alert(alerts[0].key, today)

            self.assertEqual(alert_repository.list_startup_alerts(today), [])
            self.assertEqual(
                len(alert_repository.list_startup_alerts(today + timedelta(days=7))),
                1,
            )

            new_due_date = today + timedelta(days=400)
            chofer_repository.update_fecha_vencimiento_registro(
                chofer_id,
                new_due_date.isoformat(),
            )
            chofer = chofer_repository.list_all()[0]
            self.assertEqual(chofer.regularidad_registro_meses, 24)

            self.assertEqual(
                alert_repository.list_startup_alerts(today + timedelta(days=8)),
                [],
            )

    def test_vehicle_maintenance_alert_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            vehiculo_repository = VehiculoRepository(database_path)
            mantenimiento_repository = VehiculoMantenimientoRepository(database_path)
            alert_repository = AlertRepository(database_path)
            today = date(2026, 5, 1)
            due_date = today + timedelta(days=20)

            vehiculo_id = vehiculo_repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion 1",
                patente="ABC123",
                observaciones="",
            )
            mantenimiento_id = mantenimiento_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_ultimo_mantenimiento=(today - timedelta(days=100)).isoformat(),
                fecha_proximo_mantenimiento=due_date.isoformat(),
            )

            alerts = alert_repository.list_startup_alerts(today)

            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0].source, AlertRepository.VEHICLE_MAINTENANCE_SOURCE)
            self.assertEqual(alerts[0].entity_id, mantenimiento_id)

            mantenimiento_repository.update(
                mantenimiento_id,
                fecha_ultimo_mantenimiento=(due_date + timedelta(days=1)).isoformat(),
                fecha_proximo_mantenimiento=(today + timedelta(days=180)).isoformat(),
                km_proximo_mantenimiento=0,
            )

            history = mantenimiento_repository.list_history()

            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].vehiculo_id, vehiculo_id)
            self.assertEqual(history[0].fecha_proximo_mantenimiento, due_date.isoformat())
            self.assertTrue(history[0].fuera_de_tiempo)
            self.assertEqual(alert_repository.list_startup_alerts(today), [])

    def test_vehicle_maintenance_km_alert_repeats_weekly_until_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            vehiculo_repository = VehiculoRepository(database_path)
            mantenimiento_repository = VehiculoMantenimientoRepository(database_path)
            alert_repository = AlertRepository(database_path)
            today = date(2026, 5, 1)

            vehiculo_id = vehiculo_repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion 2",
                patente="DEF456",
                km_actual=9900,
                observaciones="",
            )
            mantenimiento_id = mantenimiento_repository.create(
                vehiculo_id=vehiculo_id,
                fecha_ultimo_mantenimiento=(today - timedelta(days=100)).isoformat(),
                fecha_proximo_mantenimiento=(today + timedelta(days=180)).isoformat(),
                km_proximo_mantenimiento=10000,
                regularidad_fecha_meses=6,
                regularidad_km=10000,
            )

            alerts = alert_repository.list_startup_alerts(today)

            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0].entity_id, mantenimiento_id)
            self.assertIn("kilometraje", alerts[0].title.lower())

            alert_repository.accept_alert(alerts[0].key, today)

            self.assertEqual(alert_repository.list_startup_alerts(today), [])
            self.assertEqual(
                len(alert_repository.list_startup_alerts(today + timedelta(days=7))),
                1,
            )

            mantenimiento_repository.update(
                mantenimiento_id,
                fecha_ultimo_mantenimiento=today.isoformat(),
                fecha_proximo_mantenimiento=(today + timedelta(days=180)).isoformat(),
                km_proximo_mantenimiento=20000,
            )

            self.assertEqual(
                alert_repository.list_startup_alerts(today + timedelta(days=8)),
                [],
            )
            mantenimiento = mantenimiento_repository.get(mantenimiento_id)
            self.assertIsNotNone(mantenimiento)
            assert mantenimiento is not None
            self.assertEqual(mantenimiento.regularidad_fecha_meses, 6)
            self.assertEqual(mantenimiento.regularidad_km, 10000)

    def test_truck_can_store_default_driver(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "gestion.sqlite3"
            initialize_database(database_path, seed=False)
            chofer_repository = ChoferRepository(database_path)
            vehiculo_repository = VehiculoRepository(database_path)

            chofer_id = chofer_repository.create(
                dni="87654321",
                nombre="Carlos",
                apellido="Gomez",
                numero_telefono="",
                fecha_vencimiento_registro="2027-01-01",
            )
            vehiculo_id = vehiculo_repository.create(
                tipo="CAMION",
                nombre_identificatorio="Camion 3",
                patente="GHI789",
                chofer_predeterminado_id=chofer_id,
                observaciones="",
            )

            vehiculo = vehiculo_repository.list_all("CAMION")[0]

            self.assertEqual(vehiculo.id, vehiculo_id)
            self.assertEqual(vehiculo.chofer_predeterminado_id, chofer_id)
            self.assertEqual(vehiculo.chofer_predeterminado_nombre, "Carlos Gomez")


if __name__ == "__main__":
    unittest.main()
