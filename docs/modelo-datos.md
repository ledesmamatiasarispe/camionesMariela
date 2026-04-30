# Modelo de datos

## Entidad principal

La entidad central del sistema es el `viaje`.

Un viaje representa una operacion de transporte de la empresa y relaciona cliente, carga, origen, destino, chofer, vehiculos y valores economicos.

## Columnas recibidas

Encabezados originales:

- FECHA
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

Interpretacion actual:

- `FECHA`: fecha principal del viaje.
- `T.CARGA`: se interpreta como `tipo_carga`.
- Valores iniciales de `tipo_carga`: `GENERAL` o `PELIGROSA`.
- El primer `F.DESC`, ubicado despues de `TARIFA`, corresponde a `fecha_descarga_tarifa`.
- El segundo `F.DESC`, ubicado despues de `DEMORA`, corresponde a `fecha_descarga_demora`.
- El `F.DESC` de `VACIO` corresponde a `fecha_descarga_vacio`.

Esta decision refleja que tarifa, demora y vacio tienen cada uno su propia fecha de descarga.

## Tablas maestras

### clientes

Guarda los clientes de los viajes como entidad propia.

Campos principales:

- `id`
- `nombre`
- `domicilio_fiscal`
- `email`
- `numero_contacto`
- `activo`

### cargas

Guarda el codigo largo que identifica a cada contenedor.

Campos principales:

- `id`
- `codigo_contenedor`
- `activo`

### lugares

Guarda lugares de carga y descarga. La misma tabla sirve para origen y destino.

El lugar no queda marcado para siempre como carga o descarga. Ese rol puede variar en el tiempo y se registra en `lugar_roles`.

Campos principales:

- `id`
- `nombre`
- `direccion`
- `observaciones`
- `activo`

### lugar_roles

Guarda el rol que puede cumplir un lugar durante una vigencia determinada.

Campos principales:

- `id`
- `lugar_id`
- `rol`: `CARGA` o `DESCARGA`
- `valido_desde`
- `valido_hasta`
- `observaciones`
- `activo`

### choferes

Guarda choferes.

Campos principales:

- `id`
- `dni`
- `nombre`
- `apellido`
- `numero_telefono`
- `fecha_vencimiento_registro`
- `activo`

### vehiculos

Guarda camiones y semis como objetos del mismo tipo base.

Campos principales:

- `id`
- `tipo`
- `nombre_identificatorio`
- `patente`
- `observaciones`
- `activo`

### peajes

Guarda los peajes que pueden asociarse a los viajes.

Campos principales:

- `id`
- `nombre`
- `direccion`
- `costo`
- `activo`

### viaje_peajes

Relaciona viajes con peajes. Un viaje puede tener cero, uno o varios peajes.

Campos principales:

- `id`
- `viaje_id`
- `peaje_id`

### tipos_carga

Guarda los tipos de carga disponibles para cargar viajes.

Campos principales:

- `id`
- `codigo`
- `nombre`
- `activo`

## Tabla viajes

Campos principales:

- `fecha`
- `cliente_id`
- `carga_id`
- `lugar_carga_id`
- `lugar_descarga_id`
- `chofer_id`
- `camion_id`
- `semi_id`
- `tipo_carga`: `GENERAL` o `PELIGROSA`.
- `tarifa`: importe cobrado al cliente por tarifa del viaje.
- `fecha_descarga_tarifa`: fecha de descarga asociada a la tarifa.
- `demora`: importe cobrado al cliente por demora.
- `fecha_descarga_demora`: fecha de descarga asociada a la demora.
- `vacio`: importe cobrado al cliente por vacio.
- `fecha_descarga_vacio`: fecha de descarga asociada al vacio.
- `peajes`: importe historico de compatibilidad; el total actual sale de `viaje_peajes`.
- `observaciones`
- `estado`

## Importes del viaje

`tarifa`, `demora` y `vacio` son precios cobrados al cliente en cada viaje.

No representan cantidades, duraciones ni estados operativos. Deben tratarse como importes monetarios y mostrarse con formato de moneda en la interfaz.

`tarifa`, `demora` y `vacio` tienen cada una su propia fecha de descarga:

- `fecha_descarga_tarifa`
- `fecha_descarga_demora`
- `fecha_descarga_vacio`

## Relaciones

- Un cliente puede tener muchos viajes.
- Una carga puede estar en muchos viajes.
- Un lugar puede ser origen o destino de muchos viajes.
- Un lugar puede tener muchos roles de carga o descarga con distintas vigencias.
- Un chofer puede tener muchos viajes.
- Un vehiculo de tipo `CAMION` puede tener muchos viajes como camion.
- Un vehiculo de tipo `SEMI` puede tener muchos viajes como semi.
- Un peaje puede estar asociado a muchos viajes.
- Un viaje puede tener muchos peajes.
- Un viaje pertenece a un cliente, una carga, un origen, un destino, un chofer y al menos un camion.

## Objeto chofer

El chofer es una entidad propia, no un texto libre dentro del viaje.

Campos iniciales:

- `id`: identificador interno.
- `dni`: documento del chofer.
- `nombre`: nombre del chofer.
- `apellido`: apellido del chofer.
- `numero_telefono`: telefono de contacto del chofer.
- `fecha_vencimiento_registro`: vencimiento de su registro/licencia.

En `viajes` se guarda `chofer_id`, para mantener la relacion sin duplicar datos personales en cada viaje.

## Objeto cliente

El cliente es una entidad propia, no un texto libre dentro del viaje.

Campos iniciales:

- `id`: identificador interno.
- `nombre`: razon social o nombre visible del cliente.
- `domicilio_fiscal`: domicilio fiscal del cliente.
- `email`: correo de contacto.
- `numero_contacto`: telefono o numero de contacto principal.

En `viajes` se guarda `cliente_id`, para mantener la relacion sin duplicar datos fiscales o de contacto en cada viaje.

## Objeto carga

La carga representa, por ahora, el contenedor asociado al viaje.

Campos iniciales:

- `id`: identificador interno.
- `codigo_contenedor`: codigo largo que identifica al contenedor.

En `viajes` se guarda `carga_id`, para mantener la relacion con el contenedor sin repetir el codigo en cada viaje.

## Objeto lugar

El lugar es una entidad propia y neutral.

Campos iniciales:

- `id`: identificador interno.
- `nombre`: nombre visible del lugar.
- `direccion`: direccion fisica.
- `observaciones`: notas internas.

El uso como lugar de carga o descarga se registra en `lugar_roles`, no en el lugar en si. Esto permite que un lugar pueda cambiar de funcion con el tiempo sin perder historial.

## Objeto vehiculo

Camiones y semis comparten la misma estructura y se guardan en `vehiculos`.

Campos iniciales:

- `id`: identificador interno.
- `tipo`: `CAMION` o `SEMI`.
- `nombre_identificatorio`: nombre corto para reconocerlo en pantalla.
- `patente`: patente del vehiculo.
- `observaciones`: notas internas.

En `viajes` se guardan `camion_id` y `semi_id`. Ambos apuntan a `vehiculos`, pero `camion_id` debe corresponder a un vehiculo de tipo `CAMION` y `semi_id` a uno de tipo `SEMI`.

## Objeto peaje

El peaje es una entidad propia.

Campos iniciales:

- `id`: identificador interno.
- `nombre`: nombre del peaje.
- `direccion`: direccion o ubicacion del peaje.
- `costo`: costo del peaje.

La relacion con viajes se guarda en `viaje_peajes`, para permitir que un viaje tenga varios peajes sin repetir datos.

## Base local

La base sera SQLite y se creara automaticamente en la carpeta de datos del usuario.

No se guarda dentro de la carpeta del programa para evitar problemas de permisos en Windows y macOS.
