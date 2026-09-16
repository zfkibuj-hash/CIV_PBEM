"""
Read metadata from a Civ4 BTS ``.CivBeyondSwordSave`` file.

CvInitCore (uncompressed header) stores length-prefixed UTF-16LE strings
(CvWString: uint32 char_count, then UTF-16LE characters) plus enums for
world size / era / **game speed** / calendar and ``game_turn``.

The zlib body also carries per-player flags including ``turnActive`` used to
reject mid-turn PBEM uploads.
"""
from __future__ import annotations

import logging
import re
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# BTS default MAX_CIV_PLAYERS
_MAX_PLAYERS = 19
# Vanilla BTS GameOptionTypes count used by InitCore bool array
_NUM_GAME_OPTIONS = 24

# GameSpeedTypes in XML order (Civ4 BTS)
_SPEED_BY_ENUM = {
    0: "marathon",
    1: "epic",
    2: "normal",
    3: "quick",
}


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


@dataclass(frozen=True)
class Civ4SaveMeta:
    """InitCore + best-effort turnActive flags from the compressed body."""

    path: Path
    game_name: str = ""
    map_script: str = ""
    game_speed: str = ""  # marathon|epic|normal|quick
    game_turn: Optional[int] = None
    leaders: list[str] = field(default_factory=list)
    # player eID -> turnActive (only when detection succeeded)
    turn_active: dict[int, bool] = field(default_factory=dict)

    def leader_index(self, name: str) -> Optional[int]:
        key = normalize_leader_key(name)
        if not key:
            return None
        for i, leader in enumerate(self.leaders):
            if normalize_leader_key(leader) == key:
                return i
        return None

    def is_midturn_handoff(
        self, sender_leader: str, recipient_leader: str,
    ) -> Optional[bool]:
        """True if sender still turn-active and recipient is not.

        Returns None when flags could not be read reliably (caller should
        fail open).
        """
        if not self.turn_active:
            return None
        sid = self.leader_index(sender_leader)
        rid = self.leader_index(recipient_leader)
        if sid is None or rid is None:
            return None
        if sid not in self.turn_active or rid not in self.turn_active:
            return None
        return bool(self.turn_active[sid]) and not bool(self.turn_active[rid])


def normalize_leader_key(name: str) -> str:
    """Compare leader names from UI / native ``_to_`` filenames."""
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


def _split_save(data: bytes) -> tuple[bytes, bytes]:
    """Return (header_before_zlib, decompressed_body). Body may be empty."""
    z = data.find(b"\x78\x9c")
    if z < 0:
        return data, b""
    low, high, prev, guesses = z, len(data), 0, 0
    zend = z
    while True:
        zend = (low + high) // 2
        if zend == prev or guesses > 50:
            break
        try:
            zlib.decompress(data[z:zend])
            break
        except Exception as ex:
            prev = zend
            guesses += 1
            if "incomplete" in str(ex).lower():
                low = zend + 1
            else:
                high = zend - 1
    try:
        body = zlib.decompressobj().decompress(data[z:zend])
    except Exception:
        body = b""
    return data[:z], body


def _parse_init_core(header: bytes) -> Optional[dict]:
    """Parse CvInitCore fields from the pre-zlib header. None on failure."""
    if len(header) < 80:
        return None
    off = 0
    try:
        off += 4  # version
        off += 32  # save bits
        off += 4  # bytes to zlib
        off += 4  # save flag
        off += 4  # game type
        game_name, off = _read_wsz(header, off)
        if game_name is None:
            return None
        _, off = _read_wsz(header, off)  # game password
        _, off = _read_wsz(header, off)  # admin password
        map_script, off = _read_wsz(header, off)
        if map_script is None:
            map_script = ""
        off += 1  # wb_map_no_players
        # world, climate, sea, era, speed, timer, calendar
        if off + 28 > len(header):
            return None
        _world, _climate, _sea, _era, speed_i, _timer, _cal = struct.unpack_from(
            "<7i", header, off,
        )
        off += 28
        ncustom = struct.unpack_from("<i", header, off)[0]
        off += 4
        nhidden = struct.unpack_from("<i", header, off)[0]
        off += 4
        if ncustom < 0 or ncustom > 64 or nhidden < 0 or nhidden > 64:
            return None
        off += 4 * ncustom
        nvict = struct.unpack_from("<i", header, off)[0]
        off += 4
        if nvict < 0 or nvict > 64:
            return None
        off += nvict
        base_after_vict = off

        best: Optional[dict] = None
        for num_mp in range(1, 20):
            o = base_after_vict + _NUM_GAME_OPTIONS + num_mp + 1
            if o + 24 > len(header):
                break
            game_turn = struct.unpack_from("<i", header, o)[0]
            if not (0 <= game_turn <= 2000):
                continue
            o2 = o + 4 + 20  # skip maxturns/pitboss/target/elim/adv
            leaders, _ = _read_wsz_array(header, o2, _MAX_PLAYERS)
            nonempty = [x for x in leaders if x]
            if len(nonempty) < 2:
                continue
            if not all(_looks_like_player_name(x) for x in nonempty):
                continue
            # Prefer arrays that start with a filled slot 0
            score = len(nonempty) * 10 + (5 if leaders and leaders[0] else 0)
            cand = {
                "game_name": (game_name or "").strip(),
                "map_script": (map_script or "").strip(),
                "game_speed": _SPEED_BY_ENUM.get(speed_i, ""),
                "game_speed_raw": speed_i,
                "game_turn": game_turn,
                "leaders": leaders,
                "num_mp": num_mp,
                "score": score,
            }
            if best is None or score > best["score"]:
                best = cand
                # Strong match: first leader looks like a real name
                if leaders and leaders[0] and _looks_like_player_name(leaders[0]):
                    # keep searching for denser matches but this is good enough
                    if len(nonempty) >= 3:
                        break
        return best
    except Exception:
        logger.debug("InitCore parse failed", exc_info=True)
        return None


def _find_eid_flags(body: bytes, start: int, eid: int) -> list[tuple[int, list[int]]]:
    out: list[tuple[int, list[int]]] = []
    for i in range(start, len(body) - 13):
        if struct.unpack_from("<i", body, i + 9)[0] != eid:
            continue
        flags = list(body[i : i + 9])
        if any(f > 1 for f in flags):
            continue
        if flags[0] != 1 or flags[1] != 1:  # alive, everAlive
            continue
        out.append((i, flags))
    return out


def _detect_turn_active(body: bytes, num_players: int) -> dict[int, bool]:
    """Best-effort turnActive map keyed by player eID.

    Scans the latter half of the decompressed body for CvPlayer flag blocks.
    Returns {} when the chain cannot be resolved.
    """
    if not body or num_players < 2:
        return {}
    n = min(num_players, 8)
    start = int(len(body) * 0.55)
    # Anchor on player 1 when present (often unique spacing), else player 0
    anchor_eid = 1 if n > 1 else 0
    anchors = _find_eid_flags(body, start, anchor_eid)
    if not anchors:
        anchors = _find_eid_flags(body, start, 0)
        anchor_eid = 0
    if not anchors:
        return {}
    preferred = [a for a in anchors if a[1][2] or a[1][5]] or anchors
    a_off, a_flags = preferred[0]

    chain: dict[int, list[int]] = {anchor_eid: a_flags}
    # Walk downward
    pos = a_off
    for e in range(anchor_eid - 1, -1, -1):
        cands = [c for c in _find_eid_flags(body, start, e) if c[0] < pos]
        if not cands:
            return {}
        off, flags = max(cands, key=lambda c: c[0])
        chain[e] = flags
        pos = off
    # Walk upward
    pos = a_off
    for e in range(anchor_eid + 1, n):
        cands = [c for c in _find_eid_flags(body, start, e) if c[0] > pos]
        if not cands:
            return {}
        off, flags = min(cands, key=lambda c: c[0])
        chain[e] = flags
        pos = off

    return {e: bool(flags[2]) for e, flags in chain.items()}


def parse_civ4_save_meta(path: Path | str) -> Optional[Civ4SaveMeta]:
    """Parse game speed, turn, leaders, and turnActive flags. None on failure."""
    try:
        raw_path = Path(path)
        data = raw_path.read_bytes()
    except Exception as e:
        logger.warning("Cannot read save %s: %s", path, e)
        return None
    if len(data) < 80:
        return None

    header, body = _split_save(data)
    core = _parse_init_core(header)
    if not core:
        return None

    leaders = [x for x in core["leaders"] if x]
    turn_active: dict[int, bool] = {}
    try:
        turn_active = _detect_turn_active(body, len(leaders))
    except Exception:
        logger.debug("turnActive detect failed for %s", path, exc_info=True)

    speed = core.get("game_speed") or ""
    return Civ4SaveMeta(
        path=raw_path,
        game_name=core.get("game_name") or "",
        map_script=core.get("map_script") or "",
        game_speed=speed,
        game_turn=core.get("game_turn"),
        leaders=leaders,
        turn_active=turn_active,
    )


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
        civs, _end = _read_wsz_array(data, mid, _MAX_PLAYERS)
        if len(civs) < len(leaders):
            continue
        civ_hits = sum(1 for c in civs if c and _looks_like_player_name(c))
        score = len(nonempty) * 10 + civ_hits
        if not leaders[0]:
            score -= 5
        if best is None or score > best[0]:
            best = (score, start, leaders, civs)

    if best is None:
        # Fall back to structured InitCore parse
        meta = parse_civ4_save_meta(raw_path)
        if meta and meta.leaders:
            players = [
                SavePlayerSlot(index=i, leader_name=name, civ_name="")
                for i, name in enumerate(meta.leaders)
            ]
            return Civ4SaveInfo(
                path=raw_path,
                game_name=meta.game_name or game_name,
                map_script=meta.map_script or map_script,
                players=players,
            )
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
