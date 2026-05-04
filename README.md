# Gestion Camiones

Aplicacion de escritorio para gestionar viajes, vehiculos, choferes, clientes y peajes de la empresa Jose Romero e hijos SRL.

Funciona en Windows y macOS. Los datos se guardan localmente en una base SQLite. No requiere servidor ni conexion permanente a internet.

## Estructura del proyecto

```
src/gestion_camiones/    codigo fuente de la aplicacion
  data/                  modelos, esquema SQLite y repositorios
  services/              logica de negocio (exportacion, actualizador, configuracion)
  ui/                    interfaz grafica PySide6
  assets/                icono de la app
packaging/               configuracion de PyInstaller y scripts de empaquetado
tests/                   suite de tests automatizados
.github/workflows/       CI (tests) y release automatico via GitHub Actions
```

## Ejecutar en desarrollo (Windows)

```bat
Abrir Gestion Camiones.cmd
```

El launcher crea `.venv` si no existe, instala las dependencias y arranca la app desde `src`.

O manualmente:

```bash
python -m venv .venv
pip install -r requirements-dev.txt
pip install -e .
gestion-camiones
```

## Ejecutar tests

```bash
pip install -r requirements-dev.txt
pip install -e .
pytest tests/
```

## Publicar una nueva version

1. Actualizar `__version__` en `src/gestion_camiones/__init__.py`
2. Hacer commit y push a `main`
3. Crear y pushear el tag: `git tag v0.1.X && git push origin v0.1.X`

El workflow de GitHub Actions compila los artefactos para Windows y macOS y los adjunta al release automaticamente.

## Actualizaciones automaticas

La app consulta GitHub Releases al iniciar. Si hay una version nueva muestra un dialogo con dos opciones:

- **Actualizar ahora**: crea un backup de la base local, lanza el instalador como proceso independiente y cierra la app. El instalador descarga, verifica el checksum y reemplaza los archivos.
- **Omitir esta version**: no vuelve a preguntar por esa version hasta que haya una mas nueva.
