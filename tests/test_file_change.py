import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sim_controls_manager.file_change import (
    FileChangeError,
    apply_file_change,
    plan_file_change,
    preview_restore,
    restore_file,
    sha256,
)


class FileChangeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="sim-controls-manager-"
        )
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "controls.fixture"
        self.backups = self.root / "backups"
        self.original = bytes((0x00, 0x41, 0xFF, 0x0A))
        self.source.write_bytes(self.original)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_idempotent_plan_creates_no_backup(self) -> None:
        plan = plan_file_change(self.source, self.original)
        result = apply_file_change(plan, self.backups)
        self.assertFalse(plan.changed)
        self.assertEqual(result.status, "unchanged")
        self.assertFalse(self.backups.exists())

    def test_applies_exact_bytes_and_creates_verified_receipt(self) -> None:
        next_bytes = bytes((0x00, 0x42, 0xFE, 0x0A))
        plan = plan_file_change(self.source, next_bytes)
        result = apply_file_change(
            plan,
            self.backups,
            validate=lambda data: len(data) == 4,
            now=lambda: datetime(2026, 9, 25, 1, 2, 3, tzinfo=timezone.utc),
        )
        self.assertEqual(result.status, "applied")
        self.assertEqual(self.source.read_bytes(), next_bytes)
        self.assertEqual(Path(result.receipt.backupPath).read_bytes(), self.original)
        self.assertEqual(result.receipt.originalHash, sha256(self.original))
        self.assertEqual(result.receipt.appliedHash, sha256(next_bytes))
        saved_receipt = json.loads(result.receipt_path.read_text("utf-8"))
        self.assertEqual(saved_receipt["originalHash"], sha256(self.original))

    def test_refuses_source_change_after_preview(self) -> None:
        plan = plan_file_change(self.source, b"planned")
        self.source.write_bytes(b"changed elsewhere")
        with self.assertRaises(FileChangeError) as caught:
            apply_file_change(plan, self.backups)
        self.assertEqual(caught.exception.code, "SOURCE_CHANGED")
        self.assertFalse(self.backups.exists())

    def test_refuses_target_in_use(self) -> None:
        plan = plan_file_change(self.source, b"next")
        with self.assertRaises(FileChangeError) as caught:
            apply_file_change(plan, self.backups, is_target_in_use=lambda: True)
        self.assertEqual(caught.exception.code, "TARGET_IN_USE")
        self.assertFalse(self.backups.exists())

    def test_validates_before_backup(self) -> None:
        plan = plan_file_change(self.source, b"invalid")
        with self.assertRaises(FileChangeError) as caught:
            apply_file_change(plan, self.backups, validate=lambda _data: False)
        self.assertEqual(caught.exception.code, "VALIDATION_FAILED")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.backups.exists())

    def test_rolls_back_failed_post_write_validation(self) -> None:
        plan = plan_file_change(self.source, b"next")
        calls = 0

        def validate(_data: bytes) -> bool:
            nonlocal calls
            calls += 1
            return calls < 3

        with self.assertRaises(FileChangeError) as caught:
            apply_file_change(plan, self.backups, validate=validate)
        self.assertEqual(caught.exception.code, "VALIDATION_FAILED")
        self.assertEqual(calls, 3)
        self.assertEqual(self.source.read_bytes(), self.original)

    def _apply_fixture(self):
        plan = plan_file_change(self.source, b"applied bytes")
        return apply_file_change(plan, self.backups)

    def test_restore_preview_restore_and_idempotency(self) -> None:
        applied = self._apply_fixture()
        self.assertEqual(preview_restore(applied.receipt_path).status, "ready")
        self.assertEqual(restore_file(applied.receipt_path).status, "restored")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(
            preview_restore(applied.receipt_path).status, "already-restored"
        )
        self.assertEqual(restore_file(applied.receipt_path).status, "unchanged")

    def test_restore_refuses_intervening_change_without_confirmation(self) -> None:
        applied = self._apply_fixture()
        self.source.write_bytes(b"user changed this after apply")
        self.assertEqual(
            preview_restore(applied.receipt_path).status, "changed-since-apply"
        )
        with self.assertRaises(FileChangeError) as caught:
            restore_file(applied.receipt_path)
        self.assertEqual(caught.exception.code, "TARGET_CHANGED")
        self.assertEqual(self.source.read_bytes(), b"user changed this after apply")
        self.assertEqual(
            restore_file(
                applied.receipt_path, allow_changed_target=True
            ).status,
            "restored",
        )
        self.assertEqual(self.source.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
