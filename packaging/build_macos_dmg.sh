#!/usr/bin/env bash
set -euo pipefail

APP_PATH="${1:-dist/GestionCamiones.app}"
DMG_NAME="${2:-GestionCamiones-macOS.dmg}"
VOLUME_NAME="${3:-Gestion Camiones}"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "No se encontro ${APP_PATH}. Ejecuta PyInstaller primero." >&2
  exit 1
fi

STAGING_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${STAGING_DIR}"
}
trap cleanup EXIT

cp -R "${APP_PATH}" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"

hdiutil create \
  -volname "${VOLUME_NAME}" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_NAME}"
