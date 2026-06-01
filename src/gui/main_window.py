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
from src.models.turn_calendar import turn_to_year_str
from src.launcher import detect_civ4_path, detect_civ4_for_edition, detect_save_path, detect_steam_path, launch_civ4, is_civ4_running

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

        self.setWindowTitle("Civ4 PBEM Manager v4.0")
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

        self.lbl_games = QLabel(t("my_games"))
        self.lbl_games.setStyleSheet("color: #9e9e9e; font-size: 9pt; font-weight: bold;")
        sidebar_layout.addWidget(self.lbl_games)

        self.game_list = QListWidget()
        self.game_list.currentRowChanged.connect(self._on_game_selected)
        sidebar_layout.addWidget(self.game_list)

        self.btn_new_game = QPushButton(t("new_game"))
        self.btn_new_game.clicked.connect(self._on_new_game)
        sidebar_layout.addWidget(self.btn_new_game)

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

        self.btn_edit_game = QPushButton(t("edit_game"))
        self.btn_edit_game.clicked.connect(self._on_edit_game)
        sidebar_layout.addWidget(self.btn_edit_game)

        self.btn_stats = QPushButton(t("statistics"))
        self.btn_stats.clicked.connect(self._on_statistics)
        sidebar_layout.addWidget(self.btn_stats)

        self.btn_settings = QPushButton(t("settings"))
        self.btn_settings.clicked.connect(self._on_settings)
        sidebar_layout.addWidget(self.btn_settings)

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

        content_layout.addLayout(actions_layout)
        # History - clickable list for turn revert
        self.history_group = QGroupBox(t("history_group"))
        history_layout = QVBoxLayout(self.history_group)

        # Player filter
        filter_layout = QHBoxLayout()
        self.lbl_filter = QLabel(t("history_filter"))
        filter_layout.addWidget(self.lbl_filter)
        self.history_filter_combo = QComboBox()
        self.history_filter_combo.addItem(t("history_filter_all"), "")
        self.history_filter_combo.currentIndexChanged.connect(self._on_history_filter_changed)
        filter_layout.addWidget(self.history_filter_combo)
        filter_layout.addStretch()
        history_layout.addLayout(filter_layout)

        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(180)
        history_layout.addWidget(self.history_list)

        # Buttons row under history
        history_buttons = QHBoxLayout()

        self.btn_revert = QPushButton(t("revert_selected"))
        self.btn_revert.setStyleSheet("color: #ff9800; border-color: #ff9800;")
        self.btn_revert.clicked.connect(self._on_revert_turn)
        history_buttons.addWidget(self.btn_revert)

        self.btn_launch_turn = QPushButton(t("launch_this_turn"))
        self.btn_launch_turn.setStyleSheet("color: #42a5f5; border-color: #42a5f5;")
        self.btn_launch_turn.clicked.connect(self._on_launch_turn)
        _any_direct = self.config.get("direct_load_global", False)
        self.btn_launch_turn.setVisible(_any_direct)
        history_buttons.addWidget(self.btn_launch_turn)

        self.btn_remind = QPushButton(t("remind_player"))
        self.btn_remind.clicked.connect(self._on_remind_player)
        self.btn_remind.setStyleSheet("color: #ce93d8; border-color: #ce93d8;")
        history_buttons.addWidget(self.btn_remind)

        self.btn_launch_civ4 = QPushButton(t("launch_civ4"))
        self.btn_launch_civ4.clicked.connect(self._on_launch_civ4)
        self.btn_launch_civ4.setStyleSheet("color: #ff9800; border-color: #ff9800;")
        history_buttons.addWidget(self.btn_launch_civ4)

        history_layout.addLayout(history_buttons)

        content_layout.addWidget(self.history_group)

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
            year_str = turn_to_year_str(game.current_turn, game.game_speed)
            if is_my_turn:
                text = f">> {game.name} [{t('turn')} {game.current_turn}, {year_str}]\n   {t('your_turn')}"
            else:
                cp = game.current_player
                who = cp.name if cp else "?"
                text = f"   {game.name} [{t('turn')} {game.current_turn}, {year_str}]\n   {t('waiting')}: {who}"
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

        self.header_label.setText(f"{game.name}  -  {t('turn')} {game.current_turn} ({turn_to_year_str(game.current_turn, game.game_speed)})")

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

        # Update filter combo with players from this game
        current_filter = self.history_filter_combo.currentData()
        self.history_filter_combo.blockSignals(True)
        self.history_filter_combo.clear()
        self.history_filter_combo.addItem(t("history_filter_all"), "")
        for p in game.players:
            self.history_filter_combo.addItem(p.name, p.name)
        # Restore previous selection if still valid
        if current_filter:
            idx = self.history_filter_combo.findData(current_filter)
            if idx >= 0:
                self.history_filter_combo.setCurrentIndex(idx)
        self.history_filter_combo.blockSignals(False)

        # History (filtered)
        self._populate_history_list()

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

    def _populate_history_list(self):
        """Fill history list with turns, respecting the player filter."""
        game = self.current_game
        if not game:
            return

        self.history_list.clear()
        filter_player = self.history_filter_combo.currentData() or ""

        for turn in reversed(game.history[-50:]):
            # Apply filter
            if filter_player and turn.player_name != filter_player:
                continue

            import datetime
            dt = datetime.datetime.fromtimestamp(turn.timestamp)
            year_str = turn_to_year_str(turn.turn_number, game.game_speed)
            text = f"{dt.strftime('%d.%m %H:%M')}  {turn.player_name} -> {t('turn')} {turn.turn_number} ({year_str})  [{turn.filename}]"
            item = QListWidgetItem(text)
            idx = game.history.index(turn)
            item.setData(Qt.UserRole, idx)
            self.history_list.addItem(item)

    def _on_history_filter_changed(self, index: int):
        """Refresh history list when player filter changes."""
        self._populate_history_list()

    def _clear_game_view(self):
        """Clear the right panel when no game is selected (e.g. after delete)."""
        self.header_label.setText(t("select_game"))
        self.status_banner.setText("")
        self.status_banner.setObjectName("banner_waiting")
        self.players_label.setText("")
        self.history_list.clear()
        self.history_filter_combo.clear()
        self.history_filter_combo.addItem(t("history_filter_all"), "")

    def _on_launch_turn(self):
        """Launch Civ4 with the save file from the selected history entry."""
        if not self.current_game:
            return

        selected = self.history_list.currentItem()
        if not selected:
            QMessageBox.information(self, t("info"), t("revert_select_hint"))
            return

        history_index = selected.data(Qt.UserRole)
        if history_index is None:
            return

        game = self.current_game
        if history_index >= len(game.history):
            return

        target_turn = game.history[history_index]
        if not target_turn.filename:
            QMessageBox.warning(self, t("error"), t("launch_no_file"))
            return

        # Check if the save file exists locally
        save_dir = Path(self.config.save_path)
        local_path = save_dir / target_turn.filename

        if not local_path.exists():
            QMessageBox.warning(
                self, t("error"),
                t("launch_file_missing", filename=target_turn.filename)
            )
            return

        # Resolve which edition to use
        result = self._resolve_edition_for_launch()
        if not result:
            QMessageBox.warning(self, t("error"), t("civ4_not_found"))
            return

        edition, cfg = result
        exe_path = cfg.get("exe_path", "")
        if not exe_path:
            QMessageBox.warning(self, t("error"), t("civ4_not_found"))
            return

        if is_civ4_running():
            self.status_label.setText(t("civ4_already_running"))
            return

        # Pass save only if direct_load enabled for this edition
        save_arg = str(local_path) if self.config.get("direct_load_global", False) else None
        success, msg_key = launch_civ4(
            exe_path,
            save_file=save_arg,
            edition=edition if save_arg else "",
        )
        if success:
            self.status_label.setText(f"{t('civ4_launched')} ({target_turn.filename})")
        else:
            key = msg_key if msg_key in ("civ4_not_found", "steam_not_found") else ""
            self.status_label.setText(t(key) if key else msg_key)

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
            QMessageBox.information(self, t("info"), t("select_game_to_export"))
            return

        game = self.current_game
        export_data = {
            "civ4pbem_version": "1.1",
            "name": game.name,
            "players": [p.to_dict() for p in game.players],
            "transport_config": game.transport_config,
            "game_speed": game.game_speed,
            "smtp": self.config.smtp_config,  # Include SMTP so all players get notifications
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
            self.status_label.setText(t("exported", path=filepath))

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
                QMessageBox.warning(self, t("error"), t("import_error", error="No game name"))
                return

            # Check for duplicate
            for g in self.games:
                if g.name == name:
                    reply = QMessageBox.question(
                        self, t("info"),
                        t("game_exists_overwrite", name=name),
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
            game_speed = data.get("game_speed", "normal")

            game = Game(
                name=name,
                players=players,
                transport_config=transport_config,
                game_speed=game_speed,
            )

            # Import SMTP config if included (shared notification setup)
            imported_smtp = data.get("smtp")
            if imported_smtp and isinstance(imported_smtp, dict):
                current_smtp = self.config.smtp_config
                if not current_smtp.get("host"):
                    self.config.set("smtp", imported_smtp)

            # Ask if user wants to replace global settings with game settings
            imported_transport = data.get("transport_config", {})
            if imported_transport or imported_smtp:
                reply_replace = QMessageBox.question(
                    self,
                    t("info"),
                    t("import_replace_settings"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply_replace == QMessageBox.Yes:
                    if imported_transport:
                        self.config.set("transport", imported_transport)
                    if imported_smtp and isinstance(imported_smtp, dict):
                        self.config.set("smtp", imported_smtp)
                    self.status_label.setText(
                        t("import_settings_replaced", name=name)
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
            self.status_label.setText(t("imported", name=f"{name} ({chosen_name})"))

        except Exception as e:
            QMessageBox.warning(self, t("error"), t("import_error", error=str(e)))

    def _on_delete_game(self):
        """Delete the currently selected game."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_to_delete"))
            return

        reply = QMessageBox.warning(
            self,
            t("delete_game_title"),
            t("delete_game_confirm", name=self.current_game.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Will be connected to controller in main.py
            self._delete_game_requested = True

    def _on_game_transport(self):
        """Open transport configuration dialog for the current game."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_for_transport"))
            return

        dialog = GameTransportDialog(self.config, self.current_game, self.games, self)
        if dialog.exec_() == QDialog.Accepted:
            tc = dialog.get_transport_config()
            self.current_game.transport_config = tc
            from src.config import get_games_dir
            self.current_game.save_to_file(get_games_dir())
            self.status_label.setText(t("transport_saved", name=self.current_game.name))

    def _on_edit_game(self):
        """Open game edit dialog for changing player emails, speed, alias."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_to_export"))
            return

        dialog = EditGameDialog(self.config, self.current_game, self)
        if dialog.exec_() == QDialog.Accepted:
            from src.config import get_games_dir
            self.current_game.save_to_file(get_games_dir())
            self._update_game_view()
            self._refresh_game_list()
            self.status_label.setText(t("game_saved", name=self.current_game.name))

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
        # Sidebar
        self.lbl_games.setText(t("my_games"))
        self.btn_new_game.setText(t("new_game"))
        self.btn_import_game.setText(t("import_game"))
        self.btn_export_game.setText(t("export_game"))
        self.btn_delete_game.setText(t("delete_game"))
        self.btn_game_transport.setText(t("game_transport"))
        self.btn_edit_game.setText(t("edit_game"))
        self.btn_stats.setText(t("statistics"))
        self.btn_settings.setText(t("settings"))

        # Action buttons
        self.btn_download.setText(t("download_save"))
        self.btn_upload.setText(t("upload_save"))
        self.btn_open_folder.setText(t("open_folder"))
        self.btn_check_now.setText(t("check_now"))
        self.btn_launch_civ4.setText(t("launch_civ4"))
        self.btn_remind.setText(t("remind_player"))

        # History panel
        self.history_group.setTitle(t("history_group"))
        self.lbl_filter.setText(t("history_filter"))
        self.btn_revert.setText(t("revert_selected"))
        self.btn_launch_turn.setText(t("launch_this_turn"))
        self.btn_launch_turn.setVisible(self.config.get("direct_load_global", False))
        self.btn_remind.setText(t("remind_player"))

        # Filter combo — refresh "All players" item text
        self.history_filter_combo.blockSignals(True)
        if self.history_filter_combo.count() > 0:
            self.history_filter_combo.setItemText(0, t("history_filter_all"))
        self.history_filter_combo.blockSignals(False)

        # Status bar
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
            QMessageBox.warning(self, t("error"), f"{t('save_path')}\n{save_path}")
            return

        # Let user pick the save file
        filepath, _ = QFileDialog.getOpenFileName(
            self, t("choose_save_to_upload"), str(save_path),
            t("civ4_saves_filter")
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

    def _on_remind_player(self):
        """Send a reminder email to the current player of the selected game."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game"))
            return
        game = self.current_game
        cp = game.current_player
        if not cp:
            return
        # Signal to controller (connected in main.py)
        self._remind_game = game
        self.status_label.setText(f"{t('remind_player')}: {cp.name}...")

    def _on_statistics(self):
        """Show game statistics dialog."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("stats_no_game"))
            return
        dialog = GameStatsDialog(self.config, self.current_game, self)
        dialog.exec_()

    def _resolve_edition_for_launch(self) -> Optional[tuple[str, dict]]:
        """Determine which edition to use for launching Civ4.

        Returns (edition_key, edition_cfg) or None if nothing configured.
        If multiple editions enabled and no preference set, shows a dialog.
        Saves preference if user checks "remember".
        """
        enabled = self.config.get_enabled_editions()
        if not enabled:
            return None

        # Single edition — use it directly
        if len(enabled) == 1:
            installs = self.config.civ4_installations
            return enabled[0], installs[enabled[0]]

        # Multiple editions — check preference
        pref = self.config.preferred_edition
        if pref and pref in enabled:
            installs = self.config.civ4_installations
            return pref, installs[pref]

        # Ask user — buttons instead of dropdown, more intuitive
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox, QPushButton as _QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle(t("choose_edition_title"))
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.setStyleSheet(self.styleSheet())
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setSpacing(12)

        dlg_layout.addWidget(QLabel(t("choose_edition_label")))

        chosen_edition = [None]  # mutable container for lambda capture

        LABELS = {
            "steam": t("civ4_edition_steam"),
            "gog":   t("civ4_edition_gog"),
            "dvd":   t("civ4_edition_dvd"),
        }
        COLORS = {
            "steam": "#1b5e20",   # green
            "gog":   "#0d47a1",   # blue
            "dvd":   "#4a148c",   # purple
        }

        btn_row = QHBoxLayout()
        for e in enabled:
            btn = _QPushButton(LABELS[e])
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(100)
            color = COLORS.get(e, "#333")
            btn.setStyleSheet(
                f"background-color: {color}; color: white; "
                f"font-weight: bold; border-radius: 4px; font-size: 11pt;"
            )
            btn.clicked.connect(lambda checked, ed=e: (chosen_edition.__setitem__(0, ed), dlg.accept()))
            btn_row.addWidget(btn)
        dlg_layout.addLayout(btn_row)

        remember_cb = QCheckBox(t("remember_choice"))
        dlg_layout.addWidget(remember_cb)

        cancel_btn = _QPushButton(t("error"))  # reuse as cancel
        cancel_btn.setText("Anuluj / Cancel")
        cancel_btn.clicked.connect(dlg.reject)
        dlg_layout.addWidget(cancel_btn)

        if dlg.exec_() != QDialog.Accepted or chosen_edition[0] is None:
            return None

        chosen = chosen_edition[0]
        if remember_cb.isChecked():
            self.config.set("preferred_edition", chosen)

        installs = self.config.civ4_installations
        return chosen, installs[chosen]

    def _on_launch_civ4(self):
        """Launch Civ4 BTS with the latest save for the current game."""
        result = self._resolve_edition_for_launch()
        if not result:
            QMessageBox.warning(self, t("error"), t("civ4_not_found"))
            return

        edition, cfg = result
        exe_path = cfg.get("exe_path", "")
        if not exe_path:
            QMessageBox.warning(self, t("error"), t("civ4_not_found"))
            return

        if is_civ4_running():
            self.status_label.setText(t("civ4_already_running"))
            return

        # Find latest save only if direct_load_global enabled
        save_file = None
        if self.config.get("direct_load_global", False) and self.current_game:
            save_dir = Path(self.config.save_path)
            if save_dir.exists():
                pattern = f"{self.current_game.name}_T*.CivBeyondSwordSave"
                saves = list(save_dir.glob(pattern))
                if saves:
                    saves.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    save_file = str(saves[0])

        success, msg_key = launch_civ4(
            exe_path,
            save_file=save_file,
            edition=edition if save_file else "",
        )
        if success:
            status = t(msg_key) if msg_key in ("civ4_launched", "civ4_already_running") else msg_key
            if save_file:
                status += f" ({Path(save_file).name})"
            self.status_label.setText(status)
        else:
            key = msg_key if msg_key in ("civ4_not_found", "steam_not_found") else ""
            self.status_label.setText(t(key) if key else msg_key)

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
                            t("tray_minimized_msg")
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
        form.addRow(t("game_name"), self.name_edit)

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
        btn_detect_saves = QPushButton(t("detect_civ4"))
        btn_detect_saves.clicked.connect(self._detect_save_path)
        path_layout.addWidget(btn_detect_saves)
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

        # ---- Civ4 BTS installations (multi-edition) ----
        installs_group = QGroupBox(t("civ4_installations_group"))
        installs_layout = QVBoxLayout(installs_group)
        installs_layout.setSpacing(6)

        installs = self.config.civ4_installations
        self._edition_widgets = {}  # edition -> dict of widgets

        EDITION_LABELS = {
            "steam": t("civ4_edition_steam"),
            "gog":   t("civ4_edition_gog"),
            "dvd":   t("civ4_edition_dvd"),
        }

        for edition in ("steam", "gog", "dvd"):
            cfg = installs.get(edition, {})
            ed_group = QGroupBox(EDITION_LABELS[edition])
            ed_form = QFormLayout(ed_group)
            ed_form.setSpacing(4)

            # Enabled checkbox
            enabled_cb = QCheckBox(t("edition_enabled"))
            enabled_cb.setChecked(cfg.get("enabled", False))
            ed_form.addRow(enabled_cb)

            # exe path row — disabled until checkbox ticked
            exe_layout = QHBoxLayout()
            exe_edit = QLineEdit(cfg.get("exe_path", ""))
            exe_edit.setPlaceholderText("C:\\...\\Civ4BeyondSword.exe")
            exe_edit.setEnabled(cfg.get("enabled", False))
            exe_layout.addWidget(exe_edit)

            btn_browse = QPushButton(t("browse"))
            btn_browse.setEnabled(cfg.get("enabled", False))
            btn_browse.clicked.connect(
                lambda checked, e=exe_edit: self._browse_edition_exe(e))
            exe_layout.addWidget(btn_browse)

            btn_detect = QPushButton(t("detect_for_edition"))
            btn_detect.setEnabled(cfg.get("enabled", False))
            btn_detect.clicked.connect(
                lambda checked, ed=edition, e=exe_edit: self._detect_edition_exe(ed, e))
            exe_layout.addWidget(btn_detect)

            ed_form.addRow(t("edition_exe_path"), exe_layout)

            # Wire checkbox → enable/disable path fields
            def _toggle_edition(state, e=exe_edit, bb=btn_browse, bd=btn_detect):
                e.setEnabled(bool(state))
                bb.setEnabled(bool(state))
                bd.setEnabled(bool(state))
            enabled_cb.stateChanged.connect(_toggle_edition)

            installs_layout.addWidget(ed_group)

            self._edition_widgets[edition] = {
                "enabled": enabled_cb,
                "exe_edit": exe_edit,
                "direct_cb": None,   # global checkbox used instead
                "steam_exe_edit": None,
                "app_id_edit": None,
            }

        # Global direct load checkbox — applies to all editions
        self.direct_load_global_check = QCheckBox(t("edition_direct_load"))
        self.direct_load_global_check.setChecked(
            self.config.get("direct_load_global", False))
        installs_layout.addWidget(self.direct_load_global_check)

        # Preferred edition when multiple enabled
        pref_layout = QHBoxLayout()
        pref_layout.addWidget(QLabel(t("preferred_edition")))
        self.preferred_edition_combo = QComboBox()
        self.preferred_edition_combo.addItem(t("preferred_edition_ask"), "")
        self.preferred_edition_combo.addItem(t("civ4_edition_steam"), "steam")
        self.preferred_edition_combo.addItem(t("civ4_edition_gog"), "gog")
        self.preferred_edition_combo.addItem(t("civ4_edition_dvd"), "dvd")
        pref_val = self.config.preferred_edition
        pref_idx = self.preferred_edition_combo.findData(pref_val)
        self.preferred_edition_combo.setCurrentIndex(pref_idx if pref_idx >= 0 else 0)
        pref_layout.addWidget(self.preferred_edition_combo)
        pref_layout.addStretch()
        installs_layout.addLayout(pref_layout)

        # --- File association ---
        from src.launcher import get_current_file_association
        assoc_group = QGroupBox(t("file_assoc_group"))
        assoc_layout = QVBoxLayout(assoc_group)

        current_assoc = get_current_file_association() or t("file_assoc_none")
        assoc_current_lbl = QLabel(f"{t('file_assoc_current')} {current_assoc}")
        assoc_current_lbl.setWordWrap(True)
        assoc_current_lbl.setStyleSheet("font-size: 8pt; color: #9e9e9e;")
        assoc_layout.addWidget(assoc_current_lbl)

        assoc_hint = QLabel(t("file_assoc_set"))
        assoc_hint.setStyleSheet("font-size: 9pt;")
        assoc_layout.addWidget(assoc_hint)

        assoc_btn_row = QHBoxLayout()
        ASSOC_COLORS = {"steam": "#1b5e20", "gog": "#0d47a1", "dvd": "#4a148c"}
        for ed in ("steam", "gog", "dvd"):
            lbl = EDITION_LABELS[ed]
            btn_a = QPushButton(lbl)
            btn_a.setMinimumHeight(36)
            c = ASSOC_COLORS[ed]
            btn_a.setStyleSheet(
                f"background-color: {c}; color: white; font-weight: bold; border-radius: 4px;")
            btn_a.clicked.connect(
                lambda checked, e=ed: self._set_file_association(e))
            assoc_btn_row.addWidget(btn_a)
        assoc_layout.addLayout(assoc_btn_row)

        installs_layout.addWidget(assoc_group)

        layout.addWidget(installs_group)

        layout.addStretch()
        scroll.setWidget(tab)
        return scroll

    def _browse_edition_exe(self, target_edit):
        """Browse for exe and set into target_edit."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik .exe", target_edit.text(),
            "Executable (*.exe);;All Files (*)"
        )
        if filepath:
            target_edit.setText(filepath)

    def _detect_edition_exe(self, edition: str, target_edit):
        """Auto-detect Civ4 exe for a specific edition."""
        detected = detect_civ4_for_edition(edition)
        if detected:
            target_edit.setText(detected)
            QMessageBox.information(self, "OK", t("civ4_detected", path=detected))
        else:
            QMessageBox.information(self, t("info"), t("civ4_not_detected"))

    def _detect_steam_into_widget(self):
        """Auto-detect Steam.exe and fill into Steam edition's steam_exe field."""
        detected = detect_steam_path()
        if detected:
            widgets = self._edition_widgets.get("steam", {})
            if widgets.get("steam_exe_edit"):
                widgets["steam_exe_edit"].setText(detected)
            QMessageBox.information(self, "OK", t("steam_detected", path=detected))
        else:
            QMessageBox.information(self, t("info"), t("steam_not_detected"))

    def _set_file_association(self, edition: str):
        """Set Windows file association for .CivBeyondSwordSave for the given edition."""
        from src.launcher import set_file_association, get_current_file_association

        widgets = self._edition_widgets.get(edition, {})
        exe_path = widgets["exe_edit"].text().strip() if widgets.get("exe_edit") else ""
        steam_exe = ""
        app_id = "8800"
        if edition == "steam":
            steam_exe = widgets["steam_exe_edit"].text().strip() if widgets.get("steam_exe_edit") else ""
            app_id = widgets["app_id_edit"].text().strip() if widgets.get("app_id_edit") else "8800"

        success, result = set_file_association(
            edition=edition,
            exe_path=exe_path,
            steam_path=steam_exe,
            steam_app_id=app_id or "8800",
        )
        if success:
            QMessageBox.information(self, "OK", t("file_assoc_ok", cmd=result))
        else:
            # Translate known error keys
            msg = t(result) if result in (
                "civ4_not_found", "steam_not_found",
                "registry_windows_only", "registry_permission_error"
            ) else t("file_assoc_error", error=result)
            QMessageBox.warning(self, t("error"), msg)

    # --- Tab 2: Transport ---
    def _create_transport_tab(self) -> QWidget:
        from PyQt5.QtWidgets import QScrollArea

        # If config is locked, show lock message instead of form
        if not self.config.is_unlocked:
            locked_tab = QWidget()
            locked_layout = QVBoxLayout(locked_tab)
            locked_layout.addStretch()
            lock_label = QLabel(f"🔒 {t('transport_locked')}")
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
        type_group = QGroupBox(t("transport_method"))
        type_form = QFormLayout(type_group)
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.transport_type.currentTextChanged.connect(self._on_transport_type_changed)
        type_form.addRow(t("transport_type_label"), self.transport_type)

        self.ssl_ignore_check = QCheckBox(t("ssl_ignore"))
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        type_form.addRow(self.ssl_ignore_check)

        layout.addWidget(type_group)

        # File-based transport settings (FTP/SFTP/WebDAV)
        self.file_transport_group = QGroupBox(t("file_transport_group"))
        file_form = QFormLayout(self.file_transport_group)

        self.transport_host = QLineEdit(tc.get("host", ""))
        self.transport_host.setPlaceholderText("np. ftp.mojserwer.pl")
        file_form.addRow(t("field_host"), self.transport_host)

        self.transport_port = QSpinBox()
        self.transport_port.setRange(1, 65535)
        self.transport_port.setValue(tc.get("port", 21))
        file_form.addRow(t("field_port"), self.transport_port)

        self.transport_user = QLineEdit(tc.get("username", ""))
        file_form.addRow(t("field_login"), self.transport_user)

        self.transport_pass = QLineEdit(tc.get("password", ""))
        self.transport_pass.setEchoMode(QLineEdit.Password)
        file_form.addRow(t("field_password"), self.transport_pass)

        self.transport_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        file_form.addRow(t("field_remote_dir"), self.transport_dir)

        layout.addWidget(self.file_transport_group)

        # Email transport settings (SMTP + IMAP)
        self.email_transport_group = QGroupBox(t("email_transport_group"))
        email_form = QFormLayout(self.email_transport_group)
        email_form.setSpacing(6)

        ec = tc.get("email", {})

        self.et_mode = QComboBox()
        self.et_mode.addItems(["shared", "individual"])
        self.et_mode.setCurrentText(ec.get("mode", "shared"))
        email_form.addRow(t("field_mode"), self.et_mode)

        self.et_shared_email = QLineEdit(ec.get("shared_email", ""))
        self.et_shared_email.setPlaceholderText("wspoldzielona skrzynka, np. civ4pbem@...")
        email_form.addRow(t("field_shared_mailbox"), self.et_shared_email)

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
        email_form.addRow("SMTP " + t("field_password"), self.et_smtp_pass)

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
        email_form.addRow("IMAP " + t("field_password"), self.et_imap_pass)

        self.et_from_address = QLineEdit(ec.get("from_address", ""))
        self.et_from_address.setPlaceholderText("adres nadawcy (opcjonalnie)")
        email_form.addRow(t("field_from"), self.et_from_address)

        et_warning = QLabel(f"⚠ {t('email_warning')}")
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
            lock_label = QLabel(f"🔒 {t('smtp_locked')}")
            lock_label.setAlignment(Qt.AlignCenter)
            lock_label.setStyleSheet("font-size: 11pt; color: #ff9800; padding: 40px;")
            locked_layout.addWidget(lock_label)
            locked_layout.addStretch()
            return locked_tab

        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        sc = self.config.smtp_config

        # --- Master switch ---
        self.notifications_enabled_check = QCheckBox(t("notifications_master_switch"))
        self.notifications_enabled_check.setChecked(
            self.config.get("notifications_enabled", True))
        self.notifications_enabled_check.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(self.notifications_enabled_check)

        # Container that gets enabled/disabled by master switch
        notif_container = QWidget()
        notif_layout = QVBoxLayout(notif_container)
        notif_layout.setContentsMargins(0, 0, 0, 0)
        notif_layout.setSpacing(10)

        # --- Channels ---
        channels_group = QGroupBox(t("tab_notifications"))
        channels_layout = QVBoxLayout(channels_group)

        self.notify_via_smtp_check = QCheckBox(t("notify_via_smtp"))
        self.notify_via_smtp_check.setChecked(self.config.get("notify_via_smtp", True))
        channels_layout.addWidget(self.notify_via_smtp_check)

        self.notify_via_app_check = QCheckBox(t("notify_via_app"))
        self.notify_via_app_check.setChecked(self.config.get("notify_via_app", False))
        channels_layout.addWidget(self.notify_via_app_check)

        app_hint = QLabel(f"  ℹ {t('notify_via_app_hint')}")
        app_hint.setWordWrap(True)
        app_hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        channels_layout.addWidget(app_hint)

        notif_layout.addWidget(channels_group)

        # --- SMTP settings (shown when SMTP channel enabled) ---
        self.smtp_settings_group = QGroupBox(t("notifications_group"))
        smtp_form = QFormLayout(self.smtp_settings_group)
        smtp_form.setSpacing(8)

        self.smtp_host = QLineEdit(sc.get("host", ""))
        self.smtp_host.setPlaceholderText("np. smtp.gmail.com")
        smtp_form.addRow("Host SMTP:", self.smtp_host)

        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(sc.get("port", 587))
        smtp_form.addRow(t("field_port"), self.smtp_port)

        self.smtp_user = QLineEdit(sc.get("username", ""))
        self.smtp_user.setPlaceholderText(t("notification_empty_hint"))
        smtp_form.addRow(t("field_login"), self.smtp_user)

        self.smtp_pass = QLineEdit(sc.get("password", ""))
        self.smtp_pass.setEchoMode(QLineEdit.Password)
        self.smtp_pass.setPlaceholderText(t("notification_empty_hint"))
        smtp_form.addRow(t("field_password"), self.smtp_pass)

        self.smtp_from = QLineEdit(sc.get("from_address", ""))
        self.smtp_from.setPlaceholderText(t("notification_empty_hint"))
        smtp_form.addRow(t("field_from"), self.smtp_from)

        info_lbl = QLabel(t("notifications_info"))
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        smtp_form.addRow(info_lbl)

        notif_layout.addWidget(self.smtp_settings_group)

        # --- Message templates ---
        templates_group = QGroupBox(t("notif_templates_group"))
        tpl_layout = QVBoxLayout(templates_group)
        tpl_layout.setSpacing(8)

        VARS = ["{game}", "{turn}", "{from_player}", "{to_player}"]

        def _make_var_buttons(target_widget):
            """Return a row of variable-insert buttons for a QLineEdit or QTextEdit."""
            row = QHBoxLayout()
            hint = QLabel(t("notif_template_hint"))
            hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
            row.addWidget(hint)
            for var in VARS:
                btn = QPushButton(var)
                btn.setMaximumWidth(90)
                btn.setStyleSheet("font-size: 8pt; padding: 2px 4px;")
                if isinstance(target_widget, QTextEdit):
                    btn.clicked.connect(
                        lambda checked, v=var, w=target_widget:
                        w.insertPlainText(v))
                else:
                    btn.clicked.connect(
                        lambda checked, v=var, w=target_widget:
                        w.insert(v))
                row.addWidget(btn)
            row.addStretch()
            return row

        # Turn subject
        tpl_layout.addWidget(QLabel(t("notif_subject_template")))
        self.smtp_subject_template = QLineEdit(sc.get("subject_template", ""))
        self.smtp_subject_template.setPlaceholderText(
            "[Civ4 PBEM] {game} - Your turn! (Turn {turn})")
        tpl_layout.addWidget(self.smtp_subject_template)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_subject_template))

        # Turn body
        tpl_layout.addWidget(QLabel(t("notif_body_template")))
        self.smtp_body_template = QTextEdit()
        self.smtp_body_template.setPlainText(sc.get("body_template", ""))
        self.smtp_body_template.setPlaceholderText(
            "Hi {to_player}!\n\n{from_player} finished turn {turn} in {game}.\nYour turn!")
        self.smtp_body_template.setFixedHeight(80)
        tpl_layout.addWidget(self.smtp_body_template)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_body_template))

        # Reminder subject
        tpl_layout.addWidget(QLabel(t("notif_reminder_subject_template")))
        self.smtp_reminder_subject = QLineEdit(sc.get("reminder_subject_template", ""))
        self.smtp_reminder_subject.setPlaceholderText(
            "[Civ4 PBEM] {game} - Reminder: your turn! (Turn {turn})")
        tpl_layout.addWidget(self.smtp_reminder_subject)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_reminder_subject))

        # Reminder body
        tpl_layout.addWidget(QLabel(t("notif_reminder_body_template")))
        self.smtp_reminder_body = QTextEdit()
        self.smtp_reminder_body.setPlainText(sc.get("reminder_body_template", ""))
        self.smtp_reminder_body.setPlaceholderText(
            "Hi {to_player}!\n\nJust a reminder — it's your turn in {game}!\nTurn: {turn}")
        self.smtp_reminder_body.setFixedHeight(80)
        tpl_layout.addWidget(self.smtp_reminder_body)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_reminder_body))

        notif_layout.addWidget(templates_group)

        # --- Auto-reminder ---
        reminder_group = QGroupBox(t("reminder_auto_group"))
        reminder_form = QFormLayout(reminder_group)
        reminder_form.setSpacing(8)

        self.reminder_auto_check = QCheckBox(t("reminder_auto_enabled"))
        self.reminder_auto_check.setChecked(self.config.get("reminder_auto_enabled", False))
        reminder_form.addRow(self.reminder_auto_check)

        self.reminder_auto_days = QSpinBox()
        self.reminder_auto_days.setRange(1, 30)
        self.reminder_auto_days.setValue(self.config.get("reminder_auto_days", 2))
        self.reminder_auto_days.setSuffix(
            " dni" if self.config.language == "pl" else " days")
        reminder_form.addRow(t("reminder_auto_days"), self.reminder_auto_days)

        notif_layout.addWidget(reminder_group)
        notif_layout.addStretch()

        layout.addWidget(notif_container)

        # Wire master switch → enable/disable container
        def _toggle_notif(state):
            notif_container.setEnabled(bool(state))
        self.notifications_enabled_check.stateChanged.connect(_toggle_notif)
        notif_container.setEnabled(self.notifications_enabled_check.isChecked())

        # Wire SMTP channel → show/hide SMTP settings
        def _toggle_smtp(state):
            self.smtp_settings_group.setEnabled(bool(state))
            templates_group.setEnabled(bool(state))
        self.notify_via_smtp_check.stateChanged.connect(_toggle_smtp)
        _toggle_smtp(self.notify_via_smtp_check.isChecked())

        scroll.setWidget(tab)
        return scroll

    # --- Tab 4: Security ---
    def _create_security_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Status
        status_group = QGroupBox(t("tab_security"))
        status_layout = QVBoxLayout(status_group)

        if self.config.has_master_password:
            if self.config.is_unlocked:
                status_label = QLabel(f"🔓 {t('security_status_unlocked')}")
                status_label.setStyleSheet("color: #66bb6a; font-size: 10pt;")
            else:
                status_label = QLabel(f"🔒 {t('security_status_locked')}")
                status_label.setStyleSheet("color: #ff9800; font-size: 10pt;")
        else:
            status_label = QLabel(f"⚠ {t('security_no_password')}")
            status_label.setStyleSheet("color: #ef5350; font-size: 10pt;")

        status_layout.addWidget(status_label)
        layout.addWidget(status_group)

        # Set / Change password
        password_group = QGroupBox(t("master_password_group"))
        password_form = QFormLayout(password_group)

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText(t("new_password_placeholder"))
        password_form.addRow(t("new_password"), self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText(t("confirm_password_placeholder"))
        password_form.addRow(t("confirm_password"), self.confirm_password_edit)

        btn_set_password = QPushButton(t("set_password_btn"))
        btn_set_password.setStyleSheet("color: #ff9800; border-color: #ff9800; font-weight: bold;")
        btn_set_password.clicked.connect(self._on_set_master_password)
        password_form.addRow(btn_set_password)

        layout.addWidget(password_group)

        # Info
        info_label = QLabel(t("security_info"))
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
            QMessageBox.warning(self, t("error"), t("password_empty"))
            return

        if len(new_pass) < 4:
            QMessageBox.warning(self, t("error"), t("password_empty"))
            return

        if new_pass != confirm:
            QMessageBox.warning(self, t("error"), t("password_mismatch"))
            return

        if self.config.has_master_password and not self.config.is_unlocked:
            QMessageBox.warning(self, t("error"), t("password_locked_error"))
            return

        self.config.set_master_password(new_pass)
        QMessageBox.information(self, "OK", t("password_set_ok"))
        self.new_password_edit.clear()
        self.confirm_password_edit.clear()

    # --- Logic ---
    def _on_transport_type_changed(self, transport_type: str):
        """Show/hide transport panels based on selected type."""
        self.file_transport_group.setVisible(transport_type in ("ftp", "sftp", "webdav"))
        self.email_transport_group.setVisible(transport_type == "email")

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, t("save_path"), self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)

    def _detect_save_path(self):
        """Auto-detect Civ4 BTS save folder by checking common locations."""
        from src.launcher import detect_save_path
        detected = detect_save_path()
        if detected:
            self.path_edit.setText(detected)
            QMessageBox.information(self, "OK", t("save_path_detected", path=detected))
        else:
            QMessageBox.information(self, t("info"), t("save_path_not_detected"))

    def _browse_civ4_path(self):
        """Legacy stub — replaced by per-edition browse."""
        pass

    def _detect_civ4(self):
        """Legacy stub — replaced by per-edition detect."""
        pass

    def _browse_steam_path(self):
        """Legacy stub — replaced by per-edition browse."""
        pass

    def _detect_steam(self):
        """Legacy stub — replaced by _detect_steam_into_widget."""
        pass

    def _on_edition_changed(self, index: int):
        """Legacy stub — no longer used (multi-edition UI replaced single dropdown)."""
        pass

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

        # Civ4 installations (multi-edition)
        installs = {}
        for edition in ("steam", "gog", "dvd"):
            w = self._edition_widgets.get(edition, {})
            installs[edition] = {
                "enabled": w["enabled"].isChecked() if w.get("enabled") else False,
                "exe_path": w["exe_edit"].text().strip() if w.get("exe_edit") else "",
            }
        self.config.set("civ4_installations", installs)
        self.config.set("direct_load_global", self.direct_load_global_check.isChecked())
        self.config.set("preferred_edition", self.preferred_edition_combo.currentData())

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
            "subject_template": self.smtp_subject_template.text().strip(),
            "body_template": self.smtp_body_template.toPlainText().strip(),
            "reminder_subject_template": self.smtp_reminder_subject.text().strip(),
            "reminder_body_template": self.smtp_reminder_body.toPlainText().strip(),
        })

        # Notification channels + auto-reminder
        self.config.set("notifications_enabled",
                        self.notifications_enabled_check.isChecked())
        self.config.set("notify_via_smtp", self.notify_via_smtp_check.isChecked())
        self.config.set("notify_via_app", self.notify_via_app_check.isChecked())
        self.config.set("reminder_auto_enabled", self.reminder_auto_check.isChecked())
        self.config.set("reminder_auto_days", self.reminder_auto_days.value())

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
        copy_group = QGroupBox(t("game_transport_copy_group"))
        copy_layout = QHBoxLayout(copy_group)

        btn_copy_defaults = QPushButton(t("copy_defaults"))
        btn_copy_defaults.clicked.connect(self._copy_from_defaults)
        copy_layout.addWidget(btn_copy_defaults)

        self.copy_game_combo = QComboBox()
        self.copy_game_combo.addItem("-- " + t("copy_from") + " --")
        for g in self.all_games:
            if g.name != self.game.name and g.transport_config:
                self.copy_game_combo.addItem(g.name)
        copy_layout.addWidget(self.copy_game_combo)

        btn_copy_game = QPushButton(t("copy_from"))
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
        type_group = QGroupBox(t("transport_method"))
        type_form = QFormLayout(type_group)
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.transport_type.currentTextChanged.connect(self._on_type_changed)
        type_form.addRow(t("transport_type_label"), self.transport_type)

        self.ssl_ignore_check = QCheckBox(t("ssl_ignore"))
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        type_form.addRow(self.ssl_ignore_check)
        form_layout.addWidget(type_group)

        # File-based (FTP/SFTP/WebDAV)
        self.file_group = QGroupBox(t("file_transport_group"))
        file_form = QFormLayout(self.file_group)
        self.t_host = QLineEdit(tc.get("host", ""))
        file_form.addRow(t("field_host"), self.t_host)
        self.t_port = QSpinBox()
        self.t_port.setRange(1, 65535)
        self.t_port.setValue(tc.get("port", 21))
        file_form.addRow(t("field_port"), self.t_port)
        self.t_user = QLineEdit(tc.get("username", ""))
        file_form.addRow(t("field_login"), self.t_user)
        self.t_pass = QLineEdit(tc.get("password", ""))
        self.t_pass.setEchoMode(QLineEdit.Password)
        file_form.addRow(t("field_password"), self.t_pass)
        self.t_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        file_form.addRow(t("field_remote_dir"), self.t_dir)
        form_layout.addWidget(self.file_group)

        # Email
        self.email_group = QGroupBox(t("email_transport_group"))
        email_form = QFormLayout(self.email_group)
        ec = tc.get("email", {})
        self.e_mode = QComboBox()
        self.e_mode.addItems(["shared", "individual"])
        self.e_mode.setCurrentText(ec.get("mode", "shared"))
        email_form.addRow(t("field_mode"), self.e_mode)
        self.e_shared = QLineEdit(ec.get("shared_email", ""))
        email_form.addRow(t("field_shared_mailbox"), self.e_shared)
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
        email_form.addRow("SMTP " + t("field_password"), self.e_smtp_pass)
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
        email_form.addRow("IMAP " + t("field_password"), self.e_imap_pass)
        self.e_from = QLineEdit(ec.get("from_address", ""))
        email_form.addRow(t("field_from"), self.e_from)

        email_warning = QLabel(f"⚠ {t('email_warning')}")
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
        btn_test = QPushButton(t("transport_test_btn"))
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
            QMessageBox.warning(self, t("test_connection"), t("transport_not_configured_short"))
            return

        QApplication.processEvents()
        success = transport.connect()
        if success:
            transport.disconnect()
            QMessageBox.information(self, t("test_connection"), t("connection_ok"))
        else:
            QMessageBox.warning(self, t("test_connection"), t("connection_failed"))

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
        overview_form.addRow(t("stats_current_round"), QLabel(
            f"{stats.current_round} ({turn_to_year_str(stats.current_round, self.game.game_speed)})"
        ))
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
