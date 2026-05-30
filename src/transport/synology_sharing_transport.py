"""
Synology Sharing Links transport.

Uses Synology's File Station sharing link feature:
- Upload via File Request link (password-protected)
- Download via shared folder link (password-protected, gofile.me style)

This transport works with the web-based sharing links that Synology DSM provides,
NOT the full File Station API. This means:
- No need for a NAS user account
- Works over the internet via QuickConnect or DDNS
- Only needs the sharing URLs + password

Upload link format: https://your.synology.me:5001/sharing/XXXXXXX
Download link format: https://gofile.me/XXXXX/XXXXXXX (or direct Synology sharing link)
"""
import logging
import ssl
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import urllib.request
import urllib.error
import urllib.parse

from src.transport.base import BaseTransport

logger = logging.getLogger(__name__)


class SynologySharingTransport(BaseTransport):
    """Transport via Synology File Station sharing links.

    Config:
        upload_url: The File Request URL for uploading saves
        download_url: The shared folder URL for downloading saves
        password: Password for both upload and download links
    """

    def __init__(self, upload_url: str = "", download_url: str = "",
                 password: str = ""):
        self.upload_url = upload_url.rstrip("/")
        self.download_url = download_url.rstrip("/")
        self.password = password
        self._connected = False
        # Synology self-signed certs — create permissive SSL context
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Test that the upload URL is reachable."""
        if not self.upload_url:
            logger.error("Synology sharing: upload URL not configured")
            return False
        try:
            req = urllib.request.Request(self.upload_url, method="GET")
            urllib.request.urlopen(req, timeout=15, context=self._ssl_ctx)
            self._connected = True
            logger.info("Synology sharing transport: connection OK")
            return True
        except urllib.error.HTTPError as e:
            # A response (even error) means the server is reachable
            if e.code in (200, 401, 403, 404):
                self._connected = True
                return True
            logger.error(f"Synology sharing connection failed: HTTP {e.code}")
            return False
        except Exception as e:
            logger.error(f"Synology sharing connection failed: {e}")
            return False

    def disconnect(self):
        self._connected = False

    def upload(self, local_path: Path, remote_filename: str, game_name: str,
               to_email: str = "") -> bool:
        """Upload a file via the Synology File Request sharing link.

        Synology File Request links accept multipart/form-data POST with:
        - The file in a 'file' field
        - Password verification
        - The sharing_id extracted from the URL
        """
        if not self.upload_url:
            logger.error("Upload URL not configured")
            return False

        try:
            sharing_id = self._extract_sharing_id(self.upload_url)
            if not sharing_id:
                logger.error(f"Cannot extract sharing ID from: {self.upload_url}")
                return False

            parsed = urlparse(self.upload_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            with open(local_path, "rb") as f:
                file_data = f.read()

            # Try Synology File Station Sharing Upload API
            upload_api_url = f"{base_url}/webapi/entry.cgi"
            boundary = "----Civ4PBEMBoundary"
            body = self._build_multipart(
                boundary=boundary,
                fields={
                    "api": "SYNO.FileStation.Sharing.Upload",
                    "method": "upload",
                    "version": "1",
                    "sharing_id": sharing_id,
                    "password": self.password,
                },
                file_field="file",
                filename=remote_filename,
                file_data=file_data,
            )

            req = urllib.request.Request(upload_api_url, data=body, method="POST")
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

            response = urllib.request.urlopen(req, timeout=120, context=self._ssl_ctx)
            result = response.read().decode("utf-8", errors="replace")

            if '"success":true' in result or response.status == 200:
                logger.info(f"Synology sharing: uploaded {remote_filename}")
                self._connected = True
                return True

            # Fallback: POST directly to the sharing URL
            return self._upload_fallback(local_path, remote_filename)

        except Exception as e:
            logger.error(f"Synology sharing upload failed: {e}")
            return self._upload_fallback(local_path, remote_filename)

    def _upload_fallback(self, local_path: Path, remote_filename: str) -> bool:
        """Fallback: POST file directly to the sharing URL as multipart form."""
        try:
            with open(local_path, "rb") as f:
                file_data = f.read()

            boundary = "----Civ4PBEMUpload"
            body = self._build_multipart(
                boundary=boundary,
                fields={"password": self.password},
                file_field="file",
                filename=remote_filename,
                file_data=file_data,
            )

            req = urllib.request.Request(self.upload_url, data=body, method="POST")
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

            response = urllib.request.urlopen(req, timeout=120, context=self._ssl_ctx)
            if 200 <= response.status < 400:
                logger.info(f"Synology sharing (fallback): uploaded {remote_filename}")
                self._connected = True
                return True
            return False
        except Exception as e:
            logger.error(f"Synology sharing fallback upload failed: {e}")
            return False

    def download(self, remote_filename: str, local_path: Path, game_name: str) -> bool:
        """Download a file from the Synology shared folder link."""
        if not self.download_url:
            logger.error("Download URL not configured")
            return False

        try:
            # Try direct file access with password
            file_urls = [
                f"{self.download_url}/{remote_filename}?password={urllib.parse.quote(self.password)}",
                f"{self.download_url}/{remote_filename}",
            ]

            for url in file_urls:
                try:
                    req = urllib.request.Request(url, method="GET")
                    response = urllib.request.urlopen(req, timeout=60, context=self._ssl_ctx)
                    data = response.read()

                    # Verify it's a file (not an HTML error page)
                    if len(data) > 100 and not data[:50].startswith(b"<!DOCTYPE"):
                        with open(local_path, "wb") as f:
                            f.write(data)
                        logger.info(f"Synology sharing: downloaded {remote_filename}")
                        self._connected = True
                        return True
                except (urllib.error.HTTPError, urllib.error.URLError):
                    continue

            # Try Synology sharing download API
            return self._download_via_api(remote_filename, local_path)

        except Exception as e:
            logger.error(f"Synology sharing download failed: {e}")
            return False

    def _download_via_api(self, remote_filename: str, local_path: Path) -> bool:
        """Try downloading via Synology sharing API endpoint."""
        try:
            sharing_id = self._extract_sharing_id(self.download_url)
            if not sharing_id:
                return False

            parsed = urlparse(self.download_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            api_url = (
                f"{base_url}/webapi/entry.cgi?"
                f"api=SYNO.FileStation.Sharing.Download&method=download&version=1"
                f"&sharing_id={sharing_id}"
                f"&password={urllib.parse.quote(self.password)}"
                f"&filename={urllib.parse.quote(remote_filename)}"
            )

            req = urllib.request.Request(api_url, method="GET")
            response = urllib.request.urlopen(req, timeout=60, context=self._ssl_ctx)
            data = response.read()

            if len(data) > 0 and not data[:50].startswith(b"<!DOCTYPE"):
                with open(local_path, "wb") as f:
                    f.write(data)
                logger.info(f"Synology sharing (API): downloaded {remote_filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"Synology sharing API download failed: {e}")
            return False

    def list_files(self, game_name: str) -> list[str]:
        """Not reliably supported via sharing links. Returns empty."""
        logger.debug("Synology sharing: list_files not available via sharing links")
        return []

    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        """Cannot reliably check via sharing links."""
        return False

    def _extract_sharing_id(self, url: str) -> Optional[str]:
        """Extract the sharing ID from URL path."""
        parts = url.rstrip("/").split("/")
        return parts[-1] if parts else None

    def _build_multipart(self, boundary: str, fields: dict,
                          file_field: str = "", filename: str = "",
                          file_data: bytes = b"") -> bytes:
        """Build multipart/form-data body."""
        lines = []
        for key, value in fields.items():
            lines.append(f"--{boundary}".encode())
            lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
            lines.append(b"")
            lines.append(value.encode() if isinstance(value, str) else value)

        if file_field and file_data:
            lines.append(f"--{boundary}".encode())
            lines.append(
                f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode()
            )
            lines.append(b"Content-Type: application/octet-stream")
            lines.append(b"")
            lines.append(file_data)

        lines.append(f"--{boundary}--".encode())
        lines.append(b"")
        return b"\r\n".join(lines)
