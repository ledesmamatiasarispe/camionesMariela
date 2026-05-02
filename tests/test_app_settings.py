from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gestion_camiones.services.app_settings import load_app_settings, save_app_settings


class AppSettingsTests(unittest.TestCase):
    def test_preserves_cliente_viaje_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"

            save_app_settings(
                settings_path,
                {
                    "company_name": "Mi Empresa",
                    "cliente_viaje_fields": {
                        "1": ["fecha", "carga"],
                        "2": ["tarifa"],
                    },
                },
            )

            settings = load_app_settings(settings_path)

        self.assertEqual(settings["company_name"], "Mi Empresa")
        self.assertEqual(
            settings["cliente_viaje_fields"],
            {
                "1": ["fecha", "carga"],
                "2": ["tarifa"],
            },
        )

    def test_preserves_font_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"

            save_app_settings(
                settings_path,
                {
                    "company_name": "Mi Empresa",
                    "font_sizes": {
                        "base": 15,
                        "page_title": 22,
                        "section_title": 17,
                    },
                },
            )

            settings = load_app_settings(settings_path)

        self.assertEqual(
            settings["font_sizes"],
            {
                "base": 15,
                "page_title": 22,
                "section_title": 17,
            },
        )


if __name__ == "__main__":
    unittest.main()
