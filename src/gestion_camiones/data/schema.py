from __future__ import annotations

from contextlib import closing
import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
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
    nombre TEXT NOT NULL UNIQUE,
    telefono TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS camiones (
    id INTEGER PRIMARY KEY,
    patente TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS semis (
    id INTEGER PRIMARY KEY,
    patente TEXT NOT NULL UNIQUE,
    descripcion TEXT,
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
    FOREIGN KEY (camion_id) REFERENCES camiones(id),
    FOREIGN KEY (semi_id) REFERENCES semis(id)
);

CREATE INDEX IF NOT EXISTS idx_viajes_cliente_id ON viajes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_viajes_chofer_id ON viajes(chofer_id);
CREATE INDEX IF NOT EXISTS idx_viajes_camion_id ON viajes(camion_id);
CREATE INDEX IF NOT EXISTS idx_viajes_estado ON viajes(estado);
CREATE INDEX IF NOT EXISTS idx_viajes_fecha_descarga_programada
    ON viajes(fecha_descarga_programada);
"""


SEED_SQL = """
INSERT OR IGNORE INTO clientes (id, nombre) VALUES
    (1, 'Romero e hijos'),
    (2, 'Cliente Sur'),
    (3, 'Proveedor Norte');

INSERT OR IGNORE INTO cargas (id, descripcion) VALUES
    (1, 'Materia prima'),
    (2, 'Producto terminado'),
    (3, 'Insumos');

INSERT OR IGNORE INTO lugares (id, nombre) VALUES
    (1, 'Planta principal'),
    (2, 'Deposito norte'),
    (3, 'Cliente Sur'),
    (4, 'Puerto');

INSERT OR IGNORE INTO choferes (id, nombre, telefono) VALUES
    (1, 'Juan Perez', ''),
    (2, 'Carlos Gomez', ''),
    (3, 'Miguel Silva', '');

INSERT OR IGNORE INTO camiones (id, patente, descripcion) VALUES
    (1, 'AB123CD', 'Tractor principal'),
    (2, 'AE456FG', 'Unidad norte'),
    (3, 'AD789HI', 'Unidad sur');

INSERT OR IGNORE INTO semis (id, patente, descripcion) VALUES
    (1, 'AA111BB', 'Semi batea'),
    (2, 'AC222DD', 'Semi playo'),
    (3, 'AF333GG', 'Semi cerealero');

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
        1, 1, 1, 2, 1, 1, 1, 1, 'Completa', 120000, '2026-04-30',
        0, NULL, 0, 15000, 'Control pendiente', 'Programado'
    ),
    (
        2, 2, 2, 1, 3, 2, 2, 2, 'Completa', 180000, '2026-04-30',
        25000, NULL, 10000, 22000, 'Demora informada', 'En viaje'
    ),
    (
        3, 3, 3, 4, 1, 3, 3, 3, 'Parcial', 95000, '2026-05-01',
        0, NULL, 0, 9000, '', 'Finalizado'
    );
"""


def initialize_database(database_path: Path, *, seed: bool = True) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(SCHEMA_SQL)
        if seed:
            connection.executescript(SEED_SQL)
