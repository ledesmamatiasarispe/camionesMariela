from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chofer:
    id: int
    dni: str
    nombre: str
    apellido: str
    fecha_vencimiento_registro: str
    activo: bool

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


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
    fecha_descarga_programada: str
    demora: float
    fecha_descarga_real: str
    vacio: float
    peajes: float
    estado: str
