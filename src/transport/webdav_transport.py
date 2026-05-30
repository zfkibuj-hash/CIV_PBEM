"""
WebDAV transport implementation for Synology NAS Cloud access.
Uses simple HTTP requests (no extra library needed beyond requests).
"""
import logging
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

import urllib.request
import urllib.error
import base64

from src.transport.base import BaseTransport

logger = logging.getLogger(__name__)


class WebDAVTransport(BaseTransport):
    """Transport via WebDAV (works with Synology, Nextcloud, etc.)."""

    def __init__(self, host: str, port: int = 5006, username: str = "",
                 password: str = "", remote_dir: str = "/civ4pbem",
                 use_https: bool = True, ignore_ssl: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.use_https = use_https
        self._connected = False
        # SSL context for self-signed certs
        import ssl
        if ignore_ssl:
            self._ssl_ctx = ssl.create_default_context()
            self._ssl_ctx.check_hostname = False
            self._ssl_ctx.verify_mode = ssl.CERT_NONE
        else:
            self._ssl_ctx = None

    @property
    def base_url(self) -> str:
        scheme = "https" if self.use_https else "http"
        return f"{scheme}://{self.host}:{self.port}"

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _auth_header(self) -> str:
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _request(self, method: str, path: str, data: Optional[bytes] = None) -> Optional[bytes]:
        """Make an HTTP request to the WebDAV server."""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", self._auth_header())

        try:
            with urllib.request.urlopen(req, timeout=30, context=self._ssl_ctx) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            logger.error(f"WebDAV {method} {path} failed: HTTP {e.code}")
            return None
        except Exception as e:
            logger.error(f"WebDAV {method} {path} failed: {e}")
            return None

    def connect(self) -> bool:
        """Test connection by doing a PROPFIND on root."""
        try:
            url = f"{self.base_url}{self.remote_dir}/"
            req = urllib.request.Request(url, method="PROPFIND")
            req.add_header("Authorization", self._auth_header())
            req.add_header("Depth", "0")

            try:
                urllib.request.urlopen(req, timeout=30, context=self._ssl_ctx)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Try to create the directory
                    self._ensure_dir(self.remote_dir)
                elif e.code == 207:  # Multi-Status is success for PROPFIND
                    pass
                else:
                    raise

            self._connected = True
            logger.info(f"Connected to WebDAV {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"WebDAV connection failed: {e}")
            self._connected = False
            return False

    def disconnect(self):
        self._connected = False

    def upload(self, local_path: Path, remote_filename: str, game_name: str) -> bool:
        if not self._connected:
            if not self.connect():
                return False
        try:
            game_dir = f"{self.remote_dir}/{game_name}"
            self._ensure_dir(game_dir)
            remote_path = f"{game_dir}/{remote_filename}"

            with open(local_path, "rb") as f:
                data = f.read()

            url = f"{self.base_url}{remote_path}"
            req = urllib.request.Request(url, data=data, method="PUT")
            req.add_header("Authorization", self._auth_header())
            urllib.request.urlopen(req, timeout=60, context=self._ssl_ctx)

            logger.info(f"Uploaded {remote_filename} to WebDAV {game_dir}")
            return True
        except Exception as e:
            logger.error(f"WebDAV upload failed: {e}")
            return False

    def download(self, remote_filename: str, local_path: Path, game_name: str) -> bool:
        if not self._connected:
            if not self.connect():
                return False
        try:
            remote_path = f"{self.remote_dir}/{game_name}/{remote_filename}"
            result = self._request("GET", remote_path)
            if result is None:
                return False

            with open(local_path, "wb") as f:
                f.write(result)

            logger.info(f"Downloaded {remote_filename} from WebDAV")
            return True
        except Exception as e:
            logger.error(f"WebDAV download failed: {e}")
            return False

    def list_files(self, game_name: str) -> list[str]:
        if not self._connected:
            if not self.connect():
                return []
        try:
            path = f"{self.remote_dir}/{game_name}/"
            url = f"{self.base_url}{path}"
            req = urllib.request.Request(url, method="PROPFIND")
            req.add_header("Authorization", self._auth_header())
            req.add_header("Depth", "1")

            try:
                with urllib.request.urlopen(req, timeout=30, context=self._ssl_ctx) as response:
                    body = response.read()
            except urllib.error.HTTPError as e:
                if e.code == 207:
                    body = e.read()
                else:
                    return []

            # Parse WebDAV XML response
            root = ElementTree.fromstring(body)
            ns = {"d": "DAV:"}
            files = []
            for response_elem in root.findall("d:response", ns):
                href = response_elem.find("d:href", ns)
                if href is not None and href.text:
                    filename = href.text.rstrip("/").split("/")[-1]
                    if filename and filename != game_name:
                        files.append(filename)
            return files
        except Exception as e:
            logger.error(f"WebDAV list failed: {e}")
            return []

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        files = self.list_files(game_name)
        return remote_filename in files

    def _ensure_dir(self, path: str):
        """Create directory via MKCOL."""
        dirs = path.strip("/").split("/")
        current = ""
        for d in dirs:
            current += f"/{d}"
            try:
                url = f"{self.base_url}{current}/"
                req = urllib.request.Request(url, method="MKCOL")
                req.add_header("Authorization", self._auth_header())
                urllib.request.urlopen(req, timeout=15, context=self._ssl_ctx)
            except urllib.error.HTTPError:
                pass  # Already exists or other error
            except Exception:
                pass
