from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cliente:
    id: int
    nombre: str
    domicilio_fiscal: str
    email: str
    numero_contacto: str
    activo: bool


@dataclass(frozen=True)
class Carga:
    id: int
    codigo_contenedor: str
    activo: bool


@dataclass(frozen=True)
class Lugar:
    id: int
    nombre: str
    direccion: str
    observaciones: str
    activo: bool


@dataclass(frozen=True)
class LugarRol:
    id: int
    lugar_id: int
    lugar: str
    rol: str
    valido_desde: str
    valido_hasta: str | None
    observaciones: str
    activo: bool


@dataclass(frozen=True)
class Chofer:
    id: int
    dni: str
    nombre: str
    apellido: str
    numero_telefono: str
    fecha_vencimiento_registro: str
    activo: bool

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


@dataclass(frozen=True)
class Vehiculo:
    id: int
    tipo: str
    nombre_identificatorio: str
    patente: str
    observaciones: str
    activo: bool

    @property
    def etiqueta(self) -> str:
        return f"{self.nombre_identificatorio} - {self.patente}".strip()


@dataclass(frozen=True)
class ViajeResumen:
    id: int
    cliente: str
    carga: str
    lugar_carga: str
    lugar_descarga: str
    observaciones: str
    chofer: str
    tipo_carga: str
    camion: str
    semi: str
    tarifa: float
    fecha_descarga_tarifa: str
    demora: float
    fecha_descarga_demora: str
    vacio: float
    peajes: float
    estado: str
