from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from gestion_camiones.data.models import ViajeResumen


@dataclass(frozen=True)
class MonthlyReportSummary:
    trip_count: int
    total_amount: float


def build_monthly_report_summary(viajes: list[ViajeResumen]) -> MonthlyReportSummary:
    return MonthlyReportSummary(
        trip_count=len(viajes),
        total_amount=sum(viaje.costo_total for viaje in viajes),
    )


def export_monthly_report_excel(
    output_path: Path,
    period_label: str,
    viajes: list[ViajeResumen],
    *,
    report_title: str = "Reporte mensual",
) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Reporte mensual"

    summary = build_monthly_report_summary(viajes)
    headers = _report_headers()

    worksheet["A1"] = report_title
    worksheet["A1"].font = Font(size=16, bold=True)
    worksheet["A2"] = f"Periodo: {period_label}"
    worksheet["A3"] = f"Viajes: {summary.trip_count}"
    worksheet["D3"] = f"Total: {_format_money(summary.total_amount)}"

    header_fill = PatternFill(fill_type="solid", fgColor="24333A")
    header_font = Font(color="FFFFFF", bold=True)

    header_row = 5
    for column_index, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=header_row, column=column_index, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_index, row in enumerate(_report_rows(viajes), start=header_row + 1):
        for column_index, value in enumerate(row, start=1):
            cell = worksheet.cell(row=row_index, column=column_index, value=value)
            cell.alignment = Alignment(vertical="top")

    widths = [12, 22, 16, 18, 18, 18, 18, 16, 16, 16, 16, 16, 16, 14]
    for column_index, width in enumerate(widths, start=1):
        worksheet.column_dimensions[chr(64 + column_index)].width = width

    workbook.save(output_path)


def export_monthly_report_pdf(
    output_path: Path,
    period_label: str,
    viajes: list[ViajeResumen],
    *,
    report_title: str = "Reporte mensual",
) -> None:
    summary = build_monthly_report_summary(viajes)
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = [
        Paragraph(report_title, styles["Title"]),
        Paragraph(f"Periodo: {period_label}", styles["Heading3"]),
        Paragraph(
            f"Viajes: {summary.trip_count} | Total: {_format_money(summary.total_amount)}",
            styles["BodyText"],
        ),
        Spacer(1, 8),
    ]

    table_data = [_report_headers(), *_report_rows(viajes)]
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24333A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E0E5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (7, 1), (12, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)
    document.build(story)


def _report_headers() -> list[str]:
    return [
        "Fecha",
        "Cliente",
        "Carga",
        "Lugar carga",
        "Lugar descarga",
        "Chofer",
        "Camion",
        "Tarifa",
        "Demora",
        "Vacio",
        "Gas oil (lts)",
        "Peajes",
        "Total",
        "Estado",
    ]


def _report_rows(viajes: list[ViajeResumen]) -> list[list[str]]:
    return [
        [
            viaje.fecha,
            viaje.cliente,
            viaje.carga,
            viaje.lugar_carga,
            viaje.lugar_descarga,
            viaje.chofer,
            viaje.camion,
            _format_money(viaje.tarifa),
            _format_money(viaje.demora),
            _format_money(viaje.vacio),
            _format_decimal(viaje.gas_oil_lts),
            _format_money(viaje.peajes),
            _format_money(viaje.costo_total),
            viaje.estado,
        ]
        for viaje in viajes
    ]


def _format_money(value: float) -> str:
    return f"$ {value:,.0f}".replace(",", ".")


def _format_decimal(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
