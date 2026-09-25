"""GitHub Release checks and checksum-verified Windows self-updates."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "dillonkirsch/simrace_config"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
EXE_NAME = "SimControlsManager.exe"
_USER_AGENT = "sim-controls-manager-updater"
_REQUEST_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
_SEMVER = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z.-]+)?$"
)
_CHECKSUM = re.compile(r"^([0-9a-fA-F]{64})(?:\s+\*?\S+)?\s*$")
_MAX_EXE_BYTES = 250 * 1024 * 1024
_MAX_CHECKSUM_BYTES = 64 * 1024


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _dir_writable(path: Path) -> bool:
    probe = path / f".sim-controls-write-test-{os.getpid()}.tmp"
    try:
        with probe.open("xb"):
            pass
        probe.unlink()
        return True
    except OSError:
        try:
            probe.unlink()
        except OSError:
            pass
        return False


def needs_admin() -> bool:
    """Whether replacing the packaged executable requires elevation."""
    return is_frozen() and not _dir_writable(Path(sys.executable).parent)


def current_version() -> str:
    """Return the CI-stamped build version or the package version."""
    try:
        from sim_controls_manager import _buildinfo

        value = (getattr(_buildinfo, "VERSION", "") or "").strip()
        if value:
            return value
    except (ImportError, AttributeError):
        pass

    try:
        from importlib.metadata import version

        return "v" + version("sim-controls-manager")
    except Exception:
        try:
            from sim_controls_manager import __version__

            return "v" + __version__
        except Exception:
            return "dev"


def is_newer(latest: str, current: str) -> bool:
    """Compare semantic versions, including prerelease precedence."""
    latest_value = _parse_semver(latest)
    current_value = _parse_semver(current)
    if latest_value is None or current_value is None:
        return False

    latest_core, latest_pre = latest_value
    current_core, current_pre = current_value
    if latest_core != current_core:
        return latest_core > current_core
    if latest_pre is None:
        return current_pre is not None
    if current_pre is None:
        return False
    return _compare_prerelease(latest_pre, current_pre) > 0


def check_for_update(timeout: float = 8.0) -> dict:
    """Read the latest GitHub Release metadata without downloading an update."""
    current = current_version()
    try:
        request = urllib.request.Request(API_LATEST, headers=_REQUEST_HEADERS)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except Exception as error:
        return {"ok": False, "error": str(error), "current": current}

    tag = data.get("tag_name", "")
    exe_url = None
    sha_url = None
    for asset in data.get("assets", []):
        if asset.get("name") == EXE_NAME:
            exe_url = asset.get("browser_download_url")
        elif asset.get("name") == EXE_NAME + ".sha256":
            sha_url = asset.get("browser_download_url")

    assets_valid = bool(
        exe_url
        and sha_url
        and _allowed_download_url(exe_url)
        and _allowed_download_url(sha_url)
    )
    return {
        "ok": True,
        "current": current,
        "latest": tag,
        "update_available": is_newer(tag, current),
        "can_apply": is_frozen() and assets_valid,
        "needs_admin": needs_admin(),
        "url": data.get("html_url"),
        "notes": (data.get("body") or "")[:1200],
        "exe_url": exe_url,
        "sha_url": sha_url,
        "assets_valid": assets_valid,
    }


def apply_latest_update(timeout: float = 8.0) -> dict:
    """Check for and stage the latest update for the packaged application."""
    release = check_for_update(timeout)
    if not release.get("ok"):
        return release
    if not release.get("update_available"):
        return {
            "ok": True,
            "updated": False,
            "current": release.get("current"),
            "latest": release.get("latest"),
            "message": "Already on the latest version.",
        }
    if not release.get("assets_valid"):
        return {
            "ok": False,
            "error": "The release is missing its executable or SHA-256 checksum asset.",
        }
    return apply_update(release["exe_url"], release["sha_url"])


def apply_update(exe_url: str, sha_url: str) -> dict:
    """Download, verify, and stage a swap of the running packaged executable."""
    if not is_frozen():
        return {
            "ok": False,
            "error": "Self-update only works in the packaged app. From source, use git to update.",
        }
    if not _allowed_download_url(exe_url) or not _allowed_download_url(sha_url):
        return {"ok": False, "error": "Update assets must be HTTPS GitHub URLs."}

    current_executable = Path(sys.executable).resolve()
    stage = Path(tempfile.mkdtemp(prefix="sim-controls-manager-update-"))
    new_executable = stage / EXE_NAME
    checksum_file = stage / (EXE_NAME + ".sha256")
    log_path = stage / "update-log.txt"

    try:
        _download(exe_url, new_executable, _MAX_EXE_BYTES)
        _download(sha_url, checksum_file, _MAX_CHECKSUM_BYTES)
        checksum_match = _CHECKSUM.fullmatch(
            checksum_file.read_text("utf-8", errors="replace").strip()
        )
        if checksum_match is None:
            return {"ok": False, "error": "The release checksum file is invalid."}
        expected = checksum_match.group(1).lower()
        actual = hashlib.sha256(new_executable.read_bytes()).hexdigest().lower()
        if not hmac.compare_digest(expected, actual):
            return {
                "ok": False,
                "error": "The downloaded update failed its checksum check; it was not installed.",
            }
        if new_executable.read_bytes()[:2] != b"MZ":
            return {
                "ok": False,
                "error": "The downloaded update is not a Windows executable.",
            }
    except Exception as error:
        return {"ok": False, "error": f"Download failed: {error}"}

    protected = not _dir_writable(current_executable.parent)
    quoted_current = _batch_quote(current_executable)
    quoted_new = _batch_quote(new_executable)
    quoted_log = _batch_quote(log_path)
    batch_path = stage / "apply_update.bat"
    batch_path.write_text(
        "\r\n".join(
            (
                "@echo off",
                f'set "LOG={quoted_log}"',
                'echo [update] waiting for the app to close, then replacing it > "%LOG%"',
                "set /a tries=0",
                ":retry",
                f'move /Y "{quoted_new}" "{quoted_current}" >> "%LOG%" 2>&1',
                f'if not exist "{quoted_new}" goto done',
                "set /a tries+=1",
                "if %tries% geq 90 goto giveup",
                "ping -n 2 127.0.0.1 >NUL",
                "goto retry",
                ":done",
                'echo [update] replaced; relaunching >> "%LOG%"',
                "ping -n 5 127.0.0.1 >NUL",
                f'explorer.exe "{quoted_current}"',
                'del "%~f0"',
                "exit",
                ":giveup",
                'echo [update] ERROR: executable remained in use >> "%LOG%"',
                f'explorer.exe "{quoted_current}"',
                "exit",
                "",
            )
        ),
        encoding="utf-8",
    )

    if protected:
        try:
            import ctypes

            result = int(
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    "cmd.exe",
                    f'/c "{batch_path}"',
                    None,
                    0,
                )
            )
        except Exception as error:
            return {
                "ok": False,
                "error": f"Could not request administrator permission: {error}",
            }
        if result <= 32:
            return {
                "ok": False,
                "needs_admin": True,
                "error": "Administrator permission was required and declined.",
            }
        return {"ok": True, "restarting": True, "elevated": True}

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    subprocess.Popen(
        ["cmd", "/c", str(batch_path)],
        creationflags=flags,
        close_fds=True,
    )
    return {"ok": True, "restarting": True, "elevated": False}


def _parse_semver(value: str):
    match = _SEMVER.fullmatch(value or "")
    if match is None:
        return None
    core = tuple(int(part) for part in match.group(1, 2, 3))
    prerelease = match.group(4)
    return core, None if prerelease is None else tuple(prerelease.split("."))


def _compare_prerelease(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    for left_part, right_part in zip(left, right):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            return (int(left_part) > int(right_part)) - (int(left_part) < int(right_part))
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return (left_part > right_part) - (left_part < right_part)
    return (len(left) > len(right)) - (len(left) < len(right))


def _allowed_download_url(value: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(value)
    except (TypeError, ValueError):
        return False
    hostname = (parsed.hostname or "").lower()
    return (
        parsed.scheme == "https"
        and not parsed.username
        and not parsed.password
        and (
            hostname == "github.com"
            or hostname.endswith(".github.com")
            or hostname.endswith(".githubusercontent.com")
        )
    )


def _download(url: str, destination: Path, max_bytes: int, timeout: float = 180.0) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=timeout) as response, destination.open("xb") as output:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ValueError("download exceeds the allowed size")
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("download exceeds the allowed size")
            output.write(chunk)
        output.flush()
        os.fsync(output.fileno())


def _batch_quote(path: Path) -> str:
    value = str(path)
    if '"' in value or "\r" in value or "\n" in value:
        raise ValueError("path cannot be safely represented in a batch file")
    return value.replace("%", "%%")
