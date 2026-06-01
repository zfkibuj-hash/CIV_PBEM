"""
Civ4 turn-to-year calendar mapping.

Maps turn numbers to in-game years based on game speed.
Data sourced from Civilization 4: Beyond the Sword game mechanics.

Each speed has "iterations" — ranges of turns with different years-per-turn rates.
"""
from typing import Optional


# Format: list of (num_turns, years_per_turn) tuples for each iteration
# Fractional years_per_turn means multiple turns per year (e.g. 0.5 = 2 turns/year)
SPEED_DATA = {
    "quick": [
        (50, 60),    # 50 turns × 60 years = 3000 years (4000 BC → 1000 BC)
        (30, 40),    # 30 turns × 40 years = 1200 years (1000 BC → 200 AD)
        (20, 30),    # 20 turns × 30 years = 600 years
        (30, 20),    # 30 turns × 20 years = 600 years
        (25, 10),    # 25 turns × 10 years = 250 years
        (40, 5),     # 40 turns × 5 years = 200 years
        (65, 2),     # 65 turns × 2 years = 130 years
        (70, 1),     # 70 turns × 1 year = 70 years → 2050 AD
    ],
    "normal": [
        (75, 40),    # 75 turns × 40 years = 3000 years (4000 BC → 1000 BC)
        (60, 25),    # 60 turns × 25 years = 1500 years
        (25, 20),    # 25 turns × 20 years = 500 years
        (50, 10),    # 50 turns × 10 years = 500 years
        (60, 5),     # 60 turns × 5 years = 300 years
        (50, 2),     # 50 turns × 2 years = 100 years
        (120, 1),    # 120 turns × 1 year = 120 years
        (60, 0.5),   # 60 turns × 0.5 years = 30 years → 2050 AD
    ],
    "epic": [
        (140, 25),   # 140 turns × 25 years = 3500 years (4000 BC → 500 BC)
        (90, 15),    # 90 turns × 15 years = 1350 years
        (40, 10),    # 40 turns × 10 years = 400 years
        (90, 5),     # 90 turns × 5 years = 450 years
        (70, 2),     # 70 turns × 2 years = 140 years
        (100, 1),    # 100 turns × 1 year = 100 years
        (220, 0.5),  # 220 turns × 0.5 years = 110 years → 2050 AD
    ],
    "marathon": [
        (100, 15),   # 100 turns × 15 years = 1500 years (4000 BC → 2500 BC)
        (300, 10),   # 300 turns × 10 years = 3000 years
        (170, 5),    # 170 turns × 5 years = 850 years
        (201, 2),    # 201 turns × 2 years = 402 years
        (129, 1),    # 129 turns × 1 year = 129 years
        (180, 0.5),  # 180 turns × 0.5 years = 90 years
        (264, 0.25), # 264 turns × 0.25 years = 66 years
        (156, 1/12), # 156 turns × 1/12 year = 13 years → 2050 AD
    ],
}

# All speeds start at 4000 BC
START_YEAR = -4000  # negative = BC


def turn_to_year(turn: int, speed: str = "normal") -> float:
    """Convert a turn number to a game year.

    Args:
        turn: Turn number (0-based, turn 0 = start of game = 4000 BC)
        speed: Game speed ("quick", "normal", "epic", "marathon")

    Returns:
        Year as float. Negative = BC, positive = AD.
        e.g. -4000 = 4000 BC, 100 = 100 AD
    """
    data = SPEED_DATA.get(speed, SPEED_DATA["normal"])
    year = float(START_YEAR)
    remaining = turn

    for num_turns, years_per_turn in data:
        if remaining <= 0:
            break
        turns_in_this_range = min(remaining, num_turns)
        year += turns_in_this_range * years_per_turn
        remaining -= turns_in_this_range

    # If turn exceeds all ranges, continue with last rate
    if remaining > 0 and data:
        _, last_rate = data[-1]
        year += remaining * last_rate

    return year


def format_game_year(year: float) -> str:
    """Format a game year to a human-readable string.

    Examples:
        -4000 → "4000 BC"
        -500  → "500 BC"
        0     → "1 AD"
        100   → "100 AD"
        1980.5 → "1980 AD"
    """
    if year < 0:
        return f"{int(abs(year))} BC"
    elif year == 0:
        return "1 AD"
    else:
        return f"{int(year)} AD"


def turn_to_year_str(turn: int, speed: str = "normal") -> str:
    """Convert turn number to formatted game year string.

    Args:
        turn: Turn number (0-based)
        speed: Game speed

    Returns:
        Formatted string like "4000 BC", "100 AD", "1980 AD"
    """
    year = turn_to_year(turn, speed)
    return format_game_year(year)


def get_total_turns(speed: str = "normal") -> int:
    """Get total number of turns for a game speed."""
    data = SPEED_DATA.get(speed, SPEED_DATA["normal"])
    return sum(num_turns for num_turns, _ in data)


def get_available_speeds() -> list[str]:
    """Get list of available game speed names."""
    return list(SPEED_DATA.keys())
