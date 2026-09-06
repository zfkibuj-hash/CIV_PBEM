"""
Main application window - PyQt5 GUI with dark/light theme support.
"""
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QLineEdit, QComboBox, QFileDialog, QMessageBox,
    QApplication, QDialog, QCheckBox, QInputDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from src.config import AppConfig, version_label
from src.models.game import Game, Player
from src.i18n import t
from src.models.turn_calendar import turn_to_year_str
from src.models.statistics import format_duration
from src.launcher import launch_civ4, is_civ4_running
from src.saves import find_save_file, iter_save_dirs, latest_game_save
from src.gui.styles import get_style_for_theme
from src.gui.player_order_widget import PlayerOrderWidget
from src.gui.dialogs import (
    SettingsDialog, NewGameDialog, GameTransportDialog,
    GameStatsDialog, EditGameDialog, DangerZoneDialog,
)
from src.gui.dialogs.health_dialog import HealthDialog
from src.health_check import HealthReport

logger = logging.getLogger(__name__)

FILTER_ALL = ""
FILTER_MINE = "__mine__"


class MainWindow(QMainWindow):
    """Main application window."""

    settings_saved = Signal()
    download_file_requested = Signal(str)
    delete_remote_save_requested = Signal(str)
    delete_all_remote_requested = Signal()
    delete_game_requested = Signal()
    play_now_requested = Signal()
    push_shared_config_requested = Signal(object)
    roster_events_requested = Signal(object, list)  # Game, events
    game_imported = Signal(object)  # Game — pull turn state from server
    remind_requested = Signal(object)  # Game

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.games: list[Game] = []
        self.current_game: Optional[Game] = None
        self._minimize_to_tray = False  # Set to True by main.py when tray is available
        self._tray_icon = None  # Reference to TrayIcon, set by main.py
        self._health_report: Optional[HealthReport] = None

        self.setWindowTitle(f"Civ4 PBEM Manager {version_label()}")
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
        if hasattr(self, "player_order"):
            self.player_order.set_dark(is_dark)
            if self.current_game:
                self.player_order.update_from_game(
                    self.current_game, self.config.player_name, dark=is_dark,
                )

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
            from PySide6.QtWidgets import QApplication as _App
            screen = _App.primaryScreen()
            screen_rect = screen.availableGeometry() if screen else None
            x = geo.get("x", 100)
            y = geo.get("y", 100)
            w = geo.get("width", 900)
            h = geo.get("height", 650)
            if screen_rect:
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

        invite_row = QHBoxLayout()
        self.btn_copy_invite = QPushButton(t("copy_invite_code"))
        self.btn_copy_invite.setToolTip(t("copy_invite_code_hint"))
        self.btn_copy_invite.clicked.connect(self._on_export_invite_code)
        invite_row.addWidget(self.btn_copy_invite)

        self.btn_paste_invite = QPushButton(t("paste_invite_code"))
        self.btn_paste_invite.setToolTip(t("paste_invite_code_hint"))
        self.btn_paste_invite.clicked.connect(self._on_import_invite_code)
        invite_row.addWidget(self.btn_paste_invite)
        sidebar_layout.addLayout(invite_row)

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

        # Destructive actions are intentionally buried (not red, bottom of sidebar)
        self.btn_danger_zone = QPushButton(t("danger_zone_open"))
        self.btn_danger_zone.setFlat(True)
        self.btn_danger_zone.setStyleSheet("color: #e53935; text-align: center;")
        self.btn_danger_zone.setToolTip(t("danger_zone_hint"))
        self.btn_danger_zone.clicked.connect(self._on_danger_zone)
        sidebar_layout.addWidget(self.btn_danger_zone)

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

        # Players — colored turn-order chips
        self.player_order = PlayerOrderWidget()
        self.player_order.set_dark(self.config.get("dark_mode", True))
        content_layout.addWidget(self.player_order)

        # Primary action when it's your turn
        self.btn_play_now = QPushButton(t("play_now"))
        self.btn_play_now.setObjectName("btn_play_now")
        self.btn_play_now.setMinimumHeight(52)
        self.btn_play_now.clicked.connect(self._on_play_now)
        self.btn_play_now.hide()
        content_layout.addWidget(self.btn_play_now)

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
        self.btn_check_now.setToolTip(t("check_now_hint"))
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
        self.history_list.setMinimumHeight(200)
        self.history_list.setMaximumHeight(280)
        history_layout.addWidget(self.history_list)

        # Buttons row under history
        history_buttons = QHBoxLayout()

        self.btn_revert = QPushButton(t("revert_selected"))
        self.btn_revert.setStyleSheet("color: #ff9800; border-color: #ff9800;")
        self.btn_revert.clicked.connect(self._on_revert_turn)
        history_buttons.addWidget(self.btn_revert)

        self.btn_download_turn = QPushButton(t("history_download_this"))
        self.btn_download_turn.clicked.connect(self._on_download_selected_turn)
        history_buttons.addWidget(self.btn_download_turn)

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

        # PBEM health strip (click for details)
        self.health_banner = QLabel(t("health_ok"))
        self.health_banner.setObjectName("health_ok")
        self.health_banner.setCursor(Qt.PointingHandCursor)
        self.health_banner.setToolTip(t("health_click_hint"))
        self.health_banner.mousePressEvent = self._on_health_banner_clicked  # type: ignore[method-assign]
        right_layout.addWidget(self.health_banner)

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

    def _update_tray_pending_badge(self):
        """Reflect 'someone is waiting on your move' as a persistent tray badge,
        not just a one-off balloon — so the icon itself tells you at a glance."""
        if not self._tray_icon or not self._tray_icon.is_available:
            return
        my_name = self.config.player_name
        pending = [g.name for g in self.games if g.history and g.is_my_turn(my_name)]
        self._tray_icon.set_pending_turn(pending)

    def _load_games(self):
        """Load all game files from config directory."""
        from src.config import get_games_dir
        from src.saves import glob_saves, iter_save_dirs
        games_dir = get_games_dir()
        prev_name = self.current_game.name if self.current_game else None
        self.games = []
        try:
            save_dirs = iter_save_dirs(
                self.config.save_path,
                self.config.get("civ4_save_path", ""),
                self.config.get("mirror_saves", True),
            )
        except Exception:
            save_dirs = []
        for f in games_dir.glob("*.json"):
            # Skip remote sync / cache files (not full game documents)
            stem = f.stem
            if stem.endswith("_remote") or stem.endswith("_turns") or stem.endswith("_state"):
                continue
            if "_turns" in stem or "_state_from_server" in stem or "_turns_from_server" in stem:
                continue
            try:
                game = Game.load_from_file(f, self.config.master_password)
                local_names: list[str] = []
                for pattern in (
                    f"{game.name}_*.CivBeyondSwordSave",
                    f"*_{game.name}_*.CivBeyondSwordSave",
                ):
                    local_names.extend(
                        p.name for p in glob_saves(pattern, save_dirs, game.name)
                    )
                if game.repair_turn_state_from_saves(local_names):
                    game.save_to_file(games_dir, self.config.master_password)
                self.games.append(game)
            except Exception as e:
                logger.error(f"Failed to load game {f}: {e}")

        self._refresh_game_list()
        self._update_tray_pending_badge()
        # Restore selection + refresh right panel (otherwise banner stays stale after check)
        if prev_name:
            for i, g in enumerate(self.games):
                if g.name == prev_name:
                    self.game_list.blockSignals(True)
                    self.game_list.setCurrentRow(i)
                    self.game_list.blockSignals(False)
                    self.current_game = g
                    self._update_game_view()
                    return
        self.current_game = None
        if self.games:
            self.game_list.setCurrentRow(0)
        else:
            self._clear_game_view()

    def _refresh_game_list(self):
        """Update the game list widget."""
        self.game_list.clear()
        my_name = self.config.player_name
        for game in self.games:
            year_str = turn_to_year_str(game.current_turn, game.game_speed)
            if not game.history:
                text = (
                    f"   {game.name} [{t('turn')} {game.current_turn}, {year_str}]\n"
                    f"   {t('game_list_needs_sync')}"
                )
                item = QListWidgetItem(text)
                item.setForeground(QColor("#ef5350"))
            elif game.is_finished:
                text = (
                    f"   {game.name} [{t('turn')} {game.current_turn}, {year_str}]\n"
                    f"   {t('game_list_winner', player=game.winner)}"
                )
                item = QListWidgetItem(text)
                item.setForeground(QColor("#ffd54f"))
            elif game.is_my_turn(my_name):
                text = f">> {game.name} [{t('turn')} {game.current_turn}, {year_str}]\n   {t('your_turn')}"
                item = QListWidgetItem(text)
                item.setForeground(QColor("#66bb6a"))
            else:
                cp = game.current_player
                who = cp.name if cp else "?"
                text = f"   {game.name} [{t('turn')} {game.current_turn}, {year_str}]\n   {t('waiting')}: {who}"
                item = QListWidgetItem(text)
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

        # Empty history = never synced from FTP. Default index 0 looks like
        # "YOUR TURN" after import — that is a lie until Check fills history.
        if not game.history:
            self.status_banner.setText(t("banner_no_server_state"))
            self.status_banner.setObjectName("banner_waiting")
            self.btn_play_now.hide()
        elif game.is_finished:
            self.status_banner.setText(t("banner_winner", player=game.winner))
            self.status_banner.setObjectName("banner_winner")
            self.btn_play_now.hide()
        elif game.is_my_turn(my_name):
            self.status_banner.setText(t("your_turn_banner"))
            self.status_banner.setObjectName("banner_your_turn")
            self.btn_play_now.show()
            self.btn_play_now.setEnabled(True)
        else:
            cp = game.current_player
            who = cp.name if cp else "?"
            self.status_banner.setText(t("waiting_for", name=who))
            self.status_banner.setObjectName("banner_waiting")
            self.btn_play_now.hide()
        # Force style refresh
        self.status_banner.setStyleSheet(self.status_banner.styleSheet())
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

        # Players — chips with current highlight + wait time
        self.player_order.set_dark(self.config.get("dark_mode", True))
        self.player_order.set_overdue_days(
            self.config.get("reminder_auto_days", 2) or 2,
        )
        self.player_order.update_from_game(game, my_name)

        # Update filter combo with players from this game
        current_filter = self.history_filter_combo.currentData()
        self.history_filter_combo.blockSignals(True)
        self.history_filter_combo.clear()
        self.history_filter_combo.addItem(t("history_filter_all"), FILTER_ALL)
        self.history_filter_combo.addItem(t("history_filter_mine"), FILTER_MINE)
        my_game_name = game.get_game_player_name(my_name)
        for p in game.players:
            label = f"{p.name} {t('you_marker')}" if p.name == my_game_name else p.name
            self.history_filter_combo.addItem(label, p.name)
        if current_filter is not None and current_filter != "":
            idx = self.history_filter_combo.findData(current_filter)
            if idx >= 0:
                self.history_filter_combo.setCurrentIndex(idx)
        elif current_filter == FILTER_ALL:
            self.history_filter_combo.setCurrentIndex(0)
        self.history_filter_combo.blockSignals(False)

        # History (filtered)
        self._populate_history_list()
        try:
            self._refresh_health_from_games()
        except Exception:
            pass

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
        """Fill history list with turns, respecting the player filter.

        History stores who already uploaded. The save for the player whose
        turn it is NOW (they have not played yet) is the last uploaded file,
        from the previous player. Show that as a pending row so the filter
        for the current player still finds the save they need to load.
        """
        game = self.current_game
        if not game:
            return

        self.history_list.clear()
        filter_player = self.history_filter_combo.currentData() or ""

        if not game.history:
            item = QListWidgetItem(t("history_empty_hint"))
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor("#ef5350"))
            self.history_list.addItem(item)
            return

        my_name = self.config.player_name
        my_game_name = game.get_game_player_name(my_name)

        color_mode = game.history_color_mode or "all"
        default_palette = ["#66bb6a", "#42a5f5", "#ffa726", "#ab47bc", "#ef5350", "#26c6da", "#ec407a", "#8d6e63"]

        player_color_map = {}
        for i, p in enumerate(game.players):
            if p.name in game.player_colors:
                player_color_map[p.name] = game.player_colors[p.name]
            else:
                player_color_map[p.name] = default_palette[i % len(default_palette)]

        current = game.current_player
        incoming = game.incoming_save_filename()
        prev_for_me = game.get_previous_player(my_game_name)

        def _visible(player_name: str) -> bool:
            if not filter_player:
                return True
            if filter_player == FILTER_MINE:
                return player_name == my_game_name or (
                    prev_for_me is not None and player_name == prev_for_me.name
                )
            return player_name == filter_player

        show_pending = bool(
            current
            and incoming
            and (
                not filter_player
                or filter_player == current.name
                or (filter_player == FILTER_MINE and current.name == my_game_name)
            )
        )

        if show_pending:
            year_str = turn_to_year_str(game.current_turn, game.game_speed)
            last = game.history[-1]
            mine_tag = f"  {t('choose_save_can_download')}" if current.name == my_game_name else ""
            from_name, to_name = game.save_route(incoming)
            if from_name == "?" and last.player_name:
                from_name = last.player_name
            if to_name == "?":
                to_name = current.name
            text = (
                f"{t('history_pending_prefix')}  "
                f"{t('save_route', from_name=from_name, to_name=to_name)}  "
                f"{t('turn')} {game.current_turn} ({year_str})  "
                f"[{incoming}]{mine_tag}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, -1)
            item.setData(Qt.UserRole + 1, incoming)
            pending_color = player_color_map.get(current.name, "#66bb6a")
            item.setForeground(QColor(pending_color))
            self.history_list.addItem(item)

        for turn in reversed(game.history):
            if not _visible(turn.player_name):
                continue

            import datetime
            dt = datetime.datetime.fromtimestamp(turn.timestamp)
            year_str = turn_to_year_str(turn.turn_number, game.game_speed)
            mine_tag = ""
            if game.is_save_for_player(turn.filename, my_name):
                mine_tag = f"  {t('choose_save_can_download')}"
            from_name, to_name = game.save_route(turn.filename or "")
            if from_name == "?":
                from_name = turn.player_name
            text = (
                f"{dt.strftime('%d.%m %H:%M')}  "
                f"{t('save_route', from_name=from_name, to_name=to_name)}  "
                f"{t('turn')} {turn.turn_number} ({year_str})  [{turn.filename}]"
                f"{mine_tag}"
            )
            item = QListWidgetItem(text)
            idx = game.history.index(turn)
            item.setData(Qt.UserRole, idx)
            item.setData(Qt.UserRole + 1, turn.filename)

            if color_mode == "mine":
                if turn.player_name == my_game_name:
                    item.setForeground(QColor(player_color_map.get(my_game_name, "#66bb6a")))
                else:
                    item.setForeground(QColor("#9e9e9e"))
            else:
                color = player_color_map.get(turn.player_name, "#9e9e9e")
                item.setForeground(QColor(color))

            self.history_list.addItem(item)

        if show_pending and self.history_list.count() > 0:
            self.history_list.setCurrentRow(0)

    def _on_history_filter_changed(self, index: int):
        """Refresh history list when player filter changes."""
        self._populate_history_list()

    def _clear_game_view(self):
        """Clear the right panel when no game is selected (e.g. after delete)."""
        self.btn_play_now.hide()
        self.header_label.setText(t("select_game"))
        self.status_banner.setText("")
        self.status_banner.setObjectName("banner_waiting")
        self.player_order.clear()
        self.history_list.clear()
        self.history_filter_combo.clear()
        self.history_filter_combo.addItem(t("history_filter_all"), FILTER_ALL)
        self.history_filter_combo.addItem(t("history_filter_mine"), FILTER_MINE)

    def set_health_report(self, report: HealthReport):
        """Update the global PBEM health strip."""
        self._health_report = report
        level = report.worst_level
        self.health_banner.setText(report.summary())
        self.health_banner.setObjectName(f"health_{level}")
        self.health_banner.setToolTip(t("health_click_hint"))
        self.health_banner.style().unpolish(self.health_banner)
        self.health_banner.style().polish(self.health_banner)

    def _refresh_health_from_games(self):
        """Local-only health (no FTP) — empty history must not show All good."""
        from src.health_check import HealthReport, HealthIssue
        report = HealthReport()
        my_name = (self.config.player_name or "").strip()
        if not my_name:
            report.issues.append(HealthIssue(
                "error", "no_nick", t("health_no_nick"), t("health_no_nick_hint"),
            ))
        for game in self.games:
            if not game.history:
                report.issues.append(HealthIssue(
                    "error",
                    "not_synced",
                    t("health_not_synced", game=game.name),
                    t("health_not_synced_hint"),
                    game_name=game.name,
                ))
            elif my_name and game.get_player_index(game.get_game_player_name(my_name)) is None:
                report.issues.append(HealthIssue(
                    "error",
                    "not_in_game",
                    t("health_not_in_game", game=game.name),
                    t("health_not_in_game_hint", nick=my_name),
                    game_name=game.name,
                ))
        if not report.has_problems:
            report.issues.append(HealthIssue("ok", "all_ok", t("health_ok"), ""))
        self.set_health_report(report)

    def show_health_dialog(self):
        """Open detailed health check results."""
        if self._health_report is None:
            return
        HealthDialog(self._health_report, self).exec()

    def _on_health_banner_clicked(self, event):
        """Show health details when the strip is clicked."""
        from PySide6.QtGui import QMouseEvent
        if isinstance(event, QMouseEvent) and event.button() == Qt.LeftButton:
            self.show_health_dialog()

    def _selected_history_filename(self) -> tuple[Optional[int], str]:
        """Return (history_index, filename) for the selected history row."""
        selected = self.history_list.currentItem()
        if not selected or not self.current_game:
            return None, ""
        history_index = selected.data(Qt.UserRole)
        filename = selected.data(Qt.UserRole + 1) or ""
        if history_index == -1 and not filename:
            filename = self.current_game.incoming_save_filename() or ""
        elif isinstance(history_index, int) and history_index >= 0:
            if history_index < len(self.current_game.history) and not filename:
                filename = self.current_game.history[history_index].filename
        return history_index, filename

    def _on_download_selected_turn(self):
        """Download the selected history save. Confirm if it is not yours."""
        game = self.current_game
        if not game:
            return
        history_index, filename = self._selected_history_filename()
        if history_index is None:
            QMessageBox.information(self, t("info"), t("revert_select_hint"))
            return
        if not filename:
            QMessageBox.information(self, t("info"), t("history_download_no_file"))
            return
        my_name = self.config.player_name
        if not game.save_belongs_to_game(filename):
            QMessageBox.information(self, t("info"), t("history_download_no_file"))
            return
        if not game.is_save_for_player(filename, my_name):
            from_name, to_name = game.save_route(filename)
            reply = QMessageBox.warning(
                self, t("choose_save_title"),
                t("choose_save_not_yours_confirm", from_name=from_name, to_name=to_name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.download_file_requested.emit(filename)

    def _on_danger_zone(self):
        """Open buried destructive actions (delete game / wipe FTP)."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_to_delete"))
            return
        _idx, filename = self._selected_history_filename()
        if filename and not self.current_game.save_belongs_to_game(filename):
            filename = ""
        dialog = DangerZoneDialog(
            self.config,
            self.current_game,
            selected_remote_filename=filename or "",
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        action = dialog.chosen_action()
        if action == DangerZoneDialog.ACTION_DELETE_SELECTED_REMOTE:
            if not filename:
                QMessageBox.information(self, t("info"), t("danger_zone_no_selection"))
                return
            self.delete_remote_save_requested.emit(filename)
        elif action == DangerZoneDialog.ACTION_WIPE_SERVER:
            self.delete_all_remote_requested.emit()
        elif action == DangerZoneDialog.ACTION_DELETE_GAME:
            self.delete_game_requested.emit()

    def _on_play_now(self):
        """One-click: download (if needed) and launch Civ4."""
        if not self.current_game:
            return
        self.play_now_requested.emit()

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
        if history_index == -1:
            incoming = game.incoming_save_filename()
            if not incoming:
                QMessageBox.warning(self, t("error"), t("launch_no_file"))
                return
            filename = incoming
        else:
            if history_index >= len(game.history):
                return
            target_turn = game.history[history_index]
            if not target_turn.filename:
                QMessageBox.warning(self, t("error"), t("launch_no_file"))
                return
            filename = target_turn.filename

        # Check if the save file exists locally
        local_path = find_save_file(
            filename,
            self.config.save_path,
            self.config.get("civ4_save_path", ""),
            self.config.get("mirror_saves", True),
            prefer_civ4=True,
            game_name=game.name,
        )

        if not local_path:
            QMessageBox.warning(
                self, t("error"),
                t("launch_file_missing", filename=filename)
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
            self.status_label.setText(f"{t('civ4_launched')} ({filename})")
        else:
            key = msg_key if msg_key in ("civ4_not_found", "steam_not_found") else ""
            self.status_label.setText(t(key) if key else msg_key)

    def _on_new_game(self):
        """Create a new game dialog."""
        dialog = NewGameDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            game = dialog.get_game()
            if game:
                me = (self.config.player_name or "").strip()
                if me and game.get_player_index(me) is not None:
                    game.set_player_claim(me, self.config.install_id, me)
                from src.config import get_games_dir
                game.save_to_file(get_games_dir(), self.config.master_password)
                self.games.append(game)
                self._refresh_game_list()

    def _build_export_data(self, game) -> dict:
        """Shared JSON schema for both .civ4pbem file export and the
        copy-paste invite code — same content, two delivery mechanisms."""
        return {
            "civ4pbem_version": "1.2",
            "name": game.name,
            "players": [p.to_dict() for p in game.players],
            "transport_config": game.transport_config,
            "game_speed": game.game_speed,
            "smtp": self.config.smtp_config,
            # Include turn pointer + history so a second PC is not blank
            # before FTP sync finishes (sync still overrides from saves).
            "current_turn": game.current_turn,
            "current_player_index": game.current_player_index,
            "history": [t.to_dict() for t in game.history],
            "save_seq": int(game.save_seq or 0),
            "state_revision": int(game.state_revision or 0),
            "player_colors": game.player_colors,
            "player_claims": game.player_claims or {},
            "winner": (game.winner or "").strip(),
        }

    def _on_export_game(self):
        """Export current game config to a .civ4pbem file for sharing with other players."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_to_export"))
            return

        game = self.current_game
        export_data = self._build_export_data(game)

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

    def _on_export_invite_code(self):
        """Same data as .civ4pbem export, but as one paste-able text blob —
        for sending over Discord/Messenger instead of attaching a file.

        Note: exactly like the .civ4pbem file, this contains the FTP
        password in plain (base64 is NOT encryption, just encoding) — treat
        it the same way you'd treat the file: don't post it publicly.
        """
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_to_export"))
            return

        import json, base64
        game = self.current_game
        export_data = self._build_export_data(game)
        raw = json.dumps(export_data, ensure_ascii=False, separators=(",", ":"))
        code = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")

        clipboard = QApplication.clipboard()
        clipboard.setText(code)
        self.status_label.setText(t("invite_code_copied", name=game.name))
        QMessageBox.information(
            self, t("copy_invite_code"),
            t("invite_code_copied_body", name=game.name, chars=len(code)),
        )

    def _on_import_invite_code(self):
        """Paste an invite code produced by _on_export_invite_code and import it."""
        code, ok = QInputDialog.getMultiLineText(
            self, t("paste_invite_code"), t("paste_invite_code_prompt"), "",
        )
        if not ok or not code.strip():
            return

        import json, base64
        try:
            raw = base64.urlsafe_b64decode(code.strip().encode("ascii"))
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            QMessageBox.warning(self, t("error"), t("invite_code_invalid", error=str(e)))
            return

        self._import_game_from_data(data)

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
        except Exception as e:
            QMessageBox.warning(self, t("error"), t("import_error", error=str(e)))
            return

        self._import_game_from_data(data)

    def _import_game_from_data(self, data: dict):
        """Shared import body for both file-based (.civ4pbem) and invite-code
        imports — one code path, two ways to hand the data over."""
        try:
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
            from src.models.game import Turn
            history = [
                Turn.from_dict(t) for t in data.get("history", [])
                if isinstance(t, dict)
            ]

            game = Game(
                name=name,
                players=players,
                transport_config=transport_config,
                game_speed=game_speed,
                current_turn=int(data.get("current_turn", 0) or 0),
                current_player_index=int(data.get("current_player_index", 0) or 0),
                history=history,
                save_seq=int(data.get("save_seq", 0) or 0),
                state_revision=int(data.get("state_revision", 0) or 0),
                player_colors=data.get("player_colors") or {},
                player_claims=data.get("player_claims") or {},
                winner=(data.get("winner") or "").strip(),
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
            player_names = [p.name for p in players]
            # Try to enrich list with leader/civ from a local save of this game
            save_labels = list(player_names)
            info = None
            try:
                from src.civ4_save_info import parse_civ4_save, find_latest_game_save
                from src.saves import iter_save_dirs
                dirs = list(
                    iter_save_dirs(
                        self.config.save_path,
                        self.config.get("civ4_save_path", ""),
                        self.config.get("mirror_saves", True),
                    )
                )
                latest = find_latest_game_save(name, dirs)
                info = parse_civ4_save(latest) if latest else None
                if info and info.players:
                    # Show "Nick  |  Leader — Civ" when counts align by order
                    for i, pn in enumerate(player_names):
                        if i < len(info.players):
                            slot = info.players[i]
                            save_labels[i] = f"{pn}  |  {slot.label}"
            except Exception:
                info = None

            my_local_name = self.config.player_name

            # If local name matches a player exactly, pre-select it
            default_idx = 0
            for i, pn in enumerate(player_names):
                if pn == my_local_name:
                    default_idx = i
                    break

            from PySide6.QtWidgets import QInputDialog
            chosen_label, ok = QInputDialog.getItem(
                self,
                t("import_choose_player_title"),
                t(
                    "import_choose_player_body",
                    game=name,
                    nick=my_local_name,
                ),
                save_labels,
                default_idx,
                False,  # not editable
            )
            if not ok:
                return
            # Map label back to player name
            chosen_name = chosen_label
            if chosen_label in save_labels:
                chosen_name = player_names[save_labels.index(chosen_label)]
            elif "  |  " in chosen_label:
                chosen_name = chosen_label.split("  |  ", 1)[0].strip()

            from src.gui.dialogs.edit_game_dialog import confirm_player_claim
            if not confirm_player_claim(
                self, game, chosen_name, self.config.install_id,
            ):
                return

            # Fill empty civ4_leader fields from save slots (same order)
            try:
                if info and info.players:
                    for i, p in enumerate(players):
                        if p.civ4_leader:
                            continue
                        if i < len(info.players) and info.players[i].leader_name:
                            p.civ4_leader = info.players[i].leader_name
            except Exception:
                pass

            # Set alias: local nick -> game player name
            if chosen_name != my_local_name:
                game.local_player_alias = chosen_name
            else:
                game.local_player_alias = ""  # No alias needed, names match
            game.set_player_claim(
                chosen_name, self.config.install_id, my_local_name,
            )

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
            game.save_to_file(get_games_dir(), self.config.master_password)
            self.games.append(game)
            self._refresh_game_list()
            # Select imported game and ask controller to sync turn from server
            for i, g in enumerate(self.games):
                if g.name == game.name:
                    self.game_list.setCurrentRow(i)
                    self.current_game = g
                    self._update_game_view()
                    break
            self.status_label.setText(t("imported", name=f"{name} ({chosen_name})"))
            self.game_imported.emit(game)

        except Exception as e:
            QMessageBox.warning(self, t("error"), t("import_error", error=str(e)))

    def _confirm_admin_password(self, game) -> bool:
        """Return True if allowed (no admin_password set on the game = always OK).

        Mirrors main.py's _ask_admin_password so both use the exact same
        game.admin_password gate — one shared "admin mode" concept instead
        of a second app/UI.
        """
        if not (game.admin_password or "").strip():
            return True
        from src.gui.app_controller import AppController
        pwd, ok = QInputDialog.getText(
            self, t("admin_password_prompt"), t("admin_password_prompt"),
            QLineEdit.Password,
        )
        if not ok:
            return False
        if not AppController.verify_admin_password(game, pwd):
            QMessageBox.warning(self, t("error"), t("wrong_password"))
            return False
        return True

    def _on_game_transport(self):
        """Open transport configuration dialog for the current game."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_for_transport"))
            return
        # Transport (host/user/password) is shared infrastructure for every
        # player in the game — editing it is an admin action, not a routine
        # per-player one.
        if not self._confirm_admin_password(self.current_game):
            return

        dialog = GameTransportDialog(self.config, self.current_game, self.games, self)
        if dialog.exec() == QDialog.Accepted:
            tc = dialog.get_transport_config()
            self.current_game.transport_config = tc
            from src.config import get_games_dir
            self.current_game.save_to_file(get_games_dir(), self.config.master_password)
            self.status_label.setText(t("transport_saved", name=self.current_game.name))
            self.push_shared_config_requested.emit(self.current_game)

    def _on_edit_game(self):
        """Open game edit dialog for changing player emails, speed, alias."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game_to_export"))
            return

        dialog = EditGameDialog(self.config, self.current_game, self)
        before = self.current_game.roster_event_snapshot()
        if dialog.exec() == QDialog.Accepted:
            from src.config import get_games_dir
            self.current_game.save_to_file(get_games_dir(), self.config.master_password)
            events = self.current_game.roster_events_since(*before)
            if events:
                self.roster_events_requested.emit(self.current_game, events)
            self._update_game_view()
            self._refresh_game_list()
            self.status_label.setText(t("game_saved", name=self.current_game.name))
            self.push_shared_config_requested.emit(self.current_game)

    def _on_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
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
        self.btn_copy_invite.setText(t("copy_invite_code"))
        self.btn_copy_invite.setToolTip(t("copy_invite_code_hint"))
        self.btn_paste_invite.setText(t("paste_invite_code"))
        self.btn_paste_invite.setToolTip(t("paste_invite_code_hint"))
        self.btn_game_transport.setText(t("game_transport"))
        self.btn_edit_game.setText(t("edit_game"))
        self.btn_stats.setText(t("statistics"))
        self.btn_settings.setText(t("settings"))
        self.btn_danger_zone.setText(t("danger_zone_open"))
        self.btn_danger_zone.setToolTip(t("danger_zone_hint"))

        # Action buttons
        self.btn_play_now.setText(t("play_now"))
        self.btn_download.setText(t("download_save"))
        self.btn_upload.setText(t("upload_save"))
        self.btn_open_folder.setText(t("open_folder"))
        self.btn_check_now.setText(t("check_now"))
        self.btn_check_now.setToolTip(t("check_now_hint"))
        self.btn_launch_civ4.setText(t("launch_civ4"))
        self.btn_remind.setText(t("remind_player"))
        self.player_order.retranslate()
        if self.current_game:
            self.player_order.update_from_game(
                self.current_game, self.config.player_name,
            )

        # History panel
        self.history_group.setTitle(t("history_group"))
        self.lbl_filter.setText(t("history_filter"))
        self.btn_revert.setText(t("revert_selected"))
        self.btn_download_turn.setText(t("history_download_this"))
        self.btn_launch_turn.setText(t("launch_this_turn"))
        self.btn_launch_turn.setVisible(self.config.get("direct_load_global", False))
        self.btn_remind.setText(t("remind_player"))

        # Filter combo -- refresh "All players" item text
        self.history_filter_combo.blockSignals(True)
        if self.history_filter_combo.count() > 0:
            self.history_filter_combo.setItemText(0, t("history_filter_all"))
        if self.history_filter_combo.count() > 1:
            if self.history_filter_combo.itemData(1) == FILTER_MINE:
                self.history_filter_combo.setItemText(1, t("history_filter_mine"))
        self.history_filter_combo.blockSignals(False)

        # Status bar
        self.status_label.setText(t("ready"))
        if self._health_report:
            self.health_banner.setText(self._health_report.summary())

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
            QMessageBox.information(self, t("info"), t("revert_select_hint"))
            return

        history_index = selected.data(Qt.UserRole)
        if history_index is None:
            return
        if history_index < 0:
            QMessageBox.information(self, t("info"), t("history_pending_no_revert"))
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
        """Ask controller to nudge the current player."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("select_game"))
            return
        cp = self.current_game.current_player
        if not cp:
            return
        self.status_label.setText(f"{t('remind_player')}: {cp.name}...")
        self.remind_requested.emit(self.current_game)

    def set_status(self, text: str, *, clear_after_ms: int = 0):
        """Update status bar; optionally return to Ready after a delay."""
        self.status_label.setText(text)
        if clear_after_ms > 0:
            QTimer.singleShot(
                clear_after_ms,
                lambda: self._status_back_to_ready_if(text),
            )

    def _status_back_to_ready_if(self, expected: str):
        """Clear status only if it still shows the temporary message."""
        if self.status_label.text() == expected:
            self.status_label.setText(t("ready"))

    def _on_statistics(self):
        """Show game statistics dialog."""
        if not self.current_game:
            QMessageBox.information(self, t("info"), t("stats_no_game"))
            return
        dialog = GameStatsDialog(self.config, self.current_game, self)
        dialog.exec()

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
        from PySide6.QtWidgets import QDialog as _QDialog, QVBoxLayout as _QVBoxLayout
        from PySide6.QtWidgets import QLabel as _QLabel, QHBoxLayout as _QHBoxLayout
        from PySide6.QtWidgets import QCheckBox as _QCheckBox, QPushButton as _QPushButton
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

        if dlg.exec() != QDialog.Accepted or chosen_edition[0] is None:
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
            latest = latest_game_save(
                self.current_game,
                iter_save_dirs(
                    self.config.save_path,
                    self.config.get("civ4_save_path", ""),
                    self.config.get("mirror_saves", True),
                ),
            )
            if latest:
                preferred = find_save_file(
                    latest.name,
                    self.config.save_path,
                    self.config.get("civ4_save_path", ""),
                    self.config.get("mirror_saves", True),
                    prefer_civ4=True,
                    game_name=self.current_game.name,
                )
                save_file = str(preferred or latest)

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
        from PySide6.QtCore import QEvent
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
