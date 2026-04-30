# Tecnologia Python

## Decision inicial

La aplicacion sera una app de escritorio en Python.

Para la interfaz se propone PySide6, que permite crear ventanas nativas y funciona en Windows y macOS. Para distribuirla sin pedir instalaciones tecnicas al usuario final, se propone empaquetar con PyInstaller.

La aplicacion debe abrir como ventana grafica. La consola solo puede usarse en desarrollo o diagnostico, no como interfaz principal.

La app sera cliente solamente, sin servidor. Para datos locales se recomienda SQLite usando `sqlite3`, incluido en Python.

Las actualizaciones se consultaran contra GitHub Releases usando la API publica de GitHub.

## Por que PySide6

- Funciona en Windows y macOS.
- Permite interfaces de escritorio reales, no solo consola.
- Tiene tablas, formularios, menus y componentes maduros.
- Puede empaquetarse junto con la app.
- Evita depender del navegador del usuario.

## Por que PyInstaller

- Incluye el runtime de Python en el paquete final.
- Incluye librerias necesarias dentro del build.
- Genera ejecutables para Windows.
- Genera paquetes ejecutables para macOS cuando se corre el build desde macOS.

## Regla importante

El build de Windows debe generarse en Windows. El build de macOS debe generarse en macOS. PyInstaller no es una solucion confiable para compilar ambos sistemas desde una sola maquina.

## Flujo de desarrollo

En maquinas de desarrollo si se instalan dependencias:

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m gestion_camiones.main
```

Para que `python -m gestion_camiones.main` encuentre el paquete, ejecutar desde un entorno donde `src` este en el path o instalar el proyecto en modo editable:

```bash
python -m pip install -e .
gestion-camiones
```

## Build portable

Desde la carpeta del proyecto:

```bash
python -m pip install -r requirements-dev.txt
pyinstaller packaging/gestion-camiones.spec
```

El resultado queda en `dist/GestionCamiones`.

La configuracion inicial de PyInstaller usa `console=False`, para que el usuario final no vea una terminal al abrir la app.

## Prueba de entrega

La version entregable debe abrir en una maquina que no tenga Python instalado. Esa es la prueba central para confirmar que las dependencias quedaron incluidas.
