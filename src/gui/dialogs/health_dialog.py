"""Dialog: detailed PBEM health check results."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox,
)
from PySide6.QtCore import Qt

from src.health_check import HealthReport
from src.i18n import t


class HealthDialog(QDialog):
    """Show all health issues in plain language."""

    def __init__(self, report: HealthReport, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("health_dialog_title"))
        self.setMinimumSize(520, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        summary = QLabel(report.summary())
        summary.setWordWrap(True)
        summary.setObjectName(f"health_{report.worst_level}")
        layout.addWidget(summary)

        details = QTextEdit()
        details.setReadOnly(True)
        lines = report.lines()
        if lines:
            details.setPlainText("\n\n".join(lines))
        else:
            details.setPlainText(t("health_ok_detail"))
        layout.addWidget(details, 1)

        hint = QLabel(t("health_dialog_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #9e9e9e; font-size: 9pt;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        close_btn = buttons.button(QDialogButtonBox.Close)
        if close_btn:
            close_btn.setText(t("close"))
        layout.addWidget(buttons)
