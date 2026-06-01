"""
FTP transport implementation.
"""
import ftplib
import logging
from pathlib import Path
from typing import Optional

from src.transport.base import BaseTransport

logger = logging.getLogger(__name__)


class FTPTransport(BaseTransport):
    """Transport via FTP (plain or TLS)."""

    def __init__(self, host: str, port: int = 21, username: str = "",
                 password: str = "", remote_dir: str = "/civ4pbem",
                 use_tls: bool = False, ignore_ssl: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.use_tls = use_tls
        self.ignore_ssl = ignore_ssl
        self._ftp: Optional[ftplib.FTP] = None

    @property
    def is_connected(self) -> bool:
        if self._ftp is None:
            return False
        try:
            self._ftp.voidcmd("NOOP")
            return True
        except Exception:
            return False

    def connect(self) -> bool:
        try:
            if self.use_tls:
                import ssl
                if self.ignore_ssl:
                    ssl_ctx = ssl.create_default_context()
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode = ssl.CERT_NONE
                    self._ftp = ftplib.FTP_TLS(context=ssl_ctx)
                else:
                    self._ftp = ftplib.FTP_TLS()
            else:
                self._ftp = ftplib.FTP()

            self._ftp.connect(self.host, self.port, timeout=30)
            self._ftp.login(self.username, self.password)

            if self.use_tls:
                self._ftp.prot_p()

            # Ensure remote dir exists
            self._ensure_dir(self.remote_dir)
            logger.info(f"Connected to FTP {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            self._ftp = None
            return False

    def disconnect(self):
        if self._ftp:
            try:
                self._ftp.quit()
            except Exception:
                pass
            self._ftp = None

    def upload(self, local_path: Path, remote_filename: str, game_name: str) -> bool:
        if not self.is_connected:
            if not self.connect():
                return False
        try:
            game_dir = f"{self.remote_dir}/{game_name}"
            self._ensure_dir(game_dir)
            self._ftp.cwd(game_dir)

            with open(local_path, "rb") as f:
                self._ftp.storbinary(f"STOR {remote_filename}", f)

            logger.info(f"Uploaded {remote_filename} to {game_dir}")
            return True
        except Exception as e:
            logger.error(f"FTP upload failed: {e}")
            return False

    def download(self, remote_filename: str, local_path: Path, game_name: str) -> bool:
        if not self.is_connected:
            if not self.connect():
                return False
        try:
            game_dir = f"{self.remote_dir}/{game_name}"
            self._ftp.cwd(game_dir)

            with open(local_path, "wb") as f:
                self._ftp.retrbinary(f"RETR {remote_filename}", f.write)

            logger.info(f"Downloaded {remote_filename} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"FTP download failed: {e}")
            return False

    def list_files(self, game_name: str) -> list[str]:
        if not self.is_connected:
            if not self.connect():
                return []
        try:
            game_dir = f"{self.remote_dir}/{game_name}"
            self._ftp.cwd(game_dir)
            return self._ftp.nlst()
        except Exception as e:
            logger.error(f"FTP list failed: {e}")
            return []

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        files = self.list_files(game_name)
        return remote_filename in files

    def _ensure_dir(self, path: str):
        """Create directory on FTP if it doesn't exist."""
        dirs = path.strip("/").split("/")
        current = ""
        for d in dirs:
            current += f"/{d}"
            try:
                self._ftp.cwd(current)
            except ftplib.error_perm:
                try:
                    self._ftp.mkd(current)
                except ftplib.error_perm:
                    pass
