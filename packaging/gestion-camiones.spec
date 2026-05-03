# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_root = Path(SPECPATH).parent
version_scope = {}
exec(
    (project_root / "src" / "gestion_camiones" / "__init__.py").read_text(
        encoding="utf-8"
    ),
    version_scope,
)
app_version = version_scope["__version__"]
hiddenimports = collect_submodules("PySide6")
datas = collect_data_files("certifi")
datas += [
    (
        str(project_root / "src" / "gestion_camiones" / "assets" / "RICCO.xlsx"),
        "gestion_camiones/assets",
    ),
    (
        str(project_root / "src" / "gestion_camiones" / "assets" / "app_icon.png"),
        "gestion_camiones/assets",
    ),
    (
        str(project_root / "src" / "gestion_camiones" / "assets" / "app_icon.ico"),
        "gestion_camiones/assets",
    ),
    (
        str(project_root / "src" / "gestion_camiones" / "assets" / "app_icon.icns"),
        "gestion_camiones/assets",
    ),
]
icon_path = project_root / "src" / "gestion_camiones" / "assets" / (
    "app_icon.icns" if sys.platform == "darwin" else "app_icon.ico"
)

a = Analysis(
    [str(project_root / "src" / "gestion_camiones" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GestionCamiones",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=os.environ.get("PYINSTALLER_TARGET_ARCH"),
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path),
)

if sys.platform == "darwin":
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="GestionCamiones",
    )
    app = BUNDLE(
        coll,
        name="Gestion Camiones.app",
        icon=str(icon_path),
        bundle_identifier="com.romero.gestioncamiones",
        version=app_version,
        info_plist={
            "CFBundleName": "Gestion Camiones",
            "CFBundleDisplayName": "Gestion Camiones",
            "CFBundleShortVersionString": app_version,
            "CFBundleVersion": app_version,
            "LSMinimumSystemVersion": "13.0",
            "NSHighResolutionCapable": True,
        },
    )
else:
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="GestionCamiones",
    )
