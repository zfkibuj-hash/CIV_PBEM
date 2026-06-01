"""
Game statistics module for Civ4 PBEM Manager.
Calculates per-game and per-player statistics from turn history.
"""
import datetime
import time
from dataclasses import dataclass, field
from typing import Optional

from src.models.game import Game, Turn


@dataclass
class PlayerStats:
    """Statistics for a single player in a game."""
    name: str
    total_turns: int = 0
    total_time_seconds: float = 0.0
    fastest_turn_seconds: float = float("inf")
    slowest_turn_seconds: float = 0.0

    @property
    def avg_turn_time_seconds(self) -> float:
        """Average time per turn in seconds."""
        if self.total_turns == 0:
            return 0.0
        return self.total_time_seconds / self.total_turns

    @property
    def fastest_turn_formatted(self) -> str:
        """Fastest turn as human-readable string."""
        if self.fastest_turn_seconds == float("inf"):
            return "-"
        return format_duration(self.fastest_turn_seconds)

    @property
    def slowest_turn_formatted(self) -> str:
        """Slowest turn as human-readable string."""
        if self.slowest_turn_seconds == 0.0:
            return "-"
        return format_duration(self.slowest_turn_seconds)

    @property
    def avg_turn_time_formatted(self) -> str:
        """Average turn time as human-readable string."""
        return format_duration(self.avg_turn_time_seconds)

    @property
    def total_time_formatted(self) -> str:
        """Total time as human-readable string."""
        return format_duration(self.total_time_seconds)


@dataclass
class GameStats:
    """Aggregated statistics for a single game."""
    game_name: str
    total_turns: int = 0
    total_time_seconds: float = 0.0
    avg_turn_time_seconds: float = 0.0
    fastest_turn_seconds: float = float("inf")
    fastest_turn_player: str = ""
    slowest_turn_seconds: float = 0.0
    slowest_turn_player: str = ""
    game_started: Optional[float] = None  # timestamp
    last_activity: Optional[float] = None  # timestamp
    current_round: int = 0
    player_stats: list[PlayerStats] = field(default_factory=list)

    @property
    def total_time_formatted(self) -> str:
        return format_duration(self.total_time_seconds)

    @property
    def avg_turn_time_formatted(self) -> str:
        return format_duration(self.avg_turn_time_seconds)

    @property
    def fastest_turn_formatted(self) -> str:
        if self.fastest_turn_seconds == float("inf"):
            return "-"
        return f"{format_duration(self.fastest_turn_seconds)} ({self.fastest_turn_player})"

    @property
    def slowest_turn_formatted(self) -> str:
        if self.slowest_turn_seconds == 0.0:
            return "-"
        return f"{format_duration(self.slowest_turn_seconds)} ({self.slowest_turn_player})"

    @property
    def game_started_formatted(self) -> str:
        if self.game_started is None:
            return "-"
        dt = datetime.datetime.fromtimestamp(self.game_started)
        return dt.strftime("%Y-%m-%d %H:%M")

    @property
    def last_activity_formatted(self) -> str:
        if self.last_activity is None:
            return "-"
        dt = datetime.datetime.fromtimestamp(self.last_activity)
        return dt.strftime("%Y-%m-%d %H:%M")


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds <= 0:
        return "-"

    total_minutes = int(seconds // 60)
    hours = int(seconds // 3600)
    days = int(seconds // 86400)

    if days > 0:
        remaining_hours = hours % 24
        return f"{days}d {remaining_hours}h"
    elif hours > 0:
        remaining_minutes = total_minutes % 60
        return f"{hours}h {remaining_minutes}m"
    elif total_minutes > 0:
        return f"{total_minutes}m"
    else:
        return "< 1m"


def calculate_game_stats(game: Game) -> GameStats:
    """Calculate comprehensive statistics for a game based on its turn history.

    Turn timing is computed by comparing consecutive timestamps in history.
    Each turn's duration = time from when a player received the save until they sent theirs.
    """
    stats = GameStats(
        game_name=game.name,
        current_round=game.current_turn,
    )

    history = game.history
    if not history:
        stats.game_started = game.created_at
        return stats

    # Game timeline
    stats.game_started = game.created_at
    stats.last_activity = history[-1].timestamp
    stats.total_turns = len(history)

    # Calculate time between consecutive turns
    # Each turn[i] duration = turn[i].timestamp - turn[i-1].timestamp
    # (time between when previous player finished and this player finished)
    player_times: dict[str, list[float]] = {}

    for i, turn in enumerate(history):
        if turn.player_name not in player_times:
            player_times[turn.player_name] = []

        if i == 0:
            # First turn: time from game creation to first upload
            duration = turn.timestamp - game.created_at
        else:
            # Time since previous turn was uploaded
            duration = turn.timestamp - history[i - 1].timestamp

        # Sanity check: ignore negative or extremely short durations
        if duration < 1.0:
            duration = 1.0

        player_times[turn.player_name].append(duration)
        stats.total_time_seconds += duration

        # Track global fastest/slowest
        if duration < stats.fastest_turn_seconds:
            stats.fastest_turn_seconds = duration
            stats.fastest_turn_player = turn.player_name
        if duration > stats.slowest_turn_seconds:
            stats.slowest_turn_seconds = duration
            stats.slowest_turn_player = turn.player_name

    # Average turn time
    if stats.total_turns > 0:
        stats.avg_turn_time_seconds = stats.total_time_seconds / stats.total_turns

    # Per-player statistics
    for player in game.players:
        p_name = player.name
        times = player_times.get(p_name, [])

        p_stats = PlayerStats(name=p_name)
        p_stats.total_turns = len(times)

        if times:
            p_stats.total_time_seconds = sum(times)
            p_stats.fastest_turn_seconds = min(times)
            p_stats.slowest_turn_seconds = max(times)

        stats.player_stats.append(p_stats)

    return stats
