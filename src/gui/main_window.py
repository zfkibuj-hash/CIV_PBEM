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
from src.i18n import t, get_i18n, set_language, LANGUAGES
from src.models.statistics import calculate_game_stats, format_duration
from src.launcher import detect_civ4_path, launch_civ4, is_civ4_running

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
        self._restore_geometry()

        self._init_ui()
        self._load_games()
        self._setup_timer()

    def apply_theme(self):
        """Apply dark or light theme based on config."""
        is_dark = self.config.get("dark_mode", True)
        self.setStyleSheet(get_style_for_theme(is_dark))

    def _save_geometry(self):
        """Save window position and size to config."""
        geo = self.geometry()
        self.config.set("window_geometry", {
            "x": geo.x(),
            "y": geo.y(),
            "width": geo.width(),
            "height": geo.height(),
        })

    def _restore_geometry(self):
        """Restore window position and size from config."""
        geo = self.config.get("window_geometry")
        if geo and isinstance(geo, dict):
            from PyQt5.QtWidgets import QDesktopWidget
            # Validate the position is on-screen
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry(self)
            x = geo.get("x", 100)
            y = geo.get("y", 100)
            w = geo.get("width", 900)
            h = geo.get("height", 650)
            # Clamp to screen bounds
            if x < 0 or x > screen_rect.width() - 100:
                x = 100
            if y < 0 or y > screen_rect.height() - 100:
                y = 100
            w = max(800, min(w, screen_rect.width()))
            h = max(600, min(h, screen_rect.height()))
            self.setGeometry(x, y, w, h)
        else:
            self.resize(900, 650)

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

        lbl_games = QLabel(t("my_games"))
        lbl_games.setStyleSheet("color: #9e9e9e; font-size: 9pt; font-weight: bold;")
        sidebar_layout.addWidget(lbl_games)

        self.game_list = QListWidget()
        self.game_list.currentRowChanged.connect(self._on_game_selected)
        sidebar_layout.addWidget(self.game_list)

        btn_new_game = QPushButton(t("new_game"))
        btn_new_game.clicked.connect(self._on_new_game)
        sidebar_layout.addWidget(btn_new_game)

        self.btn_import_game = QPushButton(t("import_game"))
        self.btn_import_game.clicked.connect(self._on_import_game)
        sidebar_layout.addWidget(self.btn_import_game)

        self.btn_export_game = QPushButton(t("export_game"))
        self.btn_export_game.clicked.connect(self._on_export_game)
        sidebar_layout.addWidget(self.btn_export_game)

        self.btn_delete_game = QPushButton(t("delete_game"))
        self.btn_delete_game.setStyleSheet("color: #ef5350;")
        self.btn_delete_game.clicked.connect(self._on_delete_game)
        sidebar_layout.addWidget(self.btn_delete_game)

        self.btn_game_transport = QPushButton(t("game_transport"))
        self.btn_game_transport.clicked.connect(self._on_game_transport)
        sidebar_layout.addWidget(self.btn_game_transport)

        self.btn_stats = QPushButton(t("statistics"))
        self.btn_stats.clicked.connect(self._on_statistics)
        sidebar_layout.addWidget(self.btn_stats)

        btn_settings = QPushButton(t("settings"))
        btn_settings.clicked.connect(self._on_settings)
        sidebar_layout.addWidget(btn_settings)

        main_layout.addWidget(sidebar)

        # --- Right: game details ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header
        self.header_label = QLabel(t("select_game"))
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
        self.btn_download = QPushButton(t("download_save"))
        self.btn_download.setObjectName("btn_download")
        self.btn_download.clicked.connect(self._on_download)
        self.btn_download.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_download)

        self.btn_upload = QPushButton(t("upload_save"))
        self.btn_upload.setObjectName("btn_upload")
        self.btn_upload.clicked.connect(self._on_upload)
        self.btn_upload.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_upload)

        self.btn_open_folder = QPushButton(t("open_folder"))
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        self.btn_open_folder.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_open_folder)

        self.btn_check_now = QPushButton(t("check_now"))
        self.btn_check_now.clicked.connect(self._on_manual_check)
        self.btn_check_now.setMinimumHeight(44)
        actions_layout.addWidget(self.btn_check_now)

        self.btn_launch_civ4 = QPushButton(t("launch_civ4"))
        self.btn_launch_civ4.clicked.connect(self._on_launch_civ4)
        self.btn_launch_civ4.setMinimumHeight(44)
        self.btn_launch_civ4.setStyleSheet("color: #ff9800; border-color: #ff9800;")
        actions_layout.addWidget(self.btn_launch_civ4)

        content_layout.addLayout(actions_layout)

        # History - clickable list for turn revert
        history_group = QGroupBox(t("history_group"))
        history_layout = QVBoxLayout(history_group)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(160)
        history_layout.addWidget(self.history_list)

        self.btn_revert = QPushButton(t("revert_selected"))
        self.btn_revert.setStyleSheet("color: #ff9800; border-color: #ff9800;")
        self.btn_revert.clicked.connect(self._on_revert_turn)
        history_layout.addWidget(self.btn_revert)

        content_layout.addWidget(history_group)

        content_layout.addStretch()
        right_layout.addWidget(content)

        # Status bar
        self.status_label = QLabel(t("ready"))
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
            # Skip remote sync files (used internally for state sync)
            if f.stem.endswith("_remote"):
                continue
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
                text = f">> {game.name} [{t('turn')} {game.current_turn}]\n   {t('your_turn')}"
            else:
                cp = game.current_player
                who = cp.name if cp else "?"
                text = f"   {game.name} [{t('turn')} {game.current_turn}]\n   {t('waiting')}: {who}"
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

        self.header_label.setText(f"{game.name}  -  {t('turn')} {game.current_turn}")

        if game.is_my_turn(my_name):
            self.status_banner.setText(t("your_turn_banner"))
            self.status_banner.setObjectName("banner_your_turn")
        else:
            cp = game.current_player
            who = cp.name if cp else "?"
            self.status_banner.setText(t("waiting_for", name=who))
            self.status_banner.setObjectName("banner_waiting")
        # Force style refresh
        self.status_banner.setStyleSheet(self.status_banner.styleSheet())
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

        # Players
        players_text = t("player_order")
        parts = []
        for p in game.players:
            marker = t("you_marker") if p.name == my_name else ""
            arrow_marker = " <<" if p.name == game.current_player.name else ""
            parts.append(f"{p.name}{marker}{arrow_marker}")
        players_text += " -> ".join(parts)
        self.players_label.setText(players_text)

        # Time since last turn
        if game.history:
            import datetime, time
            last_turn = game.history[-1]
            elapsed = time.time() - last_turn.timestamp
            elapsed_str = self._format_elapsed(elapsed)
            cp_name = game.current_player.name if game.current_player else "?"
            self.players_label.setText(
                f"{players_text}\n"
                f"{t('playing_since', name=cp_name, time=elapsed_str)}"
            )

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

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        """Format elapsed seconds into a human-readable Polish string."""
        minutes = int(seconds // 60)
        hours = int(seconds // 3600)
        days = int(seconds // 86400)

        if days > 0:
            return f"{days} dni, {hours % 24} godz."
        elif hours > 0:
            return f"{hours} godz., {minutes % 60} min."
        elif minutes > 0:
            return f"{minutes} min."
        else:
            return "< 1 min."

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

    def _on_export_game(self):
        """Export current game config to a .civ4pbem file for sharing with other players."""
        if not self.current_game:
            QMessageBox.information(self, "Info", "Zaznacz gre do eksportu.")
            return

        game = self.current_game
        export_data = {
            "civ4pbem_version": "1.0",
            "name": game.name,
            "players": [p.to_dict() for p in game.players],
            "transport_config": game.transport_config,
        }

        import json
        default_name = f"{game.name}.civ4pbem"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj konfiguracje gry", default_name,
            "Civ4 PBEM Game Config (*.civ4pbem);;All Files (*)"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            self.status_label.setText(f"Wyeksportowano: {filepath}")

    def _on_import_game(self):
        """Import a game from a .civ4pbem file shared by another player."""
        import json
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importuj konfiguracje gry", "",
            "Civ4 PBEM Game Config (*.civ4pbem);;All Files (*)"
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            name = data.get("name", "")
            if not name:
                QMessageBox.warning(self, "Blad", "Plik nie zawiera nazwy gry.")
                return

            # Check for duplicate
            for g in self.games:
                if g.name == name:
                    reply = QMessageBox.question(
                        self, "Gra juz istnieje",
                        f"Gra '{name}' juz istnieje. Nadpisac?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return
                    # Remove old one
                    from src.config import get_games_dir
                    g.delete_file(get_games_dir())
                    self.games.remove(g)
                    break

            players = [Player.from_dict(p) for p in data.get("players", [])]
            transport_config = data.get("transport_config", {})

            game = Game(
                name=name,
                players=players,
                transport_config=transport_config,
            )

            # --- Player identity selection ---
            # User must confirm which player from the list they are
            player_names = [p.name for p in players]
            my_local_name = self.config.player_name

            # If local name matches a player exactly, pre-select it
            default_idx = 0
            for i, pn in enumerate(player_names):
                if pn == my_local_name:
                    default_idx = i
                    break

            from PyQt5.QtWidgets import QInputDialog
            chosen_name, ok = QInputDialog.getItem(
                self,
                "Wybierz swojego gracza / Choose your player",
                f"Gra: {name}\nTwoj lokalny nick: '{my_local_name}'\n\n"
                f"Ktorym graczem z listy jestes?\n"
                f"Which player are you?",
                player_names,
                default_idx,
                False,  # not editable
            )
            if not ok:
                return

            # Set alias: local nick → game player name
            if chosen_name != my_local_name:
                game.local_player_alias = chosen_name
            else:
                game.local_player_alias = ""  # No alias needed, names match

            # Confirm email for notifications
            chosen_player = next((p for p in players if p.name == chosen_name), None)
            if chosen_player:
                confirmed_email, ok2 = QInputDialog.getText(
                    self,
                    "Potwierdz email / Confirm email",
                    f"Gracz: {chosen_name}\n"
                    f"Email na ktory dostaniesz powiadomienie o turze:",
                    QLineEdit.Normal,
                    chosen_player.email,
                )
                if ok2 and confirmed_email.strip():
                    chosen_player.email = confirmed_email.strip()

            from src.config import get_games_dir
            game.save_to_file(get_games_dir())
            self.games.append(game)
            self._refresh_game_list()
            self.status_label.setText(f"Zaimportowano gre: {name} (gracz: {chosen_name})")

        except Exception as e:
            QMessageBox.warning(self, "Blad importu", f"Nie udalo sie zaimportowac:\n{e}")

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
            # Refresh UI labels for new language
            self._refresh_ui_language()
            self.settings_saved.emit()

    def _refresh_ui_language(self):
        """Update all UI text labels after language change."""
        self.btn_download.setText(t("download_save"))
        self.btn_upload.setText(t("upload_save"))
        self.btn_open_folder.setText(t("open_folder"))
        self.btn_check_now.setText(t("check_now"))
        self.btn_launch_civ4.setText(t("launch_civ4"))
        self.btn_revert.setText(t("revert_selected"))
        self.btn_stats.setText(t("statistics"))
        self.btn_import_game.setText(t("import_game"))
        self.btn_export_game.setText(t("export_game"))
        self.btn_delete_game.setText(t("delete_game"))
        self.btn_game_transport.setText(t("game_transport"))
        self.status_label.setText(t("ready"))
        # Refresh game view if a game is selected
        if self.current_game:
            self._update_game_view()
        else:
            self.header_label.setText(t("select_game"))

    def _on_download(self):
        """Download save from remote."""
        if not self.current_game:
            return
        self.status_label.setText(t("downloading"))
        QApplication.processEvents()

        # This will be connected to the actual transport in the app controller
        self.status_label.setText(t("downloading"))

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
        self.status_label.setText(t("checking_saves"))
        QApplication.processEvents()
        # Reset the periodic timer so the next auto-check is a full interval away
        self.check_timer.stop()
        interval_ms = self.config.check_interval_minutes * 60 * 1000
        self.check_timer.start(interval_ms)
        # The actual check logic will be connected in main.py
        self._on_check_timer()

    def _on_statistics(self):
        """Show game statistics dialog."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("stats_no_game"))
            return
        dialog = GameStatsDialog(self.config, self.current_game, self)
        dialog.exec_()

    def _on_launch_civ4(self):
        """Launch Civ4 BTS with the latest save for the current game.

        Actual launch is handled via launch_civ4_requested signal,
        connected to controller in main.py. Fallback: direct launch here.
        """
        civ4_path = self.config.civ4_path
        if not civ4_path:
            QMessageBox.warning(self, t("error"), t("civ4_not_found"))
            return

        # Check if already running (prevent duplicate instances)
        if is_civ4_running():
            self.status_label.setText(t("civ4_already_running"))
            return

        # Find the latest local save for the current game
        save_file = None
        if self.current_game:
            save_dir = Path(self.config.save_path)
            if save_dir.exists():
                pattern = f"{self.current_game.name}_T*.CivBeyondSwordSave"
                saves = list(save_dir.glob(pattern))
                if saves:
                    saves.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    save_file = str(saves[0])

        success, msg_key = launch_civ4(civ4_path, save_file=save_file)
        if success:
            status = t(msg_key) if msg_key in ("civ4_launched", "civ4_already_running") else msg_key
            if save_file:
                status += f" ({Path(save_file).name})"
            self.status_label.setText(status)
        else:
            self.status_label.setText(t(msg_key) if msg_key == "civ4_not_found" else msg_key)

    def _on_check_timer(self):
        """Periodic check for new saves."""
        self.status_label.setText(t("checking_saves"))
        # This will be implemented by app controller
        QTimer.singleShot(2000, lambda: self.status_label.setText(t("ready")))

    def closeEvent(self, event):
        """Close button (X) always quits the application. Saves geometry."""
        self._save_geometry()
        event.accept()

    def changeEvent(self, event):
        """Minimize button (—) sends to tray instead of taskbar."""
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                if self._minimize_to_tray:
                    event.ignore()
                    self.hide()
                    self.setWindowState(Qt.WindowNoState)
                    if self._tray_icon and self._tray_icon.is_available:
                        self._tray_icon.notify_status(
                            "Civ4 PBEM Manager",
                            "Zminimalizowano do tray. Kliknij dwukrotnie aby otworzyc."
                        )
                    return
        super().changeEvent(event)


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
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. WojnaSwiatowa")
        form.addRow("Nazwa gry:", self.name_edit)

        self.admin_password_edit = QLineEdit()
        self.admin_password_edit.setPlaceholderText("haslo do usuwania save'ow (opcjonalne)")
        self.admin_password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Haslo admina:", self.admin_password_edit)

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
        return Game(
            name=name,
            players=players,
            admin_password=self.admin_password_edit.text().strip(),
        )


class SettingsDialog(QDialog):
    """Application settings dialog with tabbed layout."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(t("settings_title"))
        # Remove the "?" button from title bar (useless, confuses users)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        self.setMinimumSize(580, 560)
        self.resize(640, 620)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        from PyQt5.QtWidgets import QTabWidget
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), t("tab_general"))
        tabs.addTab(self._create_transport_tab(), t("tab_transport"))
        tabs.addTab(self._create_notifications_tab(), t("tab_notifications"))
        tabs.addTab(self._create_security_tab(), t("tab_security"))
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
        from PyQt5.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Player info
        player_group = QGroupBox(t("stats_player_name"))
        player_form = QFormLayout(player_group)
        self.player_name_edit = QLineEdit(self.config.player_name)
        player_form.addRow(t("player_name"), self.player_name_edit)
        self.player_email_edit = QLineEdit(self.config.player_email)
        player_form.addRow(t("player_email"), self.player_email_edit)
        layout.addWidget(player_group)

        # Save path
        path_group = QGroupBox(t("save_path"))
        path_layout = QHBoxLayout(path_group)
        self.path_edit = QLineEdit(self.config.save_path)
        path_layout.addWidget(self.path_edit)
        btn_browse = QPushButton(t("browse"))
        btn_browse.clicked.connect(self._browse_path)
        path_layout.addWidget(btn_browse)
        layout.addWidget(path_group)

        # Check interval
        interval_group = QGroupBox(t("check_interval"))
        interval_form = QFormLayout(interval_group)
        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 60)
        self.check_interval.setValue(self.config.check_interval_minutes)
        self.check_interval.setSuffix(" min")
        interval_form.addRow(t("check_interval"), self.check_interval)
        layout.addWidget(interval_group)

        # Appearance & Language
        appearance_group = QGroupBox(t("settings_appearance"))
        appearance_form = QFormLayout(appearance_group)
        self.dark_mode_check = QCheckBox(t("dark_mode"))
        self.dark_mode_check.setChecked(self.config.get("dark_mode", True))
        appearance_form.addRow(self.dark_mode_check)

        self.auto_send_check = QCheckBox(t("auto_send"))
        self.auto_send_check.setChecked(self.config.get("auto_send", False))
        appearance_form.addRow(self.auto_send_check)

        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItem("Polski", "pl")
        self.language_combo.addItem("English", "en")
        current_lang = self.config.language
        idx = 0 if current_lang == "pl" else 1
        self.language_combo.setCurrentIndex(idx)
        appearance_form.addRow(t("language"), self.language_combo)

        layout.addWidget(appearance_group)

        # Civ4 path (for Launch button)
        launch_group = QGroupBox("Civ4 Beyond the Sword")
        launch_form = QFormLayout(launch_group)

        civ4_path_layout = QHBoxLayout()
        self.civ4_path_edit = QLineEdit(self.config.civ4_path)
        self.civ4_path_edit.setPlaceholderText("C:\\...\\Civ4BeyondSword.exe")
        civ4_path_layout.addWidget(self.civ4_path_edit)

        btn_browse_civ4 = QPushButton(t("browse"))
        btn_browse_civ4.clicked.connect(self._browse_civ4_path)
        civ4_path_layout.addWidget(btn_browse_civ4)

        btn_detect_civ4 = QPushButton(t("detect_civ4"))
        btn_detect_civ4.clicked.connect(self._detect_civ4)
        civ4_path_layout.addWidget(btn_detect_civ4)

        launch_form.addRow(t("civ4_path"), civ4_path_layout)
        layout.addWidget(launch_group)

        layout.addStretch()
        scroll.setWidget(tab)
        return scroll

    # --- Tab 2: Transport ---
    def _create_transport_tab(self) -> QWidget:
        from PyQt5.QtWidgets import QScrollArea

        # If config is locked, show lock message instead of form
        if not self.config.is_unlocked:
            locked_tab = QWidget()
            locked_layout = QVBoxLayout(locked_tab)
            locked_layout.addStretch()
            lock_label = QLabel(
                "🔒 Dane transportu sa zaszyfrowane.\n\n"
                "Odblokuj aplikacje haslem glownym\n"
                "aby wyswietlic i edytowac te ustawienia.\n\n"
                "🔒 Transport data is encrypted.\n"
                "Unlock the app with master password\n"
                "to view and edit these settings."
            )
            lock_label.setAlignment(Qt.AlignCenter)
            lock_label.setStyleSheet("font-size: 11pt; color: #ff9800; padding: 40px;")
            locked_layout.addWidget(lock_label)
            locked_layout.addStretch()
            return locked_tab

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
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email"])
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

        et_warning = QLabel(
            "⚠ Nie uzywaj prywatnego maila! Zalecane: osobna skrzynka."
        )
        et_warning.setStyleSheet("color: #ff9800; font-size: 9pt;")
        email_form.addRow(et_warning)

        layout.addWidget(self.email_transport_group)

        # Show/hide based on current type
        self._on_transport_type_changed(self.transport_type.currentText())

        layout.addStretch()
        scroll.setWidget(tab)
        return scroll

    # --- Tab 3: Notifications ---
    def _create_notifications_tab(self) -> QWidget:
        # If config is locked, show lock message
        if not self.config.is_unlocked:
            locked_tab = QWidget()
            locked_layout = QVBoxLayout(locked_tab)
            locked_layout.addStretch()
            lock_label = QLabel(
                "🔒 Dane SMTP sa zaszyfrowane.\n\n"
                "Odblokuj aplikacje haslem glownym\n"
                "aby wyswietlic i edytowac te ustawienia."
            )
            lock_label.setAlignment(Qt.AlignCenter)
            lock_label.setStyleSheet("font-size: 11pt; color: #ff9800; padding: 40px;")
            locked_layout.addWidget(lock_label)
            locked_layout.addStretch()
            return locked_tab

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

    # --- Tab 4: Security ---
    def _create_security_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Status
        status_group = QGroupBox("Status szyfrowania / Encryption status")
        status_layout = QVBoxLayout(status_group)

        if self.config.has_master_password:
            if self.config.is_unlocked:
                status_label = QLabel("🔓 Odblokowane — dane dostepne\n🔓 Unlocked — data accessible")
                status_label.setStyleSheet("color: #66bb6a; font-size: 10pt;")
            else:
                status_label = QLabel("🔒 Zablokowane — dane zaszyfrowane\n🔒 Locked — data encrypted")
                status_label.setStyleSheet("color: #ff9800; font-size: 10pt;")
        else:
            status_label = QLabel(
                "⚠ Brak hasla — dane przechowywane jako plain text!\n"
                "⚠ No password — data stored as plain text!\n\n"
                "Ustaw haslo glowne aby zaszyfrowac."
            )
            status_label.setStyleSheet("color: #ef5350; font-size: 10pt;")

        status_layout.addWidget(status_label)
        layout.addWidget(status_group)

        # Set / Change password
        password_group = QGroupBox("Haslo glowne / Master password")
        password_form = QFormLayout(password_group)

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText("Nowe haslo / New password")
        password_form.addRow("Haslo:", self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("Powtorz haslo / Confirm password")
        password_form.addRow("Powtorz:", self.confirm_password_edit)

        btn_set_password = QPushButton("Ustaw / zmien haslo")
        btn_set_password.setStyleSheet("color: #ff9800; border-color: #ff9800; font-weight: bold;")
        btn_set_password.clicked.connect(self._on_set_master_password)
        password_form.addRow(btn_set_password)

        layout.addWidget(password_group)

        # Info
        info_label = QLabel(
            "Haslo glowne szyfruje: dane transportu (FTP/SFTP/WebDAV/Email),\n"
            "loginy, hasla SMTP, hasla do serwerow.\n\n"
            "Bez hasla te dane beda wymagane przy kazdym uruchomieniu.\n"
            "UWAGA: Jesli zapomnisz hasla, musisz usunac config i ustawic od nowa!\n\n"
            "Master password encrypts: transport credentials, SMTP passwords.\n"
            "If you forget it, you must delete config and set up again."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #9e9e9e; font-size: 9pt; padding: 8px;")
        layout.addWidget(info_label)

        layout.addStretch()
        return tab

    def _on_set_master_password(self):
        """Set or change the master password."""
        new_pass = self.new_password_edit.text()
        confirm = self.confirm_password_edit.text()

        if not new_pass:
            QMessageBox.warning(self, "Blad", "Haslo nie moze byc puste.")
            return

        if len(new_pass) < 4:
            QMessageBox.warning(self, "Blad", "Haslo musi miec minimum 4 znaki.")
            return

        if new_pass != confirm:
            QMessageBox.warning(self, "Blad", "Hasla nie sa identyczne!\nPasswords don't match!")
            return

        # If already has password and is locked, can't change
        if self.config.has_master_password and not self.config.is_unlocked:
            QMessageBox.warning(
                self, "Blad",
                "Nie mozna zmienic hasla gdy config jest zablokowany.\n"
                "Najpierw odblokuj przy starcie aplikacji."
            )
            return

        self.config.set_master_password(new_pass)
        QMessageBox.information(
            self, "OK",
            "Haslo ustawione! Dane zostaly zaszyfrowane.\n"
            "Password set! Data has been encrypted.\n\n"
            "Od teraz przy starcie program bedzie pytac o haslo."
        )
        self.new_password_edit.clear()
        self.confirm_password_edit.clear()

    # --- Logic ---
    def _on_transport_type_changed(self, transport_type: str):
        """Show/hide transport panels based on selected type."""
        self.file_transport_group.setVisible(transport_type in ("ftp", "sftp", "webdav"))
        self.email_transport_group.setVisible(transport_type == "email")

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Wybierz folder save'ow", self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)

    def _browse_civ4_path(self):
        """Browse for Civ4 BTS executable."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Wybierz Civ4BeyondSword.exe", self.civ4_path_edit.text(),
            "Executable (*.exe);;All Files (*)"
        )
        if filepath:
            self.civ4_path_edit.setText(filepath)

    def _detect_civ4(self):
        """Auto-detect Civ4 BTS installation path."""
        detected = detect_civ4_path()
        if detected:
            self.civ4_path_edit.setText(detected)
            QMessageBox.information(self, "OK", t("civ4_detected", path=detected))
        else:
            QMessageBox.information(self, t("info"), t("civ4_not_detected"))

    def _save_settings(self):
        self.config.player_name = self.player_name_edit.text().strip()
        self.config.set("player_email", self.player_email_edit.text().strip())
        self.config.save_path = self.path_edit.text().strip()
        self.config.set("check_interval_minutes", self.check_interval.value())
        self.config.set("dark_mode", self.dark_mode_check.isChecked())
        self.config.set("auto_send", self.auto_send_check.isChecked())

        # Language
        new_lang = self.language_combo.currentData()
        self.config.language = new_lang
        set_language(new_lang)

        # Civ4 path
        self.config.civ4_path = self.civ4_path_edit.text().strip()

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
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(560, 500)
        self.resize(600, 560)
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
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email"])
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

        email_warning = QLabel(
            "⚠ UWAGA: Nie uzywaj prywatnego maila do transportu!\n"
            "Zalecane: osobna skrzynka na potrzeby gry (np. civ4pbem@...).\n"
            "Program kasuje/modyfikuje maile w skrzynce."
        )
        email_warning.setWordWrap(True)
        email_warning.setStyleSheet("color: #ff9800; font-size: 9pt; padding: 4px;")
        email_form.addRow(email_warning)

        form_layout.addWidget(self.email_group)

        form_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Show/hide panels
        self._on_type_changed(self.transport_type.currentText())

        # Test connection button
        btn_test = QPushButton("Testuj polaczenie")
        btn_test.clicked.connect(self._test_connection)
        layout.addWidget(btn_test)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _test_connection(self):
        """Test the transport connection with current form values."""
        from src.gui.app_controller import AppController
        from src.models.game import Game

        # Build a temporary game with current form config
        tc = self.get_transport_config()
        temp_game = Game(name="__test__", transport_config=tc)

        # Use a temporary controller to test
        transport = AppController._create_transport_for_game(None, temp_game)
        if not transport:
            QMessageBox.warning(self, "Test", "Transport nie jest skonfigurowany.")
            return

        QApplication.processEvents()
        success = transport.connect()
        if success:
            transport.disconnect()
            QMessageBox.information(self, "Test", "Polaczenie OK!")
        else:
            QMessageBox.warning(self, "Test", "Nie mozna polaczyc. Sprawdz dane.")

    def _on_type_changed(self, t: str):
        self.file_group.setVisible(t in ("ftp", "sftp", "webdav"))
        self.email_group.setVisible(t == "email")

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
        }



class GameStatsDialog(QDialog):
    """Dialog showing comprehensive game statistics."""

    def __init__(self, config: AppConfig, game: Game, parent=None):
        super().__init__(parent)
        self.config = config
        self.game = game
        self.setWindowTitle(t("stats_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(500, 450)
        self.resize(560, 500)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        stats = calculate_game_stats(self.game)

        # Game overview
        overview_group = QGroupBox(t("stats_title", name=self.game.name))
        overview_form = QFormLayout(overview_group)

        overview_form.addRow(t("stats_game_started"), QLabel(stats.game_started_formatted))
        overview_form.addRow(t("stats_last_activity"), QLabel(stats.last_activity_formatted))
        overview_form.addRow(t("stats_current_round"), QLabel(str(stats.current_round)))
        overview_form.addRow(t("stats_total_turns"), QLabel(str(stats.total_turns)))
        overview_form.addRow(t("stats_total_time"), QLabel(stats.total_time_formatted))
        overview_form.addRow(t("stats_avg_turn_time"), QLabel(stats.avg_turn_time_formatted))
        overview_form.addRow(t("stats_fastest_turn"), QLabel(stats.fastest_turn_formatted))
        overview_form.addRow(t("stats_slowest_turn"), QLabel(stats.slowest_turn_formatted))

        layout.addWidget(overview_group)

        # Per-player stats table
        player_group = QGroupBox(t("stats_per_player"))
        player_layout = QVBoxLayout(player_group)

        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            t("stats_player_name"),
            t("stats_player_turns"),
            t("stats_player_avg_time"),
            t("stats_player_total_time"),
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(stats.player_stats))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        for row, ps in enumerate(stats.player_stats):
            table.setItem(row, 0, QTableWidgetItem(ps.name))
            table.setItem(row, 1, QTableWidgetItem(str(ps.total_turns)))
            table.setItem(row, 2, QTableWidgetItem(ps.avg_turn_time_formatted))
            table.setItem(row, 3, QTableWidgetItem(ps.total_time_formatted))

        player_layout.addWidget(table)
        layout.addWidget(player_group)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
