from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from gestion_camiones.services.updater import (
    ReleaseAsset,
    ReleaseInfo,
    _parse_checksum_content,
    _write_macos_installer_script,
    _write_windows_installer_script,
    backups_dir,
    create_database_backup,
    select_checksum_asset,
    select_release_asset,
    updates_dir,
)


class SelectReleaseAssetTests(unittest.TestCase):
    def test_prefers_apple_silicon_asset_on_arm_macs(self) -> None:
        release = ReleaseInfo(
            version="0.2.0",
            name="v0.2.0",
            html_url="https://example.com/release",
            notes="",
            assets=(
                ReleaseAsset("GestionCamiones-macOS-Intel.dmg", "https://example.com/intel", 1),
                ReleaseAsset(
                    "GestionCamiones-macOS-AppleSilicon.dmg",
                    "https://example.com/arm",
                    1,
                ),
            ),
        )

        asset = select_release_asset(release, system="Darwin", machine="arm64")

        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, "GestionCamiones-macOS-AppleSilicon.dmg")

    def test_prefers_intel_asset_on_intel_macs(self) -> None:
        release = ReleaseInfo(
            version="0.2.0",
            name="v0.2.0",
            html_url="https://example.com/release",
            notes="",
            assets=(
                ReleaseAsset(
                    "GestionCamiones-macOS-AppleSilicon.dmg",
                    "https://example.com/arm",
                    1,
                ),
                ReleaseAsset("GestionCamiones-macOS-Intel.dmg", "https://example.com/intel", 1),
            ),
        )

        asset = select_release_asset(release, system="Darwin", machine="x86_64")

        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, "GestionCamiones-macOS-Intel.dmg")

    def test_prefers_windows_package_for_windows(self) -> None:
        release = ReleaseInfo(
            version="0.2.0",
            name="v0.2.0",
            html_url="https://example.com/release",
            notes="",
            assets=(
                ReleaseAsset(
                    "GestionCamiones-macOS-AppleSilicon.dmg",
                    "https://example.com/mac",
                    1,
                ),
                ReleaseAsset("GestionCamiones-Windows-x64.zip", "https://example.com/win", 1),
            ),
        )

        asset = select_release_asset(release, system="Windows", machine="AMD64")

        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, "GestionCamiones-Windows-x64.zip")

    def test_returns_none_when_no_asset_matches_system(self) -> None:
        release = ReleaseInfo(
            version="0.2.0",
            name="v0.2.0",
            html_url="https://example.com/release",
            notes="",
            assets=(ReleaseAsset("manual.pdf", "https://example.com/manual", 1),),
        )

        asset = select_release_asset(release, system="Darwin", machine="arm64")

        self.assertIsNone(asset)

    def test_selects_checksum_asset_for_package(self) -> None:
        package = ReleaseAsset("GestionCamiones-Windows-x64.zip", "https://example.com/win", 1)
        checksum = ReleaseAsset(
            "GestionCamiones-Windows-x64.zip.sha256",
            "https://example.com/win.sha256",
            1,
        )
        release = ReleaseInfo(
            version="0.2.0",
            name="v0.2.0",
            html_url="https://example.com/release",
            notes="",
            assets=(package, checksum),
        )

        asset = select_checksum_asset(release, package)

        self.assertEqual(asset, checksum)

    def test_parse_checksum_content_accepts_standard_sha256_format(self) -> None:
        checksum = "a" * 64

        parsed_checksum = _parse_checksum_content(
            f"{checksum}  GestionCamiones-Windows-x64.zip\n",
            "GestionCamiones-Windows-x64.zip",
        )

        self.assertEqual(parsed_checksum, checksum)

    def test_update_and_backup_dirs_are_created_under_app_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_data_dir = Path(temp_dir)

            self.assertEqual(updates_dir(app_data_dir), app_data_dir / "updates")
            self.assertEqual(backups_dir(app_data_dir), app_data_dir / "backups")
            self.assertTrue((app_data_dir / "updates").is_dir())
            self.assertTrue((app_data_dir / "backups").is_dir())

    def test_create_database_backup_preserves_local_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            database_path = temp_path / "gestion_camiones.sqlite3"
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute("CREATE TABLE viajes (id INTEGER PRIMARY KEY, nombre TEXT)")
                connection.execute("INSERT INTO viajes (nombre) VALUES (?)", ("Viaje A",))
                connection.commit()

            backup_path = create_database_backup(database_path, temp_path / "backups")

            with closing(sqlite3.connect(backup_path)) as connection:
                row = connection.execute("SELECT nombre FROM viajes WHERE id = 1").fetchone()

            self.assertIsNotNone(row)
            self.assertEqual(row[0], "Viaje A")

    def test_writes_macos_installer_script_for_dmg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "GestionCamiones-macOS-AppleSilicon.dmg"
            package_path.write_bytes(b"fake")

            script_path = _write_macos_installer_script(package_path, temp_path)

            content = script_path.read_text(encoding="utf-8")
            self.assertIn("hdiutil attach", content)
            self.assertIn(str(package_path), content)
            self.assertIn("open -n \"$TARGET_APP\"", content)

    def test_writes_windows_installer_script_for_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "GestionCamiones-Windows-x64.zip"
            package_path.write_bytes(b"fake")

            script_path = _write_windows_installer_script(package_path, temp_path)

            content = script_path.read_text(encoding="utf-8")
            self.assertIn("Expand-Archive", content)
            self.assertIn(str(package_path), content)
            self.assertIn("Start-Process -FilePath $ExecutablePath", content)


if __name__ == "__main__":
    unittest.main()
