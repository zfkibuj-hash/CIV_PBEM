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
APP_VERSION = "5.0.5"


def version_label() -> str:
    """UI label from APP_VERSION, e.g. v4.4.1 (patch shown when non-zero)."""
    parts = APP_VERSION.split(".")
    if len(parts) >= 3 and parts[2] not in ("0", "00"):
        return f"v{parts[0]}.{parts[1]}.{parts[2]}"
    if len(parts) >= 2:
        return f"v{parts[0]}.{parts[1]}"
    return f"v{APP_VERSION}"

DEFAULT_SAVE_PATH = str(
    Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "pbem"
)

DEFAULT_CHECK_INTERVAL_MINUTES = 5

# Keys that are stored in plain text (non-sensitive)
PUBLIC_KEYS = {
    "save_path", "check_interval_minutes", "dark_mode", "auto_send",
    "language", "player_name", "player_email",
    "window_geometry",
    # Legacy single-edition keys (kept for backwards compat)
    "civ4_path", "try_direct_load", "civ4_edition", "steam_path", "steam_app_id",
    # Multi-edition config
    "civ4_installations", "preferred_edition",
    # Global direct load (one checkbox for all editions)
    "direct_load_global", "auto_launch",
    # Notifications master switch + channels
    "notifications_enabled", "notify_via_smtp", "notify_via_app",
    # Auto-reminder
    "reminder_auto_enabled", "reminder_auto_days",
    # Export: suppress password prompt
    "export_skip_password_prompt",
    # First-run wizard completed
    "setup_complete",
    # Dual-write: program folder + folder Civ4 Load Game actually opens
    "mirror_saves", "civ4_save_path",
    "save_path_mismatch_dismissed",
    # Launch with Windows / OS login
    "autostart",
    # Stable per-install id (duplicate-alias claims on shared FTP)
    "install_id",
    # Last shown in-app notify flag timestamp per game
    "seen_notify",
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

    Encryption protects the config FILE on disk against unauthorized reading.
    At runtime, sensitive data is always available to the transport layer.
    The 'unlocked' state controls only UI VISIBILITY (whether Settings shows
    the actual credential values or masks them).

    Flow:
        config = AppConfig()
        # Transport always works (data decrypted from file at load):
        controller = AppController(config)  # uses config.transport_config

        # UI visibility controlled by unlock:
        config.is_unlocked  # False until password entered
        # Settings dialog hides credential values when locked

    First run (no encrypted section): everything visible, no password needed.
    After setting master password: file encrypted, UI locked until password.
    """

    def __init__(self):
        self._public: dict[str, Any] = {}
        self._private: dict[str, Any] = {}
        self._unlocked: bool = False
        self._master_password: Optional[str] = None
        self._has_encrypted: bool = False
        self._encrypted_blob: dict = {}
        self.load()

    @property
    def is_unlocked(self) -> bool:
        """Whether credential values are visible in UI (Settings dialogs)."""
        return self._unlocked

    @property
    def has_master_password(self) -> bool:
        """Whether a master password has been set (encrypted section exists on disk)."""
        return self._has_encrypted

    def load(self):
        """Load config from disk. Public data loads immediately.
        Private data: if encrypted, stays as blob until unlock() called for UI.
        But _private is populated either way for transport to work.
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
                # Private data NOT available until unlock() — transport won't work
                # until user provides password (this is the protection!)
                self._private = {}
            else:
                # Legacy / first run: sensitive data in plain text
                self._has_encrypted = False
                self._private = {k: v for k, v in raw.items() if k in PRIVATE_KEYS}
                self._unlocked = True
        else:
            self._public = self._public_defaults()
            self._private = self._private_defaults()
            self._unlocked = True
            self._has_encrypted = False
            self.save()
        self._ensure_install_id()

    def unlock(self, password: str) -> bool:
        """Unlock config with master password — decrypts private data.

        After successful unlock:
        - Transport credentials become available (transport works)
        - UI shows credential values in Settings

        Returns True if password correct, False otherwise.
        """
        if not self._has_encrypted:
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
        """Lock config — clear private data from memory and UI."""
        self._private = {}
        self._unlocked = False
        self._master_password = None

    def set_master_password(self, new_password: str):
        """Set or change the master password and re-encrypt data.

        Must be unlocked first (private data in memory).
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
            "player_name": "",
            "player_email": "",
            # Multi-edition Civ4 installation config
            "civ4_installations": {
                "steam": {"enabled": False, "exe_path": "", "direct_load": False},
                "gog":   {"enabled": False, "exe_path": "", "direct_load": False},
                "dvd":   {"enabled": False, "exe_path": "", "direct_load": False},
            },
            "preferred_edition": "",
            # Global direct load: try /fxsload= for all editions
            "direct_load_global": False,
            "auto_launch": False,
            # Notification channels
            "notifications_enabled": True,
            "notify_via_smtp": False,  # send email via SMTP (off by default)
            "notify_via_app": True,    # upload .flag file to transport server (default)
            # Auto-reminder: send email to current player after X days of inactivity
            "reminder_auto_enabled": False,
            "reminder_auto_days": 2,
            # Export: if True, skip "set password?" prompt before exporting .civ4pbem
            "export_skip_password_prompt": False,
            "setup_complete": False,
            "mirror_saves": True,
            "civ4_save_path": "",
            "save_path_mismatch_dismissed": "",
            "install_id": "",
            "seen_notify": {},
        }

    def _ensure_install_id(self):
        """Give this copy of the app a stable id (used for alias claims)."""
        if (self._public.get("install_id") or "").strip():
            return
        import uuid
        self._public["install_id"] = str(uuid.uuid4())
        self.save()

    @property
    def install_id(self) -> str:
        iid = (self._public.get("install_id") or "").strip()
        if not iid:
            self._ensure_install_id()
            iid = (self._public.get("install_id") or "").strip()
        return iid

    def needs_setup(self) -> bool:
        """True on first run (wizard not finished and no player name yet)."""
        if self._public.get("setup_complete"):
            return False
        return not bool((self.player_name or "").strip())

    @property
    def civ4_installations(self) -> dict:
        """Get all Civ4 installation configs."""
        return self._public.get("civ4_installations", self._public_defaults()["civ4_installations"])

    @property
    def preferred_edition(self) -> str:
        """Get preferred edition key ('steam'/'gog'/'dvd' or '')."""
        return self._public.get("preferred_edition", "")

    def get_enabled_editions(self) -> list[str]:
        """Return list of edition keys that are enabled and have a valid exe_path."""
        installs = self.civ4_installations
        result = []
        for edition in ("steam", "gog", "dvd"):
            cfg = installs.get(edition, {})
            if cfg.get("enabled") and cfg.get("exe_path"):
                result.append(edition)
        return result

    def civ4_exe_paths_for_save_detection(self) -> list[str]:
        """Exe path(s) used to detect PBEM save folders (respects preferred edition)."""
        from src.launcher import civ4_exe_paths_for_detection
        return civ4_exe_paths_for_detection(
            self.civ4_installations,
            self.preferred_edition,
        )

    # Legacy property kept for backwards compat with old code paths
    @property
    def civ4_path(self) -> str:
        """Legacy: returns first enabled exe_path, or old civ4_path key."""
        enabled = self.get_enabled_editions()
        if enabled:
            return self.civ4_installations[enabled[0]].get("exe_path", "")
        return self._public.get("civ4_path", "")

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
    def master_password(self) -> str:
        """Return master password for encrypting game files.

        Returns empty string if no master password is set or config is locked.
        """
        return self._master_password or ""
