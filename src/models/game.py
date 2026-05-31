"""
Core data models for games, players, and turns.
"""
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Player:
    """A player in the PBEM game."""
    name: str
    email: str
    order: int  # 0-based position in turn order

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(**data)


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
    # e.g. local nick "kiroman" maps to game player "K4arol"
    local_player_alias: str = ""
    # Game speed: determines turn-to-year mapping (quick/normal/epic/marathon)
    game_speed: str = "normal"

    @property
    def current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_player_index]

    @property
    def next_player(self) -> Optional[Player]:
        if not self.players:
            return None
        next_idx = (self.current_player_index + 1) % len(self.players)
        return self.players[next_idx]

    def advance_turn(self, filename: str = ""):
        """Move to the next player's turn. If we wrap around, increment turn number."""
        turn_record = Turn(
            turn_number=self.current_turn,
            player_name=self.current_player.name if self.current_player else "unknown",
            filename=filename,
        )
        self.history.append(turn_record)

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.current_turn += 1

    def revert_to_turn(self, history_index: int) -> Optional["Turn"]:
        """Revert game state to a specific point in history.

        Removes all history entries after the given index and resets
        current_turn and current_player_index to match that point.
        Returns the Turn record we reverted to, or None if invalid.
        """
        if history_index < 0 or history_index >= len(self.history):
            return None

        target_turn = self.history[history_index]

        # Remove all history after this point
        self.history = self.history[:history_index]

        # Reset game state to just before that turn was played
        self.current_turn = target_turn.turn_number

        # Find the player who made that turn and set them as current
        for i, p in enumerate(self.players):
            if p.name == target_turn.player_name:
                self.current_player_index = i
                break

        return target_turn

    def get_save_filename(self, player_name: str) -> str:
        """Generate expected save filename pattern.
        Uses the GAME player name (alias), not the local nick.
        """
        game_name = self.get_game_player_name(player_name)
        return f"{self.name}_T{self.current_turn:04d}_{game_name}.CivBeyondSwordSave"

    def is_my_turn(self, my_name: str) -> bool:
        """Check if it's the given player's turn.
        Supports alias: if local_player_alias is set, uses that for matching.
        """
        if self.current_player is None:
            return False
        game_name = self.get_game_player_name(my_name)
        return self.current_player.name == game_name

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
        for p in self.players:
            if p.name == game_name:
                return p
        return None

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
            "game_speed": self.game_speed,
        }

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
            game_speed=data.get("game_speed", "normal"),
        )

    def save_to_file(self, directory: Path):
        """Save game state to a JSON file."""
        filepath = directory / f"{self.name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def delete_file(self, directory: Path):
        """Delete game state file."""
        filepath = directory / f"{self.name}.json"
        if filepath.exists():
            filepath.unlink()

    @classmethod
    def load_from_file(cls, filepath: Path) -> "Game":
        """Load game state from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
