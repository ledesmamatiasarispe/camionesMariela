from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from gestion_camiones.data.repositories import AlertRepository, ChoferRepository
from gestion_camiones.data.schema import initialize_database


class AlertRepositoryTests(unittest.TestCase):
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

            self.assertEqual(
                alert_repository.list_startup_alerts(today + timedelta(days=8)),
                [],
            )


if __name__ == "__main__":
    unittest.main()
