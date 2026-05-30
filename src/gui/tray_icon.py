"""
System tray icon with balloon notifications.
Allows the app to run minimized in the system tray and notify the user
when it's their turn.
"""
import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject

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

    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    check_now_requested = pyqtSignal()

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

        self._tray.setToolTip("Civ4 PBEM Manager")

        # Context menu
        menu = QMenu()

        action_show = QAction("Pokaz okno", menu)
        action_show.triggered.connect(self.show_window_requested.emit)
        menu.addAction(action_show)

        action_check = QAction("Sprawdz teraz", menu)
        action_check.triggered.connect(self.check_now_requested.emit)
        menu.addAction(action_check)

        menu.addSeparator()

        action_quit = QAction("Zamknij", menu)
        action_quit.triggered.connect(self.quit_requested.emit)
        menu.addAction(action_quit)

        self._tray.setContextMenu(menu)

        # Double-click on tray icon shows window
        self._tray.activated.connect(self._on_activated)

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
            "Civ4 PBEM - Twoja kolej!",
            f"Gra: {game_name}\nTura: {turn_number}\n\nKliknij aby otworzyc.",
            QSystemTrayIcon.Information,
            10000  # Show for 10 seconds
        )
        logger.info(f"Tray notification: your turn in '{game_name}' (turn {turn_number})")

    def notify_new_save_detected(self, filename: str):
        """Show a balloon notification that a new save was detected locally."""
        if not self._tray:
            return
        self._tray.showMessage(
            "Civ4 PBEM - Nowy save wykryty!",
            f"Plik: {filename}\n\nKliknij aby wyslac.",
            QSystemTrayIcon.Information,
            8000
        )

    def notify_status(self, title: str, message: str):
        """Show a generic balloon notification."""
        if not self._tray:
            return
        self._tray.showMessage(title, message, QSystemTrayIcon.Information, 5000)
