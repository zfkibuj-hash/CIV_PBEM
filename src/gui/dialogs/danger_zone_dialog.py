"""Danger-zone actions (delete game / wipe server) — kept off the main UI."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QDialogButtonBox,
    QGroupBox, QMessageBox, QLineEdit,
)

from src.i18n import t
from src.gui.styles import get_style_for_theme
from src.models.game import Game
from src.config import AppConfig


class DangerZoneDialog(QDialog):
    """Hidden destructive actions: wipe FTP, delete one save, remove local game."""

    ACTION_DELETE_SELECTED_REMOTE = "delete_selected_remote"
    ACTION_WIPE_SERVER = "wipe_server"
    ACTION_DELETE_GAME = "delete_game"

    def __init__(
        self,
        config: AppConfig,
        game: Game,
        *,
        selected_remote_filename: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.config = config
        self.game = game
        self.selected_remote_filename = selected_remote_filename or ""
        self._action: Optional[str] = None
        self.setWindowTitle(t("danger_zone_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(420)
        self.setStyleSheet(get_style_for_theme(config.get("dark_mode", True)))
        self._init_ui()

    def chosen_action(self) -> Optional[str]:
        return self._action

    def _init_ui(self):
        layout = QVBoxLayout(self)
        warn = QLabel(t("danger_zone_hint"))
        warn.setWordWrap(True)
        warn.setStyleSheet("color: #ef5350;")
        layout.addWidget(warn)

        group = QGroupBox(t("danger_zone_group"))
        g_layout = QVBoxLayout(group)

        self.btn_del_selected = QPushButton(t("history_delete_remote"))
        self.btn_del_selected.setEnabled(bool(self.selected_remote_filename))
        if self.selected_remote_filename:
            self.btn_del_selected.setToolTip(self.selected_remote_filename)
        else:
            self.btn_del_selected.setToolTip(t("danger_zone_no_selection"))
        self.btn_del_selected.clicked.connect(
            lambda: self._pick(self.ACTION_DELETE_SELECTED_REMOTE),
        )
        g_layout.addWidget(self.btn_del_selected)

        self.btn_wipe = QPushButton(t("delete_all_remote"))
        self.btn_wipe.setStyleSheet("color: #ef5350;")
        self.btn_wipe.clicked.connect(lambda: self._pick(self.ACTION_WIPE_SERVER))
        g_layout.addWidget(self.btn_wipe)

        self.btn_del_game = QPushButton(t("delete_game"))
        self.btn_del_game.setStyleSheet("color: #ef5350;")
        self.btn_del_game.clicked.connect(lambda: self._pick(self.ACTION_DELETE_GAME))
        g_layout.addWidget(self.btn_del_game)

        layout.addWidget(group)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _pick(self, action: str):
        self._action = action
        self.accept()


def confirm_type_game_name(parent, game: Game, title: str, body: str) -> bool:
    """Require typing the exact game name before a destructive remote/local wipe."""
    from PySide6.QtWidgets import QInputDialog

    text, ok = QInputDialog.getText(
        parent,
        title,
        body + "\n\n" + t("danger_type_name_prompt", name=game.name),
        QLineEdit.Normal,
        "",
    )
    if not ok:
        return False
    if text.strip() != game.name:
        QMessageBox.warning(parent, t("error"), t("danger_type_name_mismatch"))
        return False
    return True
