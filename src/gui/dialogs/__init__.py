"""
Dialogs package for Civ4 PBEM Manager.
Exports all dialog classes for convenient importing.
"""
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.dialogs.new_game_dialog import NewGameDialog
from src.gui.dialogs.game_transport_dialog import GameTransportDialog
from src.gui.dialogs.game_stats_dialog import GameStatsDialog
from src.gui.dialogs.edit_game_dialog import EditGameDialog

__all__ = [
    "SettingsDialog",
    "NewGameDialog",
    "GameTransportDialog",
    "GameStatsDialog",
    "EditGameDialog",
]
