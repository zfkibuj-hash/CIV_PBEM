"""
Core data models for games, players, and turns.
"""
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# Optional leading save sequence: 0007_GameName_T0003_from_X_to_Y.CivBeyondSwordSave
# Width grows past 9999 (10000_…); sort/parse use the integer, not fixed 4 digits.
_SAVE_SEQ_RE = re.compile(r"^(\d+)_(.+)$", re.IGNORECASE)
_SAVE_FROM_TO_RE = re.compile(
    r"_T(\d+)_from_(.+)_to_(.+)\.CivBeyondSwordSave$",
    re.IGNORECASE,
)
_SAVE_SENDER_RE = re.compile(r"_T(\d+)_(.+)\.CivBeyondSwordSave$", re.IGNORECASE)
_NATIVE_TO_RE = re.compile(r"_to_(.+)\.CivBeyondSwordSave$", re.IGNORECASE)


def _strip_save_seq_prefix(filename: str) -> tuple[Optional[int], str]:
    """Return (seq_or_None, name_without_optional_N+_ prefix)."""
    name = Path(filename).name
    match = _SAVE_SEQ_RE.match(name)
    if not match:
        return None, name
    rest = match.group(2)
    # Only treat as seq if rest is a managed save (…_T#_…)
    if re.search(r"_T\d+_", rest, re.IGNORECASE) and rest.endswith(
        ".CivBeyondSwordSave"
    ):
        return int(match.group(1)), rest
    return None, name


@dataclass
class Player:
    """A player in the PBEM game."""
    name: str
    email: str
    order: int  # 0-based position in turn order
    civ4_leader: str = ""  # Leader name in Civ4 save (_to_Leader), optional
    # "active" (default), "defeated" (eliminated in-game), or "resigned"
    # (quit voluntarily). Either non-active state removes the player from
    # the turn rotation — see Game.get_following_player / next_player.
    status: str = "active"

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(
            name=data["name"],
            email=data.get("email", ""),
            order=int(data["order"]),
            civ4_leader=data.get("civ4_leader", ""),
            status=data.get("status", "active"),
        )


@dataclass
class Turn:
    """Record of a single turn upload."""
    turn_number: int
    player_name: str
    timestamp: float = field(default_factory=time.time)
    filename: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Turn":
        return cls(**data)


@dataclass
class Game:
    """A PBEM game instance with its own transport configuration."""
    name: str
    players: list[Player] = field(default_factory=list)
    current_turn: int = 0
    current_player_index: int = 0
    history: list[Turn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    transport_config: dict = field(default_factory=dict)
    admin_password: str = ""  # Password required to delete save files
    # Local player alias: maps local config.player_name → game player name
    local_player_alias: str = ""
    # Shared roster claims: game player name → {install_id, local_name, claimed_at}
    # Synced via .config / state.json so two PCs cannot silently pick the same slot.
    player_claims: dict = field(default_factory=dict)
    # Game speed: determines turn-to-year mapping (quick/normal/epic/marathon)
    game_speed: str = "normal"
    # Timestamp of last reminder sent (to avoid spamming)
    last_reminder_sent: float = 0.0
    # Player colors for history display (player_name -> hex color)
    player_colors: dict = field(default_factory=dict)
    # History color mode: "all" (color each player) or "mine" (highlight only own turns)
    history_color_mode: str = "all"
    # Bumped on turn advance, revert, and shared config push so clients
    # can sync even when the turn number goes BACKWARDS (revert).
    state_revision: int = 0
    # Monotonic upload counter — prefix of managed save filenames (0000_, 0001_, …).
    # Independent of Civ round (current_turn). Never reused after revert.
    save_seq: int = 0
    # Roster name of the winner; empty while the game is ongoing.
    winner: str = ""

    @property
    def current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_player_index]

    @property
    def next_player(self) -> Optional[Player]:
        """Next ACTIVE player after current_player_index (defeated/resigned skipped)."""
        if not self.players:
            return None
        n = len(self.players)
        for step in range(1, n + 1):
            idx = (self.current_player_index + step) % n
            if self.players[idx].is_active:
                return self.players[idx]
        # Nobody active (shouldn't happen in practice) — fall back to raw next.
        return self.players[(self.current_player_index + 1) % n]

    def get_player_index(self, player_name: str) -> Optional[int]:
        """Find a player's index by name (case-insensitive, then close match).

        Close match covers export typos (SzyMan vs SzyMen) so import+repair
        still advances the turn pointer from save filenames.
        """
        if not player_name:
            return None
        key = player_name.casefold()
        for i, p in enumerate(self.players):
            if p.name.casefold() == key:
                return i
        import difflib
        names = [p.name for p in self.players]
        close = difflib.get_close_matches(player_name, names, n=1, cutoff=0.75)
        if close:
            for i, p in enumerate(self.players):
                if p.name == close[0]:
                    return i
        return None

    def get_previous_player(self, player_name: str) -> Optional["Player"]:
        """Get the closest ACTIVE player before the given one (circular)."""
        idx = self.get_player_index(player_name)
        if idx is None or not self.players:
            return None
        n = len(self.players)
        for step in range(1, n + 1):
            i = (idx - step) % n
            if self.players[i].is_active:
                return self.players[i]
        return self.players[(idx - 1) % n]

    def get_following_player(self, player_name: str) -> Optional["Player"]:
        """Get the closest ACTIVE player after the given one (circular).

        This is what decides who a save is addressed to next (see
        managed_filename / get_save_filename) — skipping defeated/resigned
        players here is what keeps the PBEM chain from stalling forever on
        someone who is out of the game.
        """
        idx = self.get_player_index(player_name)
        if idx is None or not self.players:
            return None
        n = len(self.players)
        for step in range(1, n + 1):
            i = (idx + step) % n
            if self.players[i].is_active:
                return self.players[i]
        return self.players[(idx + 1) % n]

    def advance_turn(self, filename: str = ""):
        """Move to the next ACTIVE player's turn. If we wrap around, increment turn number."""
        turn_record = Turn(
            turn_number=self.current_turn,
            player_name=self.current_player.name if self.current_player else "unknown",
            filename=filename,
        )
        self.history.append(turn_record)

        n = len(self.players)
        prev_idx = self.current_player_index
        for step in range(1, n + 1):
            idx = (prev_idx + step) % n
            if self.players[idx].is_active:
                self.current_player_index = idx
                break
        else:
            self.current_player_index = (prev_idx + 1) % n
        if self.current_player_index <= prev_idx:
            self.current_turn += 1
        self.bump_revision()

    def set_player_status(self, player_name: str, status: str) -> bool:
        """Mark a player active/defeated/resigned. Returns True if state changed.

        If the player being sidelined currently holds the turn, immediately
        advances current_player_index to the next active player so the game
        doesn't sit forever "waiting" on someone who is out — this is the
        fix for the fatal-flaw case (defeat/resign stalling the whole chain).
        """
        idx = self.get_player_index(player_name)
        if idx is None:
            return False
        player = self.players[idx]
        if player.status == status:
            return False
        player.status = status
        changed = True

        if status != "active" and self.current_player_index == idx:
            self._skip_inactive_current_player()
        self.maybe_declare_winner()
        self.bump_revision()
        return changed

    @property
    def active_players(self) -> list["Player"]:
        return [p for p in self.players if p.is_active]

    @property
    def is_finished(self) -> bool:
        return bool((self.winner or "").strip())

    def maybe_declare_winner(self) -> Optional[str]:
        """If exactly one active player remains and no winner yet, they won."""
        if (self.winner or "").strip():
            return None
        active = self.active_players
        if len(active) != 1:
            return None
        self.winner = active[0].name
        return self.winner

    def roster_event_snapshot(self) -> tuple[dict[str, str], str]:
        """(player→status, winner) for diffing after a sync or edit."""
        return (
            {p.name: (p.status or "active") for p in self.players},
            (self.winner or "").strip(),
        )

    def roster_events_since(
        self, old_status: dict[str, str], old_winner: str,
    ) -> list[dict]:
        """Events since a snapshot: defeated / resigned / revived / won."""
        events: list[dict] = []
        for player in self.players:
            prev = (old_status or {}).get(player.name, "active")
            now = player.status or "active"
            if prev == now:
                continue
            if now == "defeated":
                events.append({"kind": "defeated", "player": player.name})
            elif now == "resigned":
                events.append({"kind": "resigned", "player": player.name})
            elif now == "active" and prev in ("defeated", "resigned"):
                events.append({"kind": "revived", "player": player.name})
        new_winner = (self.winner or "").strip()
        if new_winner and new_winner != (old_winner or "").strip():
            events.append({"kind": "won", "player": new_winner})
        return events

    def apply_roster_from_dict(self, data: dict) -> bool:
        """Apply winner + statuses from turns/state JSON. No revision bump."""
        if not isinstance(data, dict):
            return False
        changed = False
        raw_players = data.get("players")
        if isinstance(raw_players, list):
            remote: list[Player] = []
            for item in raw_players:
                if not isinstance(item, dict) or not item.get("name"):
                    continue
                payload = dict(item)
                payload.setdefault("order", len(remote))
                payload.setdefault("email", "")
                try:
                    remote.append(Player.from_dict(payload))
                except Exception:
                    continue
            if remote and self.merge_player_status(remote):
                changed = True
        if "winner" in data:
            winner = (data.get("winner") or "").strip()
            if winner != (self.winner or "").strip():
                self.winner = winner
                changed = True
        return changed

    def _skip_inactive_current_player(self) -> None:
        """If the current holder is defeated/resigned, move the pointer forward."""
        if not self.players:
            return
        idx = self.current_player_index
        if 0 <= idx < len(self.players) and self.players[idx].is_active:
            return
        n = len(self.players)
        start = idx if 0 <= idx < n else 0
        for step in range(1, n + 1):
            i = (start + step) % n
            if self.players[i].is_active:
                self.current_player_index = i
                return

    def merge_player_status(self, remote_players: list["Player"]) -> bool:
        """Copy roster status from remote without bumping revision."""
        changed = False
        for rp in remote_players:
            idx = self.get_player_index(rp.name)
            if idx is None:
                continue
            new_status = rp.status or "active"
            if self.players[idx].status != new_status:
                self.players[idx].status = new_status
                changed = True
        if changed:
            self._skip_inactive_current_player()
        return changed

    def _claim_slot_key(self, player_name: str) -> Optional[str]:
        if not player_name:
            return None
        fold = player_name.casefold()
        for key in self.player_claims or {}:
            if str(key).casefold() == fold:
                return key
        return None

    def other_install_claim(
        self, player_name: str, install_id: str,
    ) -> Optional[dict]:
        """Claim on this roster slot belonging to a different install, or None."""
        key = self._claim_slot_key(player_name)
        if not key:
            return None
        claim = self.player_claims.get(key) or {}
        other_id = (claim.get("install_id") or "").strip()
        mine = (install_id or "").strip()
        if other_id and mine and other_id != mine:
            return dict(claim)
        return None

    def set_player_claim(
        self, player_name: str, install_id: str, local_name: str = "",
    ) -> None:
        """Claim a roster slot for this install; drop our claim on any other slot."""
        iid = (install_id or "").strip()
        slot = (player_name or "").strip()
        if not iid or not slot:
            return
        kept = {
            k: v for k, v in (self.player_claims or {}).items()
            if (v or {}).get("install_id") != iid
        }
        kept[slot] = {
            "install_id": iid,
            "local_name": (local_name or "").strip(),
            "claimed_at": time.time(),
        }
        self.player_claims = kept

    def apply_remote_claims(self, remote_claims: dict) -> bool:
        """Merge shared claims. Newer claimed_at wins per slot."""
        if not isinstance(remote_claims, dict) or not remote_claims:
            return False
        merged = dict(self.player_claims or {})
        changed = False
        for name, claim in remote_claims.items():
            if not name or not isinstance(claim, dict):
                continue
            rid = (claim.get("install_id") or "").strip()
            if not rid:
                continue
            old = merged.get(name)
            old_ts = float((old or {}).get("claimed_at") or 0)
            new_ts = float(claim.get("claimed_at") or 0)
            if old is None or new_ts >= old_ts:
                if old != claim:
                    merged[name] = {
                        "install_id": rid,
                        "local_name": (claim.get("local_name") or "").strip(),
                        "claimed_at": new_ts,
                    }
                    changed = True
        if changed:
            self.player_claims = merged
        return changed

    def bump_revision(self):
        self.state_revision = int(self.state_revision or 0) + 1

    def managed_save_filename(
        self,
        seq: int,
        turn: int,
        sender: str,
        recipient: str,
    ) -> str:
        """Build `{seq}_{Game}_T####_from_X_to_Y.CivBeyondSwordSave`."""
        def _canon(name: str) -> str:
            idx = self.get_player_index(name)
            if idx is not None:
                return self.players[idx].name
            return (name or "unknown").strip() or "unknown"

        sender = _canon(sender)
        recipient = _canon(recipient)
        seq_i = max(0, int(seq))
        turn_i = max(0, int(turn))
        return (
            f"{seq_i:04d}_{self.name}_T{turn_i:04d}"
            f"_from_{sender}_to_{recipient}.CivBeyondSwordSave"
        )

    def slot_from_save_filename(
        self, filename: str, timestamp: float = 0.0,
    ) -> dict:
        """Parse a managed save name into queue-editor fields."""
        name = Path(filename).name
        seq = self.parse_save_seq(name)
        turn, sender, recipient = self.parse_save_filename(name)
        return {
            "filename": name,
            "seq": int(seq) if seq is not None else 0,
            "turn_number": int(turn) if turn is not None else 0,
            "from_name": sender or "",
            "to_name": recipient or "",
            "timestamp": float(timestamp or 0.0),
        }

    def apply_manual_queue(
        self,
        player_names: list[str],
        slots: list[dict],
        waiting_for: str,
        current_turn: int,
        save_seq: int,
    ) -> str:
        """Replace turn order + history from the queue editor. Empty = ok."""
        names = [n.strip() for n in player_names if (n or "").strip()]
        if not names:
            return "queue_err_no_players"
        if len(names) != len(self.players):
            return "queue_err_player_count"
        existing = {p.name.casefold(): p for p in self.players}
        seen: set[str] = set()
        new_players: list[Player] = []
        for i, name in enumerate(names):
            player = existing.get(name.casefold())
            if player is None:
                return "queue_err_unknown_player"
            fold = player.name.casefold()
            if fold in seen:
                return "queue_err_dup_player"
            seen.add(fold)
            player.order = i
            new_players.append(player)
        self.players = new_players

        history: list[Turn] = []
        known_fn: set[str] = set()
        old_ts = {t.filename: t.timestamp for t in self.history if t.filename}
        for slot in slots or []:
            fn = Path(str(slot.get("filename") or "")).name.strip()
            if not fn:
                return "queue_err_empty_file"
            if fn in known_fn:
                return "queue_err_dup_file"
            known_fn.add(fn)
            sender = (slot.get("from_name") or "").strip()
            if not sender:
                _turn, sender, _to = self.parse_save_filename(fn)
                sender = sender or "?"
            try:
                turn_n = int(slot.get("turn_number") or 0)
            except (TypeError, ValueError):
                turn_n = 0
            ts = slot.get("timestamp")
            try:
                ts_f = float(ts) if ts else 0.0
            except (TypeError, ValueError):
                ts_f = 0.0
            if ts_f <= 0:
                ts_f = float(old_ts.get(fn) or time.time())
            history.append(Turn(
                turn_number=turn_n,
                player_name=sender,
                timestamp=ts_f,
                filename=fn,
            ))
        if not history:
            return "queue_err_no_saves"

        wait = (waiting_for or "").strip()
        idx = self.get_player_index(wait)
        if idx is None:
            return "queue_err_waiting"
        self.history = history
        self.current_player_index = idx
        self.current_turn = max(0, int(current_turn))
        self.save_seq = max(0, int(save_seq))
        self.state_revision = int(self.state_revision or 0) + 5
        return ""

    def revert_to_turn(self, history_index: int) -> Optional["Turn"]:
        """Revert game state to a specific point in history.

        Removes all history entries after the given index and resets
        current_turn and current_player_index to match that point.
        Rewinds save_seq so the next upload continues after the kept save
        (revert to #17 → next file is #18), not a jump to #25.
        Returns the Turn record we reverted to, or None if invalid.
        """
        if history_index < 0 or history_index >= len(self.history):
            return None

        target_turn = self.history[history_index]

        # Remove all history after this point (target is replayed, not kept in history)
        self.history = self.history[:history_index]

        # Reset game state to just before that turn was played
        self.current_turn = target_turn.turn_number

        # Find the player who made that turn and set them as current
        idx = self.get_player_index(target_turn.player_name)
        if idx is not None:
            self.current_player_index = idx

        # Next managed upload continues after the save we reverted to
        seq = self.parse_save_seq(target_turn.filename) if target_turn.filename else None
        if seq is not None:
            self.save_seq = seq + 1
        else:
            # Legacy names: one seq slot per past upload + the kept target
            self.save_seq = len(self.history) + 1

        self.bump_revision()
        return target_turn

    def merge_player_emails(self, remote_players: list["Player"]):
        """Copy non-empty emails from remote players with the same name."""
        by_name = {p.name: p.email for p in remote_players if p.email}
        for player in self.players:
            if player.name in by_name:
                player.email = by_name[player.name]

    def remote_is_newer(self, remote: "Game") -> bool:
        """True if remote should overwrite local turn/history.

        Prefer state_revision so a revert (lower turn, higher revision) syncs.
        Fresh imports (empty history, revision 0) always take remote progress.
        Old files without revision still use turn-forward comparison.

        Never let an empty remote history (e.g. second PC published a blank
        import state.json) wipe a populated local game.
        """
        remote_rev = int(remote.state_revision or 0)
        local_rev = int(self.state_revision or 0)

        # Poison shield: blank state must not overwrite real history
        if self.history and not remote.history:
            return False

        if remote_rev > local_rev:
            return True

        # Imported / empty local game: any remote progress wins
        if not self.history and (
            remote.history
            or remote.current_turn > 0
            or remote.current_player_index > 0
            or remote_rev > 0
        ):
            return True

        if remote_rev == 0 and local_rev == 0:
            return (
                remote.current_turn > self.current_turn
                or (
                    remote.current_turn == self.current_turn
                    and remote.current_player_index > self.current_player_index
                )
                or (
                    remote.current_turn == self.current_turn
                    and remote.current_player_index == self.current_player_index
                    and len(remote.history) > len(self.history)
                )
            )
        return False

    def apply_remote_snapshot(self, remote: "Game") -> bool:
        """Apply a newer remote snapshot (turns, history, emails). Returns True if applied."""
        if not self.remote_is_newer(remote):
            return False
        self.current_turn = remote.current_turn
        self.current_player_index = remote.current_player_index
        self.history = list(remote.history)
        self.state_revision = max(
            int(remote.state_revision or 0),
            int(self.state_revision or 0),
        )
        self.save_seq = max(int(remote.save_seq or 0), int(self.save_seq or 0))
        if remote.game_speed:
            self.game_speed = remote.game_speed
        self.merge_player_emails(remote.players)
        self.merge_player_status(remote.players)
        self.apply_remote_claims(getattr(remote, "player_claims", None) or {})
        remote_winner = (getattr(remote, "winner", None) or "").strip()
        if remote_winner != (self.winner or "").strip():
            self.winner = remote_winner
        if not self.winner:
            self.maybe_declare_winner()
        return True

    def history_save_filenames(self) -> list[str]:
        """Unique managed save names from history (Check/turns.json catalog)."""
        seen: list[str] = []
        known: set[str] = set()
        for turn in self.history:
            name = (turn.filename or "").strip()
            if (
                name
                and name.endswith(".CivBeyondSwordSave")
                and self.save_belongs_to_game(name)
                and name not in known
            ):
                seen.append(name)
                known.add(name)
        return seen

    def incoming_save_filename(self) -> Optional[str]:
        """Save the current player should load (uploaded by the previous player).

        History records who already played. The file for the player who has
        not played yet is the newest uploaded save (seq, then turn) — not
        necessarily history[-1] if local order got scrambled.
        """
        names = self.history_save_filenames()
        latest = self.latest_managed_save(names)
        if latest:
            return latest
        if not self.history:
            return None
        return self.history[-1].filename or None

    @staticmethod
    def payload_state_rank(data: dict) -> tuple[int, int, int]:
        """(revision, save_seq, history_len) — higher tuple wins."""
        if not isinstance(data, dict):
            return (0, 0, 0)
        src = data
        if not data.get("history") and isinstance(data.get("game"), dict):
            src = data["game"]
        hist = src.get("history") or data.get("history") or []
        n = len(hist) if isinstance(hist, list) else 0
        rev = int(data.get("state_revision") or src.get("state_revision") or 0)
        seq = int(data.get("save_seq") or src.get("save_seq") or 0)
        return (rev, seq, n)

    @staticmethod
    def waiting_player_from_payload(data: dict) -> str:
        """Who should play, from latest save name — not a stale waiting_for field."""
        if not isinstance(data, dict):
            return "?"
        src = data
        if not data.get("history") and isinstance(data.get("game"), dict):
            src = data["game"]
        hist = src.get("history") or data.get("history") or []
        names: list[str] = []
        for row in hist:
            if isinstance(row, dict) and row.get("filename"):
                names.append(str(row["filename"]))
        best_fn = None
        best_key = (-1, -1, "")
        for fn in names:
            seq = Game.parse_save_seq(fn)
            turn, _sender, recipient = Game.parse_save_filename(fn)
            key = (seq if seq is not None else -1, turn if turn is not None else -1, fn)
            if key > best_key:
                best_key = key
                best_fn = fn
        if best_fn:
            _t, _s, recipient = Game.parse_save_filename(best_fn)
            if recipient:
                return recipient
        waiting = (data.get("waiting_for") or src.get("waiting_for") or "").strip()
        if waiting:
            return waiting
        players = src.get("players") or data.get("players") or []
        try:
            idx = int(data.get("current_player_index") or src.get("current_player_index") or 0)
        except (TypeError, ValueError):
            idx = 0
        if isinstance(players, list) and 0 <= idx < len(players):
            p = players[idx]
            if isinstance(p, dict) and p.get("name"):
                return str(p["name"])
        return (data.get("winner") or "?") or "?"

    @staticmethod
    def parse_save_seq(filename: str) -> Optional[int]:
        """Leading NNNN_ sequence, or None for legacy names without it."""
        seq, _rest = _strip_save_seq_prefix(filename)
        return seq

    @staticmethod
    def parse_save_filename(
        filename: str,
    ) -> tuple[Optional[int], Optional[str], Optional[str]]:
        """Return (turn, from_player, to_player) from a managed save name.

        New: {seq}_{Game}_T0003_from_{From}_to_{To}.CivBeyondSwordSave
        Prev: {Game}_T0003_from_{From}_to_{To}.CivBeyondSwordSave
        Old:  {Game}_T0003_{From}.CivBeyondSwordSave  (to_player is None)
        """
        _seq, name = _strip_save_seq_prefix(filename)
        match = _SAVE_FROM_TO_RE.search(name)
        if match:
            return int(match.group(1)), match.group(2), match.group(3)
        match = _SAVE_SENDER_RE.search(name)
        if not match:
            return None, None, None
        return int(match.group(1)), match.group(2), None

    def save_route(self, filename: str) -> tuple[str, str]:
        """Who sent the save and who should load it (inferred for old names)."""
        _turn, sender, recipient = self.parse_save_filename(filename)
        from_name = sender or "?"
        if recipient:
            return from_name, recipient
        if sender:
            nxt = self.get_following_player(sender)
            if nxt:
                return from_name, nxt.name
        return from_name, "?"

    def is_save_for_player(self, filename: str, player_name: str) -> bool:
        """True if this save is meant for `player_name` to load."""
        game_name = self.get_game_player_name(player_name)
        if not filename or not game_name:
            return False
        if not self.save_belongs_to_game(filename):
            return False
        _turn, sender, recipient = self.parse_save_filename(filename)
        if recipient:
            return recipient.casefold() == game_name.casefold()
        prev = self.get_previous_player(game_name)
        return bool(prev) and sender is not None and sender.casefold() == prev.name.casefold()

    def save_belongs_to_game(self, filename: str) -> bool:
        """True if filename is this game's managed save.

        Accepts:
          {seq}_{GameName}_T####_...
          {GameName}_T####_...
        """
        _seq, name = _strip_save_seq_prefix(filename)
        prefix = f"{self.name}_T"
        if not name.startswith(prefix):
            return False
        rest = name[len(prefix):]
        return bool(rest) and rest[0].isdigit()

    def native_save_belongs_to_game(self, filename: str) -> bool:
        """Civ4 native name: {GameName}_{date}_to_{Leader}.CivBeyondSwordSave.

        Game name must be a full token: ``Wojna`` does not match ``Wojna3_…``
        or ``Wojna_Extra_…`` (date is a single ``_``-free field such as
        ``4000BC``).
        """
        name = Path(filename).name
        if self.save_belongs_to_game(name):
            return False
        pattern = (
            rf"^{re.escape(self.name)}_[^_]+_to_.+\.CivBeyondSwordSave$"
        )
        return bool(re.match(pattern, name, re.IGNORECASE))

    @staticmethod
    def native_save_recipient(filename: str) -> Optional[str]:
        """Leader or name after _to_ in a Civ4 native save filename."""
        match = _NATIVE_TO_RE.search(Path(filename).name)
        return match.group(1) if match else None

    def is_local_playable_save(self, filename: str) -> bool:
        """True if file is a managed or native Civ4 save for this game."""
        return self.save_belongs_to_game(filename) or self.native_save_belongs_to_game(
            filename,
        )

    def validate_upload_filename(
        self, filename: str, local_player_name: str,
    ) -> tuple[bool, str]:
        """Validate save before upload. Returns (ok, i18n_error_key)."""
        if not self.is_my_turn(local_player_name):
            return False, "upload_not_your_turn"

        nxt = self.next_player
        if not nxt:
            return False, "upload_no_next_player"

        my_name = self.get_game_player_name(local_player_name)
        name = Path(filename).name

        if self.save_belongs_to_game(name):
            _turn, sender, recipient = self.parse_save_filename(name)
            if sender and sender.casefold() != my_name.casefold():
                return False, "upload_wrong_sender"
            if recipient and recipient.casefold() != nxt.name.casefold():
                return False, "upload_wrong_recipient"
            return True, ""

        if self.native_save_belongs_to_game(name):
            target = self.native_save_recipient(name)
            if not target:
                return False, "upload_native_no_to"
            if target.lower() == my_name.lower():
                return False, "upload_still_your_turn"
            next_leader = (nxt.civ4_leader or "").strip()
            if next_leader:
                from src.civ4_save_info import normalize_leader_key
                if normalize_leader_key(target) != normalize_leader_key(next_leader):
                    return False, "upload_wrong_leader"
            return True, ""

        if name.startswith(f"{self.name}_") and name.endswith(".CivBeyondSwordSave"):
            return False, "upload_unrecognized_name"

        return False, "upload_not_this_game"

    @staticmethod
    def match_save_to_game(filename: str, games: list["Game"]) -> Optional["Game"]:
        """Pick the game that owns this file. Longest name wins (Wojna5 over Wojna)."""
        name = Path(filename).name
        managed = [g for g in games if g.save_belongs_to_game(name)]
        if managed:
            return max(managed, key=lambda g: len(g.name))
        native = [g for g in games if g.native_save_belongs_to_game(name)]
        if native:
            return max(native, key=lambda g: len(g.name))
        return None

    def get_save_filename(self, player_name: str) -> str:
        """Managed name: {seq}_{Game}_T0003_from_{Sender}_to_{Next}.CivBeyondSwordSave."""
        sender = self.get_game_player_name(player_name)
        nxt = self.get_following_player(sender) or self.next_player
        recipient = nxt.name if nxt else "unknown"
        seq = int(self.save_seq or 0)
        # At least 4 digits (0007_); grows automatically past 9999 → 10000_
        return (
            f"{seq:04d}_{self.name}_T{self.current_turn:04d}"
            f"_from_{sender}_to_{recipient}.CivBeyondSwordSave"
        )

    def already_uploaded_latest(self, local_player_name: str) -> Optional[str]:
        """If the newest managed save was already sent by this player, return it.

        Stops the same Civ4 file being STOR'd as 0005, then 0006, then 0007
        when the turn pointer snaps back or the watcher fires twice.
        """
        my = self.get_game_player_name(local_player_name)
        latest = self.incoming_save_filename()
        if not my or not latest:
            return None
        _turn, sender, _recipient = self.parse_save_filename(latest)
        if sender and sender.casefold() == my.casefold():
            return latest
        return None

    def bump_save_seq(self):
        """Advance monotonic save counter after a successful upload."""
        self.save_seq = int(self.save_seq or 0) + 1

    def used_save_seqs(self, filenames: list[str]) -> set[int]:
        """Sequence numbers already taken by managed saves (any from/to suffix)."""
        used: set[int] = set()
        for raw in filenames or []:
            if not self.save_belongs_to_game(raw):
                continue
            seq = self.parse_save_seq(raw)
            if seq is not None:
                used.add(seq)
        return used

    def ensure_unique_save_seq(self, filenames: list[str]) -> int:
        """Pick the next unused seq from the server listing — never reuse 0001_.

        Local save_seq is stale on every other PC. Naming an upload from it
        produces a second 0001_… file. Always take max(remote)+1, then skip
        any number still occupied.
        """
        used = self.used_save_seqs(filenames)
        next_seq = (max(used) + 1) if used else 0
        seq = max(int(self.save_seq or 0), next_seq)
        while seq in used:
            seq += 1
        self.save_seq = seq
        return seq

    def sync_save_seq_from_filenames(self, filenames: list[str]) -> bool:
        """Raise save_seq above any remote/local managed save sequence."""
        before = int(self.save_seq or 0)
        self.ensure_unique_save_seq(filenames)
        return int(self.save_seq or 0) > before

    def turn_holder_from_saves(self, filenames: list[str]) -> Optional[str]:
        """Who should play next according to the newest managed save on FTP."""
        latest = self.latest_managed_save(filenames)
        if not latest:
            return None
        return self.recipient_from_save(latest)

    def recipient_from_save(self, filename: str) -> Optional[str]:
        """Player who should load this save (from managed filename)."""
        _turn, sender, recipient = self.parse_save_filename(filename)
        if recipient:
            # Prefer canonical roster spelling
            idx = self.get_player_index(recipient)
            if idx is not None:
                return self.players[idx].name
            return recipient
        if sender:
            nxt = self.get_following_player(sender)
            return nxt.name if nxt else None
        return None

    def latest_managed_save(self, filenames: list[str]) -> Optional[str]:
        """Newest managed save for this game (by seq, then turn, then name)."""
        candidates = [
            f for f in filenames
            if f.endswith(".CivBeyondSwordSave") and self.save_belongs_to_game(f)
        ]
        if not candidates:
            return None

        def sort_key(name: str) -> tuple:
            seq = self.parse_save_seq(name)
            turn, _, _ = self.parse_save_filename(name)
            return (
                seq if seq is not None else -1,
                turn if turn is not None else -1,
                name,
            )

        return sorted(candidates, key=sort_key)[-1]

    def dedupe_duplicate_history(self) -> bool:
        """Drop consecutive history rows pointing at the same save file."""
        changed = False
        i = len(self.history) - 1
        while i > 0:
            cur = self.history[i]
            prev = self.history[i - 1]
            if cur.filename and cur.filename == prev.filename:
                self.history.pop(i)
                changed = True
            i -= 1
        return changed

    def sync_current_player_from_save(self, save_filename: str) -> bool:
        """Align current_player with who should load the latest save."""
        player_name = self.recipient_from_save(save_filename)
        if not player_name:
            return False
        idx = self.get_player_index(player_name)
        if idx is None:
            return False
        # Defensive: a native (non-managed) Civ4 filename could still point at
        # a defeated/resigned player. Skip forward to the next active one so
        # we never get stuck "waiting" on someone who is out of the game.
        if not self.players[idx].is_active:
            n = len(self.players)
            for step in range(1, n + 1):
                i = (idx + step) % n
                if self.players[i].is_active:
                    idx = i
                    break
        if self.current_player_index == idx:
            return False
        self.current_player_index = idx
        self.bump_revision()
        return True

    def merge_history_from_remote_saves(self, remote_filenames: list[str]) -> bool:
        """Add any remote managed saves missing from local history (by filename).

        Other clients only see uploads they made themselves until they sync.
        After Cantrol uploads 0001_, Mihau still only has 0000_ in history —
        without this merge the UI keeps showing 'waiting for Cantrol'.
        """
        managed = [
            f for f in (remote_filenames or [])
            if f.endswith(".CivBeyondSwordSave") and self.save_belongs_to_game(f)
        ]
        if not managed:
            return False

        def sort_key(name: str) -> tuple:
            seq = self.parse_save_seq(name)
            turn, _, _ = self.parse_save_filename(name)
            return (
                seq if seq is not None else -1,
                turn if turn is not None else -1,
                name,
            )

        managed = sorted(managed, key=sort_key)
        known = {t.filename for t in self.history if t.filename}
        changed = False

        for name in managed:
            if name in known:
                continue
            turn, sender, _recipient = self.parse_save_filename(name)
            if turn is None and sender is None:
                continue
            # Prefer roster spelling for the uploader
            player = sender or "?"
            if sender:
                idx = self.get_player_index(sender)
                if idx is not None:
                    player = self.players[idx].name
            self.history.append(Turn(
                turn_number=turn if turn is not None else self.current_turn,
                player_name=player,
                filename=name,
            ))
            known.add(name)
            changed = True

        if changed:
            self.history.sort(
                key=lambda t: sort_key(t.filename) if t.filename else (-1, -1, ""),
            )
        return changed

    def repair_turn_state_from_saves(self, remote_filenames: list[str]) -> bool:
        """Fix history + turn pointer from managed save names (source of truth).

        Incomplete local folders must not win: if history already has 0004
        and the disk only still has 0003, keep 0004 as the current save.
        """
        changed = self.sync_save_seq_from_filenames(remote_filenames)
        if self.merge_history_from_remote_saves(remote_filenames):
            changed = True
        pooled = list(remote_filenames or [])
        pooled.extend(self.history_save_filenames())
        latest = self.latest_managed_save(pooled)
        if not latest:
            latest = self.incoming_save_filename()
        if not latest:
            return changed
        if self.dedupe_duplicate_history():
            changed = True
        turn, _sender, _recipient = self.parse_save_filename(latest)
        # Align round number from save (never lower — seq is the order authority)
        if turn is not None and turn > self.current_turn:
            self.current_turn = turn
            changed = True
        if self.sync_current_player_from_save(latest):
            changed = True
        elif changed:
            self.bump_revision()
        return changed

    def is_my_turn(self, my_name: str) -> bool:
        """Check if it's the given player's turn (supports local_player_alias)."""
        # Empty history = not synced from FTP yet — never pretend it's someone's turn.
        if self.is_finished:
            return False
        if not self.history:
            return False
        if self.current_player is None:
            return False
        if not (my_name or "").strip():
            return False
        game_name = self.get_game_player_name(my_name)
        return self.current_player.name.casefold() == game_name.casefold()

    def get_game_player_name(self, local_name: str) -> str:
        """Resolve local player name to game player name via alias.

        If local_player_alias is set and local_name matches the local nick,
        returns the alias (game player name). Otherwise returns local_name as-is.
        """
        if self.local_player_alias:
            # Check if local_name is the local nick (it always is when called from controller)
            # The alias IS the game player name
            return self.local_player_alias
        return local_name

    def get_my_player(self, local_name: str) -> Optional[Player]:
        """Get the Player object for the local user, resolving alias."""
        game_name = self.get_game_player_name(local_name)
        idx = self.get_player_index(game_name)
        if idx is None:
            return None
        return self.players[idx]

    def turns_log_dict(self) -> dict:
        """Server-side turn log — no passwords, just history + whose turn."""
        waiting = ""
        if self.is_finished:
            waiting = (self.winner or "").strip()
        elif self.current_player:
            waiting = self.current_player.name
        return {
            "format": 1,
            "game": self.name,
            "state_revision": int(self.state_revision or 0),
            "current_turn": int(self.current_turn or 0),
            "current_player_index": int(self.current_player_index or 0),
            "save_seq": int(self.save_seq or 0),
            "updated_at": time.time(),
            "waiting_for": waiting,
            "winner": (self.winner or "").strip(),
            "players": [
                {
                    "name": p.name,
                    "order": p.order,
                    "status": p.status or "active",
                }
                for p in self.players
            ],
            "history": [t.to_dict() for t in self.history],
        }

    def apply_turns_log(self, data: dict) -> bool:
        """Merge a remote `{game}_turns.json` into this game. Returns True if changed.

        Never lets an empty remote log wipe a non-empty local history.
        """
        if not isinstance(data, dict):
            return False
        remote_history_raw = data.get("history") or []
        if not remote_history_raw:
            return False

        remote_history = [
            Turn.from_dict(t) for t in remote_history_raw if isinstance(t, dict)
        ]
        if not remote_history:
            return False

        remote_rev = int(data.get("state_revision", 0) or 0)
        local_rev = int(self.state_revision or 0)
        remote_seq = int(data.get("save_seq", 0) or 0)
        local_seq = int(self.save_seq or 0)

        changed = False

        # Merge any filenames we don't have yet
        known = {t.filename for t in self.history if t.filename}
        for turn in remote_history:
            if turn.filename and turn.filename not in known:
                self.history.append(turn)
                known.add(turn.filename)
                changed = True
            elif not turn.filename:
                # rare: keep by (turn, player, ts)
                key = (turn.turn_number, turn.player_name, turn.timestamp)
                if not any(
                    (h.turn_number, h.player_name, h.timestamp) == key
                    for h in self.history
                ):
                    self.history.append(turn)
                    changed = True

        if changed:
            def _sk(t: Turn) -> tuple:
                seq = self.parse_save_seq(t.filename) if t.filename else -1
                return (
                    seq if seq is not None else -1,
                    int(t.turn_number or 0),
                    t.filename or "",
                )
            self.history.sort(key=_sk)

        # Adopt pointer only when remote is strictly ahead. A shorter/stale
        # turns.json (waiting_for still Mihau, history stopping at 0003)
        # must not rewind a local game that already has 0004.
        adopt_pointer = (
            local_rev == 0 and local_seq == 0 and len(self.history) <= len(remote_history)
        ) or remote_rev > local_rev or remote_seq > local_seq
        if adopt_pointer:
            idx = int(data.get("current_player_index", self.current_player_index) or 0)
            if 0 <= idx < len(self.players) and idx != self.current_player_index:
                self.current_player_index = idx
                changed = True
            turn_n = int(data.get("current_turn", self.current_turn) or 0)
            if turn_n > self.current_turn:
                self.current_turn = turn_n
                changed = True
            if remote_rev > local_rev:
                self.state_revision = remote_rev
                changed = True
            if remote_seq > local_seq:
                self.save_seq = remote_seq
                changed = True

        # If we only merged history, still align pointer from latest save name
        latest = self.incoming_save_filename()
        if latest and self.sync_current_player_from_save(latest):
            changed = True

        if self.apply_roster_from_dict(data):
            changed = True

        return changed

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
            "current_turn": self.current_turn,
            "current_player_index": self.current_player_index,
            "history": [t.to_dict() for t in self.history],
            "created_at": self.created_at,
            "transport_config": self.transport_config,
            "admin_password": self.admin_password,
            "local_player_alias": self.local_player_alias,
            "player_claims": self.player_claims,
            "game_speed": self.game_speed,
            "last_reminder_sent": self.last_reminder_sent,
            "player_colors": self.player_colors,
            "history_color_mode": self.history_color_mode,
            "state_revision": self.state_revision,
            "save_seq": int(self.save_seq or 0),
            "winner": (self.winner or "").strip(),
        }

    def to_dict_safe(self) -> dict:
        """Serialize game data with sensitive fields separated.

        Returns a dict with 'public' (safe to store plain) and
        'sensitive' (should be encrypted) sections.
        """
        public = {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
            "current_turn": self.current_turn,
            "current_player_index": self.current_player_index,
            "history": [t.to_dict() for t in self.history],
            "created_at": self.created_at,
            "local_player_alias": self.local_player_alias,
            "player_claims": self.player_claims,
            "game_speed": self.game_speed,
            "last_reminder_sent": self.last_reminder_sent,
            "player_colors": self.player_colors,
            "history_color_mode": self.history_color_mode,
            "state_revision": self.state_revision,
            "save_seq": int(self.save_seq or 0),
            "winner": (self.winner or "").strip(),
        }
        sensitive = {
            "transport_config": self.transport_config,
            "admin_password": self.admin_password,
        }
        return {"public": public, "sensitive": sensitive}

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        players = [Player.from_dict(p) for p in data.get("players", [])]
        history = [Turn.from_dict(t) for t in data.get("history", [])]
        return cls(
            name=data["name"],
            players=players,
            current_turn=data.get("current_turn", 0),
            current_player_index=data.get("current_player_index", 0),
            history=history,
            created_at=data.get("created_at", time.time()),
            transport_config=data.get("transport_config", {}),
            admin_password=data.get("admin_password", ""),
            local_player_alias=data.get("local_player_alias", ""),
            player_claims=data.get("player_claims") or {},
            game_speed=data.get("game_speed", "normal"),
            last_reminder_sent=data.get("last_reminder_sent", 0.0),
            player_colors=data.get("player_colors", {}),
            history_color_mode=data.get("history_color_mode", "all"),
            state_revision=int(data.get("state_revision", 0) or 0),
            save_seq=int(data.get("save_seq", 0) or 0),
            winner=(data.get("winner") or "").strip(),
        )

    def save_to_file(self, directory: Path, master_password: str = ""):
        """Save game state to a JSON file.

        If master_password is provided, sensitive data (transport credentials,
        admin password) is encrypted. Otherwise stored in plain text for
        backwards compatibility.
        """
        filepath = directory / f"{self.name}.json"

        if master_password:
            from src.crypto import encrypt_data
            data = self.to_dict_safe()
            output = data["public"]
            output["encrypted_sensitive"] = encrypt_data(
                data["sensitive"], master_password
            )
        else:
            output = self.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    def delete_file(self, directory: Path):
        """Delete game state file."""
        filepath = directory / f"{self.name}.json"
        if filepath.exists():
            filepath.unlink()

    @classmethod
    def load_from_file(cls, filepath: Path, master_password: str = "") -> "Game":
        """Load game state from a JSON file.

        If the file contains an 'encrypted_sensitive' section and a
        master_password is provided, decrypts the sensitive fields.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle encrypted format
        if "encrypted_sensitive" in data and master_password:
            from src.crypto import decrypt_data
            sensitive = decrypt_data(data["encrypted_sensitive"], master_password)
            if sensitive:
                data["transport_config"] = sensitive.get("transport_config", {})
                data["admin_password"] = sensitive.get("admin_password", "")
            else:
                # Decryption failed — load without credentials
                data["transport_config"] = {}
                data["admin_password"] = ""
            # Remove the encrypted blob before parsing
            del data["encrypted_sensitive"]
        elif "encrypted_sensitive" in data:
            # No password provided — skip sensitive data
            data["transport_config"] = {}
            data["admin_password"] = ""
            del data["encrypted_sensitive"]

        return cls.from_dict(data)
