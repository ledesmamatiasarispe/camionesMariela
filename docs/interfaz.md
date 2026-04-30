# Interfaz de usuario

## Decision

La aplicacion tendra una interfaz grafica de escritorio. El usuario final debe operar el sistema desde ventanas, botones, tablas, formularios y menus.

No se espera que el usuario escriba comandos, abra consolas ni ejecute scripts.

## Tecnologia

La interfaz inicial se construye con PySide6.

PySide6 permite crear:

- Ventanas de escritorio.
- Menus superiores.
- Tablas operativas.
- Formularios de carga.
- Botones y acciones.
- Dialogos de confirmacion.
- Pantallas compatibles con Windows y macOS.

## Navegacion lateral

La interfaz principal se organiza en secciones operativas. La navegacion visible
se muestra solo en la barra lateral.

Secciones iniciales:

- Cargar viaje.
- Historial viajes.
- Clientes.
- Lugares.
- Chofer.
- T.Carga.
- Vehiculos.
- Peajes.
- Estadisticas.
- Opciones.

La seccion interna puede implementarse con pestanas ocultas de PySide6, pero no
debe mostrarse una segunda fila de botones arriba del contenido.

El boton superior `Nuevo viaje` solo debe mostrarse dentro de `Cargar viaje`.
En el resto de las secciones, las acciones se resuelven dentro de cada pantalla.

Las secciones de mantenimiento, excepto `Cargar viaje`, `Estadisticas` y
`Opciones`, deben tener su propia botonera operativa:

- Crear.
- Editar.
- Eliminar.

La seccion `Cargar viaje` debe tener solo la accion de guardar el viaje cargado.

La primera seccion es `Cargar viaje`. Debe pedir los datos del viaje en el mismo
orden operativo definido por la planilla:

- Fecha.
- Cliente.
- Carga.
- Lugar de carga.
- Lugar de descarga.
- Observaciones.
- Chofer.
- Tipo de carga.
- Camion.
- Semi.
- Tarifa.
- Fecha de descarga asociada a tarifa.
- Demora.
- Fecha de descarga asociada a demora.
- Vacio.
- Peajes.

## Historial viajes

La seccion `Historial viajes` debe funcionar como historial operativo:

- Busqueda por cliente, chofer, vehiculo, lugar o peaje.
- Tabla de viajes.
- Acceso rapido a alta de viaje.
- Acceso a detalle de viaje.

## Estadisticas

La seccion `Estadisticas` debe mostrar:

- Resumen de viajes.
- Indicadores principales.
- Importes totales de tarifa, demora, vacio y peajes.

## Pantallas previstas

- Historial de viajes.
- Alta y edicion de viaje.
- Detalle de viaje.
- Cambio de estado.
- Carga de documentacion.
- Maestros: clientes, cargas, lugares, roles de lugares, choferes, vehiculos y peajes.
- Reportes/exportaciones.
- Opciones/configuracion.

## Reglas de experiencia

- La app debe abrir con doble clic desde su ejecutable o acceso directo.
- No debe mostrar una consola en uso normal.
- Los errores deben mostrarse con mensajes comprensibles.
- Las acciones criticas deben pedir confirmacion.
- Los formularios deben indicar campos obligatorios.
- La navegacion debe ser clara para usuarios no tecnicos.
