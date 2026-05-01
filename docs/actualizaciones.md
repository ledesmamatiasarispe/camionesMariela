# Actualizaciones automaticas

## Decision

La app debe poder actualizarse desde GitHub.

El canal recomendado es GitHub Releases: cada version publicada debe incluir los paquetes finales para Windows y macOS.

## Alcance inicial

La app debe poder:

- Consultar si hay una version nueva en GitHub Releases.
- Comparar la version instalada contra la ultima version publicada.
- Mostrar al usuario que hay una actualizacion disponible.
- Descargar el paquete correspondiente para el sistema y arquitectura.
- Crear un backup de la base SQLite local antes de abrir el instalador.
- Registrar errores de actualizacion de forma comprensible.

## Alcance posterior

La instalacion totalmente automatica debe evaluarse con cuidado, porque Windows y macOS manejan permisos, firma y reemplazo de ejecutables de forma distinta.

Para una primera version estable, se recomienda:

- Detectar actualizacion automaticamente.
- Avisar al usuario.
- Descargar el instalador dentro de la carpeta de datos del usuario.
- Guiar el reemplazo de la version instalada.

La app no guarda la base dentro del paquete instalado. La base SQLite vive en la
carpeta de datos del usuario, por lo que reemplazar la aplicacion no deberia
pisar los datos locales. Antes de abrir un instalador descargado, la app genera
un respaldo adicional en:

```text
<carpeta de datos de usuario>/backups
```

Los paquetes descargados se guardan en:

```text
<carpeta de datos de usuario>/updates/<version>
```

## GitHub Releases

Cada release debe usar tags versionados:

- `v0.1.1`
- `v0.2.0`
- `v1.0.0`

Cada release deberia incluir:

- Paquete para Windows.
- Paquete para macOS.
- Notas de version.
- Fecha de publicacion.
- Checksums, si se decide validar integridad.

## Repositorio

La app debe tener configurado:

- Propietario de GitHub.
- Nombre del repositorio.
- Version instalada.
- Canal de actualizacion, si en el futuro hay estable/beta.

Repositorio configurado:

- Propietario: `ledesmamatiasarispe`
- Repositorio: `camionesMariela`

## Seguridad

Recomendaciones:

- Descargar solo desde GitHub Releases del repositorio oficial.
- Validar nombre de archivo esperado por sistema operativo.
- Considerar checksums para validar descargas.
- Firmar los builds cuando el proyecto pase a uso real.
- No ejecutar scripts descargados dinamicamente.

## Implementacion inicial

Existe un servicio en `src/gestion_camiones/services/updater.py` para consultar
la ultima release de GitHub, seleccionar el paquete correcto, descargarlo y
crear un backup SQLite previo a la instalacion.
