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
                clientes.nombre AS cliente,
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
            LEFT JOIN tipos_carga ON tipos_carga.codigo = viajes.tipo_carga
        """
        params: tuple[str, ...] = ()
        if search.strip():
            query += """
                WHERE clientes.nombre LIKE ?
                   OR clientes.email LIKE ?
                   OR clientes.numero_contacto LIKE ?
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
                    peajes,
                    observaciones,
                    estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    viaje.fecha,
                    viaje.cliente_id,
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
                    peajes_total,
                    viaje.observaciones,
                    "Programado",
                ),
            )
            viaje_id = int(cursor.lastrowid)
            for peaje_id in viaje.peaje_ids:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO viaje_peajes (viaje_id, peaje_id)
                    VALUES (?, ?)
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
        observaciones: str,
        tarifa: float,
        fecha_descarga_tarifa: str,
        demora: float,
        fecha_descarga_demora: str,
        vacio: float,
        fecha_descarga_vacio: str,
        estado: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE viajes
                SET
                    fecha = ?,
                    observaciones = ?,
                    tarifa = ?,
                    fecha_descarga_tarifa = ?,
                    demora = ?,
                    fecha_descarga_demora = ?,
                    vacio = ?,
                    fecha_descarga_vacio = ?,
                    estado = ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    fecha,
                    observaciones,
                    tarifa,
                    fecha_descarga_tarifa,
                    demora,
                    fecha_descarga_demora,
                    vacio,
                    fecha_descarga_vacio,
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

    def create(
        self,
        *,
        nombre: str,
        domicilio_fiscal: str,
        email: str,
        numero_contacto: str,
    ) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO clientes (
                    nombre,
                    domicilio_fiscal,
                    email,
                    numero_contacto
                ) VALUES (?, ?, ?, ?)
                """,
                (nombre, domicilio_fiscal, email, numero_contacto),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(
        self,
        cliente_id: int,
        *,
        nombre: str,
        domicilio_fiscal: str,
        email: str,
        numero_contacto: str,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE clientes
                SET
                    nombre = ?,
                    domicilio_fiscal = ?,
                    email = ?,
                    numero_contacto = ?
                WHERE id = ?
                """,
                (nombre, domicilio_fiscal, email, numero_contacto, cliente_id),
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

    def create(self, *, nombre: str, direccion: str, costo: float) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO peajes (nombre, direccion, costo)
                VALUES (?, ?, ?)
                """,
                (nombre, direccion, costo),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(
        self,
        peaje_id: int,
        *,
        nombre: str,
        direccion: str,
        costo: float,
    ) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE peajes
                SET nombre = ?, direccion = ?, costo = ?
                WHERE id = ?
                """,
                (nombre, direccion, costo, peaje_id),
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
