"""Save-folder helpers: program folder + optional Civ4 mirror.

Civ4 PBEM layout:
  Saves/pbem/<GameName>/*.CivBeyondSwordSave

The manager keeps config.save_path at Saves/pbem and stores each game's
files in a subfolder named like the Civ4 game folder.
"""
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

SAVE_EXTENSION = ".CivBeyondSwordSave"
_SKIP_GAME_SUBDIRS = {"auto", "pitboss", "pithoss"}
_GAME_PREFIX_RE = re.compile(r"^(?:\d+_)?(.+?)_T\d+_", re.IGNORECASE)


def _norm(path: Path) -> str:
    try:
        return str(path.resolve()).lower()
    except Exception:
        return str(path).lower()


def path_has_non_ascii(path: str) -> bool:
    return any(ord(ch) > 127 for ch in path or "")


def unique_dirs(raw_paths: Iterable[str | Path]) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for raw in raw_paths:
        if not raw:
            continue
        path = Path(raw)
        key = _norm(path)
        if key in seen:
            continue
        seen.add(key)
        found.append(path)
    return found


def game_name_from_save(filename: str) -> str:
    """Extract game prefix from a standardized save filename."""
    match = _GAME_PREFIX_RE.match(Path(filename).name)
    return match.group(1) if match else ""


def discover_game_folder(save_path: str, game_name: str) -> str:
    """Resolve Civ4 subfolder under Saves/pbem for this game."""
    if not game_name:
        return ""
    root = Path(save_path)
    direct = root / game_name
    if direct.is_dir():
        return game_name
    prefix = f"{game_name}_T"
    seq_prefix_re = re.compile(rf"^\d+_{re.escape(game_name)}_T", re.IGNORECASE)
    if root.is_dir():
        try:
            for sub in sorted(root.iterdir()):
                if not sub.is_dir() or sub.name.lower() in _SKIP_GAME_SUBDIRS:
                    continue
                for save in sub.glob(f"*{SAVE_EXTENSION}"):
                    if save.name.startswith(prefix) or seq_prefix_re.match(save.name):
                        return sub.name
        except Exception:
            pass
    return game_name


def game_save_folder(save_path: str, game_name: str, *, create: bool = False) -> Path:
    """Saves/pbem/<GameName>/"""
    folder_name = discover_game_folder(save_path, game_name)
    folder = Path(save_path) / folder_name
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def local_save_path(
    save_path: str, game_name: str, filename: str, *, create: bool = False,
) -> Path:
    return game_save_folder(save_path, game_name, create=create) / filename


def _pbem_under_saves(root: Path) -> Path:
    if root.name.lower() == "pbem":
        return root
    if root.name.lower() == "saves":
        return root / "pbem"
    return root


def mirror_game_folders(
    save_path: str,
    civ4_save_path: str,
    game_name: str,
    mirror_saves: bool,
) -> list[Path]:
    """Destination game folders for mirroring (same layout as Civ4)."""
    folder_name = discover_game_folder(save_path, game_name)
    dests: list[Path] = [game_save_folder(save_path, game_name, create=False)]
    if not mirror_saves or not (civ4_save_path or "").strip():
        return unique_dirs(dests)

    civ4 = Path(civ4_save_path.strip())
    pbem = _pbem_under_saves(civ4)
    dests.append(pbem / folder_name)
    return unique_dirs(dests)


def expand_saves_siblings(path: Path) -> list[Path]:
    """If path is pbem, also include parent Saves (and vice versa)."""
    name = path.name.lower()
    extra: list[Path] = []
    if name == "pbem":
        extra.append(path.parent)
    elif name == "saves":
        extra.append(path / "pbem")
    return extra


def iter_save_dirs(
    save_path: str,
    civ4_save_path: str = "",
    mirror_saves: bool = True,
) -> list[Path]:
    """Root folders (Saves/pbem and optional Civ4 mirror roots)."""
    raw: list[str] = [save_path]
    if mirror_saves:
        if (civ4_save_path or "").strip():
            raw.append(civ4_save_path.strip())
        else:
            try:
                from src.launcher import detect_save_path
                detected = detect_save_path()
                if detected:
                    raw.append(detected)
            except Exception:
                logger.debug("detect_save_path for mirror failed", exc_info=True)

    dirs = unique_dirs(raw)
    if mirror_saves:
        sibling_raw: list[str] = []
        for folder in dirs:
            sibling_raw.extend(str(p) for p in expand_saves_siblings(folder))
        dirs = unique_dirs([str(p) for p in dirs] + sibling_raw)
    return dirs


def iter_watch_dirs(
    save_path: str,
    civ4_save_path: str = "",
    mirror_saves: bool = True,
) -> list[Path]:
    """Watch pbem roots and each per-game subfolder (where Civ4 writes saves)."""
    paths: list[Path] = []
    for root in iter_save_dirs(save_path, civ4_save_path, mirror_saves):
        paths.append(root)
        if root.name.lower() not in ("pbem", "saves"):
            continue
        pbem = root if root.name.lower() == "pbem" else root / "pbem"
        if pbem.is_dir():
            if pbem not in paths:
                paths.append(pbem)
            try:
                for sub in pbem.iterdir():
                    if sub.is_dir() and sub.name.lower() not in _SKIP_GAME_SUBDIRS:
                        paths.append(sub)
            except Exception:
                pass
    return unique_dirs(paths)


def migrate_flat_pbem_saves(save_path: str) -> int:
    """Move legacy saves sitting directly in Saves/pbem into game subfolders."""
    root = Path(save_path)
    if root.name.lower() != "pbem" or not root.is_dir():
        return 0
    moved = 0
    for save in list(root.glob(f"*{SAVE_EXTENSION}")):
        gname = game_name_from_save(save.name)
        if not gname:
            continue
        dest_dir = root / discover_game_folder(save_path, gname)
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / save.name
            if dest.exists():
                continue
            shutil.move(str(save), str(dest))
            moved += 1
            logger.info("Moved save into game folder: %s -> %s", save.name, dest_dir)
        except Exception:
            logger.warning("Failed to migrate %s", save, exc_info=True)
    return moved


def copy_save_to_dirs(
    src: Path,
    dest_dirs: Iterable[Path],
    watcher=None,
) -> list[Path]:
    """Copy one save file into each destination game folder."""
    written: list[Path] = []
    if not src.exists() or not src.is_file():
        return written
    src_key = _norm(src)
    for dest_dir in dest_dirs:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.warning("Cannot create save folder: %s", dest_dir)
            continue
        dest = dest_dir / src.name
        dest_key = _norm(dest)
        if dest_key == src_key:
            written.append(dest)
            continue
        if dest.exists():
            try:
                if dest.stat().st_size == src.stat().st_size:
                    written.append(dest)
                    continue
            except Exception:
                pass
        try:
            if watcher:
                watcher.ignore_next(str(dest))
            shutil.copy2(src, dest)
            written.append(dest)
            logger.info("Mirrored save %s -> %s", src.name, dest_dir)
        except Exception:
            logger.warning("Failed to mirror %s to %s", src.name, dest_dir, exc_info=True)
    return written


def mirror_downloaded_save(
    src: Path,
    save_path: str,
    civ4_save_path: str = "",
    game_name: str = "",
    mirror_saves: bool = True,
    watcher=None,
) -> list[Path]:
    dests = mirror_game_folders(save_path, civ4_save_path, game_name, mirror_saves)
    return copy_save_to_dirs(src, dests, watcher=watcher)


def _search_bases(dirs: Iterable[Path], game_name: str = "") -> list[Path]:
    bases: list[Path] = []
    for folder in dirs:
        if not folder.exists():
            continue
        if game_name:
            bases.append(game_save_folder(str(folder), game_name, create=False))
            bases.append(folder)
            continue
        bases.append(folder)
        if folder.name.lower() != "pbem":
            continue
        try:
            for sub in folder.iterdir():
                if sub.is_dir() and sub.name.lower() not in _SKIP_GAME_SUBDIRS:
                    bases.append(sub)
        except Exception:
            pass
    return unique_dirs(bases)


def find_save_file(
    filename: str,
    save_path: str,
    civ4_save_path: str = "",
    mirror_saves: bool = True,
    prefer_civ4: bool = False,
    game_name: str = "",
) -> Optional[Path]:
    gname = game_name or game_name_from_save(filename)
    dirs = iter_save_dirs(save_path, civ4_save_path, mirror_saves)
    bases = _search_bases(dirs, gname)

    if prefer_civ4 and civ4_save_path and gname:
        for dest in mirror_game_folders(save_path, civ4_save_path, gname, mirror_saves):
            preferred = dest / filename
            if preferred.exists():
                return preferred

    seen: set[str] = set()
    for folder in bases:
        key = _norm(folder)
        if key in seen:
            continue
        seen.add(key)
        candidate = folder / filename
        if candidate.exists():
            return candidate
    return None


def glob_saves(
    pattern: str,
    dirs: Iterable[Path],
    game_name: str = "",
) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for folder in _search_bases(dirs, game_name):
        if not folder.exists():
            continue
        try:
            matches = list(folder.glob(pattern))
        except Exception:
            continue
        for path in matches:
            key = _norm(path)
            if key in seen:
                continue
            seen.add(key)
            found.append(path)
    return found


def latest_game_save(game, dirs: Iterable[Path]) -> Optional[Path]:
    """Newest local save for a game (managed or Civ4 native naming).

    Matches both legacy `{Game}_T…` / `{Game}_*_to_…` and seq-prefixed
    `{NNNN}_{Game}_T…` files.
    """
    patterns = (
        f"{game.name}_*.CivBeyondSwordSave",
        f"*_{game.name}_*.CivBeyondSwordSave",
    )
    saves: list[Path] = []
    for pattern in patterns:
        saves.extend(glob_saves(pattern, dirs, game.name))
    # Dedupe by path
    seen: set[str] = set()
    unique: list[Path] = []
    for path in saves:
        key = _norm(path)
        if key in seen:
            continue
        seen.add(key)
        if game.is_local_playable_save(path.name):
            unique.append(path)
    if not unique:
        return None

    def sort_key(path: Path) -> tuple:
        seq = game.parse_save_seq(path.name)
        turn, _, _ = game.parse_save_filename(path.name)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        return (
            seq if seq is not None else -1,
            turn if turn is not None else -1,
            mtime,
        )

    unique.sort(key=sort_key, reverse=True)
    return unique[0]
