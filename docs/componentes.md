# Componentes iniciales

## Navegacion

- App shell con barra lateral.
- Navegacion visible solo en la barra lateral.
- Secciones principales: Cargar viaje, Historial viajes, Clientes, Lugares,
  Chofer, T.Carga, Vehiculos, Peajes, Estadisticas y Opciones.
- Items laterales equivalentes a las secciones principales.
- Botones superiores `Nuevo viaje` y `Guardar viaje` visibles solo en la
  seccion Cargar viaje.

## Datos

- Tabla de viajes.
- Bloque de facturacion de ultimos 12 meses sobre el historial.
- Tablas maestras para clientes, lugares, choferes, tipos de carga, vehiculos y peajes.
- Filtros por fecha, estado, cliente, chofer, vehiculo y lugar.
- Busqueda rapida.
- Tarjetas de resumen operativo.
- Recuadros mensuales de facturacion con rango configurable por mes y ano final.
- El rango de facturacion no permite avanzar mas alla del mes actual.
- Botonera propia Crear, Editar y Eliminar en secciones de mantenimiento.
- Sin botonera Crear, Editar y Eliminar en Cargar viaje, Estadisticas y Opciones.
- `Nuevo viaje` limpia el formulario de carga con confirmacion previa.

## Formularios

- Alta/edicion de viaje.
- El formulario de alta de viaje es la primera pestana de la app.
- El formulario de alta de viaje usa dos columnas en escritorio para reducir
  espacio vertical desperdiciado.
- Alta/edicion de clientes, cargas, lugares, choferes y vehiculos.
- Datos de cliente: nombre, domicilio fiscal, email y numero de contacto.
- Datos de carga: codigo largo identificatorio del contenedor, editable al
  cargar el viaje.
- Tipo de carga: general o carga peligrosa.
- Datos de lugar: nombre, direccion, observaciones y roles con vigencia.
- Selectores de lugar de viaje con todos los lugares activos, ordenados por uso
  historico segun carga o descarga.
- Datos de chofer: DNI, nombre, apellido, telefono y vencimiento de registro.
- Datos de peaje: nombre, direccion y costo.
- Cambio de estado.
- Carga de documentacion.
- Registro de observaciones.

## Estados visuales

Cada estado debe tener:

- Etiqueta textual.
- Color de apoyo.
- Prioridad visual.
- Descripcion operativa breve.

## Acciones frecuentes

- Nuevo viaje.
- Cambiar estado.
- Ver detalle.
- Adjuntar documento.
- Marcar observado.
- Finalizar operacion.
