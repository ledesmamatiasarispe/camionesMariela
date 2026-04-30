# Producto

## Vision

Una herramienta interna para ordenar la gestion de viajes de la empresa: cliente, carga, lugares, chofer, camion, semi, importes cobrados, peajes, observaciones y estado operativo.

Debe ser usable en equipos con Windows y macOS, manteniendo el mismo flujo funcional y una experiencia visual consistente.

Sera una app cliente sin servidor. El funcionamiento normal no debe depender de un backend remoto.

## Usuarios iniciales

- Operador de laboratorio o planta: necesita registrar y consultar rapidamente.
- Responsable de produccion: necesita ver estado general e importes asociados a cada viaje.
- Administracion: necesita revisar documentacion y trazabilidad.
- Chofer o transportista: podria necesitar informacion simple de turno o estado, si el alcance lo incluye.

## Tareas criticas

- Registrar un viaje nuevo.
- Relacionar cliente, carga, lugar de carga, lugar de descarga, chofer, camion y semi.
- Gestionar cargas como codigos largos de contenedor.
- Gestionar lugares con nombre, direccion, observaciones y roles variables de carga/descarga.
- Gestionar clientes como objetos con domicilio fiscal, email y numero de contacto.
- Gestionar choferes como objetos con DNI, nombre, apellido, telefono y vencimiento de registro.
- Gestionar camiones y semis como vehiculos con identificador, patente y observaciones.
- Registrar tarifa, demora y vacio como importes cobrados al cliente por cada viaje.
- Registrar una fecha de descarga propia para tarifa y otra para demora.
- Cambiar estado operativo.
- Ver viajes pendientes, en proceso y finalizados.
- Asociar documentacion o controles.
- Buscar por patente, chofer, proveedor, cliente, remito o fecha.

## Estados tentativos

- Programado
- En porteria
- En espera
- En laboratorio
- Autorizado
- Cargando
- Descargando
- Observado
- Finalizado
- Cancelado

## Preguntas abiertas

- Que datos son obligatorios al ingreso?
- El flujo cambia segun carga, descarga, proveedor o cliente?
- Hay integracion con planillas, Access, ERP u otro sistema existente?
- Quien puede editar estados y quien solo consulta?
- Se necesita historial/auditoria de cambios?
- La app sera de escritorio, cliente solamente, sin servidor.
- Se necesita trabajar sin conexion a internet o red interna?
