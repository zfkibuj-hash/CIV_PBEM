"""
EditGameDialog — dialog for editing an existing game's settings.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QGroupBox,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt

from src.config import AppConfig
from src.models.game import Game
from src.i18n import t
from src.gui.styles import get_style_for_theme


class EditGameDialog(QDialog):
    """Dialog for editing an existing game's settings (players, emails, speed, alias)."""

    def __init__(self, config: AppConfig, game: Game, parent=None):
        super().__init__(parent)
        self.config = config
        self.game = game
        self.setWindowTitle(t("edit_game_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(500, 400)
        self.resize(540, 450)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Game speed
        speed_group = QGroupBox(t("game_speed"))
        speed_form = QFormLayout(speed_group)
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("Quick (330)", "quick")
        self.speed_combo.addItem("Normal (500)", "normal")
        self.speed_combo.addItem("Epic (750)", "epic")
        self.speed_combo.addItem("Marathon (1500)", "marathon")
        idx = self.speed_combo.findData(self.game.game_speed)
        if idx >= 0:
            self.speed_combo.setCurrentIndex(idx)
        speed_form.addRow(t("game_speed"), self.speed_combo)
        layout.addWidget(speed_group)

        # Player alias
        alias_group = QGroupBox(t("edit_alias"))
        alias_form = QFormLayout(alias_group)
        self.alias_combo = QComboBox()
        self.alias_combo.addItem(f"({t('history_filter_all')} — no alias)", "")
        for p in self.game.players:
            self.alias_combo.addItem(p.name, p.name)
        current_alias = self.game.local_player_alias
        if current_alias:
            idx = self.alias_combo.findData(current_alias)
            if idx >= 0:
                self.alias_combo.setCurrentIndex(idx)
        alias_form.addRow(t("edit_alias_label"), self.alias_combo)
        layout.addWidget(alias_group)

        # Players — editable emails
        players_group = QGroupBox(t("edit_players"))
        players_layout = QVBoxLayout(players_group)

        self._email_edits = []
        for p in self.game.players:
            row = QHBoxLayout()
            name_label = QLabel(f"{p.name}:")
            name_label.setMinimumWidth(100)
            row.addWidget(name_label)
            email_edit = QLineEdit(p.email)
            email_edit.setPlaceholderText("email@example.com")
            row.addWidget(email_edit)
            self._email_edits.append((p, email_edit))
            players_layout.addLayout(row)

        layout.addWidget(players_group)

        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        """Apply changes to the game object."""
        # Update speed
        self.game.game_speed = self.speed_combo.currentData()

        # Update alias
        alias = self.alias_combo.currentData()
        self.game.local_player_alias = alias or ""

        # Update player emails
        for player, email_edit in self._email_edits:
            new_email = email_edit.text().strip()
            if new_email:
                player.email = new_email

        self.accept()
