# Arquitectura

## Decision

La aplicacion sera cliente solamente, sin servidor.

Cada instalacion debe poder abrir y funcionar sin depender de un servicio backend, API web o base de datos remota.

## Implicancias

- La app debe incluir su logica de negocio.
- La app debe incluir o crear su almacenamiento local.
- Las actualizaciones se distribuyen como nuevos builds de escritorio.
- La app consulta GitHub Releases para detectar nuevas versiones.
- No se requiere administrar servidor.
- No hay sincronizacion automatica entre equipos salvo que se disene especificamente.

## Almacenamiento recomendado

Para una app cliente sin servidor, la opcion inicial recomendada es SQLite.

Ventajas:

- No requiere instalar motor de base de datos.
- Vive en un archivo local.
- Es estable y ampliamente usado.
- Python lo incluye en la biblioteca estandar mediante `sqlite3`.
- Es suficiente para una app operativa con formularios, tablas, busqueda e historial.

## Ubicacion de datos

No guardar datos dentro de la carpeta del programa, porque en Windows y macOS puede requerir permisos especiales.

Usar una carpeta de datos de usuario:

- Windows: carpeta de datos de aplicacion del usuario.
- macOS: carpeta de soporte de aplicacion del usuario.

La app debe mostrar o documentar donde guarda:

- Base de datos.
- Configuracion.
- Logs.
- Archivos adjuntos, si existen.

## Uso en varias PCs

Si cada PC usa su propia base local, no hay conflicto, pero los datos no se comparten automaticamente.

Si varias PCs abren el mismo archivo SQLite desde una carpeta compartida de red, puede haber riesgos:

- Bloqueos de archivo.
- Lentitud.
- Corrupcion ante cortes de red.
- Conflictos si varias personas editan al mismo tiempo.

Para el alcance actual, evitar edicion simultanea sobre una misma base compartida salvo que se pruebe muy bien.

## Backups

Como no hay servidor, la app debe facilitar copias de seguridad.

Funciones recomendadas:

- Exportar backup de la base.
- Restaurar backup.
- Exportar reportes CSV/XLSX.
- Indicar fecha del ultimo backup.

## Recomendacion inicial

Construir primero con SQLite local y una estructura clara de datos. Luego, si aparece la necesidad real de compartir informacion entre varias PCs, evaluar sincronizacion, carpeta compartida controlada o una arquitectura con servidor.
