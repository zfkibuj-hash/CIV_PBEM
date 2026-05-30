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
    """A PBEM game instance."""
    name: str
    players: list[Player] = field(default_factory=list)
    current_turn: int = 0
    current_player_index: int = 0
    history: list[Turn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

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

    def get_save_filename(self, player_name: str) -> str:
        """Generate expected save filename pattern."""
        return f"{self.name}_T{self.current_turn:04d}_{player_name}.CivBeyondSwordSave"

    def is_my_turn(self, my_name: str) -> bool:
        """Check if it's the given player's turn."""
        if self.current_player is None:
            return False
        return self.current_player.name == my_name

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
            "current_turn": self.current_turn,
            "current_player_index": self.current_player_index,
            "history": [t.to_dict() for t in self.history],
            "created_at": self.created_at,
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
        )

    def save_to_file(self, directory: Path):
        """Save game state to a JSON file."""
        filepath = directory / f"{self.name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: Path) -> "Game":
        """Load game state from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
