"""
GameStatsDialog — dialog showing comprehensive game statistics.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QGroupBox, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt5.QtCore import Qt

from src.config import AppConfig
from src.models.game import Game
from src.models.statistics import calculate_game_stats
from src.models.turn_calendar import turn_to_year_str
from src.i18n import t
from src.gui.styles import get_style_for_theme


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
