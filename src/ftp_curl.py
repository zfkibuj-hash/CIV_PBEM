"""Pure FTP via Windows curl.exe — no Qt, no ftplib, no threads.

Safe to call from a QThread worker. Never touch GUI objects here.
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

_CONNECT = 4
_MAX_TIME = 5


def find_curl() -> Optional[str]:
    windir = os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"
    for candidate in (
        Path(windir) / "System32" / "curl.exe",
        Path(windir) / "SysWOW64" / "curl.exe",
    ):
        if candidate.is_file():
            return str(candidate)
    import shutil
    return shutil.which("curl") or shutil.which("curl.exe")


def ftp_url(host: str, port: int, remote_path: str) -> str:
    parts = [quote(p, safe="") for p in remote_path.strip("/").split("/") if p]
    enc = "/" + "/".join(parts)
    port = int(port or 21)
    if port != 21:
        return f"ftp://{host}:{port}{enc}"
    return f"ftp://{host}{enc}"


def curl_get(
    *,
    host: str,
    port: int = 21,
    username: str,
    password: str,
    remote_path: str,
    max_time: int = _MAX_TIME,
) -> tuple[Optional[bytes], str]:
    """Download one FTP file. Returns (data, error). error empty on success."""
    curl = find_curl()
    if not curl:
        return None, "curl.exe not found (System32)"

    url = ftp_url(host, port, remote_path)
    tmp = Path(tempfile.gettempdir()) / f"civ4pbem_{os.getpid()}_{int(time.time()*1000)}.bin"
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    cmd = [
        curl, "-sS", "--fail",
        "--connect-timeout", str(_CONNECT),
        "--max-time", str(max_time),
        "-u", f"{username}:{password}",
        url, "-o", str(tmp),
    ]
    logger.info("curl GET %s (max %ss)", remote_path, max_time)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=max_time + 2, creationflags=flags,
        )
        dt = time.perf_counter() - t0
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
            logger.warning("curl GET fail %.2fs: %s", dt, err[:200])
            return None, err[:200] or f"curl exit {proc.returncode}"
        data = tmp.read_bytes()
        logger.info("curl GET ok %d bytes %.2fs", len(data), dt)
        return data, ""
    except subprocess.TimeoutExpired:
        logger.error("curl GET timeout >%ss path=%s", max_time, remote_path)
        return None, f"timeout >{max_time}s"
    except Exception as e:
        logger.exception("curl GET error")
        return None, str(e)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass


def curl_put(
    *,
    host: str,
    port: int = 21,
    username: str,
    password: str,
    remote_path: str,
    local_path: Path,
    max_time: int = 15,
) -> tuple[bool, str]:
    curl = find_curl()
    if not curl:
        return False, "curl.exe not found"
    url = ftp_url(host, port, remote_path)
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    cmd = [
        curl, "-sS", "--fail",
        "--connect-timeout", str(_CONNECT),
        "--max-time", str(max_time),
        "-u", f"{username}:{password}",
        "-T", str(local_path),
        url,
    ]
    logger.info("curl PUT %s", remote_path)
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=max_time + 3, creationflags=flags,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
            return False, err[:200]
        return True, ""
    except Exception as e:
        return False, str(e)


def pull_game_state_json(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    remote_dir: str,
    game_name: str,
) -> tuple[Optional[dict], str, str]:
    """Fetch turns.json (then state.json). Max ~6s total. Returns (data, file, err)."""
    import json

    base = f"{(remote_dir or '/civ4pbem').rstrip('/')}/{game_name}"
    last_err = ""
    best: Optional[dict] = None
    best_name = ""
    best_rank = (-1, -1, -1)
    from src.models.game import Game
    for name in (f"{game_name}_turns.json", f"{game_name}_state.json"):
        path = f"{base}/{name}"
        raw, err = curl_get(
            host=host, port=port, username=username, password=password,
            remote_path=path, max_time=4,
        )
        if raw is None:
            last_err = err
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            last_err = f"bad json: {e}"
            continue
        if not isinstance(data, dict):
            last_err = "not an object"
            continue
        has_hist = bool(
            data.get("history")
            or (isinstance(data.get("game"), dict) and data["game"].get("history"))
        )
        if not has_hist:
            last_err = "empty history in file"
            continue
        rank = Game.payload_state_rank(data)
        if rank > best_rank:
            best_rank = rank
            best = data
            best_name = name
    if best is not None:
        return best, best_name, ""
    return None, "", last_err or "no turns/state on FTP"
