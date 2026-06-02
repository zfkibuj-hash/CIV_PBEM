"""
Main application window - PyQt5 GUI with dark/light theme support.
"""
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QLineEdit, QComboBox, QFileDialog, QMessageBox,
    QApplication, QDialog, QCheckBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor

from src.config import AppConfig
from src.models.game import Game, Player
from src.i18n import t
from src.models.turn_calendar import turn_to_year_str
from src.launcher import launch_civ4, is_civ4_running
from src.gui.styles import get_style_for_theme
from src.gui.dialogs import (
    SettingsDialog, NewGameDialog, GameTransportDialog,
    GameStatsDialog, EditGameDialog,
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    settings_saved = pyqtSignal()

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
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry(self)
            x = geo.get("x", 100)
            y = geo.get("y", 100)
            w = geo.get("width", 900)
            h = geo.get("height", 650)
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
        self.header_label.setObjectName("game_header")
        self.header_label.setStyleSheet(
            "padding: 12px 20px; font-size: 12pt; font-weight: bold;"
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

            # Set alias: local nick -> game player name
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

        # Filter combo -- refresh "All players" item text
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

        # Single edition -- use it directly
        if len(enabled) == 1:
            installs = self.config.civ4_installations
            return enabled[0], installs[enabled[0]]

        # Multiple editions -- check preference
        pref = self.config.preferred_edition
        if pref and pref in enabled:
            installs = self.config.civ4_installations
            return pref, installs[pref]

        # Ask user -- buttons instead of dropdown, more intuitive
        from PyQt5.QtWidgets import QDialog as _QDialog, QVBoxLayout as _QVBoxLayout
        from PyQt5.QtWidgets import QLabel as _QLabel, QHBoxLayout as _QHBoxLayout
        from PyQt5.QtWidgets import QCheckBox as _QCheckBox, QPushButton as _QPushButton
        dlg = _QDialog(self)
        dlg.setWindowTitle(t("choose_edition_title"))
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.setStyleSheet(self.styleSheet())
        dlg_layout = _QVBoxLayout(dlg)
        dlg_layout.setSpacing(12)

        dlg_layout.addWidget(_QLabel(t("choose_edition_label")))

        chosen_edition = [None]  # mutable container for lambda capture

        LABELS = {
            "steam": t("civ4_edition_steam"),
            "gog":   t("civ4_edition_gog"),
            "dvd":   t("civ4_edition_dvd"),
        }
        COLORS = {
            "steam": "#1b5e20",
            "gog":   "#0d47a1",
            "dvd":   "#4a148c",
        }

        btn_row = _QHBoxLayout()
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

        remember_cb = _QCheckBox(t("remember_choice"))
        dlg_layout.addWidget(remember_cb)

        cancel_btn = _QPushButton("Anuluj / Cancel")
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
        """Minimize button sends to tray instead of taskbar."""
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
