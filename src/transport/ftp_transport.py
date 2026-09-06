"""
FTP transport.

Downloads use Windows System32 curl.exe only (hard 8s). Never ftplib RETR —
ftplib hangs for minutes on some PCs while curl finishes in <1s.

Uploads: curl first, short ftplib STOR fallback (upload already worked for user).
"""
from __future__ import annotations

import ftplib
import logging
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from src.transport.base import (
    BaseTransport, game_remote_dir, normalize_remote_listing,
    sanitize_filename, sanitize_game_name,
)

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 4
_CURL_MAX = 6
_UPLOAD_MAX = 15


def _find_curl() -> Optional[str]:
    """Prefer System32 curl — frozen exe often has a broken PATH."""
    windir = os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"
    for candidate in (
        Path(windir) / "System32" / "curl.exe",
        Path(windir) / "SysWOW64" / "curl.exe",
    ):
        if candidate.is_file():
            return str(candidate)
    import shutil
    return shutil.which("curl") or shutil.which("curl.exe")


class FTPTransport(BaseTransport):
    """FTP via curl for GET/PUT; ftplib only as upload/list last resort."""

    def __init__(self, host: str, port: int = 21, username: str = "",
                 password: str = "", remote_dir: str = "/civ4pbem",
                 use_tls: bool = False, ignore_ssl: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.use_tls = use_tls
        self.ignore_ssl = ignore_ssl
        self._ftp = None
        self.last_error: str = ""
        self.last_step: str = ""

    @property
    def is_connected(self) -> bool:
        return True

    def _remote_path(self, remote_filename: str, game_name: str) -> str:
        remote_filename = sanitize_filename(remote_filename)
        game_name = sanitize_game_name(game_name)
        base = game_remote_dir(self.remote_dir, game_name).rstrip("/")
        return f"{base}/{remote_filename}"

    def _curl_url(self, remote_path: str) -> str:
        host = self.host
        port = int(self.port or 21)
        parts = [quote(p, safe="") for p in remote_path.strip("/").split("/") if p]
        enc = "/" + "/".join(parts)
        if port != 21:
            return f"ftp://{host}:{port}{enc}"
        return f"ftp://{host}{enc}"

    def _curl_flags(self) -> list[str]:
        # Hidden console on Windows
        return []

    def _run_curl(self, args: list[str], timeout: int) -> subprocess.CompletedProcess:
        curl = _find_curl()
        if not curl:
            raise FileNotFoundError("curl.exe not found in System32")
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        cmd = [curl, "-sS", "--fail", *args]
        # Log without credentials
        safe = []
        skip_next = False
        for a in cmd[1:]:
            if skip_next:
                safe.append("***")
                skip_next = False
                continue
            if a in ("-u", "--user"):
                safe.append(a)
                skip_next = True
                continue
            safe.append(a)
        logger.info("curl %s", " ".join(safe))
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=creationflags,
        )

    def _curl_get(self, remote_path: str) -> Optional[bytes]:
        self.last_step = f"curl-get:{remote_path}"
        self.last_error = ""
        url = self._curl_url(remote_path)
        tmp = Path(tempfile.gettempdir()) / f"civ4pbem_{int(time.time() * 1000)}.bin"
        t0 = time.perf_counter()
        try:
            proc = self._run_curl(
                [
                    "--connect-timeout", str(_CONNECT_TIMEOUT),
                    "--max-time", str(_CURL_MAX),
                    "-u", f"{self.username}:{self.password}",
                    url,
                    "-o", str(tmp),
                ],
                timeout=_CURL_MAX + 2,
            )
            elapsed = time.perf_counter() - t0
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
                self.last_error = f"curl: {err[:180]}"
                logger.warning("curl GET %s fail %.2fs: %s", remote_path, elapsed, err[:180])
                return None
            data = tmp.read_bytes()
            logger.info("curl GET %s ok %d bytes %.2fs", remote_path, len(data), elapsed)
            return data
        except subprocess.TimeoutExpired:
            self.last_error = f"curl timeout >{_CURL_MAX}s"
            logger.error(self.last_error)
            return None
        except Exception as e:
            self.last_error = str(e)
            logger.error("curl GET error: %s", e)
            return None
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    def _curl_put(self, local_path: Path, remote_path: str) -> bool:
        self.last_step = f"curl-put:{remote_path}"
        url = self._curl_url(remote_path)
        t0 = time.perf_counter()
        try:
            proc = self._run_curl(
                [
                    "--connect-timeout", str(_CONNECT_TIMEOUT),
                    "--max-time", str(_UPLOAD_MAX),
                    "-u", f"{self.username}:{self.password}",
                    "-T", str(local_path),
                    url,
                ],
                timeout=_UPLOAD_MAX + 3,
            )
            elapsed = time.perf_counter() - t0
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
                self.last_error = f"curl put: {err[:180]}"
                logger.warning("curl PUT %s fail %.2fs: %s", remote_path, elapsed, err[:180])
                return False
            logger.info("curl PUT %s ok %.2fs", remote_path, elapsed)
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error("curl PUT error: %s", e)
            return False

    def connect(self) -> bool:
        self.last_error = ""
        return True

    def disconnect(self):
        self._ftp = None

    def list_files(self, game_name: str) -> list[str]:
        # Listing is unreliable — Check must not depend on it.
        self.last_error = "NLST disabled — use named RETR"
        return []

    def fetch_turns_log_bytes(self, game_name: str) -> Optional[bytes]:
        return self.retr_bytes(f"{sanitize_game_name(game_name)}_turns.json", game_name)

    def fetch_state_bytes(self, game_name: str) -> Optional[bytes]:
        return self.retr_bytes(f"{sanitize_game_name(game_name)}_state.json", game_name)

    def retr_bytes(self, remote_filename: str, game_name: str) -> Optional[bytes]:
        """Download via curl only. No ftplib — it hangs on affected PCs."""
        remote_filename = sanitize_filename(remote_filename)
        game_name = sanitize_game_name(game_name)
        path = self._remote_path(remote_filename, game_name)

        data = self._curl_get(path)
        if data is not None:
            return data

        flat = f"{(self.remote_dir or '').rstrip('/')}/{remote_filename}"
        if flat != path:
            data = self._curl_get(flat)
            if data is not None:
                return data

        if not self.last_error:
            self.last_error = f"curl could not get {remote_filename}"
        return None

    def upload(self, local_path: Path, remote_filename: str, game_name: str) -> bool:
        remote_filename = sanitize_filename(remote_filename)
        game_name = sanitize_game_name(game_name)
        path = self._remote_path(remote_filename, game_name)

        if self._curl_put(local_path, path):
            return True

        # Short STOR fallback (uploads already work for the user via ftplib)
        box: dict = {"ok": False}

        def _stor():
            ftp = ftplib.FTP()
            try:
                ftp.connect(self.host, self.port, timeout=_CONNECT_TIMEOUT)
                ftp.login(self.username, self.password)
                ftp.set_pasv(True)
                ftp.timeout = 5
                game_dir = game_remote_dir(self.remote_dir, game_name)
                self._ensure_dir(ftp, game_dir)
                ftp.cwd(game_dir)
                with open(local_path, "rb") as f:
                    ftp.storbinary(f"STOR {remote_filename}", f)
                box["ok"] = True
            except Exception as e:
                box["err"] = e
            finally:
                try:
                    ftp.quit()
                except Exception:
                    try:
                        ftp.close()
                    except Exception:
                        pass

        thread = threading.Thread(target=_stor, daemon=True)
        thread.start()
        thread.join(timeout=10)
        if thread.is_alive() or not box.get("ok"):
            self.last_error = str(box.get("err") or self.last_error or "upload hung/failed")
            return False
        return True

    def download(
        self,
        remote_filename: str,
        local_path: Path,
        game_name: str,
        *,
        timeout: float | None = None,
        **kwargs,
    ) -> bool:
        data = self.retr_bytes(remote_filename, game_name)
        if data is None:
            return False
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        return False

    def delete(self, remote_filename: str, game_name: str) -> bool:
        self.last_error = "delete via curl not implemented"
        return False

    def _ensure_dir(self, ftp: ftplib.FTP, path: str):
        current = ""
        for d in path.strip("/").split("/"):
            if not d:
                continue
            current += f"/{d}"
            try:
                ftp.cwd(current)
            except ftplib.error_perm:
                try:
                    ftp.mkd(current)
                except ftplib.error_perm:
                    pass
                try:
                    ftp.cwd(current)
                except ftplib.error_perm:
                    pass
