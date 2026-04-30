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

Repositorio actual:

```text
git@github.com:ledesmamatiasarispe/camionesMariela.git
```

Luego conectar este proyecto local:

```bash
git remote add origin https://github.com/USUARIO_O_ORG/sistema-gestion-camiones.git
git add .
git commit -m "Base inicial de la app"
git push -u origin main
```

En este proyecto ya esta configurado como `origin`.

## Publicar una version

Crear y subir un tag:

```bash
git tag v0.1.1
git push origin v0.1.1
```

GitHub Actions ejecutara el workflow de release, construyendo paquetes para Windows y macOS y adjuntandolos a la release.

Artefactos esperados:

- `GestionCamiones-Windows-x64.zip`
- `GestionCamiones-macOS-AppleSilicon.dmg`
- `GestionCamiones-macOS-Intel.dmg`

## Firma y notarizacion de macOS

Para que el instalador de macOS se pueda abrir sin advertencias fuertes del sistema, conviene firmar y notarizar la app desde GitHub Actions.

Secrets requeridos para automatizarlo:

- `APPLE_DEVELOPER_ID_APP_CERT`: certificado `Developer ID Application` exportado a `.p12` y codificado en base64.
- `APPLE_DEVELOPER_ID_APP_CERT_PASSWORD`: password del `.p12`.
- `APPLE_DEVELOPER_ID_APP_IDENTITY`: nombre exacto de la identidad de firma.
- `APPLE_NOTARY_KEY_ID`: Key ID de App Store Connect.
- `APPLE_NOTARY_ISSUER_ID`: Issuer ID de App Store Connect.
- `APPLE_NOTARY_PRIVATE_KEY`: contenido del archivo `.p8` para `notarytool`.

Si esos secrets no estan definidos, el workflow igual construye el `.dmg`, pero quedara sin firma/notarizacion.

## Actualizaciones de la app

La app consulta GitHub Releases al iniciar y tambien desde `Opciones`.

El selector de descarga ya espera estos nombres de paquetes para elegir automaticamente el instalador correcto segun sistema y arquitectura:

- `GestionCamiones-Windows-x64.zip`
- `GestionCamiones-macOS-AppleSilicon.dmg`
- `GestionCamiones-macOS-Intel.dmg`

Los datos actuales del repositorio son `ledesmamatiasarispe/camionesMariela`.
