"""Civilization-style random PBEM game names.

Must stay inside [A-Za-z0-9_-] because the name is a folder, email subject,
and save-file prefix.
"""
from __future__ import annotations

import random
from typing import Iterable

_PREFIXES = (
    "ClashOf", "BattleFor", "WarOf", "SiegeOf", "ConquestOf", "RiseOf",
    "FallOf", "AgeOf", "StruggleFor", "CampaignOf", "CrusadeFor",
    "DominionOf", "HegemonyOf", "LegacyOf", "ThroneOf", "SandsOf",
    "FireOf", "IceOf", "DawnOf", "DuskOf", "EmpiresOf", "GodsOf",
    "KingsOf", "BloodOf", "SteelOf", "FaithOf", "HonorOf", "DestinyOf",
)

_PLACES = (
    "Rome", "Persia", "Egypt", "Carthage", "Babylon", "Maya", "Khmer",
    "Vikings", "Japan", "Mongolia", "Mali", "Inca", "Aztec", "Greece",
    "China", "India", "Spain", "France", "Russia", "England", "Germany",
    "Arabia", "Ottomans", "Korea", "Ethiopia", "Sumer", "Hittites",
    "Byzantium", "Nubia", "Gaul", "Thrace", "Nile", "Steppes", "Andes",
    "Thrones", "Stars", "Rivers", "Mountains", "Empires", "Kings",
    "Gods", "Sands", "Ice", "Fire", "Steel", "Faith", "Blood", "Honor",
    "Destiny", "Dawn", "Dusk", "Ash", "Jade", "Ivory", "Silk",
)


def generate_game_name(existing: Iterable[str] | None = None) -> str:
    """Return a unique CamelCase name like ClashOfRome / BattleForBabylon."""
    taken = {n.lower() for n in (existing or []) if n}
    for _ in range(80):
        name = random.choice(_PREFIXES) + random.choice(_PLACES)
        if name.lower() not in taken:
            return name
    return f"{random.choice(_PREFIXES)}{random.choice(_PLACES)}{random.randint(2, 99)}"
