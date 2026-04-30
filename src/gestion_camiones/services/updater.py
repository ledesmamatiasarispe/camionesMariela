from __future__ import annotations

import json
from dataclasses import dataclass
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


def check_latest_release(owner: str, repo: str, current_version: str) -> ReleaseInfo | None:
    release = _fetch_latest_release(owner, repo)
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


def _fetch_latest_release(owner: str, repo: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "gestion-camiones-updater",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
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
