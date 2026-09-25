import io
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager import updater


class FakeResponse(io.BytesIO):
    def __init__(self, value: dict) -> None:
        super().__init__(json.dumps(value).encode("utf-8"))
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class UpdaterTests(unittest.TestCase):
    def test_semantic_version_comparison(self) -> None:
        self.assertTrue(updater.is_newer("v0.1.12", "v0.1.2"))
        self.assertTrue(updater.is_newer("v0.2.0", "v0.1.99"))
        self.assertTrue(updater.is_newer("1.0.0", "v0.9.9"))
        self.assertTrue(updater.is_newer("v1.0.0", "v1.0.0-rc.1"))
        self.assertTrue(updater.is_newer("v1.0.0-rc.2", "v1.0.0-rc.1"))
        self.assertFalse(updater.is_newer("v0.1.2", "v0.1.12"))
        self.assertFalse(updater.is_newer("v0.1.0", "v0.1.0"))
        self.assertFalse(updater.is_newer("v1.0.0-rc.1", "v1.0.0"))
        self.assertFalse(updater.is_newer("garbage", "v0.1.0"))
        self.assertFalse(updater.is_newer("v0.2.0", "dev"))

    def test_current_version_is_nonempty(self) -> None:
        self.assertTrue(updater.current_version())

    def test_directory_writable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(updater._dir_writable(Path(directory)))

    def test_needs_admin_is_false_from_source(self) -> None:
        self.assertFalse(updater.needs_admin())

    def test_check_requires_executable_and_checksum_assets(self) -> None:
        release = {
            "tag_name": "v0.2.0",
            "html_url": "https://github.com/dillonkirsch/simrace_config/releases/tag/v0.2.0",
            "body": "Changes",
            "assets": [
                {
                    "name": updater.EXE_NAME,
                    "browser_download_url": "https://github.com/example/app.exe",
                },
                {
                    "name": updater.EXE_NAME + ".sha256",
                    "browser_download_url": "https://github.com/example/app.exe.sha256",
                },
            ],
        }
        with (
            mock.patch.object(updater.urllib.request, "urlopen", return_value=FakeResponse(release)),
            mock.patch.object(updater, "current_version", return_value="v0.1.0"),
            mock.patch.object(updater, "is_frozen", return_value=True),
            mock.patch.object(updater, "needs_admin", return_value=False),
        ):
            result = updater.check_for_update()
        self.assertTrue(result["ok"])
        self.assertTrue(result["update_available"])
        self.assertTrue(result["assets_valid"])
        self.assertTrue(result["can_apply"])

        release["assets"] = release["assets"][:1]
        with (
            mock.patch.object(updater.urllib.request, "urlopen", return_value=FakeResponse(release)),
            mock.patch.object(updater, "current_version", return_value="v0.1.0"),
            mock.patch.object(updater, "is_frozen", return_value=True),
            mock.patch.object(updater, "needs_admin", return_value=False),
        ):
            missing_checksum = updater.check_for_update()
        self.assertFalse(missing_checksum["assets_valid"])
        self.assertFalse(missing_checksum["can_apply"])

    def test_rejects_non_github_and_non_https_download_urls(self) -> None:
        self.assertTrue(
            updater._allowed_download_url(
                "https://github.com/dillonkirsch/simrace_config/releases/download/v1/app.exe"
            )
        )
        self.assertTrue(
            updater._allowed_download_url(
                "https://release-assets.githubusercontent.com/file"
            )
        )
        self.assertFalse(updater._allowed_download_url("http://github.com/file"))
        self.assertFalse(updater._allowed_download_url("https://example.com/file"))
        self.assertFalse(
            updater._allowed_download_url("https://github.com@example.com/file")
        )

    def test_apply_is_disabled_from_source(self) -> None:
        result = updater.apply_update(
            "https://github.com/example/app.exe",
            "https://github.com/example/app.exe.sha256",
        )
        self.assertFalse(result["ok"])
        self.assertIn("packaged app", result["error"])

    def test_packaged_apply_refuses_checksum_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / updater.EXE_NAME
            current.write_bytes(b"MZcurrent")
            stage = root / "stage"
            stage.mkdir()

            def fake_download(_url, destination, _max_bytes):
                if destination.name.endswith(".sha256"):
                    destination.write_text("0" * 64, encoding="ascii")
                else:
                    destination.write_bytes(b"MZnew executable")

            with (
                mock.patch.object(updater, "is_frozen", return_value=True),
                mock.patch.object(updater.sys, "executable", str(current)),
                mock.patch.object(updater.tempfile, "mkdtemp", return_value=str(stage)),
                mock.patch.object(updater, "_download", side_effect=fake_download),
                mock.patch.object(updater.subprocess, "Popen") as popen,
            ):
                result = updater.apply_update(
                    "https://github.com/example/app.exe",
                    "https://github.com/example/app.exe.sha256",
                )
            self.assertFalse(result["ok"])
            self.assertIn("checksum", result["error"])
            popen.assert_not_called()

    def test_packaged_apply_stages_verified_swap_helper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / updater.EXE_NAME
            current.write_bytes(b"MZcurrent")
            stage = root / "stage"
            stage.mkdir()
            new_bytes = b"MZnew executable"
            checksum = hashlib.sha256(new_bytes).hexdigest()

            def fake_download(_url, destination, _max_bytes):
                if destination.name.endswith(".sha256"):
                    destination.write_text(
                        f"{checksum}  {updater.EXE_NAME}\n", encoding="ascii"
                    )
                else:
                    destination.write_bytes(new_bytes)

            with (
                mock.patch.object(updater, "is_frozen", return_value=True),
                mock.patch.object(updater.sys, "executable", str(current)),
                mock.patch.object(updater.tempfile, "mkdtemp", return_value=str(stage)),
                mock.patch.object(updater, "_download", side_effect=fake_download),
                mock.patch.object(updater, "_dir_writable", return_value=True),
                mock.patch.object(updater.subprocess, "Popen") as popen,
            ):
                result = updater.apply_update(
                    "https://github.com/example/app.exe",
                    "https://github.com/example/app.exe.sha256",
                )
            self.assertTrue(result["ok"])
            self.assertTrue(result["restarting"])
            self.assertTrue((stage / "apply_update.bat").is_file())
            popen.assert_called_once()

    def test_cli_updater_targets_the_windowed_executable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gui = root / updater.EXE_NAME
            gui.write_bytes(b"MZcurrent")
            cli = root / updater.CLI_EXE_NAME
            cli.write_bytes(b"MZcli")
            stage = root / "stage"
            stage.mkdir()
            new_bytes = b"MZnew executable"
            checksum = hashlib.sha256(new_bytes).hexdigest()

            def fake_download(_url, destination, _max_bytes):
                if destination.name.endswith(".sha256"):
                    destination.write_text(checksum, encoding="ascii")
                else:
                    destination.write_bytes(new_bytes)

            with (
                mock.patch.object(updater, "is_frozen", return_value=True),
                mock.patch.object(updater.sys, "executable", str(cli)),
                mock.patch.object(updater.tempfile, "mkdtemp", return_value=str(stage)),
                mock.patch.object(updater, "_download", side_effect=fake_download),
                mock.patch.object(updater, "_dir_writable", return_value=True),
                mock.patch.object(updater.subprocess, "Popen"),
            ):
                result = updater.apply_update(
                    "https://github.com/example/app.exe",
                    "https://github.com/example/app.exe.sha256",
                )

            self.assertTrue(result["ok"])
            helper = (stage / "apply_update.bat").read_text("utf-8")
            self.assertIn(str(gui), helper)
            self.assertNotIn(f'"{cli}"', helper)


if __name__ == "__main__":
    unittest.main()
