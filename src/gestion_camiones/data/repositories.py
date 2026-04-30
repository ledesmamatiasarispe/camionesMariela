from __future__ import annotations

from contextlib import closing
import sqlite3
from pathlib import Path

from gestion_camiones.data.models import Chofer, Cliente, Vehiculo, ViajeResumen


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
                trim(choferes.nombre || ' ' || choferes.apellido) AS chofer,
                COALESCE(viajes.tipo_carga, '') AS tipo_carga,
                camion.nombre_identificatorio || ' - ' || camion.patente AS camion,
                COALESCE(semi.nombre_identificatorio || ' - ' || semi.patente, '') AS semi,
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
            JOIN vehiculos AS camion
                ON camion.id = viajes.camion_id AND camion.tipo = 'CAMION'
            LEFT JOIN vehiculos AS semi
                ON semi.id = viajes.semi_id AND semi.tipo = 'SEMI'
        """
        params: tuple[str, ...] = ()
        if search.strip():
            query += """
                WHERE clientes.nombre LIKE ?
                   OR clientes.email LIKE ?
                   OR clientes.numero_contacto LIKE ?
                   OR cargas.descripcion LIKE ?
                   OR lugar_carga.nombre LIKE ?
                   OR lugar_descarga.nombre LIKE ?
                   OR choferes.dni LIKE ?
                   OR choferes.nombre LIKE ?
                   OR choferes.apellido LIKE ?
                   OR camion.nombre_identificatorio LIKE ?
                   OR camion.patente LIKE ?
                   OR semi.nombre_identificatorio LIKE ?
                   OR semi.patente LIKE ?
            """
            pattern = f"%{search.strip()}%"
            params = (
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
            )

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


class ClienteRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[Cliente]:
        query = """
            SELECT
                id,
                nombre,
                domicilio_fiscal,
                email,
                numero_contacto,
                activo
            FROM clientes
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY nombre"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            Cliente(
                id=row["id"],
                nombre=row["nombre"],
                domicilio_fiscal=row["domicilio_fiscal"],
                email=row["email"],
                numero_contacto=row["numero_contacto"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


class ChoferRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[Chofer]:
        query = """
            SELECT
                id,
                dni,
                nombre,
                apellido,
                fecha_vencimiento_registro,
                activo
            FROM choferes
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY apellido, nombre"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            Chofer(
                id=row["id"],
                dni=row["dni"],
                nombre=row["nombre"],
                apellido=row["apellido"],
                fecha_vencimiento_registro=row["fecha_vencimiento_registro"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


class VehiculoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(
        self,
        tipo: str | None = None,
        include_inactive: bool = False,
    ) -> list[Vehiculo]:
        query = """
            SELECT
                id,
                tipo,
                nombre_identificatorio,
                patente,
                COALESCE(observaciones, '') AS observaciones,
                activo
            FROM vehiculos
        """
        clauses = []
        params: list[str | int] = []

        if tipo is not None:
            clauses.append("tipo = ?")
            params.append(tipo)

        if not include_inactive:
            clauses.append("activo = ?")
            params.append(1)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY tipo, nombre_identificatorio, patente"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [
            Vehiculo(
                id=row["id"],
                tipo=row["tipo"],
                nombre_identificatorio=row["nombre_identificatorio"],
                patente=row["patente"],
                observaciones=row["observaciones"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
