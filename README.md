# Sistema de gestion de viajes

Proyecto base para definir el diseno de una aplicacion de gestion de viajes, vehiculos, estados operativos y documentacion asociada.

## Objetivo

Construir una interfaz simple, clara y confiable para registrar, consultar y coordinar viajes de la empresa dentro de un flujo productivo o logistico.

La app debe tener interfaz grafica de usuario. No debe funcionar como programa de consola para el uso normal.

La aplicacion sera cliente solamente, sin servidor. Los datos deben gestionarse localmente o mediante un archivo/carpeta definido por la app.

La app debe poder buscar actualizaciones desde GitHub Releases y avisar al usuario cuando exista una version nueva.

La aplicacion debe poder funcionar tanto en Windows como en macOS. Toda decision tecnica futura debe contemplar instalacion, actualizacion, archivos locales, permisos y empaquetado para ambos sistemas operativos.

Tambien debe ser autocontenida: el usuario final no deberia tener que instalar runtimes, dependencias, gestores de paquetes ni herramientas tecnicas en cada PC. El paquete distribuible debe incluir lo necesario para ejecutar la app.

## Contenido inicial

- `src/gestion_camiones`: codigo base de la aplicacion Python.
- `pyproject.toml`: configuracion del proyecto y dependencias.
- `requirements-dev.txt`: dependencias para maquinas de desarrollo.
- `packaging/gestion-camiones.spec`: configuracion inicial de PyInstaller.
- `index.html`: maqueta estatica inicial para explorar estructura visual.
- `styles/design-system.css`: tokens, reglas base y componentes visuales reutilizables.
- `docs/producto.md`: definicion inicial del problema, usuarios y alcance.
- `docs/diseno.md`: principios visuales, tono de interfaz y reglas de estilo.
- `docs/interfaz.md`: criterio funcional para la interfaz grafica.
- `docs/componentes.md`: primeros componentes esperados para la app.
- `docs/multiplataforma.md`: criterios para que la app funcione en Windows y macOS.
- `docs/distribucion.md`: reglas para distribuir la app con dependencias incluidas.
- `docs/tecnologia-python.md`: decision tecnica inicial para construir la app en Python.
- `docs/arquitectura.md`: arquitectura cliente sin servidor y estrategia de datos.
- `docs/actualizaciones.md`: estrategia para actualizar desde GitHub Releases.
- `docs/github.md`: configuracion del repositorio, CI y releases.
- `docs/modelo-datos.md`: relaciones iniciales para gestionar viajes.

## Como abrir la maqueta

Abrir `index.html` directamente en el navegador. No requiere servidor ni instalacion de dependencias.

## Como ejecutar la app Python en desarrollo

Forma rapida en Windows:

```bat
Abrir Gestion Camiones.cmd
```

Ese launcher ejecuta siempre el codigo desde `src`, crea `.venv` si falta e instala dependencias si el entorno quedo incompleto. No usa `dist` ni el ejecutable empaquetado, por lo que no deberia romperse cuando se limpian builds o se publica una actualizacion.

En una maquina de desarrollo:

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m pip install -e .
gestion-camiones
```

Los usuarios finales no deberian hacer estos pasos. Para ellos se debe entregar un build empaquetado.

## Proximos pasos sugeridos

1. Definir usuarios principales y tareas criticas.
2. Listar estados reales de un viaje dentro del circuito logistico.
3. Diseñar las primeras pantallas: tablero diario, alta de viaje, detalle de viaje y documentacion.
4. Elegir tecnologia cuando el flujo este mas claro.
