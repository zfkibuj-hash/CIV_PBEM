"""
Main application window - PyQt5 modern dark theme GUI.
"""
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QLineEdit, QSpinBox, QComboBox, QFileDialog, QMessageBox,
    QSystemTrayIcon, QMenu, QAction, QApplication, QFormLayout,
    QDialog, QDialogButtonBox, QTextEdit, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor

from src.config import AppConfig
from src.models.game import Game, Player

logger = logging.getLogger(__name__)


DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #383838;
    border-color: #42a5f5;
}
QPushButton:pressed {
    background-color: #1a1a2e;
}
QPushButton#btn_download {
    background-color: #1b5e20;
    border-color: #4caf50;
    color: white;
    font-weight: bold;
}
QPushButton#btn_download:hover {
    background-color: #2e7d32;
}
QPushButton#btn_upload {
    background-color: #0d47a1;
    border-color: #42a5f5;
    color: white;
    font-weight: bold;
}
QPushButton#btn_upload:hover {
    background-color: #1565c0;
}
QListWidget {
    background-color: #252536;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #1a3a1a;
    border-left: 3px solid #66bb6a;
}
QListWidget::item:hover {
    background-color: #2d2d3d;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #42a5f5;
}
QLabel#status_bar {
    background-color: #1a1a2e;
    padding: 4px 12px;
    font-size: 9pt;
    color: #9e9e9e;
}
QLabel#banner_your_turn {
    background-color: #1b5e20;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#banner_waiting {
    background-color: #2d2d2d;
    color: #9e9e9e;
    padding: 8px 16px;
    font-size: 10pt;
}
QTextEdit {
    background-color: #252536;
    border: 1px solid #555;
    border-radius: 4px;
    color: #9e9e9e;
    font-size: 9pt;
}
QSplitter::handle {
    background-color: #555;
}
"""


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.games: list[Game] = []
        self.current_game: Optional[Game] = None

        self.setWindowTitle("Civ4 PBEM Manager v1.0")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(DARK_STYLE)

        self._init_ui()
        self._load_games()
        self._setup_timer()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left sidebar: game list ---
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #252536;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 8)

        lbl_games = QLabel("MOJE GRY")
        lbl_games.setStyleSheet("color: #9e9e9e; font-size: 9pt; font-weight: bold;")
        sidebar_layout.addWidget(lbl_games)

        self.game_list = QListWidget()
        self.game_list.currentRowChanged.connect(self._on_game_selected)
        sidebar_layout.addWidget(self.game_list)

        btn_new_game = QPushButton("+ Nowa gra")
        btn_new_game.clicked.connect(self._on_new_game)
        sidebar_layout.addWidget(btn_new_game)

        btn_settings = QPushButton("Ustawienia")
        btn_settings.clicked.connect(self._on_settings)
        sidebar_layout.addWidget(btn_settings)

        main_layout.addWidget(sidebar)

        # --- Right: game details ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header
        self.header_label = QLabel("Wybierz gre z listy")
        self.header_label.setStyleSheet(
            "background-color: #2d2d2d; padding: 12px 20px; "
            "font-size: 12pt; font-weight: bold;"
        )
        right_layout.addWidget(self.header_label)

        # Status banner
        self.status_banner = QLabel("")
        self.status_banner.setObjectName("banner_waiting")
        right_layout.addWidget(self.status_banner)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        # Players section
        self.players_label = QLabel("")
        self.players_label.setWordWrap(True)
        self.players_label.setStyleSheet("font-size: 10pt;")
        content_layout.addWidget(self.players_label)

        # Action buttons
        actions_layout = QHBoxLayout()
        self.btn_download = QPushButton("Pobierz save")
        self.btn_download.setObjectName("btn_download")
        self.btn_download.clicked.connect(self._on_download)
        self.btn_download.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_download)

        self.btn_upload = QPushButton("Wyslij moj save")
        self.btn_upload.setObjectName("btn_upload")
        self.btn_upload.clicked.connect(self._on_upload)
        self.btn_upload.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_upload)

        self.btn_open_folder = QPushButton("Otworz folder")
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        self.btn_open_folder.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_open_folder)

        self.btn_check_now = QPushButton("Sprawdz teraz")
        self.btn_check_now.clicked.connect(self._on_manual_check)
        self.btn_check_now.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_check_now)

        content_layout.addLayout(actions_layout)

        # History
        history_group = QGroupBox("Historia tur")
        history_layout = QVBoxLayout(history_group)
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(150)
        history_layout.addWidget(self.history_text)
        content_layout.addWidget(history_group)

        content_layout.addStretch()
        right_layout.addWidget(content)

        # Status bar
        self.status_label = QLabel("Gotowy")
        self.status_label.setObjectName("status_bar")
        right_layout.addWidget(self.status_label)

        main_layout.addWidget(right_panel)

    def _setup_timer(self):
        """Set up periodic check timer."""
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._on_check_timer)
        interval_ms = self.config.check_interval_minutes * 60 * 1000
        self.check_timer.start(interval_ms)

    def _load_games(self):
        """Load all game files from config directory."""
        from src.config import get_games_dir
        games_dir = get_games_dir()
        self.games = []
        for f in games_dir.glob("*.json"):
            try:
                game = Game.load_from_file(f)
                self.games.append(game)
            except Exception as e:
                logger.error(f"Failed to load game {f}: {e}")

        self._refresh_game_list()

    def _refresh_game_list(self):
        """Update the game list widget."""
        self.game_list.clear()
        my_name = self.config.player_name
        for game in self.games:
            is_my_turn = game.is_my_turn(my_name)
            if is_my_turn:
                text = f">> {game.name} [Tura {game.current_turn}]\n   TWOJA KOLEJ!"
            else:
                cp = game.current_player
                who = cp.name if cp else "?"
                text = f"   {game.name} [Tura {game.current_turn}]\n   Czeka: {who}"
            item = QListWidgetItem(text)
            if is_my_turn:
                item.setForeground(QColor("#66bb6a"))
            self.game_list.addItem(item)

    def _on_game_selected(self, row: int):
        """Handle game selection."""
        if 0 <= row < len(self.games):
            self.current_game = self.games[row]
            self._update_game_view()

    def _update_game_view(self):
        """Update the right panel with current game info."""
        game = self.current_game
        if not game:
            return

        my_name = self.config.player_name

        self.header_label.setText(f"{game.name}  -  Tura {game.current_turn}")

        if game.is_my_turn(my_name):
            self.status_banner.setText("  TWOJA KOLEJ! Save jest gotowy do pobrania.")
            self.status_banner.setObjectName("banner_your_turn")
        else:
            cp = game.current_player
            who = cp.name if cp else "?"
            self.status_banner.setText(f"  Czeka na: {who}")
            self.status_banner.setObjectName("banner_waiting")
        # Force style refresh
        self.status_banner.setStyleSheet(self.status_banner.styleSheet())
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

        # Players
        players_text = "Kolejnosc graczy: "
        parts = []
        for p in game.players:
            marker = " (Ty)" if p.name == my_name else ""
            arrow_marker = " <<" if p.name == game.current_player.name else ""
            parts.append(f"{p.name}{marker}{arrow_marker}")
        players_text += " -> ".join(parts)
        self.players_label.setText(players_text)

        # History
        self.history_text.clear()
        for turn in reversed(game.history[-20:]):
            import datetime
            dt = datetime.datetime.fromtimestamp(turn.timestamp)
            self.history_text.append(
                f"{dt.strftime('%d.%m %H:%M')}  {turn.player_name} -> upload (tura {turn.turn_number})"
            )

    def _on_new_game(self):
        """Create a new game dialog."""
        dialog = NewGameDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            game = dialog.get_game()
            if game:
                from src.config import get_games_dir
                game.save_to_file(get_games_dir())
                self.games.append(game)
                self._refresh_game_list()

    def _on_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.exec_()

    def _on_download(self):
        """Download save from remote."""
        if not self.current_game:
            return
        self.status_label.setText("Pobieranie save'a...")
        QApplication.processEvents()

        # This will be connected to the actual transport in the app controller
        self.status_label.setText("Pobieranie - uzyj kontrolera aplikacji")

    def _on_upload(self):
        """Upload save to remote."""
        if not self.current_game:
            return

        save_path = Path(self.config.save_path)
        if not save_path.exists():
            QMessageBox.warning(self, "Blad", f"Folder save'ow nie istnieje:\n{save_path}")
            return

        # Let user pick the save file
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Wybierz save do wyslania", str(save_path),
            "Civ4 Saves (*.CivBeyondSwordSave);;All Files (*)"
        )
        if not filepath:
            return

        self.status_label.setText(f"Wysylanie: {Path(filepath).name}...")
        QApplication.processEvents()

        # This will be connected to the actual transport in the app controller
        self.status_label.setText("Upload - uzyj kontrolera aplikacji")

    def _on_open_folder(self):
        """Open save folder in file explorer."""
        import subprocess, sys
        save_path = Path(self.config.save_path)
        if save_path.exists():
            if sys.platform == "win32":
                subprocess.Popen(f'explorer "{save_path}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(save_path)])
            else:
                subprocess.Popen(["xdg-open", str(save_path)])

    def _on_manual_check(self):
        """Manual check triggered by the user - checks and resets timer."""
        self.status_label.setText("Sprawdzanie nowych save'ow...")
        QApplication.processEvents()
        # Reset the periodic timer so the next auto-check is a full interval away
        self.check_timer.stop()
        interval_ms = self.config.check_interval_minutes * 60 * 1000
        self.check_timer.start(interval_ms)
        # The actual check logic will be connected in main.py
        self._on_check_timer()

    def _on_check_timer(self):
        """Periodic check for new saves."""
        self.status_label.setText("Sprawdzanie nowych save'ow...")
        # This will be implemented by app controller
        QTimer.singleShot(2000, lambda: self.status_label.setText("Gotowy"))

    def closeEvent(self, event):
        """Minimize to tray instead of closing, if tray is available."""
        if hasattr(self, '_minimize_to_tray') and self._minimize_to_tray:
            event.ignore()
            self.hide()
            self.status_label.setText("Zminimalizowano do tray")
        else:
            event.accept()


class NewGameDialog(QDialog):
    """Dialog for creating a new game."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Nowa gra")
        self.setMinimumWidth(450)
        self.setStyleSheet(DARK_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. WojnaSwiatowa")
        form.addRow("Nazwa gry:", self.name_edit)

        layout.addLayout(form)

        # Players
        players_group = QGroupBox("Gracze (w kolejnosci tur)")
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
            QMessageBox.warning(self, "Blad", "Podaj nazwe gry i minimum 2 graczy.")
            return None

        players = [
            Player(name=p["name"], email=p["email"], order=i)
            for i, p in enumerate(self._players_data)
        ]
        return Game(name=name, players=players)


class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Ustawienia")
        self.setMinimumWidth(500)
        self.setStyleSheet(DARK_STYLE)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Player info
        player_group = QGroupBox("Gracz")
        player_form = QFormLayout(player_group)
        self.player_name_edit = QLineEdit(self.config.player_name)
        player_form.addRow("Twoja nazwa:", self.player_name_edit)
        self.player_email_edit = QLineEdit(self.config.player_email)
        player_form.addRow("Twoj email:", self.player_email_edit)
        layout.addWidget(player_group)

        # Save path
        path_group = QGroupBox("Folder save'ow Civ4")
        path_layout = QHBoxLayout(path_group)
        self.path_edit = QLineEdit(self.config.save_path)
        path_layout.addWidget(self.path_edit)
        btn_browse = QPushButton("Zmien...")
        btn_browse.clicked.connect(self._browse_path)
        path_layout.addWidget(btn_browse)
        layout.addWidget(path_group)

        # Transport
        transport_group = QGroupBox("Transport plikow")
        transport_form = QFormLayout(transport_group)

        tc = self.config.transport_config
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        transport_form.addRow("Typ:", self.transport_type)

        self.transport_host = QLineEdit(tc.get("host", ""))
        self.transport_host.setPlaceholderText("np. ftp.mojserwer.pl")
        transport_form.addRow("Host:", self.transport_host)

        self.transport_port = QSpinBox()
        self.transport_port.setRange(1, 65535)
        self.transport_port.setValue(tc.get("port", 21))
        transport_form.addRow("Port:", self.transport_port)

        self.transport_user = QLineEdit(tc.get("username", ""))
        transport_form.addRow("Login:", self.transport_user)

        self.transport_pass = QLineEdit(tc.get("password", ""))
        self.transport_pass.setEchoMode(QLineEdit.Password)
        transport_form.addRow("Haslo:", self.transport_pass)

        self.transport_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        transport_form.addRow("Folder zdalny:", self.transport_dir)

        layout.addWidget(transport_group)

        # SMTP
        smtp_group = QGroupBox("Powiadomienia email (SMTP)")
        smtp_form = QFormLayout(smtp_group)

        sc = self.config.smtp_config
        self.smtp_host = QLineEdit(sc.get("host", ""))
        self.smtp_host.setPlaceholderText("np. smtp.gmail.com")
        smtp_form.addRow("Host SMTP:", self.smtp_host)

        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(sc.get("port", 587))
        smtp_form.addRow("Port:", self.smtp_port)

        self.smtp_user = QLineEdit(sc.get("username", ""))
        smtp_form.addRow("Login:", self.smtp_user)

        self.smtp_pass = QLineEdit(sc.get("password", ""))
        self.smtp_pass.setEchoMode(QLineEdit.Password)
        smtp_form.addRow("Haslo:", self.smtp_pass)

        self.smtp_from = QLineEdit(sc.get("from_address", ""))
        self.smtp_from.setPlaceholderText("adres nadawcy")
        smtp_form.addRow("Od:", self.smtp_from)

        layout.addWidget(smtp_group)

        # Check interval
        interval_group = QGroupBox("Sprawdzanie")
        interval_form = QFormLayout(interval_group)
        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 60)
        self.check_interval.setValue(self.config.check_interval_minutes)
        self.check_interval.setSuffix(" min")
        interval_form.addRow("Sprawdzaj co:", self.check_interval)
        layout.addWidget(interval_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Wybierz folder save'ow", self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)

    def _save_settings(self):
        self.config.player_name = self.player_name_edit.text().strip()
        self.config.set("player_email", self.player_email_edit.text().strip())
        self.config.save_path = self.path_edit.text().strip()
        self.config.set("check_interval_minutes", self.check_interval.value())
        self.config.set("transport", {
            "type": self.transport_type.currentText(),
            "host": self.transport_host.text().strip(),
            "port": self.transport_port.value(),
            "username": self.transport_user.text().strip(),
            "password": self.transport_pass.text(),
            "remote_dir": self.transport_dir.text().strip(),
        })
        self.config.set("smtp", {
            "host": self.smtp_host.text().strip(),
            "port": self.smtp_port.value(),
            "username": self.smtp_user.text().strip(),
            "password": self.smtp_pass.text(),
            "use_tls": True,
            "from_address": self.smtp_from.text().strip(),
        })
        self.accept()
