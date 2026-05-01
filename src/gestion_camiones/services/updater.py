from __future__ import annotations

import json
import platform
import shutil
import sqlite3
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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


def updates_dir(app_data_dir: Path) -> Path:
    path = app_data_dir / "updates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_dir(app_data_dir: Path) -> Path:
    path = app_data_dir / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
        with urlopen(request, timeout=30) as response:
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

    return output_path


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
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise UpdateCheckError(f"GitHub respondio con error HTTP {exc.code}.") from exc
    except URLError as exc:
        raise UpdateCheckError("No se pudo conectar con GitHub.") from exc
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
        if ".msi" in asset_name:
            score += 30
        elif ".exe" in asset_name:
            score += 20
        elif ".zip" in asset_name:
            score += 10
        if any(token in asset_name for token in ("windows", "win")):
            score += 10
        if any(token in machine for token in ("amd64", "x86_64")):
            if any(token in asset_name for token in ("x64", "x86_64", "amd64", "win64")):
                score += 20
        return score

    return 0
