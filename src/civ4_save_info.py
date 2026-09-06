"""
Read human-visible leader / civilization names from a Civ4 BTS save header.

CvInitCore stores arrays of length-prefixed UTF-16LE strings (CvWString):
uint32 char_count, then UTF-16LE characters (no trailing NUL in the count).
"""
from __future__ import annotations

import logging
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# BTS default MAX_CIV_PLAYERS
_MAX_PLAYERS = 19


@dataclass(frozen=True)
class SavePlayerSlot:
    """One civ slot from the save header."""

    index: int
    leader_name: str  # Diplomacy / custom name (often the leader)
    civ_name: str  # Long civ description, e.g. "Greek Empire"

    @property
    def label(self) -> str:
        leader = self.leader_name.strip() or f"#{self.index}"
        civ = self.civ_name.strip()
        if civ:
            return f"{leader} — {civ}"
        return leader


@dataclass(frozen=True)
class Civ4SaveInfo:
    path: Path
    game_name: str
    map_script: str
    players: list[SavePlayerSlot]

    @property
    def leader_names(self) -> list[str]:
        return [p.leader_name for p in self.players if p.leader_name]


def normalize_leader_key(name: str) -> str:
    """Compare leader names from UI / native `_to_` filenames."""
    return (name or "").replace(" ", "_").casefold()


def _read_wsz(data: bytes, offset: int) -> tuple[Optional[str], int]:
    if offset + 4 > len(data):
        return None, offset
    n = struct.unpack_from("<I", data, offset)[0]
    if n > 512:
        return None, offset
    end = offset + 4 + n * 2
    if end > len(data):
        return None, offset
    try:
        text = data[offset + 4 : end].decode("utf-16-le")
    except UnicodeDecodeError:
        return None, offset
    return text, end


def _read_wsz_array(data: bytes, offset: int, count: int = _MAX_PLAYERS) -> tuple[list[str], int]:
    items: list[str] = []
    cur = offset
    for _ in range(count):
        if cur + 4 > len(data):
            break
        n = struct.unpack_from("<I", data, cur)[0]
        if n > 512:
            break
        text, cur = _read_wsz(data, cur)
        items.append(text if text is not None else "")
    return items, cur


def _looks_like_player_name(value: str) -> bool:
    s = (value or "").strip()
    if not s or len(s) > 40:
        return False
    if any(ord(c) < 32 for c in s):
        return False
    # Hashes / paths are not leader names
    if len(s) == 32 and all(c in "0123456789abcdef" for c in s.lower()):
        return False
    if "/" in s or "\\" in s:
        return False
    return True


def parse_civ4_save(path: Path | str) -> Optional[Civ4SaveInfo]:
    """Parse leader/civ slots from a .CivBeyondSwordSave header. None on failure."""
    try:
        raw_path = Path(path)
        data = raw_path.read_bytes()
    except Exception as e:
        logger.warning("Cannot read save %s: %s", path, e)
        return None

    if len(data) < 80:
        return None

    game_name = ""
    map_script = ""
    # Game name is typically the first CvWString near the start of CvInitCore.
    for start in range(40, 80):
        name, _ = _read_wsz(data, start)
        if name and _looks_like_player_name(name) and " " not in name[:1]:
            game_name = name
            break

    best: Optional[tuple[int, int, list[str], list[str]]] = None
    # Leader-name array sits after options/flags; scan a small window.
    for start in range(120, min(600, len(data) - 80)):
        leaders, mid = _read_wsz_array(data, start, _MAX_PLAYERS)
        if len(leaders) < 4:
            continue
        nonempty = [x for x in leaders if x]
        if len(nonempty) < 2:
            continue
        if not all(_looks_like_player_name(x) for x in nonempty):
            continue
        # Remaining slots should mostly be empty (padding to MAX_PLAYERS)
        empty_tail = sum(1 for x in leaders[len(nonempty) :] if not x)
        if empty_tail < 2 and len(nonempty) < 8:
            # Still accept denser games
            pass
        civs, _end = _read_wsz_array(data, mid, _MAX_PLAYERS)
        if len(civs) < len(leaders):
            continue
        civ_hits = sum(1 for c in civs if c and _looks_like_player_name(c))
        score = len(nonempty) * 10 + civ_hits
        # Prefer arrays that start with a non-empty leader
        if not leaders[0]:
            score -= 5
        if best is None or score > best[0]:
            best = (score, start, leaders, civs)

    if best is None:
        logger.info("No player slots found in %s", path)
        return None

    _score, _start, leaders, civs = best
    # Map script: first plausible wsz after game name (often Great_Plains etc.)
    for start in range(48, 160):
        text, _ = _read_wsz(data, start)
        if text and "_" in text and _looks_like_player_name(text):
            map_script = text
            break

    players: list[SavePlayerSlot] = []
    for i, leader in enumerate(leaders):
        civ = civs[i] if i < len(civs) else ""
        if not leader and not civ:
            continue
        if not leader and not _looks_like_player_name(civ):
            continue
        players.append(
            SavePlayerSlot(
                index=i,
                leader_name=(leader or "").strip(),
                civ_name=(civ or "").strip(),
            )
        )

    if not players:
        return None

    return Civ4SaveInfo(
        path=raw_path,
        game_name=game_name,
        map_script=map_script,
        players=players,
    )


def filename_has_game_token(filename: str, game_name: str) -> bool:
    """True if *game_name* appears as a ``_``-bounded token, not a prefix.

    ``Wojna`` matches ``Wojna_T0001_…`` / ``0007_Wojna_T0001_…`` /
    ``Wojna_4000BC_to_X.CivBeyondSwordSave``. It does not match ``Wojna3_…``.
    """
    needle = (game_name or "").strip()
    if not needle:
        return False
    return bool(
        re.search(
            rf"(?:^|_){re.escape(needle)}_",
            Path(filename).name,
            re.IGNORECASE,
        )
    )


def find_latest_game_save(
    game_name: str,
    search_dirs: list[Path | str],
) -> Optional[Path]:
    """Newest .CivBeyondSwordSave whose name contains the game name as a token."""
    candidates: list[Path] = []
    if not (game_name or "").strip():
        return None
    for raw in search_dirs:
        root = Path(raw)
        if not root.is_dir():
            continue
        try:
            for path in root.rglob("*.CivBeyondSwordSave"):
                if filename_has_game_token(path.name, game_name):
                    candidates.append(path)
        except Exception:
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)
