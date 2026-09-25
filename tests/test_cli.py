import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager import cli


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="sim-controls-cli-"
        )
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_catalog(self, value) -> Path:
        path = self.root / "catalog.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_validates_and_summarizes_manual_catalog_without_writing(self) -> None:
        path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub output",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        before = path.read_bytes()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = cli.main(["catalog", "validate", str(path)])
        self.assertEqual(exit_code, 0)
        self.assertIn("Catalog is valid", output.getvalue())
        self.assertIn("pit_limiter: SimHub button 7", output.getvalue())
        self.assertEqual(path.read_bytes(), before)

    def test_runs_as_real_module_entry_point(self) -> None:
        path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub output",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        environment = os.environ.copy()
        source_root = str(Path(__file__).parents[1] / "src")
        environment["PYTHONPATH"] = source_root + os.pathsep + environment.get(
            "PYTHONPATH", ""
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sim_controls_manager",
                "catalog",
                "validate",
                str(path),
            ],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Catalog is valid", result.stdout)

    def test_reports_malformed_json(self) -> None:
        path = self.root / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            exit_code = cli.main(["catalog", "validate", str(path)])
        self.assertEqual(exit_code, 1)
        self.assertIn("Could not read catalog", errors.getvalue())

    def test_update_check_output(self) -> None:
        with mock.patch.object(
            cli.updater,
            "check_for_update",
            return_value={
                "ok": True,
                "current": "v0.1.0",
                "latest": "v0.2.0",
                "update_available": True,
                "assets_valid": True,
                "can_apply": True,
            },
        ):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = cli.main(["update", "check"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Update available: v0.2.0", output.getvalue())


if __name__ == "__main__":
    unittest.main()
