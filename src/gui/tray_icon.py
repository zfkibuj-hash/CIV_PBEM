"""
System tray icon with balloon notifications.
Allows the app to run minimized in the system tray and notify the user
when it's their turn.
"""
import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen

from src.i18n import t

logger = logging.getLogger(__name__)


def _get_icon_path() -> Path:
    """Get path to icon.ico, works both in dev and frozen .exe."""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent.parent
    return base / "icon.ico"


class TrayIcon(QObject):
    """System tray icon with context menu and balloon notifications."""

    show_window_requested = Signal()
    quit_requested = Signal()
    check_now_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray: Optional[QSystemTrayIcon] = None
        self._init_tray()

    def _init_tray(self):
        """Initialize the system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this platform")
            return

        self._tray = QSystemTrayIcon(self.parent())

        # Load icon - try multiple paths
        icon_path = _get_icon_path()
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Fallback: use application-level icon
            app = QApplication.instance()
            icon = app.windowIcon() if app else QIcon()

        if icon.isNull():
            logger.warning(f"Tray icon is null, path tried: {icon_path}")
        else:
            self._tray.setIcon(icon)

        self._icon_normal = icon
        self._icon_badge = self._make_badge_icon(icon)
        self._pending_games: list[str] = []

        self._tray.setToolTip("Civ4 PBEM Manager")

        # Context menu
        menu = QMenu()

        action_show = QAction(t("tray_show"), menu)
        action_show.triggered.connect(self.show_window_requested.emit)
        menu.addAction(action_show)

        action_check = QAction(t("tray_check"), menu)
        action_check.triggered.connect(self.check_now_requested.emit)
        menu.addAction(action_check)

        menu.addSeparator()

        action_quit = QAction(t("tray_quit"), menu)
        action_quit.triggered.connect(self.quit_requested.emit)
        menu.addAction(action_quit)

        self._tray.setContextMenu(menu)

        # Double-click on tray icon shows window
        self._tray.activated.connect(self._on_activated)

    def _make_badge_icon(self, base_icon: QIcon) -> QIcon:
        """Draw a small red dot over the base icon — no extra asset files needed."""
        if base_icon.isNull():
            return base_icon
        size = 32
        pixmap = base_icon.pixmap(size, size)
        if pixmap.isNull():
            return base_icon
        badge = QPixmap(pixmap)
        painter = QPainter(badge)
        painter.setRenderHint(QPainter.Antialiasing)
        r = max(10, size // 3)
        x = badge.width() - r - 1
        y = 1
        painter.setBrush(QColor("#e53935"))
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawEllipse(x, y, r, r)
        painter.end()
        return QIcon(badge)

    def set_pending_turn(self, games: list[str]):
        """Persistently flag (icon + tooltip) that it's your turn in `games`.
        Call this any time game state refreshes — not just on the moment a
        turn arrives — so the tray icon always reflects current reality."""
        if not self._tray:
            return
        self._pending_games = list(games or [])
        if self._pending_games:
            self._tray.setIcon(self._icon_badge)
            if len(self._pending_games) == 1:
                tooltip = t("tray_tooltip_pending_one", game=self._pending_games[0])
            else:
                tooltip = t("tray_tooltip_pending_many", n=len(self._pending_games))
        else:
            self._tray.setIcon(self._icon_normal)
            tooltip = "Civ4 PBEM Manager"
        self._tray.setToolTip(tooltip)

    def _on_activated(self, reason):
        """Handle tray icon activation (double-click)."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()

    def show(self):
        """Show the tray icon."""
        if self._tray:
            self._tray.show()

    def hide(self):
        """Hide the tray icon."""
        if self._tray:
            self._tray.hide()

    @property
    def is_available(self) -> bool:
        return self._tray is not None

    def notify_your_turn(self, game_name: str, turn_number: int):
        """Show a balloon notification that it's the user's turn."""
        if not self._tray:
            return
        self._tray.showMessage(
            t("tray_your_turn_title"),
            t("tray_your_turn_body", game=game_name, turn=turn_number),
            QSystemTrayIcon.Information,
            10000  # Show for 10 seconds
        )
        logger.info(f"Tray notification: your turn in '{game_name}' (turn {turn_number})")

    def notify_new_save_detected(self, filename: str):
        """Show a balloon notification that a new save was detected locally."""
        if not self._tray:
            return
        self._tray.showMessage(
            t("tray_new_save_title"),
            t("tray_new_save_body", filename=filename),
            QSystemTrayIcon.Information,
            8000
        )

    def notify_status(self, title: str, message: str):
        """Show a generic balloon notification."""
        if not self._tray:
            return
        self._tray.showMessage(title, message, QSystemTrayIcon.Information, 5000)

    def notify_health_problem(self, message: str):
        """Alert user when PBEM health check finds a problem."""
        if not self._tray:
            return
        self._tray.showMessage(
            t("health_tray_title"),
            message,
            QSystemTrayIcon.Warning,
            12000,
        )
