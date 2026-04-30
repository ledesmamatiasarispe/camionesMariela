from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from gestion_camiones.data.models import ViajeResumen
from gestion_camiones.services.report_exporter import (
    build_monthly_report_summary,
    export_monthly_report_excel,
    export_monthly_report_pdf,
)


def _sample_viaje() -> ViajeResumen:
    return ViajeResumen(
        id=1,
        fecha="2026-04-15",
        cliente="Cliente Uno",
        carga="CONT-001",
        lugar_carga="Buenos Aires",
        lugar_descarga="Cordoba",
        observaciones="",
        chofer="Juan Perez",
        tipo_carga="General",
        camion="Camion 1 - AAA111",
        semi="",
        tarifa=100000,
        fecha_descarga_tarifa="2026-04-16",
        demora=5000,
        fecha_descarga_demora="2026-04-16",
        vacio=2500,
        fecha_descarga_vacio="2026-04-16",
        gas_oil_lts=320.5,
        peajes=1500,
        estado="Programado",
    )


class ReportExporterTests(unittest.TestCase):
    def test_build_summary(self) -> None:
        summary = build_monthly_report_summary([_sample_viaje(), _sample_viaje()])
        self.assertEqual(summary.trip_count, 2)
        self.assertEqual(summary.total_amount, 218000)

    def test_export_excel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "reporte.xlsx"
            export_monthly_report_excel(output_path, "Abril 2026", [_sample_viaje()])

            workbook = load_workbook(output_path)
            worksheet = workbook.active

            self.assertEqual(worksheet["A1"].value, "Reporte mensual")
            self.assertEqual(worksheet["A2"].value, "Periodo: Abril 2026")
            self.assertEqual(worksheet["A6"].value, "2026-04-15")
            self.assertEqual(worksheet["M6"].value, "$ 109.000")

    def test_export_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "reporte.pdf"
            export_monthly_report_pdf(output_path, "Abril 2026", [_sample_viaje()])

            content = output_path.read_bytes()
            self.assertTrue(content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
