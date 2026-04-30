# Actualizaciones automaticas

## Decision

La app debe poder actualizarse desde GitHub.

El canal recomendado es GitHub Releases: cada version publicada debe incluir los paquetes finales para Windows y macOS.

## Alcance inicial

La app debe poder:

- Consultar si hay una version nueva en GitHub Releases.
- Comparar la version instalada contra la ultima version publicada.
- Mostrar al usuario que hay una actualizacion disponible.
- Descargar o abrir el paquete correspondiente.
- Registrar errores de actualizacion de forma comprensible.

## Alcance posterior

La instalacion totalmente automatica debe evaluarse con cuidado, porque Windows y macOS manejan permisos, firma y reemplazo de ejecutables de forma distinta.

Para una primera version estable, se recomienda:

- Detectar actualizacion automaticamente.
- Avisar al usuario.
- Descargar el instalador o abrir la pagina de descarga.
- Guiar el reemplazo de la version instalada.

## GitHub Releases

Cada release debe usar tags versionados:

- `v0.1.0`
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

## Seguridad

Recomendaciones:

- Descargar solo desde GitHub Releases del repositorio oficial.
- Validar nombre de archivo esperado por sistema operativo.
- Considerar checksums para validar descargas.
- Firmar los builds cuando el proyecto pase a uso real.
- No ejecutar scripts descargados dinamicamente.

## Implementacion inicial

Existe un servicio base en `src/gestion_camiones/services/updater.py` para consultar la ultima release de GitHub y compararla contra la version instalada.

Todavia falta conectar ese servicio a la interfaz grafica y definir el repositorio oficial.
