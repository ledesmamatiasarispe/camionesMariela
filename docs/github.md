# GitHub

## Objetivo

Usar GitHub como repositorio del codigo, historial de cambios y canal de publicacion de versiones.

## Configuracion incluida

- CI en `.github/workflows/ci.yml`.
- Build y release en `.github/workflows/release.yml`.
- Dependabot para GitHub Actions y dependencias Python.
- Plantilla de pull request.
- Plantillas para bugs y funcionalidades.

## Crear repositorio remoto

Crear un repositorio en GitHub. Nombre sugerido:

```text
sistema-gestion-camiones
```

Luego conectar este proyecto local:

```bash
git remote add origin https://github.com/USUARIO_O_ORG/sistema-gestion-camiones.git
git add .
git commit -m "Base inicial de la app"
git push -u origin main
```

Reemplazar `USUARIO_O_ORG` por el usuario u organizacion real.

## Publicar una version

Crear y subir un tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions ejecutara el workflow de release, construyendo paquetes para Windows y macOS y adjuntandolos a la release.

## Actualizaciones de la app

La app consultara GitHub Releases para detectar nuevas versiones.

Antes de conectar esa funcion a la interfaz hay que definir:

- Usuario u organizacion de GitHub.
- Nombre final del repositorio.
- Nombres esperados de paquetes para Windows y macOS.
