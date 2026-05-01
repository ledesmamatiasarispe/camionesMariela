from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

from gestion_camiones.data.models import (
    AppAlert,
    Carga,
    Chofer,
    Cliente,
    EmpresaPeaje,
    Lugar,
    LugarRol,
    Peaje,
    TipoCarga,
    Vehiculo,
    ViajeCreate,
    ViajeResumen,
)


class ViajeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_resumen(self, search: str = "") -> list[ViajeResumen]:
        query = """
            SELECT
                viajes.id,
                COALESCE(viajes.fecha, '') AS fecha,
                CASE
                    WHEN COALESCE(clientes.es_cliente_directo, 1) = 0
                         AND cliente_padre.nombre IS NOT NULL
                    THEN clientes.nombre || ' (' || cliente_padre.nombre || ')'
                    ELSE clientes.nombre
                END AS cliente,
                COALESCE(clientes.es_cliente_directo, 1) AS cliente_es_directo,
                COALESCE(viajes.carta_porte, '') AS carta_porte,
                cargas.codigo_contenedor AS carga,
                lugar_carga.nombre AS lugar_carga,
                lugar_descarga.nombre AS lugar_descarga,
                COALESCE(viajes.observaciones, '') AS observaciones,
                trim(choferes.nombre || ' ' || choferes.apellido) AS chofer,
                COALESCE(tipos_carga.nombre, viajes.tipo_carga) AS tipo_carga,
                camion.nombre_identificatorio || ' - ' || camion.patente AS camion,
                COALESCE(semi.nombre_identificatorio || ' - ' || semi.patente, '') AS semi,
                viajes.tarifa,
                COALESCE(viajes.fecha_descarga_tarifa, '') AS fecha_descarga_tarifa,
                viajes.demora,
                COALESCE(viajes.fecha_descarga_demora, '') AS fecha_descarga_demora,
                viajes.vacio,
                COALESCE(viajes.fecha_descarga_vacio, '') AS fecha_descarga_vacio,
                COALESCE(viajes.gas_oil_lts, 0) AS gas_oil_lts,
                COALESCE(
                    (
                        SELECT SUM(viaje_peajes.costo)
                        FROM viaje_peajes
                        WHERE viaje_peajes.viaje_id = viajes.id
                    ),
                    viajes.peajes
                ) AS peajes,
                viajes.estado
            FROM viajes
            JOIN clientes ON clientes.id = viajes.cliente_id
            LEFT JOIN clientes AS cliente_padre
                ON cliente_padre.id = clientes.cliente_padre_id
            JOIN cargas ON cargas.id = viajes.carga_id
            JOIN lugares AS lugar_carga ON lugar_carga.id = viajes.lugar_carga_id
            JOIN lugares AS lugar_descarga ON lugar_descarga.id = viajes.lugar_descarga_id
            JOIN choferes ON choferes.id = viajes.chofer_id
            JOIN vehiculos AS camion
                ON camion.id = viajes.camion_id AND camion.tipo = 'CAMION'
            LEFT JOIN vehiculos AS semi
                ON semi.id = viajes.semi_id AND semi.tipo = 'SEMI'
            LEFT JOIN tipos_carga ON tipos_carga.codigo = viajes.tipo_carga
        """
        params: tuple[str, ...] = ()
        if search.strip():
            query += """
                WHERE clientes.nombre LIKE ?
                   OR clientes.cuit LIKE ?
                   OR clientes.email LIKE ?
                   OR clientes.numero_contacto LIKE ?
                   OR cliente_padre.nombre LIKE ?
                   OR viajes.carta_porte LIKE ?
                   OR cargas.codigo_contenedor LIKE ?
                   OR viajes.observaciones LIKE ?
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
                pattern,
                pattern,
                pattern,
                pattern,
            )

        query += " ORDER BY viajes.fecha, viajes.fecha_descarga_tarifa, viajes.id"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [ViajeResumen(**dict(row)) for row in rows]

    def create(self, viaje: ViajeCreate) -> int:
        with closing(self._connect()) as connection:
            peajes_total = self._peajes_total(connection, viaje.peaje_ids)
            cursor = connection.execute(
                """
                INSERT INTO viajes (
                    fecha,
                    cliente_id,
                    carta_porte,
                    carga_id,
                    lugar_carga_id,
                    lugar_descarga_id,
                    chofer_id,
                    camion_id,
                    semi_id,
                    tipo_carga,
                    tarifa,
                    fecha_descarga_tarifa,
                    demora,
                    fecha_descarga_demora,
                    vacio,
                    fecha_descarga_vacio,
                    gas_oil_lts,
                    peajes,
                    observaciones,
                    estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    viaje.fecha,
                    viaje.cliente_id,
                    viaje.carta_porte,
                    viaje.carga_id,
                    viaje.lugar_carga_id,
                    viaje.lugar_descarga_id,
                    viaje.chofer_id,
                    viaje.camion_id,
                    viaje.semi_id,
                    viaje.tipo_carga,
                    viaje.tarifa,
                    viaje.fecha_descarga_tarifa,
                    viaje.demora,
                    viaje.fecha_descarga_demora,
                    viaje.vacio,
                    viaje.fecha_descarga_vacio,
                    viaje.gas_oil_lts,
                    peajes_total,
                    viaje.observaciones,
                    "Programado",
                ),
            )
            viaje_id = int(cursor.lastrowid)
            for peaje_id in viaje.peaje_ids:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO viaje_peajes (viaje_id, peaje_id, costo)
                    SELECT ?, id, costo
                    FROM peajes
                    WHERE id = ?
                    """,
                    (viaje_id, peaje_id),
                )
            connection.commit()
            return viaje_id

    def update_basic(
        self,
        viaje_id: int,
        *,
        fecha: str,
        carta_porte: str,
        observaciones: str,
        tarifa: float,
        fecha_descarga_tarifa: str,
        demora: float,
        fecha_descarga_demora: str,
        vacio: float,
        fecha_descarga_vacio: str,
        gas_oil_lts: float,
        estado: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE viajes
                SET
                    fecha = ?,
                    carta_porte = ?,
                    observaciones = ?,
                    tarifa = ?,
                    fecha_descarga_tarifa = ?,
                    demora = ?,
                    fecha_descarga_demora = ?,
                    vacio = ?,
                    fecha_descarga_vacio = ?,
                    gas_oil_lts = ?,
                    estado = ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    fecha,
                    carta_porte,
                    observaciones,
                    tarifa,
                    fecha_descarga_tarifa,
                    demora,
                    fecha_descarga_demora,
                    vacio,
                    fecha_descarga_vacio,
                    gas_oil_lts,
                    estado,
                    viaje_id,
                ),
            )
            connection.commit()

    def delete(self, viaje_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM viaje_peajes WHERE viaje_id = ?", (viaje_id,))
            connection.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
            connection.commit()

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
                SELECT COALESCE(SUM(costo), 0)
                FROM viaje_peajes
                """
            ).fetchone()[0]

        return {
            "Viajes cargados": total,
            "Tarifa total": tarifa_total,
            "Demora total": demora_total,
            "Vacio total": vacio_total,
            "Peajes total": peajes_total,
        }

    def monthly_billing(self, start_month: str, end_month: str) -> dict[str, float]:
        query = """
            SELECT
                periodo,
                SUM(tarifa + demora + vacio + peajes_total) AS total
            FROM (
                SELECT
                    substr(viajes.fecha, 1, 7) AS periodo,
                    COALESCE(viajes.tarifa, 0) AS tarifa,
                    COALESCE(viajes.demora, 0) AS demora,
                    COALESCE(viajes.vacio, 0) AS vacio,
                    COALESCE(
                        (
                            SELECT SUM(viaje_peajes.costo)
                            FROM viaje_peajes
                            WHERE viaje_peajes.viaje_id = viajes.id
                        ),
                        viajes.peajes,
                        0
                    ) AS peajes_total
                FROM viajes
                WHERE substr(viajes.fecha, 1, 7) BETWEEN ? AND ?
            )
            GROUP BY periodo
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query, (start_month, end_month)).fetchall()
        return {str(row["periodo"]): float(row["total"]) for row in rows}

    def billing_years(self) -> list[int]:
        query = """
            SELECT DISTINCT substr(fecha, 1, 4) AS year
            FROM viajes
            WHERE length(fecha) >= 4
            ORDER BY year
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query).fetchall()

        years = []
        for row in rows:
            value = str(row["year"])
            if value.isdigit():
                years.append(int(value))
        return years

    def monthly_report_rows(self, year: int, month: int) -> list[ViajeResumen]:
        period = f"{year:04d}-{month:02d}"
        return [viaje for viaje in self.list_resumen() if viaje.fecha.startswith(period)]

    def annual_report_rows(self, year: int) -> list[ViajeResumen]:
        period = f"{year:04d}-"
        return [viaje for viaje in self.list_resumen() if viaje.fecha.startswith(period)]

    def period_report_rows(
        self,
        start_date: str,
        end_date: str,
        *,
        client_search: str = "",
    ) -> list[ViajeResumen]:
        normalized_search = client_search.strip().lower()
        rows = [
            viaje
            for viaje in self.list_resumen()
            if start_date <= viaje.fecha <= end_date
        ]
        if not normalized_search:
            return rows
        return [
            viaje
            for viaje in rows
            if normalized_search in viaje.cliente.lower()
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _peajes_total(
        self,
        connection: sqlite3.Connection,
        peaje_ids: tuple[int, ...],
    ) -> float:
        if not peaje_ids:
            return 0

        placeholders = ", ".join("?" for _ in peaje_ids)
        row = connection.execute(
            f"SELECT COALESCE(SUM(costo), 0) FROM peajes WHERE id IN ({placeholders})",
            peaje_ids,
        ).fetchone()
        return float(row[0])


class ClienteRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[Cliente]:
        query = """
            SELECT
                clientes.id,
                clientes.nombre,
                clientes.cuit,
                clientes.email,
                clientes.numero_contacto,
                COALESCE(clientes.es_cliente_directo, 1) AS es_cliente_directo,
                clientes.cliente_padre_id,
                COALESCE(cliente_padre.nombre, '') AS cliente_padre_nombre,
                clientes.activo
            FROM clientes
            LEFT JOIN clientes AS cliente_padre
                ON cliente_padre.id = clientes.cliente_padre_id
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE clientes.activo = ?"
            params = (1,)

        query += " ORDER BY clientes.nombre"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            Cliente(
                id=row["id"],
                nombre=row["nombre"],
                cuit=row["cuit"],
                email=row["email"],
                numero_contacto=row["numero_contacto"],
                es_cliente_directo=bool(row["es_cliente_directo"]),
                cliente_padre_id=row["cliente_padre_id"],
                cliente_padre_nombre=row["cliente_padre_nombre"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def create(
        self,
        *,
        nombre: str,
        cuit: str,
        email: str,
        numero_contacto: str,
        es_cliente_directo: bool,
        cliente_padre_id: int | None,
    ) -> int:
        with closing(self._connect()) as connection:
            normalized_parent_id = self._normalize_cliente_padre_id(
                connection,
                cliente_padre_id,
                es_cliente_directo=es_cliente_directo,
            )
            cursor = connection.execute(
                """
                INSERT INTO clientes (
                    nombre,
                    cuit,
                    email,
                    numero_contacto,
                    es_cliente_directo,
                    cliente_padre_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    nombre,
                    cuit,
                    email,
                    numero_contacto,
                    int(es_cliente_directo),
                    normalized_parent_id,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(
        self,
        cliente_id: int,
        *,
        nombre: str,
        cuit: str,
        email: str,
        numero_contacto: str,
        es_cliente_directo: bool,
        cliente_padre_id: int | None,
    ) -> None:
        with closing(self._connect()) as connection:
            normalized_parent_id = self._normalize_cliente_padre_id(
                connection,
                cliente_padre_id,
                es_cliente_directo=es_cliente_directo,
                current_cliente_id=cliente_id,
            )
            connection.execute(
                """
                UPDATE clientes
                SET
                    nombre = ?,
                    cuit = ?,
                    email = ?,
                    numero_contacto = ?,
                    es_cliente_directo = ?,
                    cliente_padre_id = ?
                WHERE id = ?
                """,
                (
                    nombre,
                    cuit,
                    email,
                    numero_contacto,
                    int(es_cliente_directo),
                    normalized_parent_id,
                    cliente_id,
                ),
            )
            connection.commit()

    def delete(self, cliente_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE clientes SET activo = 0 WHERE id = ?",
                (cliente_id,),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _normalize_cliente_padre_id(
        self,
        connection: sqlite3.Connection,
        cliente_padre_id: int | None,
        *,
        es_cliente_directo: bool,
        current_cliente_id: int | None = None,
    ) -> int | None:
        if es_cliente_directo:
            return None
        if cliente_padre_id is None:
            raise ValueError(
                "Si el cliente no es directo, debes seleccionar un intermediario."
            )
        if current_cliente_id is not None and cliente_padre_id == current_cliente_id:
            raise ValueError("El cliente no puede apuntarse a si mismo.")

        row = connection.execute(
            "SELECT id FROM clientes WHERE id = ?",
            (cliente_padre_id,),
        ).fetchone()
        if row is None:
            raise ValueError("El intermediario seleccionado no existe.")
        return cliente_padre_id


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

    def create(self, *, codigo_contenedor: str) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                "INSERT INTO cargas (codigo_contenedor) VALUES (?)",
                (codigo_contenedor,),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def get_or_create(self, *, codigo_contenedor: str) -> int:
        codigo = codigo_contenedor.strip()
        if not codigo:
            raise ValueError("El codigo de carga es obligatorio.")

        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, activo
                FROM cargas
                WHERE codigo_contenedor = ?
                """,
                (codigo,),
            ).fetchone()
            if row is not None:
                if not row["activo"]:
                    connection.execute(
                        "UPDATE cargas SET activo = 1 WHERE id = ?",
                        (row["id"],),
                    )
                    connection.commit()
                return int(row["id"])

            cursor = connection.execute(
                "INSERT INTO cargas (codigo_contenedor) VALUES (?)",
                (codigo,),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, carga_id: int, *, codigo_contenedor: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE cargas SET codigo_contenedor = ? WHERE id = ?",
                (codigo_contenedor, carga_id),
            )
            connection.commit()

    def delete(self, carga_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute("UPDATE cargas SET activo = 0 WHERE id = ?", (carga_id,))
            connection.commit()

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

    def list_by_viaje_usage(
        self,
        rol: str,
        include_inactive: bool = False,
    ) -> list[Lugar]:
        usage_column_by_role = {
            "CARGA": "lugar_carga_id",
            "DESCARGA": "lugar_descarga_id",
        }
        usage_column = usage_column_by_role.get(rol)
        if usage_column is None:
            raise ValueError("Rol de lugar invalido.")

        query = f"""
            SELECT
                lugares.id,
                lugares.nombre,
                lugares.direccion,
                lugares.observaciones,
                lugares.activo,
                COUNT(viajes.id) AS usos
            FROM lugares
            LEFT JOIN viajes ON viajes.{usage_column} = lugares.id
        """
        params: list[int] = []

        if not include_inactive:
            query += " WHERE lugares.activo = ?"
            params.append(1)

        query += """
            GROUP BY
                lugares.id,
                lugares.nombre,
                lugares.direccion,
                lugares.observaciones,
                lugares.activo
            ORDER BY usos DESC, lugares.nombre COLLATE NOCASE
        """

        with closing(self._connect()) as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

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

    def create(
        self,
        *,
        nombre: str,
        direccion: str,
        observaciones: str,
        roles: tuple[str, ...],
    ) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO lugares (nombre, direccion, observaciones)
                VALUES (?, ?, ?)
                """,
                (nombre, direccion, observaciones),
            )
            lugar_id = int(cursor.lastrowid)
            self._set_roles(connection, lugar_id, roles)
            connection.commit()
            return lugar_id

    def update(
        self,
        lugar_id: int,
        *,
        nombre: str,
        direccion: str,
        observaciones: str,
        roles: tuple[str, ...],
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE lugares
                SET nombre = ?, direccion = ?, observaciones = ?
                WHERE id = ?
                """,
                (nombre, direccion, observaciones, lugar_id),
            )
            self._set_roles(connection, lugar_id, roles)
            connection.commit()

    def delete(self, lugar_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE lugares SET activo = 0 WHERE id = ?",
                (lugar_id,),
            )
            connection.execute(
                "UPDATE lugar_roles SET activo = 0 WHERE lugar_id = ?",
                (lugar_id,),
            )
            connection.commit()

    def _set_roles(
        self,
        connection: sqlite3.Connection,
        lugar_id: int,
        roles: tuple[str, ...],
    ) -> None:
        normalized_roles = tuple(role for role in roles if role in {"CARGA", "DESCARGA"})
        connection.execute(
            "UPDATE lugar_roles SET activo = 0 WHERE lugar_id = ?",
            (lugar_id,),
        )
        for role in normalized_roles:
            connection.execute(
                """
                INSERT INTO lugar_roles (
                    lugar_id,
                    rol,
                    valido_desde,
                    valido_hasta,
                    observaciones,
                    activo
                ) VALUES (?, ?, '', NULL, '', 1)
                """,
                (lugar_id, role),
            )

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

    def create(
        self,
        *,
        dni: str,
        nombre: str,
        apellido: str,
        numero_telefono: str,
        fecha_vencimiento_registro: str,
    ) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO choferes (
                    dni,
                    nombre,
                    apellido,
                    numero_telefono,
                    fecha_vencimiento_registro
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    dni,
                    nombre,
                    apellido,
                    numero_telefono,
                    fecha_vencimiento_registro,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(
        self,
        chofer_id: int,
        *,
        dni: str,
        nombre: str,
        apellido: str,
        numero_telefono: str,
        fecha_vencimiento_registro: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE choferes
                SET
                    dni = ?,
                    nombre = ?,
                    apellido = ?,
                    numero_telefono = ?,
                    fecha_vencimiento_registro = ?
                WHERE id = ?
                """,
                (
                    dni,
                    nombre,
                    apellido,
                    numero_telefono,
                    fecha_vencimiento_registro,
                    chofer_id,
                ),
            )
            connection.commit()

    def update_fecha_vencimiento_registro(
        self,
        chofer_id: int,
        fecha_vencimiento_registro: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE choferes
                SET fecha_vencimiento_registro = ?
                WHERE id = ?
                """,
                (fecha_vencimiento_registro, chofer_id),
            )
            connection.commit()

    def delete(self, chofer_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE choferes SET activo = 0 WHERE id = ?",
                (chofer_id,),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


class AlertRepository:
    DRIVER_LICENSE_SOURCE = "chofer_registro"

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_startup_alerts(self, today: date | None = None) -> list[AppAlert]:
        current_date = today or date.today()
        threshold_date = current_date + timedelta(days=60)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    choferes.id,
                    choferes.nombre,
                    choferes.apellido,
                    choferes.fecha_vencimiento_registro,
                    alertas_app.avisar_nuevamente_desde
                FROM choferes
                LEFT JOIN alertas_app
                    ON alertas_app.clave =
                        'chofer_registro:' || choferes.id || ':' ||
                        choferes.fecha_vencimiento_registro
                WHERE choferes.activo = 1
                  AND COALESCE(choferes.fecha_vencimiento_registro, '') != ''
                  AND choferes.fecha_vencimiento_registro <= ?
                  AND (
                      alertas_app.avisar_nuevamente_desde IS NULL
                      OR alertas_app.avisar_nuevamente_desde = ''
                      OR alertas_app.avisar_nuevamente_desde <= ?
                  )
                ORDER BY choferes.fecha_vencimiento_registro, choferes.apellido, choferes.nombre
                """,
                (threshold_date.isoformat(), current_date.isoformat()),
            ).fetchall()

        alerts: list[AppAlert] = []
        for row in rows:
            due_date = str(row["fecha_vencimiento_registro"])
            try:
                due = date.fromisoformat(due_date)
            except ValueError:
                continue
            full_name = f"{row['nombre']} {row['apellido']}".strip()
            if due < current_date:
                timing = f"vencio el {due_date}"
            else:
                days_left = (due - current_date).days
                timing = f"vence el {due_date} ({days_left} dias)"
            alerts.append(
                AppAlert(
                    key=self.driver_license_alert_key(int(row["id"]), due_date),
                    source=self.DRIVER_LICENSE_SOURCE,
                    title="Registro de chofer por vencer",
                    message=(
                        f"El registro de {full_name} {timing}.\n\n"
                        "Acepta para volver a recordar en una semana, o valida "
                        "cargando la nueva fecha de vencimiento."
                    ),
                    entity_id=int(row["id"]),
                    due_date=due_date,
                )
            )
        return alerts

    def accept_alert(self, alert_key: str, today: date | None = None) -> None:
        remind_from = (today or date.today()) + timedelta(days=7)
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO alertas_app (
                    clave,
                    avisar_nuevamente_desde,
                    actualizado_en
                ) VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(clave) DO UPDATE SET
                    avisar_nuevamente_desde = excluded.avisar_nuevamente_desde,
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (alert_key, remind_from.isoformat()),
            )
            connection.commit()

    def clear_alert(self, alert_key: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM alertas_app WHERE clave = ?", (alert_key,))
            connection.commit()

    def driver_license_alert_key(self, chofer_id: int, due_date: str) -> str:
        return f"{self.DRIVER_LICENSE_SOURCE}:{chofer_id}:{due_date}"

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

    def create(
        self,
        *,
        tipo: str,
        nombre_identificatorio: str,
        patente: str,
        observaciones: str,
    ) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO vehiculos (
                    tipo,
                    nombre_identificatorio,
                    patente,
                    observaciones
                ) VALUES (?, ?, ?, ?)
                """,
                (tipo, nombre_identificatorio, patente, observaciones),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(
        self,
        vehiculo_id: int,
        *,
        tipo: str,
        nombre_identificatorio: str,
        patente: str,
        observaciones: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE vehiculos
                SET
                    tipo = ?,
                    nombre_identificatorio = ?,
                    patente = ?,
                    observaciones = ?
                WHERE id = ?
                """,
                (
                    tipo,
                    nombre_identificatorio,
                    patente,
                    observaciones,
                    vehiculo_id,
                ),
            )
            connection.commit()

    def delete(self, vehiculo_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE vehiculos SET activo = 0 WHERE id = ?",
                (vehiculo_id,),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


class PeajeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_empresas(self, include_inactive: bool = False) -> list[EmpresaPeaje]:
        query = """
            SELECT
                id,
                nombre,
                activo
            FROM empresas_peaje
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY nombre COLLATE NOCASE"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            EmpresaPeaje(
                id=row["id"],
                nombre=row["nombre"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def create_empresa(self, *, nombre: str) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO empresas_peaje (nombre)
                VALUES (?)
                """,
                (nombre,),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_empresa(self, empresa_id: int, *, nombre: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE empresas_peaje SET nombre = ? WHERE id = ?",
                (nombre, empresa_id),
            )
            connection.commit()

    def delete_empresa(self, empresa_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE empresas_peaje SET activo = 0 WHERE id = ?",
                (empresa_id,),
            )
            connection.execute(
                "UPDATE peajes SET activo = 0 WHERE empresa_id = ?",
                (empresa_id,),
            )
            connection.commit()

    def list_all(
        self,
        include_inactive: bool = False,
        empresa_id: int | None = None,
    ) -> list[Peaje]:
        query = """
            SELECT
                peajes.id,
                peajes.empresa_id,
                COALESCE(empresas_peaje.nombre, '') AS empresa_nombre,
                peajes.nombre,
                peajes.direccion,
                peajes.costo,
                peajes.activo
            FROM peajes
            LEFT JOIN empresas_peaje ON empresas_peaje.id = peajes.empresa_id
        """
        clauses = []
        params: list[int] = []

        if not include_inactive:
            clauses.append("peajes.activo = ?")
            params.append(1)
            clauses.append("COALESCE(empresas_peaje.activo, 1) = ?")
            params.append(1)
        if empresa_id is not None:
            clauses.append("peajes.empresa_id = ?")
            params.append(empresa_id)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY empresas_peaje.nombre COLLATE NOCASE, peajes.nombre COLLATE NOCASE"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [
            Peaje(
                id=row["id"],
                empresa_id=row["empresa_id"],
                empresa_nombre=row["empresa_nombre"],
                nombre=row["nombre"],
                direccion=row["direccion"],
                costo=row["costo"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def create(
        self,
        *,
        empresa_id: int,
        nombre: str,
        direccion: str,
        costo: float,
    ) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO peajes (empresa_id, nombre, direccion, costo)
                VALUES (?, ?, ?, ?)
                """,
                (empresa_id, nombre, direccion, costo),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(
        self,
        peaje_id: int,
        *,
        empresa_id: int,
        nombre: str,
        direccion: str,
        costo: float,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE peajes
                SET empresa_id = ?, nombre = ?, direccion = ?, costo = ?
                WHERE id = ?
                """,
                (empresa_id, nombre, direccion, costo, peaje_id),
            )
            connection.commit()

    def update_cost_many(self, peaje_ids: tuple[int, ...], *, costo: float) -> None:
        if not peaje_ids:
            return

        placeholders = ", ".join("?" for _ in peaje_ids)
        with closing(self._connect()) as connection:
            connection.execute(
                f"""
                UPDATE peajes
                SET costo = ?
                WHERE id IN ({placeholders})
                """,
                (costo, *peaje_ids),
            )
            connection.commit()

    def delete(self, peaje_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE peajes SET activo = 0 WHERE id = ?",
                (peaje_id,),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


class TipoCargaRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, include_inactive: bool = False) -> list[TipoCarga]:
        query = """
            SELECT
                id,
                codigo,
                nombre,
                activo
            FROM tipos_carga
        """
        params: tuple[int, ...] = ()

        if not include_inactive:
            query += " WHERE activo = ?"
            params = (1,)

        query += " ORDER BY nombre"

        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            TipoCarga(
                id=row["id"],
                codigo=row["codigo"],
                nombre=row["nombre"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def create(self, *, codigo: str, nombre: str) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO tipos_carga (codigo, nombre)
                VALUES (?, ?)
                """,
                (codigo, nombre),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, tipo_carga_id: int, *, codigo: str, nombre: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE tipos_carga
                SET codigo = ?, nombre = ?
                WHERE id = ?
                """,
                (codigo, nombre, tipo_carga_id),
            )
            connection.commit()

    def delete(self, tipo_carga_id: int) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE tipos_carga SET activo = 0 WHERE id = ?",
                (tipo_carga_id,),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
