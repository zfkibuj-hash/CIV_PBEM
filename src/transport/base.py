"""
Base transport interface for file upload/download.
"""
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

# Allowed characters in filenames: alphanumeric, underscore, hyphen, dot
_SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9_\-\.]+$')


def sanitize_filename(filename: str) -> str:
    """Validate and sanitize a filename to prevent path traversal.

    Raises ValueError if filename contains dangerous patterns.
    Returns the sanitized filename (basename only, no directory components).
    """
    if not filename:
        raise ValueError("Empty filename")

    # Reject path traversal attempts - check BEFORE extracting basename
    if '..' in filename:
        raise ValueError(f"Unsafe filename rejected (path traversal): {filename!r}")
    if '/' in filename or '\\' in filename:
        raise ValueError(f"Unsafe filename rejected (directory separator): {filename!r}")

    # Extract basename (should be same as input if no separators)
    basename = Path(filename).name

    # Reject empty after stripping
    if not basename:
        raise ValueError(f"Filename resolves to empty: {filename!r}")

    # Reject filenames that don't match safe pattern
    if not _SAFE_FILENAME_RE.match(basename):
        raise ValueError(f"Filename contains disallowed characters: {filename!r}")

    return basename


def normalize_remote_listing(names: list[str]) -> list[str]:
    """FTP/SFTP often return full paths or '.'/'..' — keep plain basenames only."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in names or []:
        if not raw:
            continue
        name = Path(str(raw).replace("\\", "/")).name
        if not name or name in (".", ".."):
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def sanitize_game_name(game_name: str) -> str:
    """Validate and sanitize a game name used in remote paths.

    Raises ValueError if game_name contains dangerous patterns.
    """
    if not game_name:
        raise ValueError("Empty game name")

    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_\-]+$', game_name):
        raise ValueError(f"Game name contains disallowed characters: {game_name!r}")

    if '..' in game_name:
        raise ValueError(f"Unsafe game name rejected: {game_name!r}")

    return game_name


def is_game_remote_file(game_name: str, filename: str) -> bool:
    """True if filename belongs to a PBEM game on the server."""
    if not game_name or not filename:
        return False
    if filename == f"{game_name}.config":
        return True
    if filename == f"{game_name}_state.json":
        return True
    if filename == f"{game_name}_turns.json":
        return True
    if filename.startswith(f"{game_name}_notify_") and filename.endswith(".flag"):
        return True
    return (
        filename.startswith(f"{game_name}_T")
        or bool(re.match(rf"^\d+_{re.escape(game_name)}_T", filename))
    ) and filename.endswith(".CivBeyondSwordSave")


def game_remote_dir(remote_dir: str, game_name: str) -> str:
    """Per-game folder under the transport root."""
    return f"{remote_dir.rstrip('/')}/{sanitize_game_name(game_name)}"


class BaseTransport(ABC):
    """Abstract base class for all transport methods."""

    def __enter__(self):
        """Support context manager usage: auto-connect on enter."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager usage: auto-disconnect on exit."""
        try:
            self.disconnect()
        except Exception:
            pass
        return False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Returns True on success."""
        ...

    @abstractmethod
    def disconnect(self):
        """Close connection."""
        ...

    @abstractmethod
    def upload(self, local_path: Path, remote_filename: str, game_name: str) -> bool:
        """Upload a file to the remote storage. Returns True on success."""
        ...

    @abstractmethod
    def download(
        self, remote_filename: str, local_path: Path, game_name: str, **kwargs,
    ) -> bool:
        """Download a file from remote storage. Returns True on success."""
        ...

    @abstractmethod
    def list_files(self, game_name: str) -> list[str]:
        """List files available for a given game on remote."""
        ...

    @abstractmethod
    def file_exists(self, remote_filename: str, game_name: str) -> bool:
        """Check if a specific file exists on remote."""
        ...

    def delete(self, remote_filename: str, game_name: str) -> bool:
        """Delete a remote file. Returns True on success."""
        return False

    def purge_game(self, game_name: str) -> tuple[bool, int]:
        """Delete all remote files for one game. Returns (success, count)."""
        deleted = 0
        failed = 0
        for name in self.list_files(game_name):
            if self.delete(name, game_name):
                deleted += 1
            else:
                failed += 1
        if failed and not deleted:
            return False, 0
        return True, deleted

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected."""
        ...

    def get_latest_save(self, game_name: str) -> Optional[str]:
        """Get the most recently uploaded save file for a game."""
        files = self.list_files(game_name)
        if not files:
            return None
        # Sort by name (which includes turn number) to get latest
        save_files = [f for f in files if f.endswith(".CivBeyondSwordSave")]
        if not save_files:
            return None
        save_files.sort()
        return save_files[-1]
