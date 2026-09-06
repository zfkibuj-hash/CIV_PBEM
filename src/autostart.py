"""OS autostart integration (Windows Run key, Linux .desktop, macOS LaunchAgent)."""
from __future__ import annotations

import logging
import shlex
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

AUTOSTART_NAME = "Civ4PBEMManager"
START_MINIMIZED_FLAG = "--start-minimized"


def autostart_argv() -> list[str]:
    """Command argv used for OS autostart entries."""
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).resolve()), START_MINIMIZED_FLAG]

    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.exists():
        pythonw = Path(sys.executable)
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    return [str(pythonw), str(main_py), START_MINIMIZED_FLAG]


def autostart_command() -> str:
    """Shell command string for Windows Run / Linux .desktop."""
    return " ".join(shlex.quote(part) for part in autostart_argv())


def is_autostart_enabled() -> bool:
    """Return True if the app is registered to start with the OS."""
    if sys.platform == "win32":
        return _windows_is_enabled()
    if sys.platform == "darwin":
        return _macos_is_enabled()
    return _linux_is_enabled()


def set_autostart(enabled: bool) -> tuple[bool, str]:
    """Enable or disable OS autostart. Returns (success, error_message)."""
    try:
        if sys.platform == "win32":
            return _windows_set(enabled)
        if sys.platform == "darwin":
            return _macos_set(enabled)
        return _linux_set(enabled)
    except Exception as exc:
        logger.exception("Autostart change failed")
        return False, str(exc)


def reconcile_autostart(want_enabled: bool) -> tuple[bool, str]:
    """Apply config preference to the OS if it drifted."""
    if want_enabled == is_autostart_enabled():
        return True, ""
    return set_autostart(want_enabled)


def _windows_is_enabled() -> bool:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            winreg.QueryValueEx(key, AUTOSTART_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False


def _windows_set(enabled: bool) -> tuple[bool, str]:
    import winreg

    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    if enabled:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, autostart_command())
        logger.info("Windows autostart enabled: %s", autostart_command())
        return True, ""

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, AUTOSTART_NAME)
        logger.info("Windows autostart disabled")
        return True, ""
    except FileNotFoundError:
        return True, ""


def _linux_desktop_path() -> Path:
    return Path.home() / ".config" / "autostart" / f"{AUTOSTART_NAME.lower()}.desktop"


def _linux_is_enabled() -> bool:
    return _linux_desktop_path().exists()


def _linux_set(enabled: bool) -> tuple[bool, str]:
    path = _linux_desktop_path()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Civ4 PBEM Manager\n"
            f"Exec={autostart_command()}\n"
            "Terminal=false\n"
            "Hidden=false\n"
            "X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
        logger.info("Linux autostart enabled: %s", path)
        return True, ""

    if path.exists():
        path.unlink()
        logger.info("Linux autostart disabled")
    return True, ""


def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.{AUTOSTART_NAME.lower()}.plist"


def _macos_is_enabled() -> bool:
    return _macos_plist_path().exists()


def _macos_set(enabled: bool) -> tuple[bool, str]:
    import plistlib

    path = _macos_plist_path()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        plist = {
            "Label": f"com.{AUTOSTART_NAME.lower()}",
            "ProgramArguments": autostart_argv(),
            "RunAtLoad": True,
        }
        with path.open("wb") as fh:
            plistlib.dump(plist, fh)
        logger.info("macOS autostart enabled: %s", path)
        return True, ""

    if path.exists():
        path.unlink()
        logger.info("macOS autostart disabled")
    return True, ""
