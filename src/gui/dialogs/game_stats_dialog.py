"""
GameStatsDialog — dialog showing comprehensive game statistics.
"""
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QGroupBox, QDialogButtonBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

from src.config import AppConfig
from src.models.game import Game
from src.models.statistics import calculate_game_stats
from src.models.turn_calendar import turn_to_year_str
from src.i18n import t
from src.gui.styles import get_style_for_theme

RegenerateFn = Callable[[Game], tuple[bool, str, int]]


class GameStatsDialog(QDialog):
    """Dialog showing comprehensive game statistics."""

    def __init__(
        self,
        config: AppConfig,
        game: Game,
        parent=None,
        regenerate: Optional[RegenerateFn] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.game = game
        self._regenerate = regenerate
        self.setWindowTitle(t("stats_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(500, 450)
        self.resize(560, 520)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()
        self._refresh_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        overview_group = QGroupBox(t("stats_title", name=self.game.name))
        overview_form = QFormLayout(overview_group)
        self._overview_labels: dict[str, QLabel] = {}
        for key in (
            "stats_game_started",
            "stats_last_activity",
            "stats_current_round",
            "stats_total_turns",
            "stats_total_time",
            "stats_avg_turn_time",
            "stats_fastest_turn",
            "stats_slowest_turn",
        ):
            label = QLabel("-")
            self._overview_labels[key] = label
            overview_form.addRow(t(key), label)
        layout.addWidget(overview_group)

        player_group = QGroupBox(t("stats_per_player"))
        player_layout = QVBoxLayout(player_group)
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            t("stats_player_name"),
            t("stats_player_turns"),
            t("stats_player_avg_time"),
            t("stats_player_total_time"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        player_layout.addWidget(self._table)
        layout.addWidget(player_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        if self._regenerate:
            regen = buttons.addButton(
                t("stats_regenerate"), QDialogButtonBox.ActionRole,
            )
            regen.setToolTip(t("stats_regenerate_hint"))
            regen.clicked.connect(self._on_regenerate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_stats(self):
        stats = calculate_game_stats(self.game)
        round_text = (
            f"{stats.current_round} "
            f"({turn_to_year_str(self.game.calendar_turn(stats.current_round), self.game.game_speed)})"
        )
        values = {
            "stats_game_started": stats.game_started_formatted,
            "stats_last_activity": stats.last_activity_formatted,
            "stats_current_round": round_text,
            "stats_total_turns": str(stats.total_turns),
            "stats_total_time": stats.total_time_formatted,
            "stats_avg_turn_time": stats.avg_turn_time_formatted,
            "stats_fastest_turn": stats.fastest_turn_formatted,
            "stats_slowest_turn": stats.slowest_turn_formatted,
        }
        for key, text in values.items():
            self._overview_labels[key].setText(text)

        table = self._table
        table.setRowCount(len(stats.player_stats))
        for row, ps in enumerate(stats.player_stats):
            table.setItem(row, 0, QTableWidgetItem(ps.name))
            table.setItem(row, 1, QTableWidgetItem(str(ps.total_turns)))
            table.setItem(row, 2, QTableWidgetItem(ps.avg_turn_time_formatted))
            table.setItem(row, 3, QTableWidgetItem(ps.total_time_formatted))

    def _on_regenerate(self):
        if not self._regenerate:
            return
        ok, msg, _count = self._regenerate(self.game)
        self._refresh_stats()
        box = QMessageBox.information if ok else QMessageBox.warning
        box(self, t("statistics"), msg)
