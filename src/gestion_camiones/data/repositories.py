from __future__ import annotations

from contextlib import closing
import sqlite3
from pathlib import Path

from gestion_camiones.data.models import ViajeResumen


class ViajeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_resumen(self, search: str = "") -> list[ViajeResumen]:
        query = """
            SELECT
                viajes.id,
                clientes.nombre AS cliente,
                cargas.descripcion AS carga,
                lugar_carga.nombre AS lugar_carga,
                lugar_descarga.nombre AS lugar_descarga,
                COALESCE(viajes.observaciones, '') AS observaciones,
                choferes.nombre AS chofer,
                COALESCE(viajes.tipo_carga, '') AS tipo_carga,
                camiones.patente AS camion,
                COALESCE(semis.patente, '') AS semi,
                viajes.tarifa,
                COALESCE(viajes.fecha_descarga_programada, '') AS fecha_descarga_programada,
                viajes.demora,
                COALESCE(viajes.fecha_descarga_real, '') AS fecha_descarga_real,
                viajes.vacio,
                viajes.peajes,
                viajes.estado
            FROM viajes
            JOIN clientes ON clientes.id = viajes.cliente_id
            JOIN cargas ON cargas.id = viajes.carga_id
            JOIN lugares AS lugar_carga ON lugar_carga.id = viajes.lugar_carga_id
            JOIN lugares AS lugar_descarga ON lugar_descarga.id = viajes.lugar_descarga_id
            JOIN choferes ON choferes.id = viajes.chofer_id
            JOIN camiones ON camiones.id = viajes.camion_id
            LEFT JOIN semis ON semis.id = viajes.semi_id
        """
        params: tuple[str, ...] = ()
        if search.strip():
            query += """
                WHERE clientes.nombre LIKE ?
                   OR cargas.descripcion LIKE ?
                   OR lugar_carga.nombre LIKE ?
                   OR lugar_descarga.nombre LIKE ?
                   OR choferes.nombre LIKE ?
                   OR camiones.patente LIKE ?
                   OR semis.patente LIKE ?
            """
            pattern = f"%{search.strip()}%"
            params = (pattern, pattern, pattern, pattern, pattern, pattern, pattern)

        query += " ORDER BY viajes.fecha_descarga_programada, viajes.id"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [ViajeResumen(**dict(row)) for row in rows]

    def dashboard_metrics(self) -> dict[str, int]:
        with closing(self._connect()) as connection:
            total = connection.execute("SELECT COUNT(*) FROM viajes").fetchone()[0]
            en_viaje = connection.execute(
                "SELECT COUNT(*) FROM viajes WHERE estado = 'En viaje'"
            ).fetchone()[0]
            demorados = connection.execute(
                "SELECT COUNT(*) FROM viajes WHERE demora > 0"
            ).fetchone()[0]
            finalizados = connection.execute(
                "SELECT COUNT(*) FROM viajes WHERE estado = 'Finalizado'"
            ).fetchone()[0]

        return {
            "Viajes cargados": total,
            "En viaje": en_viaje,
            "Con demora": demorados,
            "Finalizados": finalizados,
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
