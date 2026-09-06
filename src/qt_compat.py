"""
Qt compatibility shim: PySide6 with PyQt5-style API names.

This module re-exports PySide6 classes with compatibility aliases so the
rest of the codebase can use familiar names (Signal instead of pyqtSignal, etc.)
while running on PySide6 (LGPL license — free to distribute).

Usage in other modules:
    from src.qt_compat import Signal, Slot, Qt, QTimer, ...

Or for widgets:
    from src.qt_compat import (
        QMainWindow, QWidget, QPushButton, QLabel, ...
    )
"""

# --- Core ---
from PySide6.QtCore import (
    Qt,
    QObject,
    QTimer,
    QEvent,
    Signal,
    Slot,
)

# Compatibility aliases for code that uses PyQt5 names
pyqtSignal = Signal
pyqtSlot = Slot

# --- GUI ---
from PySide6.QtGui import (
    QIcon,
    QColor,
    QAction,
)

# --- Widgets ---
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QDialogButtonBox,
    QFrame,
    QMenu,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSystemTrayIcon,
)
