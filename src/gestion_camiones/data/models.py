from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cliente:
    id: int
    nombre: str
    cuit: str
    email: str
    numero_contacto: str
    es_cliente_directo: bool
    cliente_padre_id: int | None
    cliente_padre_nombre: str
    activo: bool

    @property
    def etiqueta(self) -> str:
        if self.es_cliente_directo or not self.cliente_padre_nombre:
            return self.nombre
        return f"{self.nombre} ({self.cliente_padre_nombre})"


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
    regularidad_registro_meses: int
    activo: bool

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


@dataclass(frozen=True)
class AppAlert:
    key: str
    source: str
    title: str
    message: str
    entity_id: int
    due_date: str


@dataclass(frozen=True)
class Vehiculo:
    id: int
    tipo: str
    nombre_identificatorio: str
    patente: str
    km_actual: int
    chofer_predeterminado_id: int | None
    chofer_predeterminado_nombre: str
    observaciones: str
    activo: bool

    @property
    def etiqueta(self) -> str:
        return f"{self.nombre_identificatorio} - {self.patente}".strip()


@dataclass(frozen=True)
class VehiculoMantenimiento:
    id: int
    vehiculo_id: int
    vehiculo_etiqueta: str
    fecha_ultimo_mantenimiento: str
    fecha_proximo_mantenimiento: str
    km_proximo_mantenimiento: int
    regularidad_fecha_meses: int
    regularidad_km: int
    descripcion: str
    observaciones: str
    activo: bool


@dataclass(frozen=True)
class VehiculoMantenimientoHistorial:
    id: int
    mantenimiento_id: int
    vehiculo_id: int
    vehiculo_etiqueta: str
    fecha_ultimo_mantenimiento: str
    fecha_proximo_mantenimiento: str
    km_proximo_mantenimiento: int
    fuera_de_tiempo: bool


@dataclass(frozen=True)
class VehiculoCombustibleCarga:
    id: int
    vehiculo_id: int
    vehiculo_etiqueta: str
    fecha_carga: str
    litros_cargados: float
    km_actual_camion: int
    creado_en: str


@dataclass(frozen=True)
class VehiculoCombustibleConsumo:
    vehiculo_id: int
    vehiculo_etiqueta: str
    cargas: int
    km_recorridos: int
    litros_computados: float
    consumo_litros_100km: float | None
    ultimo_consumo_litros_100km: float | None
    ultimo_chofer: str


@dataclass(frozen=True)
class EmpresaPeaje:
    id: int
    nombre: str
    activo: bool


@dataclass(frozen=True)
class Peaje:
    id: int
    empresa_id: int
    empresa_nombre: str
    nombre: str
    direccion: str
    costo: float
    activo: bool


@dataclass(frozen=True)
class TipoCarga:
    id: int
    codigo: str
    nombre: str
    activo: bool


@dataclass(frozen=True)
class ViajeResumen:
    id: int
    fecha: str
    cliente: str
    carta_porte: str
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
    fecha_descarga_vacio: str
    lugar_descarga_vacio: str
    gas_oil_lts: float
    peajes: float
    estado: str
    cliente_es_directo: bool = True

    @property
    def costo_total(self) -> float:
        return self.tarifa + self.demora + self.vacio + self.peajes


@dataclass(frozen=True)
class ViajeCreate:
    fecha: str
    cliente_id: int
    carta_porte: str
    carga_id: int
    lugar_carga_id: int
    lugar_descarga_id: int
    lugar_descarga_vacio_id: int | None
    observaciones: str
    chofer_id: int
    tipo_carga: str
    camion_id: int
    semi_id: int | None
    tarifa: float
    fecha_descarga_tarifa: str
    demora: float
    fecha_descarga_demora: str
    vacio: float
    fecha_descarga_vacio: str
    gas_oil_lts: float
    peaje_ids: tuple[int, ...]
