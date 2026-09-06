"""
NewGameDialog — dialog for creating a new PBEM game.
"""
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QGroupBox, QListWidget,
    QPushButton, QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Qt

from src.config import AppConfig
from src.models.game import Game, Player
from src.i18n import t
from src.gui.styles import get_style_for_theme


class NewGameDialog(QDialog):
    """Dialog for creating a new game."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(t("new_game_title"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(450)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(t("game_name_placeholder"))
        name_row.addWidget(self.name_edit)
        btn_random = QPushButton(t("random_game_name"))
        btn_random.clicked.connect(self._randomize_name)
        name_row.addWidget(btn_random)
        form.addRow(t("game_name"), name_row)

        self.admin_password_edit = QLineEdit()
        self.admin_password_edit.setPlaceholderText(t("admin_password_placeholder"))
        self.admin_password_edit.setEchoMode(QLineEdit.Password)
        form.addRow(t("admin_password"), self.admin_password_edit)

        # Game speed selector
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("Quick (330 tur)", "quick")
        self.speed_combo.addItem("Normal (500 tur)", "normal")
        self.speed_combo.addItem("Epic (750 tur)", "epic")
        self.speed_combo.addItem("Marathon (1500 tur)", "marathon")
        self.speed_combo.setCurrentIndex(1)  # Default: Normal
        form.addRow(t("game_speed"), self.speed_combo)

        layout.addLayout(form)

        # Players
        players_group = QGroupBox(t("players_group"))
        players_layout = QVBoxLayout(players_group)

        self.players_list = QListWidget()
        players_layout.addWidget(self.players_list)

        player_add_layout = QHBoxLayout()
        self.player_name_edit = QLineEdit()
        self.player_name_edit.setPlaceholderText("Nazwa gracza")
        player_add_layout.addWidget(self.player_name_edit)

        self.player_email_edit = QLineEdit()
        self.player_email_edit.setPlaceholderText("Email gracza")
        player_add_layout.addWidget(self.player_email_edit)

        btn_add_player = QPushButton("Dodaj")
        btn_add_player.clicked.connect(self._add_player)
        player_add_layout.addWidget(btn_add_player)

        players_layout.addLayout(player_add_layout)

        btn_remove_player = QPushButton("Usun zaznaczonego")
        btn_remove_player.clicked.connect(self._remove_player)
        players_layout.addWidget(btn_remove_player)

        layout.addWidget(players_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Pre-add self as first player
        my_name = self.config.player_name
        my_email = self.config.player_email
        if my_name:
            self._players_data = [{"name": my_name, "email": my_email}]
            self.players_list.addItem(f"{my_name} <{my_email}> (Ty)")
        else:
            self._players_data = []

        self._randomize_name()

    def _existing_game_names(self) -> set[str]:
        from src.config import get_games_dir
        names = set()
        try:
            for f in get_games_dir().glob("*.json"):
                if not f.stem.endswith("_remote"):
                    names.add(f.stem)
        except Exception:
            pass
        return names

    def _randomize_name(self):
        from src.game_names import generate_game_name
        self.name_edit.setText(generate_game_name(self._existing_game_names()))

    def _add_player(self):
        name = self.player_name_edit.text().strip()
        email = self.player_email_edit.text().strip()
        if not name:
            return
        self._players_data.append({"name": name, "email": email})
        self.players_list.addItem(f"{name} <{email}>")
        self.player_name_edit.clear()
        self.player_email_edit.clear()

    def _remove_player(self):
        row = self.players_list.currentRow()
        if row >= 0:
            self.players_list.takeItem(row)
            self._players_data.pop(row)

    def get_game(self) -> Optional[Game]:
        name = self.name_edit.text().strip()
        if not name or len(self._players_data) < 2:
            QMessageBox.warning(self, t("error"), t("error_min_players"))
            return None

        existing = self._existing_game_names()
        if name.lower() in {n.lower() for n in existing}:
            QMessageBox.warning(self, t("error"), t("game_name_taken", name=name))
            return None

        # Validate game name: only alphanumeric, underscore, hyphen allowed
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            QMessageBox.warning(
                self, t("error"),
                "Nazwa gry moze zawierac tylko litery, cyfry, podkreslniki i myslniki.\n"
                "Game name can only contain letters, digits, underscores, and hyphens."
            )
            return None

        # Validate player names: no characters that break filename patterns
        for p in self._players_data:
            pname = p["name"]
            if not re.match(r'^[a-zA-Z0-9_\-]+$', pname):
                QMessageBox.warning(
                    self, t("error"),
                    f"Nazwa gracza '{pname}' zawiera niedozwolone znaki.\n"
                    f"Dozwolone: litery, cyfry, podkreslniki, myslniki.\n\n"
                    f"Player name '{pname}' contains disallowed characters."
                )
                return None

        players = [
            Player(name=p["name"], email=p["email"], order=i)
            for i, p in enumerate(self._players_data)
        ]
        return Game(
            name=name,
            players=players,
            admin_password=self.admin_password_edit.text().strip(),
            game_speed=self.speed_combo.currentData(),
        )
