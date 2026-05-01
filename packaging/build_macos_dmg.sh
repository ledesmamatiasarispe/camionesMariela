#!/usr/bin/env bash
set -euo pipefail

APP_PATH="${1:-dist/Gestion Camiones.app}"
DMG_NAME="${2:-GestionCamiones-macOS.dmg}"
VOLUME_NAME="${3:-Instalar Gestion Camiones}"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "No se encontro ${APP_PATH}. Ejecuta PyInstaller primero." >&2
  exit 1
fi

STAGING_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${STAGING_DIR}"
}
trap cleanup EXIT

APP_BUNDLE_NAME="$(basename "${APP_PATH}")"

cp -R "${APP_PATH}" "${STAGING_DIR}/${APP_BUNDLE_NAME}"
ln -s /Applications "${STAGING_DIR}/Applications"
cat > "${STAGING_DIR}/1 - INSTALAR GESTION CAMIONES.txt" <<EOF
1. Arrastra "${APP_BUNDLE_NAME}" a "Applications".
2. Espera a que termine la copia.
3. Abre la app desde Finder > Applications.
4. Despues de copiarla, puedes expulsar este disco.
EOF

create_dmg() {
  hdiutil create \
    -volname "${VOLUME_NAME}" \
    -srcfolder "${STAGING_DIR}" \
    -ov \
    -format UDZO \
    "${DMG_NAME}"
}

create_dmg || {
  echo "Primer intento de crear DMG fallo; reintentando..." >&2
  rm -f "${DMG_NAME}"
  sleep 5
  create_dmg
}
