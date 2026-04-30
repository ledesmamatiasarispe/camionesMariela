from __future__ import annotations

import unittest

from gestion_camiones.services.updater import ReleaseAsset, ReleaseInfo, select_release_asset


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


if __name__ == "__main__":
    unittest.main()
