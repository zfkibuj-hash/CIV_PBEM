"""
Base transport interface for file upload/download.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseTransport(ABC):
    """Abstract base class for all transport methods."""

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
    def download(self, remote_filename: str, local_path: Path, game_name: str) -> bool:
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
