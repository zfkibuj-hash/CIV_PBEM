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


def ftp_list_urls(host: str, port: int, remote_dir: str) -> list[str]:
    """Directory URLs for curl LIST. Trailing slash is required (else RETR)."""
    rel = ftp_url(host, port, remote_dir)
    if not rel.endswith("/"):
        rel += "/"
    parts = [quote(p, safe="") for p in (remote_dir or "").strip("/").split("/") if p]
    port_i = int(port or 21)
    hostport = f"{host}:{port_i}" if port_i != 21 else host
    abs_url = f"ftp://{hostport}/%2f{'/'.join(parts)}/" if parts else f"ftp://{hostport}/%2f/"
    urls = [rel]
    if abs_url not in urls:
        urls.append(abs_url)
    return urls


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
    create_dirs: bool = False,
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
    ]
    if create_dirs:
        cmd.append("--ftp-create-dirs")
    cmd.extend(["-T", str(local_path), url])
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


def parse_ftp_list_text(text: str) -> list[str]:
    """Basenames from FTP LIST (Unix or DOS). Skips directories."""
    names: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("total "):
            continue
        if line[0] in "dD" and (len(line) == 1 or line[1] in "-rwx"):
            continue
        if "<DIR>" in line.upper():
            continue
        parts = line.split()
        if not parts:
            continue
        if line[0] in "-l" and len(parts) >= 9:
            name = line.split(None, 8)[-1]
        else:
            name = parts[-1]
        name = Path(str(name).replace("\\", "/")).name
        if name and name not in (".", ".."):
            names.append(name)
    if not names:
        for raw in (text or "").splitlines():
            n = Path(raw.strip().replace("\\", "/")).name
            if n.lower().endswith(".civbeyondswordsave"):
                names.append(n)
    return names


def curl_list(
    *,
    host: str,
    port: int = 21,
    username: str,
    password: str,
    remote_dir: str,
    max_time: int = 8,
) -> tuple[list[str], str]:
    """FTP LIST via curl (not NLST). Empty list + error on failure/timeout."""
    curl = find_curl()
    if not curl:
        return [], "curl.exe not found (System32)"
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    last_err = ""
    for url in ftp_list_urls(host, port, remote_dir):
        cmd = [
            curl, "-sS",
            "--connect-timeout", str(_CONNECT),
            "--max-time", str(max_time),
            "-u", f"{username}:{password}",
            url,
        ]
        logger.info("curl LIST %s (max %ss)", url.split("@")[-1] if "@" in url else url, max_time)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=max_time + 2, creationflags=flags,
            )
        except subprocess.TimeoutExpired:
            last_err = f"timeout >{max_time}s"
            logger.error("curl LIST timeout >%ss", max_time)
            continue
        except Exception as e:
            last_err = str(e)
            logger.exception("curl LIST error")
            continue
        if proc.returncode != 0:
            last_err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()[:200]
            logger.warning("curl LIST fail: %s", last_err)
            continue
        names = parse_ftp_list_text(proc.stdout or "")
        if names:
            logger.info("curl LIST ok %d names", len(names))
            return names, ""
        last_err = "empty listing"
    return [], last_err or "empty listing"


def curl_delete(
    *,
    host: str,
    port: int = 21,
    username: str,
    password: str,
    remote_dir: str,
    filename: str,
    max_time: int = 8,
) -> tuple[bool, str]:
    """FTP DELE via curl QUOTE. Filename must be a basename."""
    name = Path(str(filename or "")).name
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        return False, "bad filename"
    curl = find_curl()
    if not curl:
        return False, "curl.exe not found"
    url = ftp_list_urls(host, port, remote_dir)[0]
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    cmd = [
        curl, "-sS",
        "--connect-timeout", str(_CONNECT),
        "--max-time", str(max_time),
        "-u", f"{username}:{password}",
        "-Q", f"DELE {name}",
        url,
    ]
    logger.info("curl DELE %s", name)
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=max_time + 2, creationflags=flags,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout >{max_time}s"
    except Exception as e:
        return False, str(e)
    if proc.returncode == 0:
        return True, ""
    # Some hosts want an absolute path in DELE
    abs_name = f"{(remote_dir or '').rstrip('/')}/{name}".replace("//", "/")
    cmd_abs = [
        curl, "-sS",
        "--connect-timeout", str(_CONNECT),
        "--max-time", str(max_time),
        "-u", f"{username}:{password}",
        "-Q", f"DELE {abs_name}",
        url,
    ]
    try:
        proc2 = subprocess.run(
            cmd_abs, capture_output=True, text=True,
            timeout=max_time + 2, creationflags=flags,
        )
    except Exception as e:
        err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        return False, err[:200] or str(e)
    if proc2.returncode != 0:
        err = (proc2.stderr or proc2.stdout or proc.stderr or f"exit {proc2.returncode}").strip()
        return False, err[:200] or f"curl exit {proc2.returncode}"
    return True, ""
