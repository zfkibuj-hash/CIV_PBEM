"""Check GitHub Releases and self-update the frozen Windows .exe."""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

GITHUB_REPO = "zfkibuj-hash/CIV_PBEM"
RELEASES_LATEST_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
USER_AGENT = "Civ4PBEMManager-Updater"
DOWNLOAD_TIMEOUT_S = 120
API_TIMEOUT_S = 8


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str
    version: str
    name: str
    body: str
    html_url: str
    exe_url: str
    exe_name: str
    exe_size: int


def is_frozen_exe() -> bool:
    return bool(getattr(sys, "frozen", False)) and Path(sys.executable).suffix.lower() == ".exe"


def current_exe_path() -> Optional[Path]:
    if not is_frozen_exe():
        return None
    return Path(sys.executable).resolve()


def parse_version(raw: str) -> tuple[int, ...]:
    """Parse ``v5.0.12`` / ``5.0.12`` into a comparable tuple."""
    s = (raw or "").strip()
    if s.lower().startswith("v"):
        s = s[1:]
    # Take leading dotted numeric prefix only
    m = re.match(r"^(\d+(?:\.\d+)*)", s)
    if not m:
        return (0,)
    parts = [int(p) for p in m.group(1).split(".")]
    return tuple(parts) if parts else (0,)


def is_newer(remote: str, local: str) -> bool:
    """True if *remote* version is strictly greater than *local*."""
    a, b = parse_version(remote), parse_version(local)
    # Pad to same length
    n = max(len(a), len(b))
    a = a + (0,) * (n - len(a))
    b = b + (0,) * (n - len(b))
    return a > b


def pick_exe_asset(assets: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Prefer Civ4PBEMManager*.exe, else first .exe asset."""
    exes = [
        a for a in (assets or [])
        if str(a.get("name") or "").lower().endswith(".exe")
        and a.get("browser_download_url")
    ]
    if not exes:
        return None
    preferred = [
        a for a in exes
        if "civ4pbemmanager" in str(a.get("name") or "").lower()
    ]
    return preferred[0] if preferred else exes[0]


def fetch_latest_release(
    *,
    url: str = RELEASES_LATEST_URL,
    timeout: float = API_TIMEOUT_S,
) -> ReleaseInfo:
    """Fetch latest GitHub release metadata. Raises on network/parse errors."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return release_info_from_payload(data)


def release_info_from_payload(data: dict[str, Any]) -> ReleaseInfo:
    tag = str(data.get("tag_name") or "").strip()
    if not tag:
        raise ValueError("release missing tag_name")
    asset = pick_exe_asset(list(data.get("assets") or []))
    if not asset:
        raise ValueError("release has no .exe asset")
    version = tag[1:] if tag.lower().startswith("v") else tag
    return ReleaseInfo(
        tag=tag,
        version=version,
        name=str(data.get("name") or tag),
        body=str(data.get("body") or ""),
        html_url=str(data.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases"),
        exe_url=str(asset["browser_download_url"]),
        exe_name=str(asset.get("name") or "Civ4PBEMManager.exe"),
        exe_size=int(asset.get("size") or 0),
    )


def should_offer_update(
    release: ReleaseInfo,
    local_version: str,
    skipped_version: str = "",
) -> bool:
    if not is_newer(release.version, local_version):
        return False
    skipped = (skipped_version or "").strip()
    if skipped and parse_version(skipped) == parse_version(release.version):
        return False
    return True


def unblock_windows_file(path: Path) -> bool:
    """Strip Mark-of-the-Web (Zone.Identifier) so SmartScreen is less noisy.

    Does not defeat Smart App Control / lack of code signing — only removes the
    "downloaded from the Internet" alternate data stream when present.
    """
    if os.name != "nt":
        return False
    path = Path(path)
    ads = f"{path}:Zone.Identifier"
    try:
        if os.path.exists(ads):
            os.remove(ads)
            logger.info("Removed Zone.Identifier from %s", path)
            return True
    except OSError as e:
        logger.warning("Could not unblock %s: %s", path, e)
    # Also try PowerShell Unblock-File (no-op if already clean)
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Unblock-File -LiteralPath '{path}'",
            ],
            capture_output=True,
            timeout=15,
            creationflags=0x08000000 if os.name == "nt" else 0,  # CREATE_NO_WINDOW
        )
    except Exception:
        pass
    return False


def download_to(url: str, dest: Path, *, timeout: float = DOWNLOAD_TIMEOUT_S) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".partial")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp, partial.open("wb") as out:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
    partial.replace(dest)
    unblock_windows_file(dest)
    return dest


def schedule_replace_and_restart(
    current_exe: Path,
    new_exe: Path,
    *,
    pid: Optional[int] = None,
) -> Path:
    """Write a helper .bat that replaces the running exe after this process exits."""
    if os.name != "nt":
        raise RuntimeError("Self-update is only supported on Windows")
    current_exe = Path(current_exe).resolve()
    new_exe = Path(new_exe).resolve()
    if not new_exe.is_file():
        raise FileNotFoundError(str(new_exe))
    # Unblock before swap (MOTW may appear on some Windows builds)
    unblock_windows_file(new_exe)
    pid = int(pid if pid is not None else os.getpid())

    bat = Path(tempfile.gettempdir()) / f"civ4pbem_update_{pid}.bat"
    # Escape for cmd: wrap paths in quotes; avoid parentheses issues in echo.
    cur = str(current_exe)
    new = str(new_exe)
    bat_text = f"""@echo off
setlocal
set PID={pid}
set "NEW={new}"
set "CUR={cur}"
:wait
tasklist /FI "PID eq %PID%" 2>NUL | find "%PID%" >NUL
if not errorlevel 1 (
  timeout /t 1 /nobreak >NUL
  goto wait
)
timeout /t 1 /nobreak >NUL
powershell -NoProfile -Command "Unblock-File -LiteralPath '%NEW%'" >NUL 2>&1
del /F /Q "%CUR%" >NUL 2>&1
move /Y "%NEW%" "%CUR%" >NUL
if errorlevel 1 (
  copy /Y "%NEW%" "%CUR%" >NUL
)
powershell -NoProfile -Command "Unblock-File -LiteralPath '%CUR%'" >NUL 2>&1
start "" "%CUR%"
del /F /Q "%~f0" >NUL 2>&1
"""
    bat.write_text(bat_text, encoding="utf-8")
    # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP so bat survives our exit
    creationflags = 0x00000008 | 0x00000200
    subprocess.Popen(
        ["cmd.exe", "/c", str(bat)],
        close_fds=True,
        creationflags=creationflags,
        cwd=str(Path(tempfile.gettempdir())),
    )
    logger.info("Scheduled update helper: %s (pid=%s)", bat, pid)
    return bat


def default_download_path(exe_name: str = "Civ4PBEMManager.exe") -> Path:
    safe = Path(exe_name).name or "Civ4PBEMManager.exe"
    return Path(tempfile.gettempdir()) / f"Civ4PBEMManager_new_{os.getpid()}{Path(safe).suffix}"


def truncate_release_notes(body: str, max_chars: int = 1200) -> str:
    text = (body or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"
