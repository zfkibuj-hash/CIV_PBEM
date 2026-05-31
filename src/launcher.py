"""
Auto-launch module for Civilization 4: Beyond the Sword.
Handles detecting Civ4 installation and launching the game.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Common installation paths for Civ4 BTS on Windows
_COMMON_PATHS = [
    # Steam
    r"C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"D:\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"D:\SteamLibrary\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"E:\SteamLibrary\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    # GOG
    r"C:\Program Files (x86)\GOG Galaxy\Games\Civilization IV Complete\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\GOG Games\Civilization IV Complete\Beyond the Sword\Civ4BeyondSword.exe",
    # Standard installs
    r"C:\Program Files (x86)\Firaxis Games\Sid Meier's Civilization 4\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files\Firaxis Games\Sid Meier's Civilization 4\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files (x86)\2K Games\Firaxis Games\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files (x86)\Civilization IV\Beyond the Sword\Civ4BeyondSword.exe",
]

# Process names to check if Civ4 is already running
_CIV4_PROCESS_NAMES = [
    "Civ4BeyondSword.exe",
    "CivilizationIV.exe",
    "Civilization4.exe",
]


def detect_civ4_path() -> Optional[str]:
    """Auto-detect Civ4 Beyond the Sword executable path.

    Checks common installation directories on Windows.
    Returns the path if found, None otherwise.
    """
    if sys.platform != "win32":
        # On non-Windows, we can't reliably detect - user must set manually
        return None

    # Check common paths
    for path_str in _COMMON_PATHS:
        path = Path(path_str)
        if path.exists():
            logger.info(f"Auto-detected Civ4 BTS at: {path}")
            return str(path)

    # Try Windows Registry (Steam)
    try:
        import winreg
        # Try Steam path from registry
        steam_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Valve\Steam"
        )
        steam_path, _ = winreg.QueryValueEx(steam_key, "InstallPath")
        winreg.CloseKey(steam_key)

        civ4_steam = Path(steam_path) / "steamapps" / "common" / \
            "Sid Meier's Civilization IV Beyond the Sword" / "Civ4BeyondSword.exe"
        if civ4_steam.exists():
            return str(civ4_steam)
    except Exception:
        pass

    # Try Civ4 registry key directly
    try:
        import winreg
        civ4_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Firaxis Games\Sid Meier's Civilization 4 - Beyond the Sword"
        )
        install_path, _ = winreg.QueryValueEx(civ4_key, "INSTALLDIR")
        winreg.CloseKey(civ4_key)

        exe_path = Path(install_path) / "Civ4BeyondSword.exe"
        if exe_path.exists():
            return str(exe_path)
    except Exception:
        pass

    return None


def is_civ4_running() -> bool:
    """Check if Civilization 4 is currently running.

    Uses tasklist on Windows to check for the process.
    """
    if sys.platform != "win32":
        # On Linux/Mac, use 'ps' or 'pgrep'
        try:
            result = subprocess.run(
                ["pgrep", "-f", "Civ4BeyondSword"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    try:
        result = subprocess.run(
            ["tasklist", "/NH", "/FI", "IMAGENAME eq Civ4BeyondSword.exe"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return "Civ4BeyondSword.exe" in result.stdout
    except Exception:
        return False


def launch_civ4(exe_path: str, save_file: Optional[str] = None) -> tuple[bool, str]:
    """Launch Civilization 4: Beyond the Sword.

    Args:
        exe_path: Full path to Civ4BeyondSword.exe
        save_file: Optional path to a save file to load directly

    Returns:
        Tuple of (success, message)
    """
    if not exe_path:
        return False, "civ4_not_found"

    path = Path(exe_path)
    if not path.exists():
        return False, "civ4_not_found"

    # Check if already running
    if is_civ4_running():
        return True, "civ4_already_running"

    try:
        # Build command
        cmd = [str(path)]

        # If a save file is provided, pass it as argument
        # Civ4 BTS accepts save file path as command line argument
        if save_file and Path(save_file).exists():
            cmd.append(str(Path(save_file)))

        # Launch the game
        working_dir = str(path.parent)

        if sys.platform == "win32":
            # On Windows, use subprocess with DETACHED_PROCESS flag
            # so the game runs independently of our app
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                cmd,
                cwd=working_dir,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            # On Linux/Mac (e.g., via Wine)
            subprocess.Popen(
                cmd,
                cwd=working_dir,
                start_new_session=True,
                close_fds=True,
            )

        logger.info(f"Launched Civ4 BTS: {exe_path}")
        return True, "civ4_launched"

    except FileNotFoundError:
        logger.error(f"Civ4 executable not found: {exe_path}")
        return False, "civ4_not_found"
    except PermissionError:
        logger.error(f"Permission denied launching Civ4: {exe_path}")
        return False, "civ4_not_found"
    except Exception as e:
        logger.error(f"Failed to launch Civ4: {e}")
        return False, f"Error: {e}"
