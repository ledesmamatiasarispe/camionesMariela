from __future__ import annotations

from contextlib import closing
import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    domicilio_fiscal TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    numero_contacto TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cargas (
    id INTEGER PRIMARY KEY,
    codigo_contenedor TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lugares (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    direccion TEXT NOT NULL DEFAULT '',
    observaciones TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lugar_roles (
    id INTEGER PRIMARY KEY,
    lugar_id INTEGER NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('CARGA', 'DESCARGA')),
    valido_desde TEXT NOT NULL DEFAULT '',
    valido_hasta TEXT,
    observaciones TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lugar_id) REFERENCES lugares(id)
);

CREATE TABLE IF NOT EXISTS choferes (
    id INTEGER PRIMARY KEY,
    dni TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    numero_telefono TEXT NOT NULL DEFAULT '',
    fecha_vencimiento_registro TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehiculos (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('CAMION', 'SEMI')),
    nombre_identificatorio TEXT NOT NULL,
    patente TEXT NOT NULL UNIQUE,
    observaciones TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS viajes (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    carga_id INTEGER NOT NULL,
    lugar_carga_id INTEGER NOT NULL,
    lugar_descarga_id INTEGER NOT NULL,
    chofer_id INTEGER NOT NULL,
    camion_id INTEGER NOT NULL,
    semi_id INTEGER,
    tipo_carga TEXT,
    tarifa NUMERIC NOT NULL DEFAULT 0,
    fecha_descarga_tarifa TEXT,
    demora NUMERIC NOT NULL DEFAULT 0,
    fecha_descarga_demora TEXT,
    vacio NUMERIC NOT NULL DEFAULT 0,
    peajes NUMERIC NOT NULL DEFAULT 0,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'Programado',
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (carga_id) REFERENCES cargas(id),
    FOREIGN KEY (lugar_carga_id) REFERENCES lugares(id),
    FOREIGN KEY (lugar_descarga_id) REFERENCES lugares(id),
    FOREIGN KEY (chofer_id) REFERENCES choferes(id),
    FOREIGN KEY (camion_id) REFERENCES vehiculos(id),
    FOREIGN KEY (semi_id) REFERENCES vehiculos(id)
);

CREATE INDEX IF NOT EXISTS idx_viajes_cliente_id ON viajes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_viajes_chofer_id ON viajes(chofer_id);
CREATE INDEX IF NOT EXISTS idx_viajes_camion_id ON viajes(camion_id);
CREATE INDEX IF NOT EXISTS idx_viajes_estado ON viajes(estado);
"""


POST_MIGRATION_SQL = """
CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cargas_codigo_contenedor
    ON cargas(codigo_contenedor);
CREATE INDEX IF NOT EXISTS idx_lugares_nombre ON lugares(nombre);
CREATE INDEX IF NOT EXISTS idx_lugar_roles_lugar_id ON lugar_roles(lugar_id);
CREATE INDEX IF NOT EXISTS idx_lugar_roles_rol ON lugar_roles(rol);
CREATE UNIQUE INDEX IF NOT EXISTS idx_choferes_dni ON choferes(dni);
CREATE INDEX IF NOT EXISTS idx_choferes_apellido_nombre ON choferes(apellido, nombre);
CREATE INDEX IF NOT EXISTS idx_vehiculos_tipo ON vehiculos(tipo);
CREATE INDEX IF NOT EXISTS idx_vehiculos_nombre_identificatorio
    ON vehiculos(nombre_identificatorio);
CREATE INDEX IF NOT EXISTS idx_viajes_cliente_id ON viajes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_viajes_chofer_id ON viajes(chofer_id);
CREATE INDEX IF NOT EXISTS idx_viajes_camion_id ON viajes(camion_id);
CREATE INDEX IF NOT EXISTS idx_viajes_estado ON viajes(estado);
CREATE INDEX IF NOT EXISTS idx_viajes_fecha_descarga_tarifa
    ON viajes(fecha_descarga_tarifa);
CREATE INDEX IF NOT EXISTS idx_viajes_fecha_descarga_demora
    ON viajes(fecha_descarga_demora);
"""


SEED_SQL = """
INSERT OR IGNORE INTO clientes (
    id,
    nombre,
    domicilio_fiscal,
    email,
    numero_contacto
) VALUES
    (
        1,
        'Romero e hijos',
        'Domicilio fiscal pendiente',
        'administracion@romero.local',
        ''
    ),
    (
        2,
        'Cliente Sur',
        'Domicilio fiscal pendiente',
        'contacto@clientesur.local',
        ''
    ),
    (
        3,
        'Proveedor Norte',
        'Domicilio fiscal pendiente',
        'contacto@proveedornorte.local',
        ''
    );

INSERT OR IGNORE INTO cargas (id, codigo_contenedor, descripcion) VALUES
    (1, 'CONT-00000000000000000001', 'Materia prima'),
    (2, 'CONT-00000000000000000002', 'Producto terminado'),
    (3, 'CONT-00000000000000000003', 'Insumos');

INSERT OR IGNORE INTO lugares (id, nombre, direccion, observaciones) VALUES
    (1, 'Planta principal', 'Direccion pendiente', ''),
    (2, 'Deposito norte', 'Direccion pendiente', ''),
    (3, 'Cliente Sur', 'Direccion pendiente', ''),
    (4, 'Puerto', 'Direccion pendiente', '');

INSERT OR IGNORE INTO lugar_roles (
    id,
    lugar_id,
    rol,
    valido_desde,
    valido_hasta,
    observaciones
) VALUES
    (1, 1, 'CARGA', '2026-01-01', NULL, ''),
    (2, 1, 'DESCARGA', '2026-01-01', NULL, ''),
    (3, 2, 'CARGA', '2026-01-01', NULL, ''),
    (4, 3, 'DESCARGA', '2026-01-01', NULL, ''),
    (5, 4, 'CARGA', '2026-01-01', NULL, '');

INSERT OR IGNORE INTO choferes (
    id,
    dni,
    nombre,
    apellido,
    numero_telefono,
    fecha_vencimiento_registro
) VALUES
    (1, '20123456', 'Juan', 'Perez', '', '2027-12-31'),
    (2, '24987654', 'Carlos', 'Gomez', '', '2026-11-30'),
    (3, '28765432', 'Miguel', 'Silva', '', '2028-03-15');

INSERT OR IGNORE INTO vehiculos (
    id,
    tipo,
    nombre_identificatorio,
    patente,
    observaciones
) VALUES
    (1, 'CAMION', 'Tractor principal', 'AB123CD', ''),
    (2, 'CAMION', 'Unidad norte', 'AE456FG', ''),
    (3, 'CAMION', 'Unidad sur', 'AD789HI', ''),
    (1001, 'SEMI', 'Semi batea', 'AA111BB', ''),
    (1002, 'SEMI', 'Semi playo', 'AC222DD', ''),
    (1003, 'SEMI', 'Semi cerealero', 'AF333GG', '');

INSERT OR IGNORE INTO viajes (
    id,
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
    peajes,
    observaciones,
    estado
) VALUES
    (
        1, 1, 1, 2, 1, 1, 1, 1001, 'Completa', 120000, '2026-04-30',
        0, NULL, 0, 15000, 'Control pendiente', 'Programado'
    ),
    (
        2, 2, 2, 1, 3, 2, 2, 1002, 'Completa', 180000, '2026-04-30',
        25000, NULL, 10000, 22000, 'Demora informada', 'En viaje'
    ),
    (
        3, 3, 3, 4, 1, 3, 3, 1003, 'Parcial', 95000, '2026-05-01',
        0, NULL, 0, 9000, '', 'Finalizado'
    );
"""


def initialize_database(database_path: Path, *, seed: bool = True) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(SCHEMA_SQL)
        _migrate_clientes(connection)
        _migrate_cargas(connection)
        _migrate_lugares(connection)
        _migrate_choferes(connection)
        _migrate_vehiculos(connection)
        _migrate_viajes_to_vehiculos(connection)
        _migrate_viaje_fechas_descarga(connection)
        _migrate_lugar_roles_from_viajes(connection)
        connection.executescript(POST_MIGRATION_SQL)
        if seed:
            connection.executescript(SEED_SQL)
        connection.commit()


def _migrate_clientes(connection: sqlite3.Connection) -> None:
    columns = _table_columns(connection, "clientes")

    if "domicilio_fiscal" not in columns:
        connection.execute(
            "ALTER TABLE clientes ADD COLUMN domicilio_fiscal TEXT NOT NULL DEFAULT ''"
        )
    if "email" not in columns:
        connection.execute("ALTER TABLE clientes ADD COLUMN email TEXT NOT NULL DEFAULT ''")
    if "numero_contacto" not in columns:
        connection.execute(
            "ALTER TABLE clientes ADD COLUMN numero_contacto TEXT NOT NULL DEFAULT ''"
        )


def _migrate_cargas(connection: sqlite3.Connection) -> None:
    columns = _table_columns(connection, "cargas")

    if "codigo_contenedor" not in columns:
        connection.execute("ALTER TABLE cargas ADD COLUMN codigo_contenedor TEXT")

    description_expression = "descripcion" if "descripcion" in columns else "''"
    connection.execute(
        f"""
        UPDATE cargas
        SET codigo_contenedor = COALESCE(
            NULLIF(codigo_contenedor, ''),
            NULLIF({description_expression}, ''),
            'CONT-PENDIENTE-' || id
        )
        """
    )


def _migrate_lugares(connection: sqlite3.Connection) -> None:
    columns = _table_columns(connection, "lugares")

    if "direccion" not in columns:
        connection.execute("ALTER TABLE lugares ADD COLUMN direccion TEXT NOT NULL DEFAULT ''")
    if "observaciones" not in columns:
        connection.execute(
            "ALTER TABLE lugares ADD COLUMN observaciones TEXT NOT NULL DEFAULT ''"
        )


def _migrate_choferes(connection: sqlite3.Connection) -> None:
    columns = _table_columns(connection, "choferes")
    required_columns = {
        "dni",
        "nombre",
        "apellido",
        "numero_telefono",
        "fecha_vencimiento_registro",
    }

    if required_columns.issubset(columns):
        return

    if "dni" not in columns:
        connection.execute("ALTER TABLE choferes ADD COLUMN dni TEXT")
    if "apellido" not in columns:
        connection.execute("ALTER TABLE choferes ADD COLUMN apellido TEXT")
    if "numero_telefono" not in columns:
        connection.execute(
            "ALTER TABLE choferes ADD COLUMN numero_telefono TEXT NOT NULL DEFAULT ''"
        )
    if "fecha_vencimiento_registro" not in columns:
        connection.execute("ALTER TABLE choferes ADD COLUMN fecha_vencimiento_registro TEXT")

    if "telefono" in columns:
        connection.execute(
            """
            UPDATE choferes
            SET numero_telefono = COALESCE(
                NULLIF(numero_telefono, ''),
                COALESCE(telefono, '')
            )
            """
        )

    connection.execute(
        """
        UPDATE choferes
        SET
            dni = COALESCE(NULLIF(dni, ''), 'PENDIENTE-' || id),
            apellido = COALESCE(
                NULLIF(apellido, ''),
                CASE
                    WHEN instr(trim(nombre), ' ') > 0
                    THEN substr(trim(nombre), instr(trim(nombre), ' ') + 1)
                    ELSE ''
                END
            ),
            nombre = CASE
                WHEN instr(trim(nombre), ' ') > 0
                THEN substr(trim(nombre), 1, instr(trim(nombre), ' ') - 1)
                ELSE trim(nombre)
            END,
            numero_telefono = COALESCE(numero_telefono, ''),
            fecha_vencimiento_registro = COALESCE(fecha_vencimiento_registro, '')
        """
    )


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def _migrate_vehiculos(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "camiones"):
        connection.execute(
            """
            INSERT OR IGNORE INTO vehiculos (
                id,
                tipo,
                nombre_identificatorio,
                patente,
                observaciones,
                activo,
                creado_en
            )
            SELECT
                id,
                'CAMION',
                COALESCE(NULLIF(descripcion, ''), patente),
                patente,
                COALESCE(descripcion, ''),
                activo,
                creado_en
            FROM camiones
            """
        )

    if _table_exists(connection, "semis"):
        connection.execute(
            """
            INSERT OR IGNORE INTO vehiculos (
                id,
                tipo,
                nombre_identificatorio,
                patente,
                observaciones,
                activo,
                creado_en
            )
            SELECT
                id + 1000,
                'SEMI',
                COALESCE(NULLIF(descripcion, ''), patente),
                patente,
                COALESCE(descripcion, ''),
                activo,
                creado_en
            FROM semis
            """
        )


def _migrate_viajes_to_vehiculos(connection: sqlite3.Connection) -> None:
    if _viajes_references_vehiculos(connection):
        return

    columns = _table_columns(connection, "viajes")
    fecha_descarga_tarifa = (
        "fecha_descarga_tarifa"
        if "fecha_descarga_tarifa" in columns
        else "fecha_descarga_programada"
        if "fecha_descarga_programada" in columns
        else "NULL"
    )
    fecha_descarga_demora = (
        "fecha_descarga_demora"
        if "fecha_descarga_demora" in columns
        else "fecha_descarga_real"
        if "fecha_descarga_real" in columns
        else "NULL"
    )

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("ALTER TABLE viajes RENAME TO viajes_legacy")
    connection.execute(
        """
        CREATE TABLE viajes (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER NOT NULL,
            carga_id INTEGER NOT NULL,
            lugar_carga_id INTEGER NOT NULL,
            lugar_descarga_id INTEGER NOT NULL,
            chofer_id INTEGER NOT NULL,
            camion_id INTEGER NOT NULL,
            semi_id INTEGER,
            tipo_carga TEXT,
            tarifa NUMERIC NOT NULL DEFAULT 0,
            fecha_descarga_tarifa TEXT,
            demora NUMERIC NOT NULL DEFAULT 0,
            fecha_descarga_demora TEXT,
            vacio NUMERIC NOT NULL DEFAULT 0,
            peajes NUMERIC NOT NULL DEFAULT 0,
            observaciones TEXT,
            estado TEXT NOT NULL DEFAULT 'Programado',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (carga_id) REFERENCES cargas(id),
            FOREIGN KEY (lugar_carga_id) REFERENCES lugares(id),
            FOREIGN KEY (lugar_descarga_id) REFERENCES lugares(id),
            FOREIGN KEY (chofer_id) REFERENCES choferes(id),
            FOREIGN KEY (camion_id) REFERENCES vehiculos(id),
            FOREIGN KEY (semi_id) REFERENCES vehiculos(id)
        )
        """
    )
    connection.execute(
        f"""
        INSERT INTO viajes (
            id,
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
            peajes,
            observaciones,
            estado,
            creado_en,
            actualizado_en
        )
        SELECT
            id,
            cliente_id,
            carga_id,
            lugar_carga_id,
            lugar_descarga_id,
            chofer_id,
            camion_id,
            CASE WHEN semi_id IS NULL THEN NULL ELSE semi_id + 1000 END,
            tipo_carga,
            tarifa,
            {fecha_descarga_tarifa},
            demora,
            {fecha_descarga_demora},
            vacio,
            peajes,
            observaciones,
            estado,
            creado_en,
            actualizado_en
        FROM viajes_legacy
        """
    )
    connection.execute("DROP TABLE viajes_legacy")
    connection.execute("PRAGMA foreign_keys = ON")


def _migrate_viaje_fechas_descarga(connection: sqlite3.Connection) -> None:
    columns = _table_columns(connection, "viajes")

    if "fecha_descarga_tarifa" not in columns:
        connection.execute("ALTER TABLE viajes ADD COLUMN fecha_descarga_tarifa TEXT")
    if "fecha_descarga_demora" not in columns:
        connection.execute("ALTER TABLE viajes ADD COLUMN fecha_descarga_demora TEXT")

    columns = _table_columns(connection, "viajes")
    if "fecha_descarga_programada" in columns:
        connection.execute(
            """
            UPDATE viajes
            SET fecha_descarga_tarifa = COALESCE(
                NULLIF(fecha_descarga_tarifa, ''),
                fecha_descarga_programada
            )
            """
        )

    if "fecha_descarga_real" in columns:
        connection.execute(
            """
            UPDATE viajes
            SET fecha_descarga_demora = COALESCE(
                NULLIF(fecha_descarga_demora, ''),
                fecha_descarga_real
            )
            """
        )


def _migrate_lugar_roles_from_viajes(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "viajes"):
        return

    connection.execute(
        """
        INSERT INTO lugar_roles (
            lugar_id,
            rol,
            valido_desde,
            valido_hasta,
            observaciones
        )
        SELECT DISTINCT
            viajes.lugar_carga_id,
            'CARGA',
            '',
            NULL,
            'Rol inferido desde viajes existentes'
        FROM viajes
        WHERE viajes.lugar_carga_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM lugar_roles
              WHERE lugar_roles.lugar_id = viajes.lugar_carga_id
                AND lugar_roles.rol = 'CARGA'
          )
        """
    )
    connection.execute(
        """
        INSERT INTO lugar_roles (
            lugar_id,
            rol,
            valido_desde,
            valido_hasta,
            observaciones
        )
        SELECT DISTINCT
            viajes.lugar_descarga_id,
            'DESCARGA',
            '',
            NULL,
            'Rol inferido desde viajes existentes'
        FROM viajes
        WHERE viajes.lugar_descarga_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM lugar_roles
              WHERE lugar_roles.lugar_id = viajes.lugar_descarga_id
                AND lugar_roles.rol = 'DESCARGA'
          )
        """
    )


def _viajes_references_vehiculos(connection: sqlite3.Connection) -> bool:
    references = connection.execute("PRAGMA foreign_key_list(viajes)").fetchall()
    return any(row[2] == "vehiculos" for row in references)


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None
