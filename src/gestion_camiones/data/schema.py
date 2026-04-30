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
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lugares (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS choferes (
    id INTEGER PRIMARY KEY,
    dni TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
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
    fecha_descarga_programada TEXT,
    demora NUMERIC NOT NULL DEFAULT 0,
    fecha_descarga_real TEXT,
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
CREATE INDEX IF NOT EXISTS idx_viajes_fecha_descarga_programada
    ON viajes(fecha_descarga_programada);
"""


POST_MIGRATION_SQL = """
CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
CREATE UNIQUE INDEX IF NOT EXISTS idx_choferes_dni ON choferes(dni);
CREATE INDEX IF NOT EXISTS idx_choferes_apellido_nombre ON choferes(apellido, nombre);
CREATE INDEX IF NOT EXISTS idx_vehiculos_tipo ON vehiculos(tipo);
CREATE INDEX IF NOT EXISTS idx_vehiculos_nombre_identificatorio
    ON vehiculos(nombre_identificatorio);
CREATE INDEX IF NOT EXISTS idx_viajes_cliente_id ON viajes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_viajes_chofer_id ON viajes(chofer_id);
CREATE INDEX IF NOT EXISTS idx_viajes_camion_id ON viajes(camion_id);
CREATE INDEX IF NOT EXISTS idx_viajes_estado ON viajes(estado);
CREATE INDEX IF NOT EXISTS idx_viajes_fecha_descarga_programada
    ON viajes(fecha_descarga_programada);
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

INSERT OR IGNORE INTO cargas (id, descripcion) VALUES
    (1, 'Materia prima'),
    (2, 'Producto terminado'),
    (3, 'Insumos');

INSERT OR IGNORE INTO lugares (id, nombre) VALUES
    (1, 'Planta principal'),
    (2, 'Deposito norte'),
    (3, 'Cliente Sur'),
    (4, 'Puerto');

INSERT OR IGNORE INTO choferes (
    id,
    dni,
    nombre,
    apellido,
    fecha_vencimiento_registro
) VALUES
    (1, '20123456', 'Juan', 'Perez', '2027-12-31'),
    (2, '24987654', 'Carlos', 'Gomez', '2026-11-30'),
    (3, '28765432', 'Miguel', 'Silva', '2028-03-15');

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
    fecha_descarga_programada,
    demora,
    fecha_descarga_real,
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
        _migrate_choferes(connection)
        _migrate_vehiculos(connection)
        _migrate_viajes_to_vehiculos(connection)
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


def _migrate_choferes(connection: sqlite3.Connection) -> None:
    columns = _table_columns(connection, "choferes")
    required_columns = {"dni", "nombre", "apellido", "fecha_vencimiento_registro"}

    if required_columns.issubset(columns):
        return

    if "dni" not in columns:
        connection.execute("ALTER TABLE choferes ADD COLUMN dni TEXT")
    if "apellido" not in columns:
        connection.execute("ALTER TABLE choferes ADD COLUMN apellido TEXT")
    if "fecha_vencimiento_registro" not in columns:
        connection.execute("ALTER TABLE choferes ADD COLUMN fecha_vencimiento_registro TEXT")

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
            fecha_descarga_programada TEXT,
            demora NUMERIC NOT NULL DEFAULT 0,
            fecha_descarga_real TEXT,
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
        """
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
            fecha_descarga_programada,
            demora,
            fecha_descarga_real,
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
            fecha_descarga_programada,
            demora,
            fecha_descarga_real,
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


def _viajes_references_vehiculos(connection: sqlite3.Connection) -> bool:
    references = connection.execute("PRAGMA foreign_key_list(viajes)").fetchall()
    return any(row[2] == "vehiculos" for row in references)


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None
