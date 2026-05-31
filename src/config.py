"""
Application configuration management.

Config is split into two parts:
- PUBLIC: non-sensitive settings (save_path, dark_mode, language, etc.) — plain JSON
- PRIVATE: sensitive data (transport credentials, SMTP passwords) — AES-256 encrypted

The private section is stored as an encrypted blob in config.json under "encrypted" key.
On startup, user must provide master password to unlock. Without it, transport/notifications
won't work and credentials are hidden in the UI.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from src.crypto import encrypt_data, decrypt_data, hash_password_check

logger = logging.getLogger(__name__)

APP_NAME = "Civ4PBEMManager"
APP_VERSION = "1.1.0"

DEFAULT_SAVE_PATH = str(
    Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "pbem"
)

DEFAULT_CHECK_INTERVAL_MINUTES = 5

# Keys that are stored in plain text (non-sensitive)
PUBLIC_KEYS = {
    "save_path", "check_interval_minutes", "dark_mode", "auto_send",
    "language", "civ4_path", "player_name", "player_email",
}

# Keys that are encrypted (sensitive — contain credentials)
PRIVATE_KEYS = {
    "transport", "smtp",
}


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
    """Application-wide configuration with encrypted sensitive data.

    Usage:
        config = AppConfig()
        # Public data available immediately:
        print(config.player_name)

        # Sensitive data locked until unlock:
        print(config.is_unlocked)  # False
        config.unlock("my_master_password")
        print(config.transport_config)  # Now accessible

    On first run (no encrypted section), config behaves as if unlocked
    with empty sensitive data. User sets master password in Settings.
    """

    def __init__(self):
        self._public: dict[str, Any] = {}
        self._private: dict[str, Any] = {}
        self._unlocked: bool = False
        self._master_password: Optional[str] = None
        self._has_encrypted: bool = False  # True if config file has encrypted section
        self.load()

    @property
    def is_unlocked(self) -> bool:
        """Whether sensitive data is currently accessible."""
        return self._unlocked

    @property
    def has_master_password(self) -> bool:
        """Whether a master password has been set (encrypted section exists)."""
        return self._has_encrypted

    def load(self):
        """Load config from disk. Public data loads immediately.
        Encrypted data stays locked until unlock() is called.
        """
        path = get_config_path()
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            # Load public keys
            self._public = {k: v for k, v in raw.items() if k in PUBLIC_KEYS}

            # Check for encrypted section
            if "encrypted" in raw:
                self._has_encrypted = True
                self._encrypted_blob = raw["encrypted"]
                self._unlocked = False
                self._private = {}
            else:
                # Legacy / first run: sensitive data in plain text (migrate on next save)
                self._has_encrypted = False
                self._private = {k: v for k, v in raw.items() if k in PRIVATE_KEYS}
                self._unlocked = True  # No encryption yet → open access
        else:
            self._public = self._public_defaults()
            self._private = self._private_defaults()
            self._unlocked = True  # Fresh install, no password set yet
            self._has_encrypted = False
            self.save()

    def unlock(self, password: str) -> bool:
        """Unlock sensitive data with master password.

        Returns True if password correct, False otherwise.
        """
        if not self._has_encrypted:
            # No encryption set — nothing to unlock
            self._unlocked = True
            return True

        decrypted = decrypt_data(self._encrypted_blob, password)
        if decrypted is None:
            return False

        self._private = decrypted
        self._unlocked = True
        self._master_password = password
        logger.info("Config unlocked successfully")
        return True

    def lock(self):
        """Lock sensitive data (clear from memory)."""
        self._private = {}
        self._unlocked = False
        self._master_password = None

    def set_master_password(self, new_password: str):
        """Set or change the master password and re-encrypt data.

        Must be unlocked first (or fresh install with no encryption).
        """
        if not self._unlocked:
            raise RuntimeError("Cannot set password while locked")
        self._master_password = new_password
        self._has_encrypted = True
        self.save()

    def save(self):
        """Save config to disk. Sensitive data is encrypted if master password is set."""
        path = get_config_path()
        output = dict(self._public)

        if self._master_password and self._has_encrypted:
            # Encrypt sensitive data
            output["encrypted"] = encrypt_data(self._private, self._master_password)
        elif self._has_encrypted and not self._unlocked:
            # Still locked — preserve existing encrypted blob unchanged
            output["encrypted"] = self._encrypted_blob
        else:
            # No encryption (legacy mode or fresh install) — save plain
            output.update(self._private)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    def _public_defaults(self) -> dict[str, Any]:
        return {
            "save_path": DEFAULT_SAVE_PATH,
            "check_interval_minutes": DEFAULT_CHECK_INTERVAL_MINUTES,
            "dark_mode": True,
            "auto_send": False,
            "language": "pl",
            "civ4_path": "",
            "player_name": "",
            "player_email": "",
        }

    def _private_defaults(self) -> dict[str, Any]:
        return {
            "transport": {
                "type": "ftp",
                "host": "",
                "port": 21,
                "username": "",
                "password": "",
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
        }

    # --- Public getters/setters (always available) ---

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. For private keys, returns default if locked."""
        if key in PUBLIC_KEYS:
            return self._public.get(key, default)
        if key in PRIVATE_KEYS:
            if self._unlocked:
                return self._private.get(key, default)
            return default
        # Check both
        if key in self._public:
            return self._public[key]
        if self._unlocked and key in self._private:
            return self._private[key]
        return default

    def set(self, key: str, value: Any):
        """Set a config value and save."""
        if key in PUBLIC_KEYS:
            self._public[key] = value
        elif key in PRIVATE_KEYS:
            if not self._unlocked:
                raise RuntimeError(f"Cannot set '{key}' while config is locked")
            self._private[key] = value
        else:
            # Unknown key — store in public
            self._public[key] = value
        self.save()

    @property
    def save_path(self) -> str:
        return self._public.get("save_path", DEFAULT_SAVE_PATH)

    @save_path.setter
    def save_path(self, value: str):
        self._public["save_path"] = value
        self.save()

    @property
    def check_interval_minutes(self) -> int:
        return self._public.get("check_interval_minutes", DEFAULT_CHECK_INTERVAL_MINUTES)

    @property
    def transport_config(self) -> dict:
        """Get transport config. Returns empty dict if locked."""
        if not self._unlocked:
            return {}
        return self._private.get("transport", {})

    @property
    def smtp_config(self) -> dict:
        """Get SMTP config. Returns empty dict if locked."""
        if not self._unlocked:
            return {}
        return self._private.get("smtp", {})

    @property
    def player_name(self) -> str:
        return self._public.get("player_name", "")

    @player_name.setter
    def player_name(self, value: str):
        self._public["player_name"] = value
        self.save()

    @property
    def player_email(self) -> str:
        return self._public.get("player_email", "")

    @property
    def language(self) -> str:
        return self._public.get("language", "pl")

    @language.setter
    def language(self, value: str):
        self._public["language"] = value
        self.save()

    @property
    def civ4_path(self) -> str:
        return self._public.get("civ4_path", "")

    @civ4_path.setter
    def civ4_path(self, value: str):
        self._public["civ4_path"] = value
        self.save()
