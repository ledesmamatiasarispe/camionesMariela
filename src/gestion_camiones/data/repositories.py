from __future__ import annotations

from contextlib import closing
import sqlite3
from pathlib import Path

from gestion_camiones.data.models import (
    Carga,
    Chofer,
    Cliente,
    Lugar,
    LugarRol,
    Peaje,
    Vehiculo,
    ViajeResumen,
)


class ViajeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_resumen(self, search: str = "") -> list[ViajeResumen]:
        query = """
            SELECT
                viajes.id,
                clientes.nombre AS cliente,
                cargas.codigo_contenedor AS carga,
                lugar_carga.nombre AS lugar_carga,
                lugar_descarga.nombre AS lugar_descarga,
                COALESCE(viajes.observaciones, '') AS observaciones,
                trim(choferes.nombre || ' ' || choferes.apellido) AS chofer,
                CASE viajes.tipo_carga
                    WHEN 'PELIGROSA' THEN 'Carga peligrosa'
                    ELSE 'General'
                END AS tipo_carga,
                camion.nombre_identificatorio || ' - ' || camion.patente AS camion,
                COALESCE(semi.nombre_identificatorio || ' - ' || semi.patente, '') AS semi,
                viajes.tarifa,
                COALESCE(viajes.fecha_descarga_tarifa, '') AS fecha_descarga_tarifa,
                viajes.demora,
                COALESCE(viajes.fecha_descarga_demora, '') AS fecha_descarga_demora,
                viajes.vacio,
                COALESCE(
                    (
                        SELECT SUM(peajes.costo)
                        FROM viaje_peajes
                        JOIN peajes ON peajes.id = viaje_peajes.peaje_id
                        WHERE viaje_peajes.viaje_id = viajes.id
                    ),
                    viajes.peajes
                ) AS peajes,
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
                   OR cargas.codigo_contenedor LIKE ?
                   OR lugar_carga.nombre LIKE ?
                   OR lugar_carga.direccion LIKE ?
                   OR lugar_carga.observaciones LIKE ?
                   OR lugar_descarga.nombre LIKE ?
                   OR lugar_descarga.direccion LIKE ?
                   OR lugar_descarga.observaciones LIKE ?
                   OR choferes.dni LIKE ?
                   OR choferes.nombre LIKE ?
                   OR choferes.apellido LIKE ?
                   OR choferes.numero_telefono LIKE ?
                   OR camion.nombre_identificatorio LIKE ?
                   OR camion.patente LIKE ?
                   OR semi.nombre_identificatorio LIKE ?
                   OR semi.patente LIKE ?
                   OR EXISTS (
                       SELECT 1
                       FROM viaje_peajes
                       JOIN peajes ON peajes.id = viaje_peajes.peaje_id
                       WHERE viaje_peajes.viaje_id = viajes.id
                         AND (
                             peajes.nombre LIKE ?
                             OR peajes.direccion LIKE ?
                         )
                   )
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
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
            )

        query += " ORDER BY viajes.fecha_descarga_tarifa, viajes.id"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [ViajeResumen(**dict(row)) for row in rows]

    def dashboard_metrics(self) -> dict[str, int | float]:
        with closing(self._connect()) as connection:
            total = connection.execute("SELECT COUNT(*) FROM viajes").fetchone()[0]
            tarifa_total = connection.execute(
                "SELECT COALESCE(SUM(tarifa), 0) FROM viajes"
            ).fetchone()[0]
            demora_total = connection.execute(
                "SELECT COALESCE(SUM(demora), 0) FROM viajes"
            ).fetchone()[0]
            vacio_total = connection.execute(
                "SELECT COALESCE(SUM(vacio), 0) FROM viajes"
            ).fetchone()[0]
            peajes_total = connection.execute(
                """
                SELECT COALESCE(SUM(peajes.costo), 0)
                FROM viaje_peajes
                JOIN peajes ON peajes.id = viaje_peajes.peaje_id
                """
            ).fetchone()[0]

        return {
            "Viajes cargados": total,
            "Tarifa total": tarifa_total,
            "Demora total": demora_total,
            "Vacio total": vacio_total,
            "Peajes total": peajes_total,
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


class CargaRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[Carga]:
        query = """
            SELECT
                id,
                codigo_contenedor,
                activo
            FROM cargas
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY codigo_contenedor"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            Carga(
                id=row["id"],
                codigo_contenedor=row["codigo_contenedor"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


class LugarRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[Lugar]:
        query = """
            SELECT
                id,
                nombre,
                direccion,
                observaciones,
                activo
            FROM lugares
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY nombre"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            Lugar(
                id=row["id"],
                nombre=row["nombre"],
                direccion=row["direccion"],
                observaciones=row["observaciones"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def list_roles(
        self,
        rol: str | None = None,
        include_inactive: bool = False,
    ) -> list[LugarRol]:
        query = """
            SELECT
                lugar_roles.id,
                lugar_roles.lugar_id,
                lugares.nombre AS lugar,
                lugar_roles.rol,
                lugar_roles.valido_desde,
                lugar_roles.valido_hasta,
                lugar_roles.observaciones,
                lugar_roles.activo
            FROM lugar_roles
            JOIN lugares ON lugares.id = lugar_roles.lugar_id
        """
        clauses = []
        params: list[str | int] = []

        if rol is not None:
            clauses.append("lugar_roles.rol = ?")
            params.append(rol)

        if not include_inactive:
            clauses.append("lugar_roles.activo = ?")
            params.append(1)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY lugares.nombre, lugar_roles.rol, lugar_roles.valido_desde"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [
            LugarRol(
                id=row["id"],
                lugar_id=row["lugar_id"],
                lugar=row["lugar"],
                rol=row["rol"],
                valido_desde=row["valido_desde"],
                valido_hasta=row["valido_hasta"],
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
                numero_telefono,
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
                numero_telefono=row["numero_telefono"],
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


class PeajeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[Peaje]:
        query = """
            SELECT
                id,
                nombre,
                direccion,
                costo,
                activo
            FROM peajes
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY nombre"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            Peaje(
                id=row["id"],
                nombre=row["nombre"],
                direccion=row["direccion"],
                costo=row["costo"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
