"""Player-order chips: colored pills, current player highlight + brief pulse."""
from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect,
)

from src.i18n import t

DEFAULT_PALETTE = [
    "#66bb6a", "#42a5f5", "#ffa726", "#ab47bc",
    "#ef5350", "#26c6da", "#ec407a", "#8d6e63",
]
_OVERDUE_DAYS_DEFAULT = 2


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return 102, 187, 106
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(hex_color: str, toward: str, amount: float) -> str:
    """Blend hex_color toward another color (0=keep, 1=toward)."""
    r1, g1, b1 = _hex_to_rgb(hex_color)
    r2, g2, b2 = _hex_to_rgb(toward)
    r = int(r1 + (r2 - r1) * amount)
    g = int(g1 + (g2 - g1) * amount)
    b = int(b1 + (b2 - b1) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def _format_chip_elapsed(seconds: float) -> str:
    minutes = int(seconds // 60)
    hours = int(seconds // 3600)
    days = int(seconds // 86400)
    if days > 0:
        return f"{days}d {hours % 24}h"
    if hours > 0:
        return f"{hours}h {minutes % 60}m"
    if minutes > 0:
        return f"{minutes}m"
    return "<1m"


class PlayerChip(QLabel):
    """Single player pill in the turn order."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("playerChip")
        self._base_color = "#66bb6a"
        self._current = False
        self._mine = False
        self._overdue = False
        self._inactive = False
        self._winner = False
        self._pulse_bright = False
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)
        self._anim: Optional[QPropertyAnimation] = None

    def configure(
        self,
        name: str,
        color: str,
        *,
        is_current: bool,
        is_mine: bool,
        elapsed: Optional[float] = None,
        overdue_days: int = _OVERDUE_DAYS_DEFAULT,
        dark: bool = True,
        status: str = "active",
        is_winner: bool = False,
    ):
        self._base_color = color or "#66bb6a"
        self._current = is_current and status == "active" and not is_winner
        self._mine = is_mine
        self._overdue = False
        self._inactive = status in ("defeated", "resigned") and not is_winner
        self._winner = is_winner

        lines = [name]
        if is_mine:
            lines[0] = f"{name} {t('you_marker')}"
        if is_winner:
            lines.append(t("chip_winner"))
        elif status == "defeated":
            lines.append(t("chip_defeated"))
        elif status == "resigned":
            lines.append(t("chip_resigned"))
        elif self._current and is_mine:
            lines.append(t("chip_play"))
        if self._current and elapsed is not None:
            self._overdue = elapsed >= overdue_days * 86400
            lines.append(_format_chip_elapsed(elapsed))

        self.setText("\n".join(lines))
        font = QFont(self.font())
        font.setBold(self._current or is_winner)
        font.setPointSize(10 if (self._current or is_winner) else 9)
        font.setStrikeOut(self._inactive)
        self.setFont(font)
        self._apply_style(dark=dark)
        self.setToolTip(self._tooltip(name, self._current, elapsed, status, is_winner))

    def _tooltip(self, name: str, is_current: bool, elapsed: Optional[float],
                 status: str = "active", is_winner: bool = False) -> str:
        if is_winner:
            return t("chip_winner_tooltip", name=name)
        if status == "defeated":
            return t("chip_defeated_tooltip", name=name)
        if status == "resigned":
            return t("chip_resigned_tooltip", name=name)
        if not is_current:
            return name
        if elapsed is None:
            return t("chip_waiting", name=name)
        return t("chip_waiting_time", name=name, time=_format_chip_elapsed(elapsed))

    def _apply_style(self, dark: bool = True):
        color = self._base_color
        if self._overdue:
            color = _mix(color, "#ef5350", 0.55)

        if self._winner:
            bg = "#b8860b" if dark else "#ffc107"
            border = "#ffd54f"
            border_w = 3
            text = "#ffffff" if dark else "#111111"
            pad = "8px 14px"
        elif self._inactive:
            bg = _mix("#888888", "#1e1e1e" if dark else "#f5f5f5", 0.55)
            border = "#666666"
            border_w = 1
            text = "#9e9e9e" if dark else "#757575"
            pad = "6px 12px"
        elif self._current:
            bg = _mix(color, "#ffffff" if dark else "#000000", 0.12)
            border = color if not self._pulse_bright else _mix(color, "#ffffff", 0.55)
            border_w = 3 if not self._pulse_bright else 4
            text = "#ffffff" if dark else "#111111"
            pad = "8px 14px"
        else:
            bg = _mix(color, "#1e1e1e" if dark else "#f5f5f5", 0.72)
            border = _mix(color, "#555555" if dark else "#bdbdbd", 0.4)
            border_w = 1
            text = "#e0e0e0" if dark else "#212121"
            pad = "6px 12px"

        self.setStyleSheet(
            f"QLabel#playerChip {{"
            f"  background-color: {bg};"
            f"  color: {text};"
            f"  border: {border_w}px solid {border};"
            f"  border-radius: 14px;"
            f"  padding: {pad};"
            f"  min-width: 72px;"
            f"}}"
        )

    def pulse(self, dark: bool = True):
        """Brief highlight pulse when this player becomes current."""
        if self._anim:
            self._anim.stop()
        self._pulse_bright = True
        self._apply_style(dark=dark)

        anim = QPropertyAnimation(self._opacity, b"opacity", self)
        anim.setDuration(900)
        anim.setStartValue(0.55)
        anim.setKeyValueAt(0.35, 1.0)
        anim.setKeyValueAt(0.7, 0.7)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _end():
            self._pulse_bright = False
            self._apply_style(dark=dark)

        anim.finished.connect(_end)
        self._anim = anim
        anim.start()


class PlayerOrderWidget(QWidget):
    """Horizontal turn-order strip with colored player chips."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playerOrder")
        self._dark = True
        self._last_current: Optional[str] = None
        self._overdue_days = _OVERDUE_DAYS_DEFAULT

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.title = QLabel(t("player_order"))
        self.title.setObjectName("playerOrderTitle")
        self.title.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        root.addWidget(self.title)

        self.row = QWidget()
        self.row_layout = QHBoxLayout(self.row)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.row_layout.setSpacing(6)
        self.row_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        root.addWidget(self.row)

        self._chips: list[PlayerChip] = []
        self._arrows: list[QLabel] = []

    def set_dark(self, dark: bool):
        self._dark = dark

    def set_overdue_days(self, days: int):
        self._overdue_days = max(1, int(days or _OVERDUE_DAYS_DEFAULT))

    def clear(self):
        self._last_current = None
        self._rebuild([], current_name=None, my_name="", elapsed=None, colors={})

    def update_from_game(self, game, my_local_name: str, *, dark: bool | None = None):
        if dark is not None:
            self._dark = dark
        if not game or not game.players:
            self.clear()
            return

        my_name = game.get_game_player_name(my_local_name)
        # No history ⇒ not synced — do not highlight index-0 as "PLAY"
        current = None
        if game.history and game.current_player and not game.is_finished:
            current = game.current_player.name
        colors = {}
        for i, p in enumerate(game.players):
            colors[p.name] = game.player_colors.get(
                p.name, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)],
            )
        statuses = {p.name: (p.status or "active") for p in game.players}
        winner = (game.winner or "").strip()

        elapsed = None
        if game.history:
            elapsed = time.time() - game.history[-1].timestamp

        pulse_name = None
        if current and current != self._last_current and self._last_current is not None:
            pulse_name = current

        self._rebuild(
            [p.name for p in game.players],
            current_name=current,
            my_name=my_name,
            elapsed=elapsed,
            colors=colors,
            pulse_name=pulse_name,
            statuses=statuses,
            winner=winner,
        )
        self._last_current = current

    def retranslate(self):
        self.title.setText(t("player_order"))

    def _rebuild(
        self,
        names: list[str],
        *,
        current_name: Optional[str],
        my_name: str,
        elapsed: Optional[float],
        colors: dict,
        pulse_name: Optional[str] = None,
        statuses: Optional[dict] = None,
        winner: str = "",
    ):
        while self.row_layout.count():
            item = self.row_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._chips.clear()
        self._arrows.clear()

        for i, name in enumerate(names):
            if i > 0:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #888; font-size: 14pt; padding: 0 2px;")
                arrow.setAlignment(Qt.AlignCenter)
                self.row_layout.addWidget(arrow)
                self._arrows.append(arrow)

            chip = PlayerChip(self.row)
            is_current = name == current_name
            chip.configure(
                name,
                colors.get(name, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]),
                is_current=is_current,
                is_mine=(name == my_name),
                elapsed=elapsed if is_current else None,
                overdue_days=self._overdue_days,
                dark=self._dark,
                status=(statuses or {}).get(name, "active"),
                is_winner=bool(winner) and name == winner,
            )
            chip.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self.row_layout.addWidget(chip)
            self._chips.append(chip)

            if pulse_name and name == pulse_name:
                QTimer.singleShot(30, lambda c=chip: c.pulse(dark=self._dark))

        self.row_layout.addStretch(1)
        self.title.setText(t("player_order"))
