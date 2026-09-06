"""Dialog: list every remote save; any file can be downloaded (confirm if not yours)."""
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.i18n import t
from src.models.game import Game


class ChooseSaveDialog(QDialog):
    """Show all remote saves. Green = yours; others are emergency downloads."""

    def __init__(self, game: Game, filenames: list[str], player_name: str, parent=None):
        super().__init__(parent)
        filenames = [n for n in filenames if game.save_belongs_to_game(n)]
        self._game = game
        self._player_name = player_name
        self._filename = ""
        self.setWindowTitle(t("choose_save_title"))
        self.setMinimumSize(520, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        hint = QLabel(t("choose_save_mine_hint", name=game.get_game_player_name(player_name)))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        mine_rows: list[int] = []

        def sort_key(name: str) -> tuple:
            seq = Game.parse_save_seq(name)
            turn, _, _ = Game.parse_save_filename(name)
            return (
                seq if seq is not None else -1,
                turn if turn is not None else -1,
                name,
            )

        sorted_files = sorted(filenames, key=sort_key, reverse=True)
        for name in sorted_files:
            seq = Game.parse_save_seq(name)
            turn, _sender, _recipient = Game.parse_save_filename(name)
            is_mine = game.is_save_for_player(name, player_name)
            from_name, to_name = game.save_route(name)
            seq_txt = f"#{seq}" if seq is not None else "#—"
            turn_txt = f"T{turn:04d}" if turn is not None else "?"
            suffix = t("choose_save_can_download") if is_mine else t("choose_save_other_player")
            route = t("save_route", from_name=from_name, to_name=to_name)
            item = QListWidgetItem(f"{seq_txt} {turn_txt}  {route}  {suffix}\n{name}")
            item.setData(Qt.UserRole, name)
            if is_mine:
                item.setForeground(QColor("#66bb6a"))
                mine_rows.append(self.list_widget.count())
            else:
                item.setForeground(QColor("#ffa726"))
            self.list_widget.addItem(item)

        if mine_rows:
            self.list_widget.setCurrentRow(mine_rows[-1])
        elif self.list_widget.count():
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

        self.list_widget.itemDoubleClicked.connect(self._on_double_click)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)
        self._ok = buttons.button(QDialogButtonBox.Ok)
        self._ok.setEnabled(self.list_widget.count() > 0)
        layout.addWidget(buttons)

        if not mine_rows and self.list_widget.count():
            empty = QLabel(t("choose_save_none_mine"))
            empty.setWordWrap(True)
            layout.insertWidget(1, empty)

    def _on_double_click(self, item: QListWidgetItem):
        if self._try_accept(item):
            self.accept()

    def _accept_selected(self):
        item = self.list_widget.currentItem()
        if self._try_accept(item):
            self.accept()

    def _try_accept(self, item: Optional[QListWidgetItem]) -> bool:
        if not item:
            return False
        filename = item.data(Qt.UserRole) or ""
        if not filename:
            return False
        if not self._confirm_if_other(filename):
            return False
        self._filename = filename
        return True

    def _confirm_if_other(self, filename: str) -> bool:
        if self._game.is_save_for_player(filename, self._player_name):
            return True
        from_name, to_name = self._game.save_route(filename)
        reply = QMessageBox.warning(
            self,
            t("choose_save_title"),
            t("choose_save_not_yours_confirm", from_name=from_name, to_name=to_name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def selected_filename(self) -> str:
        return self._filename
