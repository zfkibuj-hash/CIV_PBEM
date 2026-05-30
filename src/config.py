"""
Application configuration management.
Stores settings in a JSON file in the user's app data directory.
"""
import json
import os
from pathlib import Path
from typing import Any, Optional

APP_NAME = "Civ4PBEMManager"
APP_VERSION = "1.0.0"

DEFAULT_SAVE_PATH = str(
    Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "pbem"
)

DEFAULT_CHECK_INTERVAL_MINUTES = 5


def get_config_dir() -> Path:
    """Get the application config directory (platform-aware)."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".config"
    config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def get_games_dir() -> Path:
    """Directory where game definitions are stored."""
    games_dir = get_config_dir() / "games"
    games_dir.mkdir(parents=True, exist_ok=True)
    return games_dir


class AppConfig:
    """Application-wide configuration."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self.load()

    def load(self):
        path = get_config_path()
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = self._defaults()
            self.save()

    def save(self):
        path = get_config_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def _defaults(self) -> dict[str, Any]:
        return {
            "save_path": DEFAULT_SAVE_PATH,
            "check_interval_minutes": DEFAULT_CHECK_INTERVAL_MINUTES,
            "dark_mode": True,
            "auto_send": False,  # True = send save without popup (balloon only, for fullscreen play)
            "language": "pl",  # "pl" or "en"
            "civ4_path": "",  # Path to Civ4BeyondSword.exe
            "transport": {
                "type": "ftp",  # ftp, sftp, webdav
                "host": "",
                "port": 21,
                "username": "",
                "password": "",  # stored via keyring in production
                "remote_dir": "/civ4pbem",
            },
            "smtp": {
                "host": "",
                "port": 587,
                "username": "",
                "password": "",
                "use_tls": True,
                "from_address": "",
            },
            "player_name": "",
            "player_email": "",
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    @property
    def save_path(self) -> str:
        return self._data.get("save_path", DEFAULT_SAVE_PATH)

    @save_path.setter
    def save_path(self, value: str):
        self._data["save_path"] = value
        self.save()

    @property
    def check_interval_minutes(self) -> int:
        return self._data.get("check_interval_minutes", DEFAULT_CHECK_INTERVAL_MINUTES)

    @property
    def transport_config(self) -> dict:
        return self._data.get("transport", {})

    @property
    def smtp_config(self) -> dict:
        return self._data.get("smtp", {})

    @property
    def player_name(self) -> str:
        return self._data.get("player_name", "")

    @player_name.setter
    def player_name(self, value: str):
        self._data["player_name"] = value
        self.save()

    @property
    def player_email(self) -> str:
        return self._data.get("player_email", "")

    @property
    def language(self) -> str:
        return self._data.get("language", "pl")

    @language.setter
    def language(self, value: str):
        self._data["language"] = value
        self.save()

    @property
    def civ4_path(self) -> str:
        return self._data.get("civ4_path", "")

    @civ4_path.setter
    def civ4_path(self, value: str):
        self._data["civ4_path"] = value
        self.save()
