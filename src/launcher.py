"""
Auto-launch module for Civilization 4: Beyond the Sword.
Handles detecting Civ4 installation and launching the game with optional save loading.

Edition-specific launch behaviour:
  - "steam"  : Steam.exe -applaunch <app_id> /FXSLOAD="<save>"
  - "gog"    : Civ4BeyondSword.exe /fxsload="<save>"
  - "dvd"    : Civ4BeyondSword.exe /fxsload="<save>"  (same as GOG)
  - ""       : plain launch, no save argument (safe fallback)

/fxsload= syntax confirmed from Windows registry:
  "C:\\...\\Civ4BeyondSword.exe" /fxsload="%1"
Both opening and closing quotes are required.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_STEAM_APP_ID = "8800"

# Steam Civ4 BTS paths — note the extra "Beyond the Sword\" subfolder
_STEAM_CIV4_PATHS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Civ4BeyondSword.exe",
    r"D:\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Civ4BeyondSword.exe",
    r"D:\SteamLibrary\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Civ4BeyondSword.exe",
    r"E:\SteamLibrary\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Civ4BeyondSword.exe",
    # Fallback: some installs without the extra subfolder
    r"C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
]

# GOG Civ4 BTS paths
_GOG_CIV4_PATHS = [
    r"C:\Program Files (x86)\GOG Galaxy\Games\Civilization IV Complete\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\GOG Games\Civilization IV Complete\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\GOG Games\Civilization IV - Beyond the Sword\Beyond the Sword\Civ4BeyondSword.exe",
    r"D:\GOG Games\Civilization IV Complete\Beyond the Sword\Civ4BeyondSword.exe",
]

# DVD/retail Civ4 BTS paths
_DVD_CIV4_PATHS = [
    r"C:\Program Files (x86)\Firaxis Games\Sid Meier's Civilization 4\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files\Firaxis Games\Sid Meier's Civilization 4\Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files (x86)\2K Games\Firaxis Games\Sid Meier's Civilization IV Beyond the Sword\Civ4BeyondSword.exe",
    r"C:\Program Files (x86)\Civilization IV\Beyond the Sword\Civ4BeyondSword.exe",
]

# All paths combined (for generic detect)
_COMMON_CIV4_PATHS = _STEAM_CIV4_PATHS + _GOG_CIV4_PATHS + _DVD_CIV4_PATHS

# Common Steam.exe locations
_COMMON_STEAM_PATHS = [
    r"C:\Program Files (x86)\Steam\Steam.exe",
    r"C:\Program Files\Steam\Steam.exe",
    r"D:\Steam\Steam.exe",
    r"D:\SteamLibrary\Steam.exe",
    r"E:\Steam\Steam.exe",
]

_CIV4_PROCESS_NAMES = [
    "Civ4BeyondSword.exe",
    "CivilizationIV.exe",
    "Civilization4.exe",
]

_COMMON_SAVE_PATHS = [
    str(Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "pbem"),
    str(Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "multi"),
    str(Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "hotseat"),
    str(Path.home() / "Documents" / "My Games" / "Beyond the Sword" / "Saves"),
    str(Path.home() / "OneDrive" / "Documents" / "My Games" / "Beyond the Sword" / "Saves" / "pbem"),
    str(Path.home() / "OneDrive" / "Documents" / "My Games" / "Beyond the Sword" / "Saves"),
    str(Path.home() / "Dokumenty" / "My Games" / "Beyond the Sword" / "Saves" / "pbem"),
    str(Path.home() / "Dokumenty" / "My Games" / "Beyond the Sword" / "Saves"),
]


def detect_save_path() -> Optional[str]:
    """Auto-detect Civ4 BTS save folder."""
    for path_str in _COMMON_SAVE_PATHS:
        path = Path(path_str)
        if path.exists():
            logger.info(f"Auto-detected save path: {path}")
            return str(path)

    home = Path.home()
    for docs_name in ["Documents", "Dokumenty", "Mes documents"]:
        saves_dir = home / docs_name / "My Games" / "Beyond the Sword" / "Saves"
        if saves_dir.exists():
            pbem = saves_dir / "pbem"
            if pbem.exists():
                return str(pbem)
            return str(saves_dir)
    return None


def detect_civ4_for_edition(edition: str) -> Optional[str]:
    """Auto-detect Civ4 BTS exe for a specific edition (steam/gog/dvd).

    Returns path to Civ4BeyondSword.exe if found, None otherwise.
    """
    if sys.platform != "win32":
        return None

    if edition == "steam":
        for path_str in _STEAM_CIV4_PATHS:
            if Path(path_str).exists():
                return path_str
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_install, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            base = (Path(steam_install) / "steamapps" / "common"
                    / "Sid Meier's Civilization IV Beyond the Sword")
            for candidate in [
                base / "Beyond the Sword" / "Civ4BeyondSword.exe",
                base / "Civ4BeyondSword.exe",
            ]:
                if candidate.exists():
                    return str(candidate)
        except Exception:
            pass

    elif edition == "gog":
        for path_str in _GOG_CIV4_PATHS:
            if Path(path_str).exists():
                return path_str
        try:
            import winreg
            for reg_key in [
                r"SOFTWARE\WOW6432Node\Firaxis Games\Sid Meier's Civilization 4 Complete",
                r"SOFTWARE\WOW6432Node\Firaxis Games\Sid Meier's Civilization 4 - Beyond the Sword",
            ]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key)
                    install_dir, _ = winreg.QueryValueEx(key, "INSTALLDIR")
                    winreg.CloseKey(key)
                    for candidate in [
                        Path(install_dir) / "Beyond the Sword" / "Civ4BeyondSword.exe",
                        Path(install_dir) / "Civ4BeyondSword.exe",
                    ]:
                        if candidate.exists():
                            return str(candidate)
                except Exception:
                    continue
        except Exception:
            pass

    elif edition == "dvd":
        for path_str in _DVD_CIV4_PATHS:
            if Path(path_str).exists():
                return path_str
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Firaxis Games\Sid Meier's Civilization 4 - Beyond the Sword"
            )
            install_path, _ = winreg.QueryValueEx(key, "INSTALLDIR")
            winreg.CloseKey(key)
            candidate = Path(install_path) / "Civ4BeyondSword.exe"
            if candidate.exists():
                return str(candidate)
        except Exception:
            pass

    return None


def detect_civ4_path() -> Optional[str]:
    """Auto-detect any Civ4 BTS installation (generic, tries all editions)."""
    for edition in ("steam", "gog", "dvd"):
        found = detect_civ4_for_edition(edition)
        if found:
            return found
    return None


def detect_steam_path() -> Optional[str]:
    """Auto-detect Steam.exe path."""
    if sys.platform != "win32":
        return None

    for path_str in _COMMON_STEAM_PATHS:
        if Path(path_str).exists():
            return path_str

    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\WOW6432Node\Valve\Steam")
        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        steam_exe = Path(install_path) / "Steam.exe"
        if steam_exe.exists():
            return str(steam_exe)
    except Exception:
        pass

    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
        steam_exe, _ = winreg.QueryValueEx(key, "SteamExe")
        winreg.CloseKey(key)
        if Path(steam_exe).exists():
            return steam_exe
    except Exception:
        pass

    return None


def is_civ4_running() -> bool:
    """Check if Civilization 4 is currently running."""
    if sys.platform != "win32":
        try:
            result = subprocess.run(["pgrep", "-f", "Civ4BeyondSword"],
                                    capture_output=True, text=True)
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


def _popen_detached(cmd, cwd: str):
    """Launch a process fully detached from the parent."""
    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            cmd, cwd=cwd,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
            shell=isinstance(cmd, str),
        )
    else:
        subprocess.Popen(cmd, cwd=cwd, start_new_session=True, close_fds=True)


def launch_civ4(
    exe_path: str,
    save_file: Optional[str] = None,
    edition: str = "",
    steam_path: str = "",
    steam_app_id: str = DEFAULT_STEAM_APP_ID,
) -> tuple[bool, str]:
    """Launch Civilization 4: Beyond the Sword.

    Args:
        exe_path:      Full path to Civ4BeyondSword.exe.
        save_file:     Optional save file to load directly (requires edition set).
        edition:       "steam", "gog", "dvd", or "" (plain launch).
        steam_path:    Path to Steam.exe (required for edition="steam").
        steam_app_id:  Steam App ID (default "8800").

    Launch commands (confirmed from Windows registry research):
        steam -> Steam.exe -applaunch <id> /FXSLOAD="<save>"
        gog   -> Civ4BeyondSword.exe /fxsload="<save>"
        dvd   -> Civ4BeyondSword.exe /fxsload="<save>"
        ""    -> Civ4BeyondSword.exe  (no save arg)
    """
    if not exe_path:
        return False, "civ4_not_found"

    civ4_path = Path(exe_path)
    if not civ4_path.exists():
        return False, "civ4_not_found"

    if is_civ4_running():
        return True, "civ4_already_running"

    working_dir = str(civ4_path.parent)

    try:
        if save_file and Path(save_file).exists() and edition in ("steam", "gog", "dvd"):
            save_path = Path(save_file)
            # All editions use the same syntax: exe /fxsload="<path>"
            # Confirmed from Windows registry research on Steam, GOG and DVD installs.
            cmd_str = f'"{civ4_path}" /fxsload="{save_path}"'
            logger.info(f"{edition} launch with save: {cmd_str}")
            _popen_detached(cmd_str, working_dir)
        else:
            logger.info(f"Plain launch: {civ4_path}")
            _popen_detached([str(civ4_path)], working_dir)

        logger.info(f"Launched Civ4 BTS ({edition or 'plain'}): {exe_path}")
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


def set_file_association(edition: str, exe_path: str, steam_path: str = "",
                         steam_app_id: str = DEFAULT_STEAM_APP_ID) -> tuple[bool, str]:
    """Set Windows file association for .CivBeyondSwordSave.

    All editions use the same syntax: "exe" /fxsload="%1"
    The only difference is the path to Civ4BeyondSword.exe.
    Writes to HKCU (no admin rights needed).

    Returns (success, command_string_or_error).
    """
    if sys.platform != "win32":
        return False, "registry_windows_only"

    if not exe_path or not Path(exe_path).exists():
        return False, "civ4_not_found"

    try:
        import winreg

        cmd = f'"{exe_path}" /fxsload="%1"'
        base = r"Software\Classes"

        # .CivBeyondSwordSave -> CivBeyondSwordSave
        ext_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   rf"{base}\.CivBeyondSwordSave")
        winreg.SetValueEx(ext_key, "", 0, winreg.REG_SZ, "CivBeyondSwordSave")
        winreg.CloseKey(ext_key)

        # Friendly name
        name_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                    rf"{base}\CivBeyondSwordSave")
        winreg.SetValueEx(name_key, "", 0, winreg.REG_SZ, "Civ4 Beyond the Sword Save")
        winreg.CloseKey(name_key)

        # CivBeyondSwordSave\shell\open\command
        cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   rf"{base}\CivBeyondSwordSave\shell\open\command")
        winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(cmd_key)

        logger.info(f"File association set for {edition}: {cmd}")
        return True, cmd

    except PermissionError:
        return False, "registry_permission_error"
    except Exception as e:
        logger.error(f"Failed to set file association: {e}")
        return False, str(e)


def get_current_file_association() -> Optional[str]:
    """Read current .CivBeyondSwordSave open command from registry.

    Checks HKCU first (user-level), then HKLM (system-level).
    Returns the command string or None if not set.
    """
    if sys.platform != "win32":
        return None

    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = winreg.OpenKey(
                    hive,
                    r"SOFTWARE\Classes\CivBeyondSwordSave\shell\open\command"
                    if hive == winreg.HKEY_LOCAL_MACHINE
                    else r"Software\Classes\CivBeyondSwordSave\shell\open\command"
                )
                cmd, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                return cmd
            except Exception:
                continue
    except Exception:
        pass
    return None
