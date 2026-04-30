# Modelo de datos

## Entidad principal

La entidad central del sistema es el `viaje`.

Un viaje representa una operacion de transporte de la empresa y relaciona cliente, carga, origen, destino, chofer, camion, semi y valores economicos.

## Columnas recibidas

Encabezados originales:

- CLIENTE
- CARGA
- LUGAR CARGA
- L.DESCARGA
- OBSERVACIONES
- CHOFER
- T.CARGA
- CAMION
- SEMI
- TARIFA
- F.DESC
- DEMORA
- F.DESC
- VACIO
- PEAJES

## Interpretacion inicial

Hay dos encabezados que conviene confirmar:

- `T.CARGA`: por ahora se interpreta como `tipo_carga`.
- `F.DESC`: aparece dos veces. Por ahora se divide en `fecha_descarga_programada` y `fecha_descarga_real`.

Esta decision permite avanzar con la estructura sin perder informacion. Si el significado real es distinto, se renombra antes de cargar datos definitivos.

## Tablas maestras

### clientes

Guarda los clientes de los viajes.

Campos principales:

- `id`
- `nombre`
- `activo`

### cargas

Guarda tipos o descripciones de carga.

Campos principales:

- `id`
- `descripcion`
- `activo`

### lugares

Guarda lugares de carga y descarga. La misma tabla sirve para origen y destino.

Campos principales:

- `id`
- `nombre`
- `activo`

### choferes

Guarda choferes.

Campos principales:

- `id`
- `nombre`
- `telefono`
- `activo`

### camiones

Guarda unidades tractoras o camiones.

Campos principales:

- `id`
- `patente`
- `descripcion`
- `activo`

### semis

Guarda semirremolques.

Campos principales:

- `id`
- `patente`
- `descripcion`
- `activo`

## Tabla viajes

Campos principales:

- `cliente_id`
- `carga_id`
- `lugar_carga_id`
- `lugar_descarga_id`
- `chofer_id`
- `camion_id`
- `semi_id`
- `tipo_carga`
- `tarifa`
- `fecha_descarga_programada`
- `demora`
- `fecha_descarga_real`
- `vacio`
- `peajes`
- `observaciones`
- `estado`

## Relaciones

- Un cliente puede tener muchos viajes.
- Una carga puede estar en muchos viajes.
- Un lugar puede ser origen o destino de muchos viajes.
- Un chofer puede tener muchos viajes.
- Un camion puede tener muchos viajes.
- Un semi puede tener muchos viajes.
- Un viaje pertenece a un cliente, una carga, un origen, un destino, un chofer y un camion.

## Base local

La base sera SQLite y se creara automaticamente en la carpeta de datos del usuario.

No se guarda dentro de la carpeta del programa para evitar problemas de permisos en Windows y macOS.
