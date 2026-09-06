"""
Dialogs package for Civ4 PBEM Manager.
Exports all dialog classes for convenient importing.
"""
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.dialogs.new_game_dialog import NewGameDialog
from src.gui.dialogs.game_transport_dialog import GameTransportDialog
from src.gui.dialogs.game_stats_dialog import GameStatsDialog
from src.gui.dialogs.edit_game_dialog import EditGameDialog
from src.gui.dialogs.setup_wizard import SetupWizard
from src.gui.dialogs.choose_save_dialog import ChooseSaveDialog
from src.gui.dialogs.choose_save_path_dialog import ChooseSavePathDialog
from src.gui.dialogs.danger_zone_dialog import DangerZoneDialog

__all__ = [
    "SettingsDialog",
    "NewGameDialog",
    "GameTransportDialog",
    "GameStatsDialog",
    "EditGameDialog",
    "SetupWizard",
    "ChooseSaveDialog",
    "ChooseSavePathDialog",
    "DangerZoneDialog",
]
