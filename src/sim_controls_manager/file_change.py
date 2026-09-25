"""Adapter-independent guarded file apply, backup, and restore operations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

RECEIPT_VERSION = 1
_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")

Validator = Callable[[bytes], bool | None]
TargetInUseCheck = Callable[[], bool]


class FileChangeError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class FileChangePlan:
    source_path: Path
    source_hash: str
    next_hash: str
    next_bytes: bytes
    changed: bool


@dataclass(frozen=True, slots=True)
class Receipt:
    receiptVersion: int
    createdAt: str
    originalPath: str
    backupPath: str
    originalHash: str
    appliedHash: str
    originalMode: int


@dataclass(frozen=True, slots=True)
class ApplyResult:
    status: str
    receipt_path: Path | None = None
    receipt: Receipt | None = None


@dataclass(frozen=True, slots=True)
class RestorePreview:
    receipt: Receipt
    current_hash: str | None
    status: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plan_file_change(source_path: str | Path, next_bytes: bytes) -> FileChangePlan:
    """Read a source file and return a byte-exact, read-only change plan."""
    if not isinstance(next_bytes, bytes):
        raise TypeError("next_bytes must be bytes")
    path = Path(source_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("source_path must name a file")
    source_bytes = path.read_bytes()
    source_hash = sha256(source_bytes)
    next_hash = sha256(next_bytes)
    return FileChangePlan(
        source_path=path,
        source_hash=source_hash,
        next_hash=next_hash,
        next_bytes=bytes(next_bytes),
        changed=source_hash != next_hash,
    )


def apply_file_change(
    plan: FileChangePlan,
    backup_directory: str | Path,
    *,
    validate: Validator | None = None,
    is_target_in_use: TargetInUseCheck | None = None,
    now: Callable[[], datetime] | None = None,
) -> ApplyResult:
    """Apply a previewed change with backup, validation, and rollback."""
    if not isinstance(plan, FileChangePlan):
        raise TypeError("plan must be a FileChangePlan")
    validate = validate or (lambda _data: True)
    is_target_in_use = is_target_in_use or (lambda: False)
    now = now or (lambda: datetime.now(timezone.utc))

    if is_target_in_use():
        raise FileChangeError(
            "TARGET_IN_USE",
            "Refusing to write while the target game or process is running",
        )

    current_bytes = plan.source_path.read_bytes()
    if sha256(current_bytes) != plan.source_hash:
        raise FileChangeError(
            "SOURCE_CHANGED",
            "The source file changed after preview; create a new preview before applying",
        )
    if sha256(plan.next_bytes) != plan.next_hash:
        raise FileChangeError(
            "PLAN_CHANGED", "The proposed bytes no longer match the previewed change"
        )
    if not plan.changed:
        return ApplyResult(status="unchanged")

    _run_validation(validate, plan.next_bytes, "Proposed content failed validation")

    backup_dir = Path(backup_directory).expanduser().resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    source_stat = plan.source_path.stat()
    original_mode = stat.S_IMODE(source_stat.st_mode)
    timestamp_value = now()
    timestamp = _format_timestamp(timestamp_value)
    suffix = uuid.uuid4().hex
    backup_path = backup_dir / f"{timestamp}-{suffix}-{plan.source_path.name}.bak"
    receipt_path = backup_dir / f"{timestamp}-{suffix}-receipt.json"

    _write_exclusive(backup_path, current_bytes, original_mode)
    if sha256(backup_path.read_bytes()) != plan.source_hash:
        _unlink_if_present(backup_path)
        raise FileChangeError(
            "BACKUP_INVALID", "Backup hash does not match the previewed source"
        )

    temp_path = _temporary_sibling(plan.source_path, "write")
    replacement_completed = False
    try:
        _write_exclusive(temp_path, plan.next_bytes, original_mode)
        temporary_bytes = temp_path.read_bytes()
        if sha256(temporary_bytes) != plan.next_hash:
            raise FileChangeError(
                "TEMP_INVALID", "Temporary file hash does not match the preview"
            )
        _run_validation(
            validate, temporary_bytes, "Temporary content failed validation"
        )

        os.replace(temp_path, plan.source_path)
        replacement_completed = True

        applied_bytes = plan.source_path.read_bytes()
        if sha256(applied_bytes) != plan.next_hash:
            raise FileChangeError(
                "POST_WRITE_INVALID", "Written file hash does not match the preview"
            )
        _run_validation(
            validate, applied_bytes, "Written content failed post-write validation"
        )

        receipt = Receipt(
            receiptVersion=RECEIPT_VERSION,
            createdAt=_as_utc(timestamp_value).isoformat().replace("+00:00", "Z"),
            originalPath=str(plan.source_path),
            backupPath=str(backup_path),
            originalHash=plan.source_hash,
            appliedHash=plan.next_hash,
            originalMode=original_mode,
        )
        _write_json_exclusive(receipt_path, asdict(receipt))
        return ApplyResult("applied", receipt_path, receipt)
    except Exception as error:
        _unlink_if_present(receipt_path)
        if replacement_completed:
            try:
                _restore_from_backup(
                    backup_path,
                    plan.source_path,
                    plan.source_hash,
                    original_mode,
                )
            except Exception as rollback_error:
                raise FileChangeError(
                    "ROLLBACK_FAILED",
                    "Apply failed and the automatic rollback also failed: "
                    f"{rollback_error}",
                ) from error
        raise
    finally:
        _unlink_if_present(temp_path)


def preview_restore(receipt_path: str | Path) -> RestorePreview:
    """Inspect a restore receipt and target without writing anything."""
    receipt = _read_receipt(receipt_path)
    backup_path = Path(receipt.backupPath)
    try:
        backup_bytes = backup_path.read_bytes()
    except OSError as error:
        raise FileChangeError("BACKUP_INVALID", f"Could not read backup: {error}") from error
    if sha256(backup_bytes) != receipt.originalHash:
        raise FileChangeError("BACKUP_INVALID", "Backup no longer matches its receipt")

    original_path = Path(receipt.originalPath)
    try:
        current_hash = sha256(original_path.read_bytes())
    except FileNotFoundError:
        current_hash = None

    if current_hash == receipt.originalHash:
        status = "already-restored"
    elif current_hash == receipt.appliedHash:
        status = "ready"
    elif current_hash is None:
        status = "target-missing"
    else:
        status = "changed-since-apply"
    return RestorePreview(receipt, current_hash, status)


def restore_file(
    receipt_path: str | Path,
    *,
    allow_changed_target: bool = False,
    is_target_in_use: TargetInUseCheck | None = None,
    validate: Validator | None = None,
) -> ApplyResult:
    """Restore a backup, refusing intervening changes unless confirmed."""
    is_target_in_use = is_target_in_use or (lambda: False)
    if is_target_in_use():
        raise FileChangeError(
            "TARGET_IN_USE",
            "Refusing to restore while the target game or process is running",
        )

    preview = preview_restore(receipt_path)
    if preview.status == "already-restored":
        return ApplyResult("unchanged", Path(receipt_path), preview.receipt)
    if preview.status != "ready" and not allow_changed_target:
        raise FileChangeError(
            "TARGET_CHANGED",
            f"Restore target is {preview.status}; preview and explicitly confirm "
            "before overwriting it",
        )

    backup_bytes = Path(preview.receipt.backupPath).read_bytes()
    if validate is not None:
        _run_validation(validate, backup_bytes, "Backup failed restore validation")
    _restore_from_backup(
        Path(preview.receipt.backupPath),
        Path(preview.receipt.originalPath),
        preview.receipt.originalHash,
        preview.receipt.originalMode,
    )
    return ApplyResult("restored", Path(receipt_path), preview.receipt)


def _run_validation(validate: Validator, data: bytes, message: str) -> None:
    try:
        result = validate(bytes(data))
        if result is False:
            raise ValueError("validator returned false")
    except FileChangeError:
        raise
    except Exception as error:
        raise FileChangeError("VALIDATION_FAILED", f"{message}: {error}") from error


def _write_exclusive(path: Path, data: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    try:
        path.chmod(mode)
    except OSError:
        pass


def _write_json_exclusive(path: Path, value: dict) -> None:
    data = (json.dumps(value, indent=2) + "\n").encode("utf-8")
    try:
        _write_exclusive(path, data)
    except Exception:
        _unlink_if_present(path)
        raise


def _restore_from_backup(
    backup_path: Path,
    target_path: Path,
    expected_hash: str,
    mode: int,
) -> None:
    temp_path = _temporary_sibling(target_path, "restore")
    try:
        _write_exclusive(temp_path, backup_path.read_bytes(), mode)
        os.replace(temp_path, target_path)
        if sha256(target_path.read_bytes()) != expected_hash:
            raise FileChangeError(
                "RESTORE_INVALID", "Restored file hash does not match its receipt"
            )
    finally:
        _unlink_if_present(temp_path)


def _read_receipt(path: str | Path) -> Receipt:
    try:
        value = json.loads(Path(path).expanduser().resolve(strict=True).read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FileChangeError(
            "RECEIPT_INVALID", f"Could not read restore receipt: {error}"
        ) from error

    required_strings = (
        "createdAt",
        "originalPath",
        "backupPath",
        "originalHash",
        "appliedHash",
    )
    if (
        not isinstance(value, dict)
        or value.get("receiptVersion") != RECEIPT_VERSION
        or any(not isinstance(value.get(key), str) or not value[key] for key in required_strings)
        or not isinstance(value.get("originalMode"), int)
        or not _HASH_PATTERN.fullmatch(value.get("originalHash", ""))
        or not _HASH_PATTERN.fullmatch(value.get("appliedHash", ""))
        or not Path(value.get("originalPath", "")).is_absolute()
        or not Path(value.get("backupPath", "")).is_absolute()
    ):
        raise FileChangeError(
            "RECEIPT_INVALID", "Restore receipt has an unsupported shape or version"
        )
    try:
        return Receipt(**value)
    except TypeError as error:
        raise FileChangeError(
            "RECEIPT_INVALID", "Restore receipt contains unsupported fields"
        ) from error


def _temporary_sibling(target_path: Path, purpose: str) -> Path:
    return target_path.parent / (
        f".{target_path.name}.sim-controls-{purpose}-{uuid.uuid4().hex}.tmp"
    )


def _format_timestamp(value: datetime) -> str:
    return _as_utc(value).strftime("%Y-%m-%dT%H-%M-%S.%fZ")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("now() must return a datetime")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _unlink_if_present(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
