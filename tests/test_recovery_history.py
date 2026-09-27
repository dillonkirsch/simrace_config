import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from sim_controls_manager.file_change import apply_file_change, plan_file_change, restore_file
from sim_controls_manager.recovery_history import discover_history, inspect_entry, target_identity


class RecoveryHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.history = self.root / "backups"

    def tearDown(self):
        self.temporary.cleanup()

    def apply_fixture(self, name="controls.json", day=1):
        target = self.root / str(day) / name
        target.parent.mkdir(parents=True)
        target.write_bytes(b"original")
        return apply_file_change(plan_file_change(target, b"applied"), self.history,
                                 now=lambda: datetime(2026, 9, day, tzinfo=timezone.utc))

    def test_discovers_newest_first_and_preserves_simulator_identity(self):
        older = self.apply_fixture("controls.ini", 1)
        newest = self.apply_fixture("controls.json", 2)
        entries = discover_history(self.history)
        self.assertEqual([entry.path for entry in entries], [newest.receipt_path, older.receipt_path])
        self.assertEqual([entry.simulator for entry in entries], ["ACC", "Assetto Corsa"])
        self.assertTrue(all(entry.status == "ready" for entry in entries))

    def test_reports_changed_missing_and_restored_without_mutating_files(self):
        result = self.apply_fixture()
        target = Path(result.receipt.originalPath)
        target.write_bytes(b"user change")
        self.assertEqual(inspect_entry(result.receipt_path).status, "changed-since-apply")
        self.assertEqual(target.read_bytes(), b"user change")
        target.unlink()
        self.assertEqual(inspect_entry(result.receipt_path).status, "target-missing")
        target.write_bytes(b"applied")
        restore_file(result.receipt_path)
        self.assertEqual(inspect_entry(result.receipt_path).status, "already-restored")

    def test_invalid_backup_does_not_hide_other_receipts(self):
        damaged = self.apply_fixture(day=1)
        good = self.apply_fixture(day=2)
        Path(damaged.receipt.backupPath).write_bytes(b"corruption")
        entries = discover_history(self.history)
        self.assertEqual([entry.status for entry in entries], ["ready", "invalid"])
        self.assertEqual(entries[0].path, good.receipt_path)
        self.assertIn("Backup", entries[1].error)

    def test_malformed_receipt_remains_visible(self):
        self.history.mkdir()
        for index, data in enumerate(("not JSON", '[]', json.dumps({"createdAt": None, "originalPath": 7}))):
            (self.history / f"{index}-receipt.json").write_text(data)
        entries = discover_history(self.history)
        self.assertEqual(len(entries), 3)
        self.assertTrue(all(entry.status == "invalid" for entry in entries))
        self.assertTrue(all(entry.date_label == "Unknown date" for entry in entries))

    def test_external_receipt_is_included_once(self):
        result = self.apply_fixture()
        self.assertEqual(len(discover_history(self.history, (result.receipt_path,))), 1)
        self.assertEqual(discover_history(self.root / "empty", (result.receipt_path,))[0].status, "ready")

    def test_known_target_names(self):
        self.assertEqual(target_identity("iRacing/profiles/controls/Road/controls.cfg"), ("iRacing", "Road"))
        self.assertEqual(target_identity("ACE/input_devices.inputdeviceconfiguration"), ("Assetto Corsa EVO", "Live controls"))
        self.assertEqual(target_identity("LMU/Presets/Tablet.json"), ("Le Mans Ultimate", "Tablet"))
