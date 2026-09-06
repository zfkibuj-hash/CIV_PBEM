"""
SFTP transport implementation using paramiko.
"""
import logging
import stat
from pathlib import Path
from typing import Optional

import paramiko

from src.transport.base import (
    BaseTransport, game_remote_dir, normalize_remote_listing,
    sanitize_filename, sanitize_game_name,
)

logger = logging.getLogger(__name__)


class SFTPTransport(BaseTransport):
    """Transport via SFTP (SSH File Transfer Protocol)."""

    def __init__(self, host: str, port: int = 22, username: str = "",
                 password: str = "", remote_dir: str = "/civ4pbem",
                 key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.key_path = key_path
        self._ssh: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None

    @property
    def is_connected(self) -> bool:
        if self._ssh is None or self._sftp is None:
            return False
        try:
            self._sftp.stat(".")
            return True
        except Exception:
            return False

    def connect(self) -> bool:
        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.load_system_host_keys()
            self._ssh.set_missing_host_key_policy(paramiko.WarningPolicy())

            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": 30,
            }

            if self.key_path:
                connect_kwargs["key_filename"] = self.key_path
            else:
                connect_kwargs["password"] = self.password

            self._ssh.connect(**connect_kwargs)
            self._sftp = self._ssh.open_sftp()

            self._ensure_dir(self.remote_dir)
            logger.info(f"Connected to SFTP {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"SFTP connection failed: {e}")
            self._ssh = None
            self._sftp = None
            return False

    def disconnect(self):
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._ssh:
            try:
                self._ssh.close()
            except Exception:
                pass
            self._ssh = None

    def _game_dir(self, game_name: str) -> str:
        return game_remote_dir(self.remote_dir, game_name)

    def _remote_path(self, game_name: str, remote_filename: str) -> str:
        return f"{self._game_dir(sanitize_game_name(game_name))}/{sanitize_filename(remote_filename)}"

    def upload(self, local_path: Path, remote_filename: str, game_name: str) -> bool:
        if not self.is_connected:
            if not self.connect():
                return False
        try:
            remote_filename = sanitize_filename(remote_filename)
            game_name = sanitize_game_name(game_name)
            game_dir = self._game_dir(game_name)
            self._ensure_dir(game_dir)
            remote_path = f"{game_dir}/{remote_filename}"
            self._sftp.put(str(local_path), remote_path)
            logger.info(f"Uploaded {remote_filename} to {game_dir}")
            return True
        except Exception as e:
            logger.error(f"SFTP upload failed: {e}")
            return False

    def download(self, remote_filename: str, local_path: Path, game_name: str, **kwargs) -> bool:
        if not self.is_connected:
            if not self.connect():
                return False
        try:
            remote_filename = sanitize_filename(remote_filename)
            game_name = sanitize_game_name(game_name)
            remote_path = self._remote_path(game_name, remote_filename)
            self._sftp.get(remote_path, str(local_path))
            logger.info(f"Downloaded {remote_filename} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"SFTP download failed: {e}")
            return False

    def list_files(self, game_name: str) -> list[str]:
        if not self.is_connected:
            if not self.connect():
                return []
        try:
            game_name = sanitize_game_name(game_name)
            game_dir = self._game_dir(game_name)
            entries = self._sftp.listdir_attr(game_dir)
            return normalize_remote_listing(
                [e.filename for e in entries if not stat.S_ISDIR(e.st_mode)]
            )
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"SFTP list failed: {e}")
            return []

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        files = self.list_files(game_name)
        return remote_filename in files

    def delete(self, remote_filename: str, game_name: str) -> bool:
        if not self.is_connected:
            if not self.connect():
                return False
        try:
            remote_filename = sanitize_filename(remote_filename)
            game_name = sanitize_game_name(game_name)
            remote_path = self._remote_path(game_name, remote_filename)
            self._sftp.remove(remote_path)
            logger.info("SFTP deleted %s", remote_path)
            return True
        except Exception as e:
            logger.error("SFTP delete failed: %s", e)
            return False

    def _ensure_dir(self, path: str):
        """Create directory on SFTP if it doesn't exist."""
        dirs = path.strip("/").split("/")
        current = ""
        for d in dirs:
            current += f"/{d}"
            try:
                self._sftp.stat(current)
            except FileNotFoundError:
                try:
                    self._sftp.mkdir(current)
                except Exception:
                    pass
