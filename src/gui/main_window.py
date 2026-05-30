"""
Main application window - PyQt5 GUI with dark/light theme support.
"""
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QLineEdit, QSpinBox, QComboBox, QFileDialog, QMessageBox,
    QSystemTrayIcon, QMenu, QAction, QApplication, QFormLayout,
    QDialog, QDialogButtonBox, QTextEdit, QSplitter, QFrame,
    QCheckBox
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
QWidget#sidebar {
    background-color: #252536;
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
QTabWidget::pane {
    border: 1px solid #555;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #555;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #42a5f5;
    border-bottom: 2px solid #42a5f5;
}
QTabBar::tab:hover:!selected {
    background-color: #383838;
}
"""


LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #212121;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QWidget#sidebar {
    background-color: #e0e0e0;
}
QGroupBox {
    border: 1px solid #bdbdbd;
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
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
    color: #212121;
}
QPushButton:hover {
    background-color: #e3f2fd;
    border-color: #1976d2;
}
QPushButton:pressed {
    background-color: #bbdefb;
}
QPushButton#btn_download {
    background-color: #4caf50;
    border-color: #388e3c;
    color: white;
    font-weight: bold;
}
QPushButton#btn_download:hover {
    background-color: #66bb6a;
}
QPushButton#btn_upload {
    background-color: #1976d2;
    border-color: #1565c0;
    color: white;
    font-weight: bold;
}
QPushButton#btn_upload:hover {
    background-color: #42a5f5;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #e8f5e9;
    border-left: 3px solid #4caf50;
}
QListWidget::item:hover {
    background-color: #f5f5f5;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 20px;
    color: #212121;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #1976d2;
}
QLabel#status_bar {
    background-color: #e0e0e0;
    padding: 4px 12px;
    font-size: 9pt;
    color: #616161;
}
QLabel#banner_your_turn {
    background-color: #4caf50;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#banner_waiting {
    background-color: #eeeeee;
    color: #616161;
    padding: 8px 16px;
    font-size: 10pt;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    color: #616161;
    font-size: 9pt;
}
QSplitter::handle {
    background-color: #bdbdbd;
}
QTabWidget::pane {
    border: 1px solid #bdbdbd;
    background-color: #f5f5f5;
}
QTabBar::tab {
    background-color: #e0e0e0;
    color: #212121;
    border: 1px solid #bdbdbd;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #f5f5f5;
    color: #1976d2;
    border-bottom: 2px solid #1976d2;
}
QTabBar::tab:hover:!selected {
    background-color: #eeeeee;
}
QCheckBox {
    color: #212121;
}
"""


def get_style_for_theme(dark: bool) -> str:
    """Return the appropriate stylesheet."""
    return DARK_STYLE if dark else LIGHT_STYLE


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.games: list[Game] = []
        self.current_game: Optional[Game] = None
        self._minimize_to_tray = False  # Set to True by main.py when tray is available
        self._tray_icon = None  # Reference to TrayIcon, set by main.py

        self.setWindowTitle("Civ4 PBEM Manager v1.0")
        self.setMinimumSize(800, 600)
        self.apply_theme()

        self._init_ui()
        self._load_games()
        self._setup_timer()

    def apply_theme(self):
        """Apply dark or light theme based on config."""
        is_dark = self.config.get("dark_mode", True)
        self.setStyleSheet(get_style_for_theme(is_dark))

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left sidebar: game list ---
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setObjectName("sidebar")
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

        self.btn_delete_game = QPushButton("Usun gre")
        self.btn_delete_game.setStyleSheet("color: #ef5350;")
        self.btn_delete_game.clicked.connect(self._on_delete_game)
        sidebar_layout.addWidget(self.btn_delete_game)

        self.btn_game_transport = QPushButton("Transport gry...")
        self.btn_game_transport.clicked.connect(self._on_game_transport)
        sidebar_layout.addWidget(self.btn_game_transport)

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

        # History - clickable list for turn revert
        history_group = QGroupBox("Historia tur (kliknij aby przywrocic)")
        history_layout = QVBoxLayout(history_group)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(160)
        history_layout.addWidget(self.history_list)

        self.btn_revert = QPushButton("Przywroc zaznaczona ture")
        self.btn_revert.setStyleSheet("color: #ff9800; border-color: #ff9800;")
        self.btn_revert.clicked.connect(self._on_revert_turn)
        history_layout.addWidget(self.btn_revert)

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
        self.history_list.clear()
        for turn in reversed(game.history[-20:]):
            import datetime
            dt = datetime.datetime.fromtimestamp(turn.timestamp)
            text = f"{dt.strftime('%d.%m %H:%M')}  {turn.player_name} -> tura {turn.turn_number}  [{turn.filename}]"
            item = QListWidgetItem(text)
            # Store the history index as user data
            idx = game.history.index(turn)
            item.setData(Qt.UserRole, idx)
            self.history_list.addItem(item)

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

    def _on_delete_game(self):
        """Delete the currently selected game."""
        if not self.current_game:
            QMessageBox.information(self, "Info", "Zaznacz gre do usuniecia.")
            return

        reply = QMessageBox.warning(
            self,
            "Usuwanie gry",
            f"Czy na pewno chcesz usunac gre '{self.current_game.name}'?\n\n"
            f"Ta operacja jest nieodwracalna!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Will be connected to controller in main.py
            self._delete_game_requested = True

    def _on_game_transport(self):
        """Open transport configuration dialog for the current game."""
        if not self.current_game:
            QMessageBox.information(self, "Info", "Zaznacz gre aby skonfigurowac transport.")
            return

        dialog = GameTransportDialog(self.config, self.current_game, self.games, self)
        if dialog.exec_() == QDialog.Accepted:
            tc = dialog.get_transport_config()
            self.current_game.transport_config = tc
            from src.config import get_games_dir
            self.current_game.save_to_file(get_games_dir())
            self.status_label.setText(f"Transport gry '{self.current_game.name}' zapisany.")

    settings_saved = pyqtSignal()

    def _on_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.apply_theme()
            self.settings_saved.emit()

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

    def _on_revert_turn(self):
        """Revert game to a selected turn from history."""
        if not self.current_game:
            return

        selected = self.history_list.currentItem()
        if not selected:
            QMessageBox.information(self, "Info", "Zaznacz ture z listy aby ja przywrocic.")
            return

        history_index = selected.data(Qt.UserRole)
        if history_index is None:
            return

        game = self.current_game
        target = game.history[history_index] if history_index < len(game.history) else None
        if not target:
            return

        reply = QMessageBox.warning(
            self,
            "Przywrocenie tury",
            f"Czy na pewno chcesz przywrocic gre do tury {target.turn_number} "
            f"(gracz: {target.player_name})?\n\n"
            f"Wszystkie pozniejsze tury zostana usuniete.\n"
            f"Wszyscy gracze otrzymaja powiadomienie.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Actual revert will be handled by controller (connected in main.py)
            self._revert_history_index = history_index
            self.status_label.setText(f"Przywracanie tury {target.turn_number}...")

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
        if self._minimize_to_tray:
            event.ignore()
            self.hide()
            # Show tray balloon so user knows the app is still running
            if self._tray_icon and self._tray_icon.is_available:
                self._tray_icon.notify_status(
                    "Civ4 PBEM Manager",
                    "Aplikacja dziala w tle. Kliknij dwukrotnie aby otworzyc."
                )
        else:
            event.accept()


class NewGameDialog(QDialog):
    """Dialog for creating a new game."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Nowa gra")
        self.setMinimumWidth(450)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
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
    """Application settings dialog with tabbed layout."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Ustawienia")
        self.setMinimumSize(520, 480)
        self.resize(540, 520)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        from PyQt5.QtWidgets import QTabWidget
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "Ogolne")
        tabs.addTab(self._create_transport_tab(), "Transport")
        tabs.addTab(self._create_notifications_tab(), "Powiadomienia")
        layout.addWidget(tabs)

        # Buttons at the bottom (always visible)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --- Tab 1: General ---
    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

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

        # Check interval
        interval_group = QGroupBox("Sprawdzanie")
        interval_form = QFormLayout(interval_group)
        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 60)
        self.check_interval.setValue(self.config.check_interval_minutes)
        self.check_interval.setSuffix(" min")
        interval_form.addRow("Sprawdzaj co:", self.check_interval)
        layout.addWidget(interval_group)

        # Appearance
        appearance_group = QGroupBox("Wyglad")
        appearance_form = QFormLayout(appearance_group)
        self.dark_mode_check = QCheckBox("Tryb ciemny")
        self.dark_mode_check.setChecked(self.config.get("dark_mode", True))
        appearance_form.addRow(self.dark_mode_check)
        layout.addWidget(appearance_group)

        layout.addStretch()
        return tab

    # --- Tab 2: Transport ---
    def _create_transport_tab(self) -> QWidget:
        from PyQt5.QtWidgets import QScrollArea

        # Use a scroll area so email fields never overlap on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        tc = self.config.transport_config

        # Transport type selector
        type_group = QGroupBox("Metoda transportu")
        type_form = QFormLayout(type_group)
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email", "synology"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.transport_type.currentTextChanged.connect(self._on_transport_type_changed)
        type_form.addRow("Typ:", self.transport_type)

        self.ssl_ignore_check = QCheckBox("Ignoruj bledy SSL (self-signed certs)")
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        type_form.addRow(self.ssl_ignore_check)

        layout.addWidget(type_group)

        # File-based transport settings (FTP/SFTP/WebDAV)
        self.file_transport_group = QGroupBox("Serwer plikow (FTP/SFTP/WebDAV)")
        file_form = QFormLayout(self.file_transport_group)

        self.transport_host = QLineEdit(tc.get("host", ""))
        self.transport_host.setPlaceholderText("np. ftp.mojserwer.pl")
        file_form.addRow("Host:", self.transport_host)

        self.transport_port = QSpinBox()
        self.transport_port.setRange(1, 65535)
        self.transport_port.setValue(tc.get("port", 21))
        file_form.addRow("Port:", self.transport_port)

        self.transport_user = QLineEdit(tc.get("username", ""))
        file_form.addRow("Login:", self.transport_user)

        self.transport_pass = QLineEdit(tc.get("password", ""))
        self.transport_pass.setEchoMode(QLineEdit.Password)
        file_form.addRow("Haslo:", self.transport_pass)

        self.transport_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        file_form.addRow("Folder zdalny:", self.transport_dir)

        layout.addWidget(self.file_transport_group)

        # Email transport settings (SMTP + IMAP)
        self.email_transport_group = QGroupBox("Transport email (SMTP + IMAP)")
        email_form = QFormLayout(self.email_transport_group)
        email_form.setSpacing(6)

        ec = tc.get("email", {})

        self.et_mode = QComboBox()
        self.et_mode.addItems(["shared", "individual"])
        self.et_mode.setCurrentText(ec.get("mode", "shared"))
        email_form.addRow("Tryb:", self.et_mode)

        self.et_shared_email = QLineEdit(ec.get("shared_email", ""))
        self.et_shared_email.setPlaceholderText("wspoldzielona skrzynka, np. civ4pbem@...")
        email_form.addRow("Skrzynka wspolna:", self.et_shared_email)

        self.et_smtp_host = QLineEdit(ec.get("smtp_host", ""))
        self.et_smtp_host.setPlaceholderText("np. smtp.gmail.com")
        email_form.addRow("SMTP host:", self.et_smtp_host)

        self.et_smtp_port = QSpinBox()
        self.et_smtp_port.setRange(1, 65535)
        self.et_smtp_port.setValue(ec.get("smtp_port", 587))
        email_form.addRow("SMTP port:", self.et_smtp_port)

        self.et_smtp_user = QLineEdit(ec.get("smtp_user", ""))
        email_form.addRow("SMTP login:", self.et_smtp_user)

        self.et_smtp_pass = QLineEdit(ec.get("smtp_password", ""))
        self.et_smtp_pass.setEchoMode(QLineEdit.Password)
        email_form.addRow("SMTP haslo:", self.et_smtp_pass)

        self.et_imap_host = QLineEdit(ec.get("imap_host", ""))
        self.et_imap_host.setPlaceholderText("np. imap.gmail.com")
        email_form.addRow("IMAP host:", self.et_imap_host)

        self.et_imap_port = QSpinBox()
        self.et_imap_port.setRange(1, 65535)
        self.et_imap_port.setValue(ec.get("imap_port", 993))
        email_form.addRow("IMAP port:", self.et_imap_port)

        self.et_imap_user = QLineEdit(ec.get("imap_user", ""))
        email_form.addRow("IMAP login:", self.et_imap_user)

        self.et_imap_pass = QLineEdit(ec.get("imap_password", ""))
        self.et_imap_pass.setEchoMode(QLineEdit.Password)
        email_form.addRow("IMAP haslo:", self.et_imap_pass)

        self.et_from_address = QLineEdit(ec.get("from_address", ""))
        self.et_from_address.setPlaceholderText("adres nadawcy (opcjonalnie)")
        email_form.addRow("Od:", self.et_from_address)

        layout.addWidget(self.email_transport_group)

        # Synology Sharing Links settings
        self.synology_transport_group = QGroupBox("Synology - linki udostepniania")
        syno_form = QFormLayout(self.synology_transport_group)

        snc = tc.get("synology", {})
        self.syno_upload_url = QLineEdit(snc.get("upload_url", ""))
        self.syno_upload_url.setPlaceholderText("https://twoj.synology.me:5001/sharing/XXXXXXX")
        syno_form.addRow("URL uploadu:", self.syno_upload_url)

        self.syno_upload_password = QLineEdit(snc.get("upload_password", ""))
        self.syno_upload_password.setEchoMode(QLineEdit.Password)
        syno_form.addRow("Haslo uploadu:", self.syno_upload_password)

        self.syno_download_url = QLineEdit(snc.get("download_url", ""))
        self.syno_download_url.setPlaceholderText("https://gofile.me/XXXXX/XXXXXXX")
        syno_form.addRow("URL pobierania:", self.syno_download_url)

        self.syno_download_password = QLineEdit(snc.get("download_password", ""))
        self.syno_download_password.setEchoMode(QLineEdit.Password)
        self.syno_download_password.setPlaceholderText("puste = takie samo jak uploadu")
        syno_form.addRow("Haslo pobierania:", self.syno_download_password)

        layout.addWidget(self.synology_transport_group)

        # Show/hide based on current type
        self._on_transport_type_changed(self.transport_type.currentText())

        layout.addStretch()
        scroll.setWidget(tab)
        return scroll

    # --- Tab 3: Notifications ---
    def _create_notifications_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

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
        self.smtp_user.setPlaceholderText("puste = z transportu email")
        smtp_form.addRow("Login:", self.smtp_user)

        self.smtp_pass = QLineEdit(sc.get("password", ""))
        self.smtp_pass.setEchoMode(QLineEdit.Password)
        self.smtp_pass.setPlaceholderText("puste = z transportu email")
        smtp_form.addRow("Haslo:", self.smtp_pass)

        self.smtp_from = QLineEdit(sc.get("from_address", ""))
        self.smtp_from.setPlaceholderText("puste = login SMTP")
        smtp_form.addRow("Od:", self.smtp_from)

        layout.addWidget(smtp_group)

        info_label = QLabel(
            "Host i port musisz podac recznie.\n"
            "Login i haslo: jesli puste, beda uzyte dane\n"
            "z zakladki Transport (jesli typ = email)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #9e9e9e; font-size: 9pt; padding: 8px;")
        layout.addWidget(info_label)

        layout.addStretch()
        return tab

    # --- Logic ---
    def _on_transport_type_changed(self, transport_type: str):
        """Show/hide transport panels based on selected type."""
        self.file_transport_group.setVisible(transport_type in ("ftp", "sftp", "webdav"))
        self.email_transport_group.setVisible(transport_type == "email")
        self.synology_transport_group.setVisible(transport_type == "synology")

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
        self.config.set("dark_mode", self.dark_mode_check.isChecked())

        transport_data = {
            "type": self.transport_type.currentText(),
            "ignore_ssl_errors": self.ssl_ignore_check.isChecked(),
            "host": self.transport_host.text().strip(),
            "port": self.transport_port.value(),
            "username": self.transport_user.text().strip(),
            "password": self.transport_pass.text(),
            "remote_dir": self.transport_dir.text().strip(),
            "email": {
                "smtp_host": self.et_smtp_host.text().strip(),
                "smtp_port": self.et_smtp_port.value(),
                "smtp_user": self.et_smtp_user.text().strip(),
                "smtp_password": self.et_smtp_pass.text(),
                "smtp_use_tls": True,
                "imap_host": self.et_imap_host.text().strip(),
                "imap_port": self.et_imap_port.value(),
                "imap_user": self.et_imap_user.text().strip(),
                "imap_password": self.et_imap_pass.text(),
                "imap_use_ssl": True,
                "mode": self.et_mode.currentText(),
                "shared_email": self.et_shared_email.text().strip(),
                "from_address": self.et_from_address.text().strip(),
            },
            "synology": {
                "upload_url": self.syno_upload_url.text().strip(),
                "upload_password": self.syno_upload_password.text(),
                "download_url": self.syno_download_url.text().strip(),
                "download_password": self.syno_download_password.text(),
            },
        }
        self.config.set("transport", transport_data)

        self.config.set("smtp", {
            "host": self.smtp_host.text().strip(),
            "port": self.smtp_port.value(),
            "username": self.smtp_user.text().strip(),
            "password": self.smtp_pass.text(),
            "use_tls": True,
            "from_address": self.smtp_from.text().strip(),
        })

        # Apply theme change immediately to parent window
        parent = self.parent()
        if parent and hasattr(parent, 'apply_theme'):
            parent.apply_theme()

        self.accept()



class GameTransportDialog(QDialog):
    """Per-game transport configuration dialog.

    Allows configuring transport for individual games with option to
    copy settings from defaults (global config) or from another game.
    """

    def __init__(self, config: AppConfig, game: Game, all_games: list, parent=None):
        super().__init__(parent)
        self.config = config
        self.game = game
        self.all_games = all_games
        self.setWindowTitle(f"Transport: {game.name}")
        self.setMinimumSize(520, 480)
        self.resize(540, 520)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        from PyQt5.QtWidgets import QScrollArea
        layout = QVBoxLayout(self)

        # Copy from section
        copy_group = QGroupBox("Kopiuj ustawienia z...")
        copy_layout = QHBoxLayout(copy_group)

        btn_copy_defaults = QPushButton("Domyslne (globalne)")
        btn_copy_defaults.clicked.connect(self._copy_from_defaults)
        copy_layout.addWidget(btn_copy_defaults)

        self.copy_game_combo = QComboBox()
        self.copy_game_combo.addItem("-- wybierz gre --")
        for g in self.all_games:
            if g.name != self.game.name and g.transport_config:
                self.copy_game_combo.addItem(g.name)
        copy_layout.addWidget(self.copy_game_combo)

        btn_copy_game = QPushButton("Kopiuj")
        btn_copy_game.clicked.connect(self._copy_from_game)
        copy_layout.addWidget(btn_copy_game)

        layout.addWidget(copy_group)

        # Transport config (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        form_layout = QVBoxLayout(content)

        tc = self.game.transport_config or {}

        # Type
        type_group = QGroupBox("Metoda transportu")
        type_form = QFormLayout(type_group)
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email", "synology"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.transport_type.currentTextChanged.connect(self._on_type_changed)
        type_form.addRow("Typ:", self.transport_type)

        self.ssl_ignore_check = QCheckBox("Ignoruj bledy SSL")
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        type_form.addRow(self.ssl_ignore_check)
        form_layout.addWidget(type_group)

        # File-based (FTP/SFTP/WebDAV)
        self.file_group = QGroupBox("Serwer (FTP/SFTP/WebDAV)")
        file_form = QFormLayout(self.file_group)
        self.t_host = QLineEdit(tc.get("host", ""))
        file_form.addRow("Host:", self.t_host)
        self.t_port = QSpinBox()
        self.t_port.setRange(1, 65535)
        self.t_port.setValue(tc.get("port", 21))
        file_form.addRow("Port:", self.t_port)
        self.t_user = QLineEdit(tc.get("username", ""))
        file_form.addRow("Login:", self.t_user)
        self.t_pass = QLineEdit(tc.get("password", ""))
        self.t_pass.setEchoMode(QLineEdit.Password)
        file_form.addRow("Haslo:", self.t_pass)
        self.t_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        file_form.addRow("Folder:", self.t_dir)
        form_layout.addWidget(self.file_group)

        # Email
        self.email_group = QGroupBox("Email (SMTP + IMAP)")
        email_form = QFormLayout(self.email_group)
        ec = tc.get("email", {})
        self.e_mode = QComboBox()
        self.e_mode.addItems(["shared", "individual"])
        self.e_mode.setCurrentText(ec.get("mode", "shared"))
        email_form.addRow("Tryb:", self.e_mode)
        self.e_shared = QLineEdit(ec.get("shared_email", ""))
        email_form.addRow("Skrzynka:", self.e_shared)
        self.e_smtp_host = QLineEdit(ec.get("smtp_host", ""))
        email_form.addRow("SMTP host:", self.e_smtp_host)
        self.e_smtp_port = QSpinBox()
        self.e_smtp_port.setRange(1, 65535)
        self.e_smtp_port.setValue(ec.get("smtp_port", 587))
        email_form.addRow("SMTP port:", self.e_smtp_port)
        self.e_smtp_user = QLineEdit(ec.get("smtp_user", ""))
        email_form.addRow("SMTP login:", self.e_smtp_user)
        self.e_smtp_pass = QLineEdit(ec.get("smtp_password", ""))
        self.e_smtp_pass.setEchoMode(QLineEdit.Password)
        email_form.addRow("SMTP haslo:", self.e_smtp_pass)
        self.e_imap_host = QLineEdit(ec.get("imap_host", ""))
        email_form.addRow("IMAP host:", self.e_imap_host)
        self.e_imap_port = QSpinBox()
        self.e_imap_port.setRange(1, 65535)
        self.e_imap_port.setValue(ec.get("imap_port", 993))
        email_form.addRow("IMAP port:", self.e_imap_port)
        self.e_imap_user = QLineEdit(ec.get("imap_user", ""))
        email_form.addRow("IMAP login:", self.e_imap_user)
        self.e_imap_pass = QLineEdit(ec.get("imap_password", ""))
        self.e_imap_pass.setEchoMode(QLineEdit.Password)
        email_form.addRow("IMAP haslo:", self.e_imap_pass)
        self.e_from = QLineEdit(ec.get("from_address", ""))
        email_form.addRow("Od:", self.e_from)
        form_layout.addWidget(self.email_group)

        # Synology
        self.syno_group = QGroupBox("Synology Sharing")
        syno_form = QFormLayout(self.syno_group)
        sc = tc.get("synology", {})
        self.s_upload_url = QLineEdit(sc.get("upload_url", ""))
        syno_form.addRow("URL uploadu:", self.s_upload_url)
        self.s_upload_pass = QLineEdit(sc.get("upload_password", ""))
        self.s_upload_pass.setEchoMode(QLineEdit.Password)
        syno_form.addRow("Haslo uploadu:", self.s_upload_pass)
        self.s_download_url = QLineEdit(sc.get("download_url", ""))
        syno_form.addRow("URL pobierania:", self.s_download_url)
        self.s_download_pass = QLineEdit(sc.get("download_password", ""))
        self.s_download_pass.setEchoMode(QLineEdit.Password)
        self.s_download_pass.setPlaceholderText("puste = jak uploadu")
        syno_form.addRow("Haslo pobierania:", self.s_download_pass)
        form_layout.addWidget(self.syno_group)

        form_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Show/hide panels
        self._on_type_changed(self.transport_type.currentText())

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_type_changed(self, t: str):
        self.file_group.setVisible(t in ("ftp", "sftp", "webdav"))
        self.email_group.setVisible(t == "email")
        self.syno_group.setVisible(t == "synology")

    def _copy_from_defaults(self):
        """Copy transport config from global defaults."""
        tc = self.config.transport_config
        self._apply_config(tc)
        self.status = "Skopiowano z domyslnych"

    def _copy_from_game(self):
        """Copy transport config from another game."""
        game_name = self.copy_game_combo.currentText()
        if game_name == "-- wybierz gre --":
            return
        for g in self.all_games:
            if g.name == game_name and g.transport_config:
                self._apply_config(g.transport_config)
                break

    def _apply_config(self, tc: dict):
        """Apply a transport config dict to the form fields."""
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        self.t_host.setText(tc.get("host", ""))
        self.t_port.setValue(tc.get("port", 21))
        self.t_user.setText(tc.get("username", ""))
        self.t_pass.setText(tc.get("password", ""))
        self.t_dir.setText(tc.get("remote_dir", "/civ4pbem"))

        ec = tc.get("email", {})
        self.e_mode.setCurrentText(ec.get("mode", "shared"))
        self.e_shared.setText(ec.get("shared_email", ""))
        self.e_smtp_host.setText(ec.get("smtp_host", ""))
        self.e_smtp_port.setValue(ec.get("smtp_port", 587))
        self.e_smtp_user.setText(ec.get("smtp_user", ""))
        self.e_smtp_pass.setText(ec.get("smtp_password", ""))
        self.e_imap_host.setText(ec.get("imap_host", ""))
        self.e_imap_port.setValue(ec.get("imap_port", 993))
        self.e_imap_user.setText(ec.get("imap_user", ""))
        self.e_imap_pass.setText(ec.get("imap_password", ""))
        self.e_from.setText(ec.get("from_address", ""))

        sc = tc.get("synology", {})
        self.s_upload_url.setText(sc.get("upload_url", ""))
        self.s_upload_pass.setText(sc.get("upload_password", ""))
        self.s_download_url.setText(sc.get("download_url", ""))
        self.s_download_pass.setText(sc.get("download_password", ""))

    def get_transport_config(self) -> dict:
        """Build transport config dict from form fields."""
        return {
            "type": self.transport_type.currentText(),
            "ignore_ssl_errors": self.ssl_ignore_check.isChecked(),
            "host": self.t_host.text().strip(),
            "port": self.t_port.value(),
            "username": self.t_user.text().strip(),
            "password": self.t_pass.text(),
            "remote_dir": self.t_dir.text().strip(),
            "email": {
                "mode": self.e_mode.currentText(),
                "shared_email": self.e_shared.text().strip(),
                "smtp_host": self.e_smtp_host.text().strip(),
                "smtp_port": self.e_smtp_port.value(),
                "smtp_user": self.e_smtp_user.text().strip(),
                "smtp_password": self.e_smtp_pass.text(),
                "smtp_use_tls": True,
                "imap_host": self.e_imap_host.text().strip(),
                "imap_port": self.e_imap_port.value(),
                "imap_user": self.e_imap_user.text().strip(),
                "imap_password": self.e_imap_pass.text(),
                "imap_use_ssl": True,
                "from_address": self.e_from.text().strip(),
            },
            "synology": {
                "upload_url": self.s_upload_url.text().strip(),
                "upload_password": self.s_upload_pass.text(),
                "download_url": self.s_download_url.text().strip(),
                "download_password": self.s_download_pass.text(),
            },
        }
