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

- Resumen de viajes.
- Indicadores principales.
- Busqueda por cliente, chofer, vehiculo o lugar.
- Tabla de viajes.
- Acceso rapido a alta de viaje.
- Acceso a detalle de viaje.

## Pantallas previstas

- Tablero operativo.
- Listado de viajes.
- Alta y edicion de viaje.
- Detalle de viaje.
- Cambio de estado.
- Carga de documentacion.
- Maestros: clientes, cargas, lugares, choferes y vehiculos.
- Reportes/exportaciones.
- Configuracion.

## Reglas de experiencia

- La app debe abrir con doble clic desde su ejecutable o acceso directo.
- No debe mostrar una consola en uso normal.
- Los errores deben mostrarse con mensajes comprensibles.
- Las acciones criticas deben pedir confirmacion.
- Los formularios deben indicar campos obligatorios.
- La navegacion debe ser clara para usuarios no tecnicos.
