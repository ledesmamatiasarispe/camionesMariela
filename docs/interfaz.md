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

## Pantalla inicial

La primera pantalla debe funcionar como tablero operativo:

- Resumen de camiones del dia.
- Indicadores principales.
- Busqueda por patente o proveedor.
- Tabla de camiones activos.
- Acceso rapido a alta de camion.
- Acceso a detalle de camion.

## Pantallas previstas

- Tablero operativo.
- Listado de camiones.
- Alta y edicion de camion.
- Detalle de camion.
- Cambio de estado.
- Carga de documentacion.
- Reportes/exportaciones.
- Configuracion.

## Reglas de experiencia

- La app debe abrir con doble clic desde su ejecutable o acceso directo.
- No debe mostrar una consola en uso normal.
- Los errores deben mostrarse con mensajes comprensibles.
- Las acciones criticas deben pedir confirmacion.
- Los formularios deben indicar campos obligatorios.
- La navegacion debe ser clara para usuarios no tecnicos.
