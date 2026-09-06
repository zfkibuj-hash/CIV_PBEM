"""Dialog: pick a detected Civ4 save folder."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.i18n import t
from src.launcher import (
    canonical_pbem_save_dir,
    civ4_load_game_dir,
    count_saves_in_folder,
    list_civ4_save_candidates,
    resolve_save_layout,
    save_path_from_civ4_settings,
)


class ChooseSavePathDialog(QDialog):
    """List detected save folders; user picks one with 'Use this'."""

    def __init__(
        self,
        candidates: list[tuple[int, Path]],
        extra_exes: Optional[list[str]] = None,
        *,
        current: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._candidates = candidates
        self._exes = extra_exes or []
        self._current = current or ""
        self._selected_path = ""
        self._selected_mirror = ""

        self.setWindowTitle(t("choose_save_path_title"))
        self.setMinimumSize(560, 380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        hint = QLabel(t("choose_save_path_hint"))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_use_this)
        layout.addWidget(self.list_widget, 1)

        self.check_saves = QCheckBox(t("choose_save_path_check_saves"))
        self.check_saves.setChecked(True)
        self.check_saves.toggled.connect(self._refresh_list)
        layout.addWidget(self.check_saves)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.btn_use = QPushButton(t("choose_save_path_use"))
        self.btn_use.setObjectName("btn_download")
        self.btn_use.setMinimumHeight(36)
        self.btn_use.clicked.connect(self._on_use_this)
        buttons.addWidget(self.btn_use)
        btn_cancel = QPushButton(t("cancel"))
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

        self._refresh_list()
        self._select_current()

    @property
    def selected_path(self) -> str:
        return self._selected_path

    @property
    def selected_mirror_path(self) -> str:
        return self._selected_mirror

    @classmethod
    def pick(
        cls,
        parent=None,
        extra_exes: Optional[list[str]] = None,
        *,
        current: str = "",
    ) -> Optional[str]:
        """Detect folders and let the user pick one. Returns pbem path or None."""
        ranked = list_civ4_save_candidates(extra_exes, force=True)
        if not ranked:
            QMessageBox.information(parent, t("info"), t("save_path_not_detected"))
            return None
        dlg = cls(ranked, extra_exes, current=current, parent=parent)
        if dlg.exec() == QDialog.Accepted:
            return dlg.selected_path or None
        return None

    def _select_current(self):
        if not self._current:
            if self.list_widget.count():
                self.list_widget.setCurrentRow(0)
            return
        current_pbem = str(canonical_pbem_save_dir(self._current, create=False)).lower()
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            path = item.data(Qt.UserRole) if item else ""
            if path and str(path).lower() == current_pbem:
                self.list_widget.setCurrentRow(row)
                return
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _refresh_list(self):
        show_saves = self.check_saves.isChecked()
        self.list_widget.clear()
        for _score, path in self._candidates:
            path_str = str(path)
            load_game = str(civ4_load_game_dir(path_str))
            lines = [path_str]
            if load_game.lower() != path_str.lower():
                lines.append(t("save_path_load_game", path=load_game))
            if save_path_from_civ4_settings(path_str, self._exes):
                lines.append(t("save_path_from_civ4_badge"))
            if show_saves:
                count = count_saves_in_folder(path_str)
                if count:
                    lines.append(t("save_path_has_saves", count=count))
                else:
                    lines.append(t("save_path_no_saves"))
            item = QListWidgetItem("\n".join(lines))
            item.setData(Qt.UserRole, path_str)
            if show_saves:
                count = count_saves_in_folder(path_str)
                if count:
                    item.setForeground(QColor("#66bb6a"))
                else:
                    item.setForeground(QColor("#ffb74d"))
            self.list_widget.addItem(item)
        self._select_current()

    def _on_use_this(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, t("info"), t("choose_save_path_pick_one"))
            return
        raw = item.data(Qt.UserRole) or ""
        if not raw:
            return
        pbem, mirror = resolve_save_layout(raw, create=True)
        self._selected_path = pbem
        self._selected_mirror = mirror
        self.accept()
