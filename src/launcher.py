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
import re
import shutil
import subprocess
import sys
import time
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

_BTS_RELATIVE = [
    Path("Beyond the Sword") / "Civ4BeyondSword.exe",
    Path("Civ4BeyondSword.exe"),
]

_STEAM_GAME_FOLDER = "Sid Meier's Civilization IV Beyond the Sword"


def _bts_exe_under(base: Path) -> Optional[str]:
    """Return Civ4BeyondSword.exe if it exists under a BTS install root."""
    for rel in _BTS_RELATIVE:
        candidate = base / rel
        if candidate.exists():
            return str(candidate)
    return None


def _steam_library_roots() -> list[Path]:
    """Steam install dir plus extra libraries from libraryfolders.vdf."""
    roots: list[Path] = []
    steam_exe = None
    for path_str in _COMMON_STEAM_PATHS:
        if Path(path_str).exists():
            steam_exe = path_str
            break
    if steam_exe is None:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\WOW6432Node\Valve\Steam")
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            candidate = Path(install_path) / "Steam.exe"
            if candidate.exists():
                steam_exe = str(candidate)
        except Exception:
            pass
    if steam_exe is None:
        return roots

    steam_dir = Path(steam_exe).parent
    roots.append(steam_dir)
    vdf = steam_dir / "steamapps" / "libraryfolders.vdf"
    if vdf.exists():
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r'"path"\s+"([^"]+)"', text):
                raw = match.group(1).replace("\\\\", "\\")
                extra = Path(raw)
                if extra.exists() and extra not in roots:
                    roots.append(extra)
        except Exception:
            logger.debug("Could not parse Steam libraryfolders.vdf", exc_info=True)
    return roots


_CIV4_PROCESS_NAMES = [
    "Civ4BeyondSword.exe",
    "CivilizationIV.exe",
    "Civilization4.exe",
]

# GUID strings for SHGetKnownFolderPath
_FOLDERID_DOCUMENTS = "FDD39AD0-238F-46AF-ADB4-6C85480369C7"
_FOLDERID_ONEDRIVE = "A52BBA46-E9E1-435F-B3D9-28DAA648C0F6"


def _windows_known_folder(guid_str: str) -> Optional[Path]:
    """Resolve a Windows Known Folder (handles OneDrive-redirected Documents)."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]

        parts = guid_str.split("-")
        g = GUID()
        g.Data1 = int(parts[0], 16)
        g.Data2 = int(parts[1], 16)
        g.Data3 = int(parts[2], 16)
        rest = parts[3] + parts[4]
        for i in range(8):
            g.Data4[i] = int(rest[i * 2:i * 2 + 2], 16)

        path_ptr = ctypes.c_wchar_p()
        hr = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(g), 0, None, ctypes.byref(path_ptr)
        )
        if hr != 0 or not path_ptr.value:
            return None
        path = Path(path_ptr.value)
        ctypes.windll.ole32.CoTaskMemFree(path_ptr)
        return path if path.exists() else path
    except Exception:
        logger.debug("SHGetKnownFolderPath failed for %s", guid_str, exc_info=True)
        return None


def _windows_documents_csidl() -> Optional[Path]:
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        # CSIDL_PERSONAL = 5
        hr = ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
        if hr != 0 or not buf.value:
            return None
        return Path(buf.value)
    except Exception:
        return None


def _document_roots() -> list[Path]:
    """All plausible 'Documents' folders, including OneDrive copies.

    Windows + OneDrive often leaves TWO trees that both look like
    Documents\\My Games\\Beyond the Sword\\Saves\\pbem. Civ4 uses the
    Known Folder path (usually the one with CivilizationIV.ini and
    Saves\\pbem\\auto). Python's Path.home()/Documents is frequently the other.
    """
    roots: list[Path] = []
    seen: set[str] = set()

    def add(p: Optional[Path]):
        if p is None:
            return
        try:
            key = str(p.resolve()).lower()
        except Exception:
            key = str(p).lower()
        if key in seen:
            return
        seen.add(key)
        roots.append(p)

    add(_windows_known_folder(_FOLDERID_DOCUMENTS))
    add(_windows_documents_csidl())
    add(_registry_documents())
    home = Path.home()
    for name in ("Documents", "Dokumenty", "Mes documents"):
        add(home / name)

    onedrive = _windows_known_folder(_FOLDERID_ONEDRIVE)
    add(onedrive)
    for env_key in ("ONEDRIVE", "OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        val = os.environ.get(env_key)
        if val:
            add(Path(val))
            add(Path(val) / "Documents")
            add(Path(val) / "Dokumenty")
    try:
        for child in home.iterdir():
            if child.is_dir() and child.name.lower().startswith("onedrive"):
                add(child)
                add(child / "Documents")
                add(child / "Dokumenty")
    except Exception:
        pass

    # OneDrive sometimes lives on D:/E: (not under the user profile)
    for drive in ("D", "E", "F"):
        try:
            root = Path(f"{drive}:/")
            if not root.exists():
                continue
            for child in root.iterdir():
                if child.is_dir() and child.name.lower().startswith("onedrive"):
                    add(child)
                    add(child / "Documents")
                    add(child / "Dokumenty")
        except Exception:
            pass

    return roots


def _registry_documents() -> Optional[Path]:
    """Documents path from Explorer 'User Shell Folders' (OneDrive redirect)."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as key:
            val, _ = winreg.QueryValueEx(key, "Personal")
        expanded = os.path.expandvars(str(val))
        return Path(expanded) if expanded else None
    except Exception:
        return None


def _norm_path(path: Path) -> str:
    try:
        return str(path.resolve()).lower()
    except Exception:
        return str(path).lower()


def _child_ci(parent: Path, name: str) -> Optional[Path]:
    """Find a direct child by name, ignoring case (OneDrive can be case-sensitive)."""
    if parent is None:
        return None
    exact = parent / name
    try:
        if exact.exists():
            return exact
    except Exception:
        pass
    try:
        want = name.lower()
        for child in parent.iterdir():
            if child.name.lower() == want:
                return child
    except Exception:
        return None
    return None


def _bts_user_dirs_under(docs: Path) -> list[Path]:
    """Civ4 user dirs: <docs>/My Games/Beyond the Sword (any casing)."""
    found: list[Path] = []
    my_games = _child_ci(docs, "My Games") or _child_ci(docs, "Moje gry")
    if my_games is None:
        return found
    try:
        for child in my_games.iterdir():
            if child.is_dir() and child.name.lower() == "beyond the sword":
                found.append(child)
    except Exception:
        pass
    return found


def _civ_save_stats(folder: Path) -> tuple[int, float]:
    """Count .CivBeyondSwordSave files in this folder (not subfolders)."""
    count = 0
    newest = 0.0
    if not folder.is_dir():
        return 0, 0.0
    try:
        for save in folder.glob("*.CivBeyondSwordSave"):
            count += 1
            try:
                newest = max(newest, save.stat().st_mtime)
            except OSError:
                pass
    except Exception:
        pass
    return count, newest


def _has_nonempty_subdir(folder: Path, name: str) -> bool:
    child = _child_ci(folder, name)
    if child is None or not child.is_dir():
        return False
    try:
        return any(child.iterdir())
    except Exception:
        return False


def _score_save_folder(folder: Path, bts_root: Path) -> int:
    """Higher score = folder Civ4 actually writes / Load Game opens.

    Real save files and recency beat empty Saves\\pbem\\auto leftovers in
    the local Documents copy next to a redirected OneDrive.
    """
    if not folder.is_dir():
        return -1
    score = 1
    ini = _child_ci(bts_root, "CivilizationIV.ini") or _child_ci(bts_root, "Civilization.ini")
    if ini is not None:
        score += 80

    count, newest = _civ_save_stats(folder)
    score += min(100, count * 5)
    if newest:
        age_days = (time.time() - newest) / 86400.0
        if age_days <= 14:
            score += 50
        elif age_days <= 90:
            score += 25
        elif age_days <= 365:
            score += 10

    path_l = str(folder).replace("/", "\\").lower()
    if "onedrive" in path_l:
        score += 30
    # Local leftover Documents\\... next to OneDrive-redirected files
    if "\\documents\\my games\\" in path_l and "onedrive" not in path_l:
        score -= 20

    if _has_nonempty_subdir(folder, "auto"):
        score += 10
    if _has_nonempty_subdir(folder, "pitboss") or _has_nonempty_subdir(folder, "pithoss"):
        score += 10
    return score


def _save_targets_for_bts(bts: Path) -> list[Path]:
    """One canonical PBEM folder per Civ4 user dir (Saves\\pbem)."""
    saves = _child_ci(bts, "Saves")
    if saves is None:
        return []
    return [canonical_pbem_save_dir(saves, create=False)]


def _bts_root_for_save_folder(folder: Path) -> Path:
    name = folder.name.lower()
    if name == "pbem":
        return folder.parent.parent
    if name == "saves":
        return folder.parent
    return folder


def canonical_pbem_save_dir(path: Path | str, *, create: bool = False) -> Path:
    """PBEM saves always live in Saves\\pbem (create subfolder when needed)."""
    p = Path(path)
    if p.name.lower() == "pbem":
        if create:
            p.mkdir(parents=True, exist_ok=True)
        return p
    if p.name.lower() == "saves":
        pbem = _child_ci(p, "pbem")
        if pbem is None:
            pbem = p / "pbem"
        if create:
            try:
                pbem.mkdir(parents=True, exist_ok=True)
            except Exception:
                return p
        return pbem
    return p


def civ4_load_game_dir(path: Path | str) -> Path:
    """Folder Civ4 opens in Load Game (parent Saves when using Saves\\pbem)."""
    p = Path(path)
    if p.name.lower() == "pbem":
        return p.parent
    return p


def resolve_save_layout(path: Path | str, *, create: bool = False) -> tuple[str, str]:
    """Return (pbem_folder, civ4_load_game_folder)."""
    pbem = canonical_pbem_save_dir(path, create=create)
    mirror = civ4_load_game_dir(pbem)
    return str(pbem), str(mirror)


def _score_save_tree(folder: Path, bts: Path) -> int:
    """Score a Saves tree; counts files in pbem and stray saves in parent Saves."""
    canonical = canonical_pbem_save_dir(folder, create=False)
    scores: list[int] = []
    if canonical.is_dir():
        scores.append(_score_save_folder(canonical, bts))
    saves_parent = (
        canonical.parent
        if canonical.name.lower() == "pbem"
        else (folder if folder.name.lower() == "saves" else None)
    )
    if saves_parent is not None and saves_parent.is_dir():
        scores.append(_score_save_folder(saves_parent, bts))
    return max(scores) if scores else -1


def _named_shortcut(folder: Path, stem: str) -> Optional[Path]:
    want = {stem.lower(), f"{stem.lower()}.lnk"}
    try:
        for child in folder.iterdir():
            if child.name.lower() in want:
                return child
    except Exception:
        return None
    return None


def _decode_lnk_sz(data: bytes, offset: int, unicode: bool) -> str:
    if offset <= 0 or offset >= len(data):
        return ""
    blob = data[offset:]
    if unicode:
        return blob.decode("utf-16-le", errors="ignore").split("\x00", 1)[0].strip()
    return blob.split(b"\x00", 1)[0].decode("cp1252", errors="replace").strip()


def _parse_lnk_binary(path: Path) -> tuple[str, str]:
    """Return (target_path, arguments) from a .lnk. Empty strings if unknown."""
    try:
        data = path.read_bytes()
    except Exception:
        return "", ""
    if len(data) < 76 or data[0:2] != b"L\x00":
        return "", ""
    flags = int.from_bytes(data[20:24], "little")
    pos = 76
    try:
        if flags & 0x01:  # HasLinkTargetIDList
            idlist_size = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2 + idlist_size
        target = ""
        if flags & 0x02 and pos + 32 <= len(data):  # HasLinkInfo
            info_size = int.from_bytes(data[pos:pos + 4], "little")
            info = data[pos:pos + info_size]
            header_size = int.from_bytes(info[4:8], "little") if len(info) >= 8 else 0
            ansi_off = int.from_bytes(info[16:20], "little") if len(info) >= 20 else 0
            target = _decode_lnk_sz(info, ansi_off, False)
            if header_size >= 0x24 and len(info) >= 32:
                uni_off = int.from_bytes(info[28:32], "little")
                uni = _decode_lnk_sz(info, uni_off, True)
                if uni:
                    target = uni
            pos += info_size
        args = ""
        is_unicode = bool(flags & 0x80)
        # StringData in flag order: name, relative path, working dir, arguments
        for bit in (0x04, 0x08, 0x10, 0x20):
            if not (flags & bit):
                continue
            if pos + 2 > len(data):
                break
            nchars = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
            if nchars > 4096:
                break
            if is_unicode:
                nbytes = nchars * 2
                raw = data[pos:pos + nbytes]
                pos += nbytes
                text = raw.decode("utf-16-le", errors="ignore").rstrip("\x00")
            else:
                raw = data[pos:pos + nchars]
                pos += nchars
                text = raw.decode("cp1252", errors="replace").rstrip("\x00")
            if bit == 0x20:
                args = text
        return target, args
    except Exception:
        logger.debug("Failed to parse shortcut %s", path, exc_info=True)
        return "", ""


def _parse_altroot(args: str) -> Optional[Path]:
    if not args:
        return None
    match = re.search(r'/altroot\s*=\s*"([^"]+)"', args, re.IGNORECASE)
    if not match:
        match = re.search(r"/altroot\s*=\s*(\S+)", args, re.IGNORECASE)
    if not match:
        return None
    raw = os.path.expandvars(match.group(1).strip().strip('"'))
    if raw == ".":
        return None
    path = Path(raw)
    return path if raw else None


_INI_PATH_KEYS = {
    "userdir", "userpath", "savedir", "savepath", "savespath",
    "altroot", "rootdir", "rootpath",
}


def _parse_civ4_ini_paths(ini: Path) -> list[Path]:
    found: list[Path] = []
    try:
        text = ini.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            text = ini.read_text(encoding="cp1252", errors="ignore")
    except Exception:
        return found
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";") or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, val = stripped.partition("=")
        if key.strip().lower() not in _INI_PATH_KEYS:
            continue
        raw = os.path.expandvars(val.strip().strip('"'))
        if raw:
            found.append(Path(raw))
    return found


def _expand_civ4_user_hint(hint: Path) -> list[Path]:
    """Turn a Civ4 user-root / INI / Saves hint into save-folder candidates."""
    try:
        if hint.is_file():
            hint = hint.parent
    except Exception:
        return []
    name = hint.name.lower()
    if name.endswith(".ini"):
        hint = hint.parent
        name = hint.name.lower()
    if name == "pbem":
        return [hint] if hint.is_dir() else []
    if name == "saves":
        return [canonical_pbem_save_dir(hint, create=False)] if hint.is_dir() else []
    if hint.is_dir():
        targets = _save_targets_for_bts(hint)
        if targets:
            return targets
        saves = hint / "Saves"
        if saves.is_dir():
            return [saves]
    return []


def _bts_install_dirs(extra_exes: Optional[list[str]] = None) -> list[Path]:
    dirs: list[Path] = []
    seen: set[str] = set()

    def add_exe(exe: Optional[str]):
        if not exe:
            return
        folder = Path(exe)
        if folder.suffix.lower() == ".exe":
            folder = folder.parent
        try:
            if not folder.exists():
                return
            key = _norm_path(folder)
        except Exception:
            return
        if key in seen:
            return
        seen.add(key)
        dirs.append(folder)

    if extra_exes:
        for exe in extra_exes:
            add_exe(exe)
    for edition in ("steam", "gog", "dvd"):
        add_exe(detect_civ4_for_edition(edition))
    return dirs


def _steam_altroot_paths() -> list[Path]:
    found: list[Path] = []
    for root in _steam_library_roots():
        userdata = root / "userdata"
        if not userdata.is_dir():
            continue
        try:
            vdffiles = list(userdata.glob("*/config/localconfig.vdf"))
        except Exception:
            continue
        for vdf in vdffiles:
            try:
                text = vdf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for match in re.finditer(
                r'LaunchOptions"\s+"([^"]*altroot[^"]*)"', text, re.IGNORECASE
            ):
                alt = _parse_altroot(match.group(1))
                if alt is not None:
                    found.append(alt)
    return found


def civ4_settings_save_paths(extra_exes: Optional[list[str]] = None) -> list[Path]:
    """Folders Civ4 itself points at: _Civ4Saves, _Civ4Config, INI keys, /ALTROOT."""
    hints: list[Path] = []
    seen: set[str] = set()

    def add(path: Optional[Path]):
        if path is None:
            return
        try:
            key = _norm_path(path)
        except Exception:
            key = str(path).lower()
        if key in seen:
            return
        seen.add(key)
        hints.append(path)

    for install in _bts_install_dirs(extra_exes):
        saves_lnk = _named_shortcut(install, "_Civ4Saves")
        if saves_lnk is not None:
            target, args = _parse_lnk_binary(saves_lnk)
            if target:
                add(Path(os.path.expandvars(target)))
            add(_parse_altroot(args))
        config_lnk = _named_shortcut(install, "_Civ4Config")
        if config_lnk is not None:
            target, args = _parse_lnk_binary(config_lnk)
            if target:
                add(Path(os.path.expandvars(target)))
            add(_parse_altroot(args))
        local_ini = _child_ci(install, "CivilizationIV.ini")
        if local_ini is not None:
            add(local_ini)
            for p in _parse_civ4_ini_paths(local_ini):
                add(p)

    for alt in _steam_altroot_paths():
        add(alt)

    expanded: list[Path] = []
    seen_out: set[str] = set()
    for hint in hints:
        for folder in _expand_civ4_user_hint(hint):
            key = _norm_path(folder)
            if key in seen_out:
                continue
            seen_out.add(key)
            expanded.append(folder)
            logger.info("Civ4 settings save folder: %s (from %s)", folder, hint)
    return expanded


_CANDIDATE_CACHE: dict[str, tuple[float, list[tuple[int, Path]]]] = {}
_CANDIDATE_TTL = 45.0


def list_civ4_save_candidates(
    extra_exes: Optional[list[str]] = None,
    force: bool = False,
) -> list[tuple[int, Path]]:
    """Return (score, Saves\\pbem path) — one entry per Civ4 user dir.

    Paths that Civilization 4 itself points at (_Civ4Saves, ini, /ALTROOT)
    get a large bonus so they beat leftover Documents copies.
    """
    cache_key = "|".join(sorted(extra_exes or []))
    now = time.time()
    cached = _CANDIDATE_CACHE.get(cache_key)
    if not force and cached and now - cached[0] < _CANDIDATE_TTL:
        return cached[1]

    found: dict[str, tuple[int, Path]] = {}

    def consider(target: Path, from_settings: bool):
        if target.is_file():
            target = target.parent
        canonical = canonical_pbem_save_dir(target, create=False)
        saves_parent = canonical.parent if canonical.name.lower() == "pbem" else target
        if not canonical.parent.exists() and not saves_parent.exists():
            return
        bts = _bts_root_for_save_folder(canonical)
        score = _score_save_tree(target, bts)
        if score < 0:
            return
        if from_settings:
            score += 220
        bts_key = _norm_path(bts)
        prev = found.get(bts_key)
        if prev is None or score > prev[0]:
            found[bts_key] = (score, canonical)

    for hinted in civ4_settings_save_paths(extra_exes):
        consider(hinted, True)

    for docs in _document_roots():
        for bts in _bts_user_dirs_under(docs):
            for target in _save_targets_for_bts(bts):
                consider(target, False)

    ranked = sorted(found.values(), key=lambda x: x[0], reverse=True)
    for score, path in ranked:
        logger.info("Civ4 save candidate (%s): %s", score, path)
    _CANDIDATE_CACHE[cache_key] = (now, ranked)
    return ranked


def is_civ4_live_save_dir(path_str: str) -> bool:
    """True if this folder has real saves or a live Civ4 auto/pitboss dir."""
    if not path_str:
        return False
    path = Path(path_str)
    if not path.exists():
        return False
    count, _newest = _civ_save_stats(path)
    if count > 0:
        return True
    if _has_nonempty_subdir(path, "auto"):
        return True
    if _has_nonempty_subdir(path, "pitboss") or _has_nonempty_subdir(path, "pithoss"):
        return True
    return False


def same_save_dir(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return _norm_path(Path(a)) == _norm_path(Path(b))


def civ4_exe_paths_for_detection(
    installations: Optional[dict] = None,
    preferred_edition: str = "",
) -> list[str]:
    """Exe paths for save-folder detection.

    When preferred_edition is set, only that install is used so Steam (OneDrive)
    and GOG/DVD save trees do not trigger cross-edition warnings.
    """
    installs = installations or {}
    if preferred_edition:
        cfg = installs.get(preferred_edition, {})
        exe = (cfg or {}).get("exe_path", "")
        if exe:
            return [exe]

    paths: list[str] = []
    for edition in ("steam", "gog", "dvd"):
        cfg = installs.get(edition, {})
        if cfg.get("enabled") and cfg.get("exe_path"):
            paths.append(cfg["exe_path"])
    return paths


def suggested_civ4_save_path(
    configured: str,
    extra_exes: Optional[list[str]] = None,
) -> Optional[str]:
    """If a better Civ4 save folder exists than config, return it."""
    if configured and save_path_from_civ4_settings(configured, extra_exes):
        return None

    ranked = list_civ4_save_candidates(extra_exes)
    if not ranked:
        return None
    live_score, live_path = ranked[0]
    live = str(live_path)
    configured_pbem = str(canonical_pbem_save_dir(configured or "", create=False))
    if configured and same_save_dir(configured_pbem, live):
        return None
    configured_score = -1
    if configured:
        for score, path in ranked:
            if same_save_dir(str(path), configured):
                configured_score = score
                break
        if configured_score < 0:
            cfg = Path(configured)
            bts = cfg
            name = cfg.name.lower()
            if name == "pbem":
                bts = cfg.parent.parent
            elif name == "saves":
                bts = cfg.parent
            configured_score = _score_save_folder(cfg, bts) if cfg.exists() else 0
    if live_score > configured_score + 15:
        return live
    return None


_SKIP_SAVE_SUBDIRS = {"auto", "pitboss", "pithoss"}


def count_saves_in_folder(path_str: str) -> int:
    """Count .CivBeyondSwordSave files in pbem folder (+ stray files in parent Saves)."""
    folder = Path(path_str)
    if not folder.is_dir() and folder.parent.name.lower() != "saves":
        return 0
    canonical = canonical_pbem_save_dir(folder, create=False)
    count, _newest = _civ_save_stats(canonical) if canonical.is_dir() else (0, 0.0)
    if canonical.name.lower() == "pbem":
        parent = canonical.parent
        if parent.is_dir() and parent.name.lower() == "saves":
            root_count, _ = _civ_save_stats(parent)
            count += root_count
    try:
        for sub in canonical.iterdir():
            if not sub.is_dir() or sub.name.lower() in _SKIP_SAVE_SUBDIRS:
                continue
            sub_count, _ = _civ_save_stats(sub)
            count += sub_count
    except Exception:
        pass
    return count


def copy_missing_pbem_saves(src: str, dest: str) -> int:
    """Copy .CivBeyondSwordSave files that exist in src but not dest.

    Also copies one level of game subfolders, skipping auto/pitboss.
    """
    src_p, dest_p = Path(src), Path(dest)
    if not src_p.is_dir():
        return 0
    try:
        dest_p.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.warning("Cannot create destination save folder: %s", dest_p)
        return 0
    if same_save_dir(str(src_p), str(dest_p)):
        return 0

    copied = 0

    def maybe_copy(file: Path, dest_dir: Path):
        nonlocal copied
        dest_file = dest_dir / file.name
        if dest_file.exists():
            return
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dest_file)
            copied += 1
            logger.info("Copied save %s -> %s", file.name, dest_dir)
        except Exception:
            logger.warning("Failed to copy %s", file, exc_info=True)

    for save in src_p.glob("*.CivBeyondSwordSave"):
        maybe_copy(save, dest_p)
    try:
        for sub in src_p.iterdir():
            if not sub.is_dir() or sub.name.lower() in _SKIP_SAVE_SUBDIRS:
                continue
            for save in sub.glob("*.CivBeyondSwordSave"):
                maybe_copy(save, dest_p / sub.name)
    except Exception:
        logger.debug("copy_missing_pbem_saves scan failed", exc_info=True)
    return copied


def detect_save_path(
    extra_exes: Optional[list[str]] = None, force: bool = False
) -> Optional[str]:
    """Auto-detect the PBEM save folder (always Saves\\pbem under the live Civ4 user dir)."""
    ranked = list_civ4_save_candidates(extra_exes, force=force)
    if not ranked:
        return None
    score, path = ranked[0]
    pbem, _mirror = resolve_save_layout(path, create=True)
    logger.info("Auto-detected Civ4 PBEM save path (score %s): %s", score, pbem)
    return pbem


def save_path_from_civ4_settings(
    path: str, extra_exes: Optional[list[str]] = None
) -> bool:
    """True if `path` matches a Saves tree Civ4's shortcuts/ini point at."""
    if not path:
        return False
    ours = _norm_path(canonical_pbem_save_dir(path))
    for hinted in civ4_settings_save_paths(extra_exes):
        if _norm_path(canonical_pbem_save_dir(hinted)) == ours:
            return True
    return False


def ensure_pbem_save_path(extra_exes: Optional[list[str]] = None) -> str:
    """Return Saves\\pbem for the live Civ4 user dir; create folders if needed."""
    ranked = list_civ4_save_candidates(extra_exes)
    if ranked:
        _score, path = ranked[0]
        pbem, _mirror = resolve_save_layout(path, create=True)
        return pbem

    docs = None
    for root in _document_roots():
        if root.is_dir() and "onedrive" in str(root).lower():
            if _child_ci(root, "My Games") is not None:
                docs = root
                break
    if docs is None:
        docs = _windows_known_folder(_FOLDERID_DOCUMENTS) or _windows_documents_csidl()
    if docs is None:
        docs = Path.home() / "Documents"
    saves = docs / "My Games" / "Beyond the Sword" / "Saves"
    saves.mkdir(parents=True, exist_ok=True)
    pbem, _mirror = resolve_save_layout(saves, create=True)
    logger.info("Created Civ4 PBEM save folder: %s", pbem)
    return pbem


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
        for root in _steam_library_roots():
            found = _bts_exe_under(root / "steamapps" / "common" / _STEAM_GAME_FOLDER)
            if found:
                return found

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


def detect_all_editions() -> dict[str, str]:
    """Auto-detect every installed Civ4 BTS edition. edition -> exe path."""
    found: dict[str, str] = {}
    for edition in ("steam", "gog", "dvd"):
        path = detect_civ4_for_edition(edition)
        if path:
            found[edition] = path
            logger.info(f"Auto-detected Civ4 {edition}: {path}")
    return found


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
        try:
            import ctypes
            SHCNE_ASSOCCHANGED = 0x08000000
            SHCNF_IDLIST = 0x0000
            ctypes.windll.shell32.SHChangeNotify(
                SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None
            )
        except Exception:
            pass
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
