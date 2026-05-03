from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sqlite3
import ssl
import subprocess
import sys
import textwrap
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    name: str
    html_url: str
    notes: str
    assets: tuple[ReleaseAsset, ...]


class UpdateCheckError(RuntimeError):
    """Error al consultar actualizaciones."""


class UpdateDownloadError(RuntimeError):
    """Error al descargar una actualizacion."""


class UpdateInstallError(RuntimeError):
    """Error al preparar la instalacion automatica."""


def check_latest_release(owner: str, repo: str, current_version: str) -> ReleaseInfo | None:
    release = _fetch_latest_release(owner, repo)
    if release is None:
        return None
    latest_version = _normalize_version(release["tag_name"])

    if _version_tuple(latest_version) <= _version_tuple(current_version):
        return None

    assets = tuple(
        ReleaseAsset(
            name=asset["name"],
            download_url=asset["browser_download_url"],
            size=asset.get("size", 0),
        )
        for asset in release.get("assets", [])
    )

    return ReleaseInfo(
        version=latest_version,
        name=release.get("name") or release["tag_name"],
        html_url=release["html_url"],
        notes=release.get("body") or "",
        assets=assets,
    )


def select_release_asset(
    release: ReleaseInfo,
    *,
    system: str | None = None,
    machine: str | None = None,
) -> ReleaseAsset | None:
    normalized_system = (system or platform.system()).lower()
    normalized_machine = (machine or platform.machine()).lower()
    ranked_assets = sorted(
        (
            (_asset_match_score(asset.name.lower(), normalized_system, normalized_machine), asset)
            for asset in release.assets
        ),
        key=lambda item: item[0],
        reverse=True,
    )

    if not ranked_assets or ranked_assets[0][0] <= 0:
        return None

    return ranked_assets[0][1]


def select_checksum_asset(release: ReleaseInfo, package_asset: ReleaseAsset) -> ReleaseAsset | None:
    expected_names = (
        f"{package_asset.name}.sha256",
        f"{package_asset.name}.sha256sum",
        f"{package_asset.name}.sha256.txt",
    )
    assets_by_name = {asset.name.lower(): asset for asset in release.assets}

    for expected_name in expected_names:
        asset = assets_by_name.get(expected_name.lower())
        if asset is not None:
            return asset

    package_stem = package_asset.name.lower()
    for asset in release.assets:
        asset_name = asset.name.lower()
        if (
            asset_name.endswith((".sha256", ".sha256sum", ".sha256.txt"))
            and package_stem in asset_name
        ):
            return asset

    return None


def updates_dir(app_data_dir: Path) -> Path:
    path = app_data_dir / "updates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_dir(app_data_dir: Path) -> Path:
    path = app_data_dir / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def launch_update_installer(package_path: Path, app_data_dir: Path) -> Path:
    system = platform.system()
    scripts_dir = app_data_dir / "updates" / "installers"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    if system == "Darwin":
        script_path = _write_macos_installer_script(package_path, scripts_dir)
        subprocess.Popen(
            ["/bin/bash", str(script_path)],
            close_fds=True,
            start_new_session=True,
        )
        return script_path

    if system == "Windows":
        script_path = _write_windows_installer_script(package_path, scripts_dir)
        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                str(os.getpid()),
            ],
            close_fds=True,
            creationflags=creationflags,
        )
        return script_path

    raise UpdateInstallError("La instalacion automatica no esta disponible en este sistema.")


def create_database_backup(database_path: Path, destination_dir: Path) -> Path:
    if not database_path.exists():
        raise UpdateDownloadError("No se encontro la base de datos local para respaldar.")

    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = destination_dir / f"{database_path.stem}-backup-{timestamp}{database_path.suffix}"

    try:
        with closing(sqlite3.connect(database_path)) as source:
            with closing(sqlite3.connect(backup_path)) as destination:
                source.backup(destination)
    except sqlite3.Error as exc:
        raise UpdateDownloadError("No se pudo crear el backup de la base local.") from exc

    return backup_path


def download_release_asset(
    asset: ReleaseAsset,
    destination_dir: Path,
    *,
    checksum_asset: ReleaseAsset | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    file_name = _safe_asset_filename(asset.name)
    output_path = destination_dir / file_name
    partial_path = output_path.with_suffix(output_path.suffix + ".part")

    request = Request(
        asset.download_url,
        headers={"User-Agent": "gestion-camiones-updater"},
    )

    try:
        with _open_url(request, timeout=30) as response:
            total_size = int(response.headers.get("Content-Length") or asset.size or 0)
            downloaded = 0
            with partial_path.open("wb") as file:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    file.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback is not None:
                        progress_callback(downloaded, total_size)
        shutil.move(str(partial_path), output_path)
    except (OSError, HTTPError, URLError) as exc:
        try:
            partial_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise UpdateDownloadError("No se pudo descargar la actualizacion.") from exc

    if checksum_asset is not None:
        _verify_asset_checksum(output_path, checksum_asset)

    return output_path


def _verify_asset_checksum(package_path: Path, checksum_asset: ReleaseAsset) -> None:
    expected_checksum = _download_expected_checksum(checksum_asset, package_path.name)
    actual_checksum = _sha256_file(package_path)

    if actual_checksum.lower() != expected_checksum.lower():
        try:
            package_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise UpdateDownloadError(
            "La actualizacion descargada no coincide con el checksum publicado."
        )


def _download_expected_checksum(checksum_asset: ReleaseAsset, package_name: str) -> str:
    request = Request(
        checksum_asset.download_url,
        headers={"User-Agent": "gestion-camiones-updater"},
    )

    try:
        with _open_url(request, timeout=30) as response:
            content = response.read(1024 * 32).decode("utf-8", errors="replace")
    except (OSError, HTTPError, URLError) as exc:
        raise UpdateDownloadError("No se pudo descargar el checksum de la actualizacion.") from exc

    checksum = _parse_checksum_content(content, package_name)
    if checksum is None:
        raise UpdateDownloadError("El checksum publicado no tiene un formato valido.")
    return checksum


def _parse_checksum_content(content: str, package_name: str) -> str | None:
    normalized_package_name = Path(package_name).name
    for line in content.splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            continue

        parts = stripped_line.replace("*", " ").split()
        if not parts:
            continue

        checksum = parts[0]
        if len(checksum) != 64 or any(char not in "0123456789abcdefABCDEF" for char in checksum):
            continue

        if len(parts) == 1 or normalized_package_name in parts[1:]:
            return checksum

    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_macos_installer_script(package_path: Path, scripts_dir: Path) -> Path:
    if package_path.suffix.lower() != ".dmg":
        raise UpdateInstallError("macOS requiere un paquete .dmg para instalacion automatica.")

    target_app = _preferred_macos_install_target()
    log_path = scripts_dir / "install-macos.log"
    script_path = scripts_dir / "install-macos.sh"
    script = f"""\
#!/usr/bin/env bash
set -euo pipefail

PACKAGE={_shell_quote(package_path)}
TARGET_APP={_shell_quote(target_app)}
CURRENT_PID="{os.getpid()}"
LOG_PATH={_shell_quote(log_path)}

exec >> "$LOG_PATH" 2>&1
echo "Iniciando instalacion automatica macOS: $(date)"

while kill -0 "$CURRENT_PID" 2>/dev/null; do
  sleep 1
done

MOUNT_DIR="$(mktemp -d)"
cleanup() {{
  hdiutil detach "$MOUNT_DIR" -quiet || true
  rm -rf "$MOUNT_DIR"
}}
trap cleanup EXIT

hdiutil attach "$PACKAGE" -nobrowse -readonly -mountpoint "$MOUNT_DIR"
SOURCE_APP="$(find "$MOUNT_DIR" -maxdepth 1 -name '*.app' -type d | head -n 1)"
if [[ -z "$SOURCE_APP" ]]; then
  echo "No se encontro una app dentro del DMG."
  exit 1
fi

TARGET_PARENT="$(dirname "$TARGET_APP")"
if [[ -w "$TARGET_PARENT" ]]; then
  rm -rf "$TARGET_APP"
  ditto "$SOURCE_APP" "$TARGET_APP"
  xattr -dr com.apple.quarantine "$TARGET_APP" || true
else
  osascript - "$SOURCE_APP" "$TARGET_APP" <<'OSA'
on run argv
  set sourceApp to item 1 of argv
  set targetApp to item 2 of argv
  set removeCommand to "/bin/rm -rf " & quoted form of targetApp
  set copyCommand to "/usr/bin/ditto " & quoted form of sourceApp & " " & quoted form of targetApp
  set xattrCommand to "/usr/bin/xattr -dr com.apple.quarantine "
  set quarantineCommand to xattrCommand & quoted form of targetApp & " || true"
  set installCommand to removeCommand & "; " & copyCommand & "; " & quarantineCommand
  do shell script installCommand with administrator privileges
end run
OSA
fi

open -n "$TARGET_APP"
echo "Instalacion automatica macOS finalizada: $(date)"
"""
    script_path.write_text(textwrap.dedent(script), encoding="utf-8")
    script_path.chmod(0o700)
    return script_path


def _write_windows_installer_script(package_path: Path, scripts_dir: Path) -> Path:
    if package_path.suffix.lower() != ".zip":
        raise UpdateInstallError("Windows requiere un paquete .zip para instalacion automatica.")

    install_dir = Path(sys.executable).resolve().parent
    executable_path = Path(sys.executable).resolve()
    staging_dir = scripts_dir / "windows-staging"
    log_path = scripts_dir / "install-windows.log"
    script_path = scripts_dir / "install-windows.ps1"
    script = f"""\
$ErrorActionPreference = "Stop"
param(
    [int]$CurrentPid
)
$Package = {_powershell_quote(package_path)}
$InstallDir = {_powershell_quote(install_dir)}
$ExecutablePath = {_powershell_quote(executable_path)}
$StagingDir = {_powershell_quote(staging_dir)}
$LogPath = {_powershell_quote(log_path)}

Start-Transcript -Path $LogPath -Append | Out-Null
try {{
    Write-Output "Iniciando instalacion automatica Windows: $(Get-Date)"
    if ($CurrentPid) {{
        try {{ Wait-Process -Id $CurrentPid -ErrorAction SilentlyContinue }} catch {{ }}
    }}

    if (Test-Path -LiteralPath $StagingDir) {{
        Remove-Item -LiteralPath $StagingDir -Recurse -Force
    }}
    New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null
    Expand-Archive -LiteralPath $Package -DestinationPath $StagingDir -Force

    $SourceDir = Join-Path $StagingDir "GestionCamiones"
    if (-not (Test-Path -LiteralPath $SourceDir)) {{
        $SourceExe = Get-ChildItem -LiteralPath $StagingDir -Recurse -Filter "GestionCamiones.exe" |
            Select-Object -First 1
        if ($null -eq $SourceExe) {{
            throw "No se encontro GestionCamiones.exe dentro del ZIP."
        }}
        $SourceDir = $SourceExe.Directory.FullName
    }}

    Copy-Item -Path (Join-Path $SourceDir "*") -Destination $InstallDir -Recurse -Force
    Start-Process -FilePath $ExecutablePath
    Write-Output "Instalacion automatica Windows finalizada: $(Get-Date)"
}} finally {{
    Stop-Transcript | Out-Null
}}
"""
    script_path.write_text(textwrap.dedent(script), encoding="utf-8")
    return script_path


def _current_macos_app_path() -> Path | None:
    executable_path = Path(sys.executable).resolve()
    try:
        app_path = executable_path.parents[2]
    except IndexError:
        return None
    if app_path.suffix == ".app" and app_path.exists():
        return app_path
    return None


def _preferred_macos_install_target() -> Path:
    current_app_path = _current_macos_app_path()
    applications_path = Path("/Applications/Gestion Camiones.app")
    user_applications_path = Path.home() / "Applications" / "Gestion Camiones.app"

    if applications_path.exists():
        return applications_path
    if current_app_path is not None and "/Applications/" in str(current_app_path):
        return current_app_path
    if user_applications_path.exists():
        return user_applications_path
    if current_app_path is not None:
        return current_app_path
    return applications_path


def _shell_quote(path: Path) -> str:
    value = str(path)
    return "'" + value.replace("'", "'\\''") + "'"


def _powershell_quote(path: Path) -> str:
    value = str(path)
    return "'" + value.replace("'", "''") + "'"


def _open_url(request: Request, *, timeout: int):
    context = ssl.create_default_context(cafile=certifi.where())
    return urlopen(request, timeout=timeout, context=context)


def _fetch_latest_release(owner: str, repo: str) -> dict[str, Any] | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gestion-camiones-updater",
        },
    )

    try:
        with _open_url(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise UpdateCheckError(f"GitHub respondio con error HTTP {exc.code}.") from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise UpdateCheckError(f"No se pudo conectar con GitHub. Detalle: {reason}") from exc
    except json.JSONDecodeError as exc:
        raise UpdateCheckError("GitHub devolvio una respuesta invalida.") from exc


def _normalize_version(version: str) -> str:
    return version.strip().removeprefix("v").removeprefix("V")


def _version_tuple(version: str) -> tuple[int, ...]:
    parts = []
    for part in _normalize_version(version).split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _safe_asset_filename(value: str) -> str:
    file_name = Path(value).name.strip()
    if not file_name:
        raise UpdateDownloadError("El archivo de actualizacion no tiene nombre valido.")
    for invalid_char in '<>:"/\\|?*':
        file_name = file_name.replace(invalid_char, "_")
    return file_name


def _asset_match_score(asset_name: str, system: str, machine: str) -> int:
    score = 0

    if system == "darwin":
        if not any(token in asset_name for token in (".dmg", ".pkg", "macos", "osx")):
            return 0
        score += 100
        if ".dmg" in asset_name:
            score += 20
        if any(token in asset_name for token in ("macos", "osx", "darwin")):
            score += 10

        if any(token in machine for token in ("arm64", "aarch64")):
            if any(token in asset_name for token in ("arm64", "applesilicon", "apple-silicon")):
                score += 40
            elif "universal" in asset_name:
                score += 30
            elif "intel" in asset_name or "x86_64" in asset_name:
                score -= 20
        else:
            if any(token in asset_name for token in ("x86_64", "intel")):
                score += 40
            elif "universal" in asset_name:
                score += 30
            elif "arm64" in asset_name or "applesilicon" in asset_name:
                score -= 20
        return score

    if system == "windows":
        if not any(token in asset_name for token in (".msi", ".exe", ".zip", "windows", "win")):
            return 0
        score += 100
        if ".zip" in asset_name:
            score += 30
        elif ".exe" in asset_name:
            score += 20
        elif ".msi" in asset_name:
            score += 10
        if any(token in asset_name for token in ("windows", "win")):
            score += 10
        if any(token in machine for token in ("amd64", "x86_64")):
            if any(token in asset_name for token in ("x64", "x86_64", "amd64", "win64")):
                score += 20
        return score

    return 0
