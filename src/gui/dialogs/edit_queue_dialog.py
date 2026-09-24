"""Manual turn-queue editor: player order, save slots, whose turn."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSizePolicy, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.config import AppConfig
from src.gui.player_order_widget import DEFAULT_PALETTE, _hex_to_rgb
from src.gui.styles import get_style_for_theme
from src.i18n import t
from src.models.game import Game
from src.saves import iter_save_dirs

COL_SEQ, COL_TURN, COL_FROM, COL_TO, COL_FILE = range(5)

# Distinct soft hues for Civ4 turn numbers (independent of player colors).
_TURN_PALETTE = [
    "#2e7d32", "#1565c0", "#6a1b9a", "#00838f",
    "#ef6c00", "#ad1457", "#4527a0", "#00695c",
    "#c62828", "#37474f", "#558b2f", "#0277bd",
]
_SEQ_GAP_BG = "#b71c1c"
_SEQ_GAP_FG = "#ffffff"

ListRemoteFn = Callable[[], tuple[list[str], str]]


def _contrast_fg(hex_color: str) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    return "#111111" if luma > 160 else "#f5f5f5"


def _player_color_map(game: Game) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, p in enumerate(game.players):
        stored = (game.player_colors or {}).get(p.name)
        out[p.name] = stored if stored else DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]
    return out


def _turn_color_map(slots: list[dict]) -> dict[int, str]:
    """Stable color per distinct turn number (order of first appearance)."""
    mapping: dict[int, str] = {}
    for slot in slots:
        tn = int(slot.get("turn_number") or 0)
        if tn not in mapping:
            mapping[tn] = _TURN_PALETTE[len(mapping) % len(_TURN_PALETTE)]
    return mapping


def _widget_style(bg: str, fg: str) -> str:
    return (
        f"background-color: {bg}; color: {fg}; "
        f"selection-background-color: {bg}; selection-color: {fg};"
    )


def _apply_slot_widget_colors(
    table: QTableWidget,
    slots: list[dict],
    player_colors: dict[str, str],
) -> None:
    """Color seq/turn/from/to cell widgets (editable tables)."""
    turns = _turn_color_map(slots)
    prev_seq: Optional[int] = None
    for r, slot in enumerate(slots):
        seq = int(slot.get("seq") or 0)
        seq_gap = prev_seq is not None and seq != prev_seq + 1
        prev_seq = seq
        seq_w = table.cellWidget(r, COL_SEQ)
        turn_w = table.cellWidget(r, COL_TURN)
        from_w = table.cellWidget(r, COL_FROM)
        to_w = table.cellWidget(r, COL_TO)
        if seq_w is not None:
            seq_w.setStyleSheet(
                _widget_style(_SEQ_GAP_BG, _SEQ_GAP_FG) if seq_gap else ""
            )
        if turn_w is not None:
            bg = turns.get(int(slot.get("turn_number") or 0), _TURN_PALETTE[0])
            turn_w.setStyleSheet(_widget_style(bg, _contrast_fg(bg)))
        for w, key in ((from_w, "from_name"), (to_w, "to_name")):
            if w is None:
                continue
            bg = player_colors.get(slot.get(key) or "")
            w.setStyleSheet(_widget_style(bg, _contrast_fg(bg)) if bg else "")


class _QueuePreviewDialog(QDialog):
    """Editable From-transport preview: fix seq/turn/from/to + rebuild names."""

    def __init__(
        self,
        config: AppConfig,
        game: Game,
        slots: list[dict],
        source_key: str,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config
        self.game = game
        self._propagating = False
        self.result_slots: list[dict] = []
        self.setWindowTitle(t("edit_queue_from_server_preview_title"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(860, 560)
        self.resize(980, 640)
        self.setStyleSheet(get_style_for_theme(config.get("dark_mode", True)))

        source_txt = t(f"edit_queue_from_server_src_{source_key}")
        layout = QVBoxLayout(self)
        hint = QLabel(
            t(
                "edit_queue_from_server_preview_hint",
                source=source_txt,
                n=len(slots),
            )
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #9e9e9e;")
        layout.addWidget(hint)

        self.chk_propagate = QCheckBox(t("edit_queue_propagate"))
        self.chk_propagate.setChecked(True)
        self.chk_propagate.setToolTip(t("edit_queue_propagate_hint"))
        layout.addWidget(self.chk_propagate)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("edit_queue_col_seq"),
            t("edit_queue_col_turn"),
            t("edit_queue_col_from"),
            t("edit_queue_col_to"),
            t("edit_queue_col_file"),
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_SEQ, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_TURN, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_FROM, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_TO, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_FILE, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        row_btns = QHBoxLayout()
        self.btn_remove = QPushButton(t("edit_queue_remove"))
        self.btn_remove.clicked.connect(self._remove_rows)
        self.btn_up = QPushButton(t("edit_queue_up"))
        self.btn_up.clicked.connect(lambda: self._move_table(-1))
        self.btn_down = QPushButton(t("edit_queue_down"))
        self.btn_down.clicked.connect(lambda: self._move_table(1))
        self.btn_rebuild = QPushButton(t("edit_queue_rebuild"))
        self.btn_rebuild.clicked.connect(self._rebuild_selected_name)
        self.btn_rebuild_all = QPushButton(t("edit_queue_rebuild_all"))
        self.btn_rebuild_all.clicked.connect(self._rebuild_all_names)
        for b in (
            self.btn_remove, self.btn_up, self.btn_down,
            self.btn_rebuild, self.btn_rebuild_all,
        ):
            row_btns.addWidget(b)
        row_btns.addStretch()
        layout.addLayout(row_btns)

        buttons = QDialogButtonBox()
        btn_load = buttons.addButton(
            t("edit_queue_from_server_load"), QDialogButtonBox.AcceptRole,
        )
        buttons.addButton(QDialogButtonBox.Cancel)
        btn_load.clicked.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._replace_table(slots, select=len(slots) - 1 if slots else -1)
        if self.table.rowCount() > 0:
            item = self.table.item(self.table.rowCount() - 1, COL_FILE)
            if item is not None:
                self.table.scrollToItem(item)

    def _player_names(self) -> list[str]:
        return [p.name for p in self.game.players]

    def _player_combo(self, selected: str) -> QComboBox:
        box = QComboBox()
        for name in self._player_names():
            box.addItem(name, name)
        if selected:
            idx = box.findData(selected)
            if idx >= 0:
                box.setCurrentIndex(idx)
            else:
                box.addItem(selected, selected)
                box.setCurrentIndex(box.count() - 1)
        box.currentIndexChanged.connect(self._on_route_changed)
        return box

    def _append_slot(self, slot: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        seq = QSpinBox()
        seq.setRange(0, 99999)
        seq.setValue(int(slot.get("seq") or 0))
        turn = QSpinBox()
        turn.setRange(0, 9999)
        turn.setValue(int(slot.get("turn_number") or 0))
        seq.valueChanged.connect(self._on_seq_spin)
        turn.valueChanged.connect(self._on_turn_spin)
        self.table.setCellWidget(r, COL_SEQ, seq)
        self.table.setCellWidget(r, COL_TURN, turn)
        self.table.setCellWidget(r, COL_FROM, self._player_combo(slot.get("from_name") or ""))
        self.table.setCellWidget(r, COL_TO, self._player_combo(slot.get("to_name") or ""))
        file_item = QTableWidgetItem(slot.get("filename") or "")
        file_item.setData(Qt.UserRole, float(slot.get("timestamp") or 0.0))
        self.table.setItem(r, COL_FILE, file_item)

    def _read_slot(self, row: int) -> dict:
        seq_w = self.table.cellWidget(row, COL_SEQ)
        turn_w = self.table.cellWidget(row, COL_TURN)
        from_w = self.table.cellWidget(row, COL_FROM)
        to_w = self.table.cellWidget(row, COL_TO)
        item = self.table.item(row, COL_FILE)
        return {
            "seq": int(seq_w.value()) if seq_w else 0,
            "turn_number": int(turn_w.value()) if turn_w else 0,
            "from_name": (from_w.currentData() or from_w.currentText()) if from_w else "",
            "to_name": (to_w.currentData() or to_w.currentText()) if to_w else "",
            "filename": (item.text() if item else "").strip(),
            "timestamp": float(item.data(Qt.UserRole) or 0) if item else 0.0,
        }

    def _read_slots(self) -> list[dict]:
        return [self._read_slot(r) for r in range(self.table.rowCount())]

    def _replace_table(self, slots: list[dict], select: int = -1):
        self.table.setRowCount(0)
        for slot in slots:
            self._append_slot(slot)
        if 0 <= select < self.table.rowCount():
            self.table.selectRow(select)
        self._apply_colors()

    def _apply_colors(self):
        colors = _player_color_map(self.game)
        for i, name in enumerate(self._player_names()):
            colors.setdefault(name, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)])
        _apply_slot_widget_colors(self.table, self._read_slots(), colors)

    def _selected_rows(self) -> list[int]:
        return sorted({idx.row() for idx in self.table.selectedIndexes()})

    def _selected_row(self) -> int:
        rows = self._selected_rows()
        return rows[-1] if rows else self.table.currentRow()

    def _row_of_widget(self, widget) -> int:
        if widget is None:
            return -1
        for r in range(self.table.rowCount()):
            if (
                self.table.cellWidget(r, COL_SEQ) is widget
                or self.table.cellWidget(r, COL_TURN) is widget
            ):
                return r
        return -1

    def _on_seq_spin(self, _value: int = 0):
        if self._propagating or not self.chk_propagate.isChecked():
            self._apply_colors()
            return
        row = self._row_of_widget(self.sender())
        if row >= 0:
            self._propagate_from(row, seq=True, turn=False)

    def _on_turn_spin(self, _value: int = 0):
        if self._propagating or not self.chk_propagate.isChecked():
            self._apply_colors()
            return
        row = self._row_of_widget(self.sender())
        if row >= 0:
            self._propagate_from(row, seq=False, turn=True)

    def _on_route_changed(self):
        self._apply_colors()

    def _propagate_from(self, start: int, *, seq: bool, turn: bool):
        slots = self._read_slots()
        if start < 0 or start >= len(slots):
            return
        n_players = max(1, len(self._player_names()))
        if seq:
            Game.propagate_queue_seq(slots, start)
        if turn:
            Game.propagate_queue_turn(slots, start, n_players)
        for i in range(start, len(slots)):
            self.game.refresh_queue_slot_filename(slots[i])
        self._propagating = True
        try:
            for i in range(start, min(len(slots), self.table.rowCount())):
                seq_w = self.table.cellWidget(i, COL_SEQ)
                turn_w = self.table.cellWidget(i, COL_TURN)
                if seq_w:
                    seq_w.blockSignals(True)
                    seq_w.setValue(int(slots[i].get("seq") or 0))
                    seq_w.blockSignals(False)
                if turn_w:
                    turn_w.blockSignals(True)
                    turn_w.setValue(int(slots[i].get("turn_number") or 0))
                    turn_w.blockSignals(False)
                item = self.table.item(i, COL_FILE)
                if item is None:
                    item = QTableWidgetItem()
                    self.table.setItem(i, COL_FILE, item)
                item.setText(slots[i].get("filename") or "")
        finally:
            self._propagating = False
        self._apply_colors()

    def _remove_rows(self):
        rows = self._selected_rows()
        if not rows:
            return
        drop = set(rows)
        slots = [s for i, s in enumerate(self._read_slots()) if i not in drop]
        select = min(rows[0], max(0, len(slots) - 1)) if slots else -1
        self._replace_table(slots, select=select)

    def _move_table(self, delta: int):
        row = self._selected_row()
        if row < 0:
            return
        dest = row + delta
        slots = self._read_slots()
        if dest < 0 or dest >= len(slots):
            return
        slots[row], slots[dest] = slots[dest], slots[row]
        self._replace_table(slots, select=dest)

    def _rebuild_selected_name(self):
        row = self._selected_row()
        if row < 0:
            return
        slots = self._read_slots()
        slot = slots[row]
        slot["filename"] = self.game.managed_save_filename(
            slot["seq"], slot["turn_number"], slot["from_name"], slot["to_name"],
        )
        self._replace_table(slots, select=row)

    def _rebuild_all_names(self):
        slots = self._read_slots()
        for slot in slots:
            slot["filename"] = self.game.managed_save_filename(
                slot["seq"], slot["turn_number"], slot["from_name"], slot["to_name"],
            )
        select = self._selected_row()
        self._replace_table(slots, select=select if select >= 0 else len(slots) - 1)

    def _accept(self):
        self.result_slots = self._read_slots()
        self.accept()


class EditQueueDialog(QDialog):
    """Assign each save to a queue slot and set who plays next."""

    def __init__(
        self,
        config: AppConfig,
        game: Game,
        parent=None,
        list_remote: Optional[ListRemoteFn] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.game = game
        self._list_remote = list_remote
        self._publish = True
        self._propagating = False
        self.setWindowTitle(t("edit_queue_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(920, 660)
        self.resize(1040, 720)
        self.setStyleSheet(get_style_for_theme(config.get("dark_mode", True)))
        self._init_ui()
        self._load_from_game()

    def publish_to_server(self) -> bool:
        return self._publish

    def _player_names(self) -> list[str]:
        return [p.name for p in self.game.players]

    def _init_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel(t("edit_queue_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #9e9e9e;")
        layout.addWidget(hint)

        order_box = QGroupBox(t("edit_queue_order"))
        order_l = QHBoxLayout(order_box)
        order_l.setContentsMargins(6, 6, 6, 6)
        self.order_list = QListWidget()
        self.order_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.order_list.setMinimumHeight(120)
        self.order_list.setMaximumHeight(180)
        order_l.addWidget(self.order_list, 1)
        order_btns = QVBoxLayout()
        self.btn_order_up = QPushButton(t("edit_queue_up"))
        self.btn_order_up.clicked.connect(lambda: self._move_list(self.order_list, -1))
        self.btn_order_down = QPushButton(t("edit_queue_down"))
        self.btn_order_down.clicked.connect(lambda: self._move_list(self.order_list, 1))
        order_btns.addWidget(self.btn_order_up)
        order_btns.addWidget(self.btn_order_down)
        order_btns.addStretch()
        order_l.addLayout(order_btns)
        layout.addWidget(order_box)

        pointer_row = QHBoxLayout()
        pointer_row.setSpacing(6)
        pointer_row.setContentsMargins(0, 2, 0, 4)
        ptr_lbl = QLabel(t("edit_queue_pointer") + ":")
        ptr_lbl.setStyleSheet("font-weight: 600;")
        pointer_row.addWidget(ptr_lbl)
        pointer_row.addWidget(QLabel(t("edit_queue_waiting")))
        self.wait_combo = QComboBox()
        self.wait_combo.setMinimumWidth(120)
        self.wait_combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        pointer_row.addWidget(self.wait_combo)
        pointer_row.addWidget(QLabel(t("edit_queue_turn")))
        self.turn_spin = QSpinBox()
        self.turn_spin.setRange(0, 9999)
        self.turn_spin.setFixedWidth(72)
        pointer_row.addWidget(self.turn_spin)
        pointer_row.addWidget(QLabel(t("edit_queue_next_seq")))
        self.seq_spin = QSpinBox()
        self.seq_spin.setRange(0, 99999)
        self.seq_spin.setFixedWidth(80)
        pointer_row.addWidget(self.seq_spin)
        self.chk_sync_wait = QCheckBox(t("edit_queue_sync_wait"))
        self.chk_sync_wait.setChecked(True)
        self.chk_propagate = QCheckBox(t("edit_queue_propagate"))
        self.chk_propagate.setChecked(True)
        self.chk_propagate.setToolTip(t("edit_queue_propagate_hint"))
        pointer_row.addWidget(self.chk_sync_wait)
        pointer_row.addWidget(self.chk_propagate)
        pointer_row.addStretch()
        layout.addLayout(pointer_row)

        saves = QGroupBox(t("edit_queue_saves"))
        saves_l = QVBoxLayout(saves)
        saves_hint = QLabel(t("edit_queue_saves_hint"))
        saves_hint.setWordWrap(True)
        saves_hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        saves_l.addWidget(saves_hint)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("edit_queue_col_seq"),
            t("edit_queue_col_turn"),
            t("edit_queue_col_from"),
            t("edit_queue_col_to"),
            t("edit_queue_col_file"),
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_SEQ, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_TURN, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_FROM, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_TO, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_FILE, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._update_remove_label)
        saves_l.addWidget(self.table, 1)

        row_btns = QHBoxLayout()
        self.btn_add = QPushButton(t("edit_queue_add"))
        self.btn_add.clicked.connect(self._add_row)
        self.btn_remove = QPushButton(t("edit_queue_remove"))
        self.btn_remove.clicked.connect(self._remove_row)
        self.btn_up = QPushButton(t("edit_queue_up"))
        self.btn_up.clicked.connect(lambda: self._move_table(-1))
        self.btn_down = QPushButton(t("edit_queue_down"))
        self.btn_down.clicked.connect(lambda: self._move_table(1))
        self.btn_pick = QPushButton(t("edit_queue_pick"))
        self.btn_pick.clicked.connect(self._pick_file)
        self.btn_rebuild = QPushButton(t("edit_queue_rebuild"))
        self.btn_rebuild.clicked.connect(self._rebuild_selected_name)
        self.btn_from_server = QPushButton(t("edit_queue_from_server"))
        self.btn_from_server.setToolTip(t("edit_queue_from_server_hint"))
        self.btn_from_server.clicked.connect(self._rebuild_from_server)
        self.btn_current = QPushButton(t("edit_queue_set_current"))
        self.btn_current.clicked.connect(self._set_row_current)
        for b in (
            self.btn_add, self.btn_remove, self.btn_up, self.btn_down,
            self.btn_pick, self.btn_rebuild, self.btn_from_server, self.btn_current,
        ):
            row_btns.addWidget(b)
        row_btns.addStretch()
        saves_l.addLayout(row_btns)
        layout.addWidget(saves, 1)

        self.chk_publish = QCheckBox(t("edit_queue_publish"))
        self.chk_publish.setChecked(True)
        layout.addWidget(self.chk_publish)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_remove_label()

    def _load_from_game(self):
        colors = _player_color_map(self.game)
        self.order_list.clear()
        for p in self.game.players:
            item = QListWidgetItem(p.name)
            item.setTextAlignment(Qt.AlignCenter)
            bg = colors.get(p.name) or DEFAULT_PALETTE[0]
            item.setBackground(QColor(bg))
            item.setForeground(QColor(_contrast_fg(bg)))
            self.order_list.addItem(item)
        self._refill_wait_combo()
        wait = self.game.current_player.name if self.game.current_player else ""
        sync = self.chk_sync_wait.isChecked()
        self.chk_sync_wait.setChecked(False)
        self.table.setRowCount(0)
        for turn in self.game.history:
            slot = self.game.slot_from_save_filename(
                turn.filename or "", timestamp=turn.timestamp,
            )
            if turn.player_name and not slot["from_name"]:
                slot["from_name"] = turn.player_name
            if turn.turn_number and not slot["turn_number"]:
                slot["turn_number"] = int(turn.turn_number)
            self._append_slot(slot)
        self.chk_sync_wait.setChecked(sync)
        idx = self.wait_combo.findData(wait)
        self.wait_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.turn_spin.setValue(int(self.game.current_turn or 0))
        self.seq_spin.setValue(int(self.game.save_seq or 0))
        self._apply_table_colors()

    def _refill_wait_combo(self):
        current = self.wait_combo.currentData()
        self.wait_combo.blockSignals(True)
        self.wait_combo.clear()
        for name in self._order_names():
            self.wait_combo.addItem(name, name)
        if current:
            idx = self.wait_combo.findData(current)
            if idx >= 0:
                self.wait_combo.setCurrentIndex(idx)
        self.wait_combo.blockSignals(False)

    def _order_names(self) -> list[str]:
        names = []
        for i in range(self.order_list.count()):
            names.append(self.order_list.item(i).text())
        return names or self._player_names()

    def _player_combo(self, selected: str) -> QComboBox:
        box = QComboBox()
        names = self._order_names()
        for name in names:
            box.addItem(name, name)
        if selected:
            idx = box.findData(selected)
            if idx >= 0:
                box.setCurrentIndex(idx)
            else:
                box.addItem(selected, selected)
                box.setCurrentIndex(box.count() - 1)
        box.currentIndexChanged.connect(self._on_route_changed)
        return box

    def _append_slot(self, slot: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        seq = QSpinBox()
        seq.setRange(0, 99999)
        seq.setValue(int(slot.get("seq") or 0))
        turn = QSpinBox()
        turn.setRange(0, 9999)
        turn.setValue(int(slot.get("turn_number") or 0))
        seq.valueChanged.connect(self._on_seq_spin)
        turn.valueChanged.connect(self._on_turn_spin)
        self.table.setCellWidget(r, COL_SEQ, seq)
        self.table.setCellWidget(r, COL_TURN, turn)
        self.table.setCellWidget(r, COL_FROM, self._player_combo(slot.get("from_name") or ""))
        self.table.setCellWidget(r, COL_TO, self._player_combo(slot.get("to_name") or ""))
        file_item = QTableWidgetItem(slot.get("filename") or "")
        ts = float(slot.get("timestamp") or 0.0)
        file_item.setData(Qt.UserRole, ts)
        self.table.setItem(r, COL_FILE, file_item)

    def _read_slot(self, row: int) -> dict:
        seq_w = self.table.cellWidget(row, COL_SEQ)
        turn_w = self.table.cellWidget(row, COL_TURN)
        from_w = self.table.cellWidget(row, COL_FROM)
        to_w = self.table.cellWidget(row, COL_TO)
        item = self.table.item(row, COL_FILE)
        return {
            "seq": int(seq_w.value()) if seq_w else 0,
            "turn_number": int(turn_w.value()) if turn_w else 0,
            "from_name": (from_w.currentData() or from_w.currentText()) if from_w else "",
            "to_name": (to_w.currentData() or to_w.currentText()) if to_w else "",
            "filename": (item.text() if item else "").strip(),
            "timestamp": float(item.data(Qt.UserRole) or 0) if item else 0.0,
        }

    def _read_slots(self) -> list[dict]:
        return [self._read_slot(r) for r in range(self.table.rowCount())]

    def _replace_table(self, slots: list[dict], select: int = -1):
        self.table.setRowCount(0)
        for slot in slots:
            self._append_slot(slot)
        if 0 <= select < self.table.rowCount():
            self.table.selectRow(select)
        self._apply_table_colors()

    def _player_colors(self) -> dict[str, str]:
        colors = _player_color_map(self.game)
        # Also map names that appear only in the order list / table.
        for i, name in enumerate(self._order_names()):
            if name and name not in colors:
                colors[name] = DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]
        return colors

    def _apply_table_colors(self):
        """Seq=gap only; Turn=same T grouped; From/To=player colors."""
        _apply_slot_widget_colors(self.table, self._read_slots(), self._player_colors())

    def _selected_rows(self) -> list[int]:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        return rows

    def _selected_row(self) -> int:
        rows = self._selected_rows()
        if rows:
            return rows[-1]
        return self.table.currentRow()

    def _update_remove_label(self):
        n = len(self._selected_rows())
        if n > 1:
            self.btn_remove.setText(t("edit_queue_remove_n", n=n))
        else:
            self.btn_remove.setText(t("edit_queue_remove"))

    def _add_row(self):
        names = self._order_names()
        slots = self._read_slots()
        seq = 0
        turn = 0
        from_name = names[0] if names else ""
        to_name = names[1] if len(names) > 1 else from_name
        if slots:
            last = slots[-1]
            seq = int(last.get("seq") or 0) + 1
            turn = int(last.get("turn_number") or 0)
            from_name = last.get("to_name") or from_name
            if from_name in names:
                to_name = names[(names.index(from_name) + 1) % len(names)]
        fn = self.game.managed_save_filename(seq, turn, from_name, to_name)
        slots.append({
            "seq": seq,
            "turn_number": turn,
            "from_name": from_name,
            "to_name": to_name,
            "filename": fn,
            "timestamp": 0.0,
        })
        self._replace_table(slots, select=len(slots) - 1)
        self._maybe_sync_wait()

    def _remove_row(self):
        rows = self._selected_rows()
        if not rows:
            return
        drop = set(rows)
        slots = [s for i, s in enumerate(self._read_slots()) if i not in drop]
        select = min(rows[0], max(0, len(slots) - 1)) if slots else -1
        self._replace_table(slots, select=select)
        self._maybe_sync_wait()
        self._update_remove_label()

    def _move_table(self, delta: int):
        row = self._selected_row()
        if row < 0:
            return
        dest = row + delta
        slots = self._read_slots()
        if dest < 0 or dest >= len(slots):
            return
        slots[row], slots[dest] = slots[dest], slots[row]
        self._replace_table(slots, select=dest)
        self._maybe_sync_wait()

    def _move_list(self, widget: QListWidget, delta: int):
        row = widget.currentRow()
        dest = row + delta
        if row < 0 or dest < 0 or dest >= widget.count():
            return
        item = widget.takeItem(row)
        widget.insertItem(dest, item)
        widget.setCurrentRow(dest)
        self._refill_wait_combo()
        slots = self._read_slots()
        self._replace_table(slots, select=self._selected_row())

    def _pick_file(self):
        row = self._selected_row()
        start = self.config.save_path or str(Path.home())
        dirs = list(iter_save_dirs(
            self.config.save_path,
            self.config.get("civ4_save_path", ""),
            self.config.get("mirror_saves", True),
        ))
        if dirs:
            start = str(dirs[0])
        path, _ = QFileDialog.getOpenFileName(
            self, t("edit_queue_pick"), start, t("civ4_saves_filter"),
        )
        if not path:
            return
        slot = self.game.slot_from_save_filename(path)
        slots = self._read_slots()
        if row < 0:
            slots.append(slot)
            row = len(slots) - 1
        else:
            slot["timestamp"] = slots[row].get("timestamp") or 0.0
            slots[row] = slot
        self._replace_table(slots, select=row)
        self._maybe_sync_wait()

    def _row_of_widget(self, widget) -> int:
        if widget is None:
            return -1
        for r in range(self.table.rowCount()):
            if (
                self.table.cellWidget(r, COL_SEQ) is widget
                or self.table.cellWidget(r, COL_TURN) is widget
            ):
                return r
        return -1

    def _on_seq_spin(self, _value: int = 0):
        if self._propagating or not self.chk_propagate.isChecked():
            return
        row = self._row_of_widget(self.sender())
        if row >= 0:
            self._propagate_from(row, seq=True, turn=False)

    def _on_turn_spin(self, _value: int = 0):
        if self._propagating or not self.chk_propagate.isChecked():
            return
        row = self._row_of_widget(self.sender())
        if row >= 0:
            self._propagate_from(row, seq=False, turn=True)

    def _propagate_from(self, start: int, *, seq: bool, turn: bool):
        slots = self._read_slots()
        if start < 0 or start >= len(slots):
            return
        n_players = max(1, len(self._order_names()))
        if seq:
            Game.propagate_queue_seq(slots, start)
        if turn:
            Game.propagate_queue_turn(slots, start, n_players)
        for i in range(start, len(slots)):
            self.game.refresh_queue_slot_filename(slots[i])
        self._write_slots_from(start, slots)
        self._sync_pointer_from_slots(slots)
        self._apply_table_colors()
        self._maybe_sync_wait()

    def _write_slots_from(self, start: int, slots: list[dict]):
        self._propagating = True
        try:
            for i in range(start, min(len(slots), self.table.rowCount())):
                seq_w = self.table.cellWidget(i, COL_SEQ)
                turn_w = self.table.cellWidget(i, COL_TURN)
                if seq_w:
                    seq_w.blockSignals(True)
                    seq_w.setValue(int(slots[i].get("seq") or 0))
                    seq_w.blockSignals(False)
                if turn_w:
                    turn_w.blockSignals(True)
                    turn_w.setValue(int(slots[i].get("turn_number") or 0))
                    turn_w.blockSignals(False)
                item = self.table.item(i, COL_FILE)
                if item is None:
                    item = QTableWidgetItem()
                    self.table.setItem(i, COL_FILE, item)
                item.setText(slots[i].get("filename") or "")
        finally:
            self._propagating = False

    def _sync_pointer_from_slots(self, slots: list[dict]):
        if not slots:
            return
        max_seq = max(int(s.get("seq") or 0) for s in slots)
        self.seq_spin.setValue(max_seq + 1)

    def _rebuild_from_server(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            if self._list_remote:
                names, source = self._list_remote()
            else:
                names, source = self.game.history_save_filenames(), "local"
        except Exception as e:
            QMessageBox.warning(self, t("error"), str(e))
            return
        finally:
            QApplication.restoreOverrideCursor()
        slots = self.game.slots_from_save_names(names)
        if not slots:
            QMessageBox.warning(self, t("error"), t("edit_queue_from_server_empty"))
            return
        # Unknown source keys fall back to generic "server" label.
        src_key = source if source in (
            "ftp", "email", "sftp", "webdav", "local", "server",
        ) else "server"
        preview = _QueuePreviewDialog(self.config, self.game, slots, src_key, self)
        if preview.exec() != QDialog.Accepted:
            return
        slots = preview.result_slots or slots
        self._replace_table(slots, select=len(slots) - 1)
        if self.table.rowCount() > 0:
            last_item = self.table.item(self.table.rowCount() - 1, COL_FILE)
            if last_item is not None:
                self.table.scrollToItem(last_item)
        self._sync_pointer_from_slots(slots)
        last = slots[-1]
        if last.get("turn_number") is not None:
            self.turn_spin.setValue(int(last.get("turn_number") or 0))
        to_name = last.get("to_name") or ""
        if to_name:
            idx = self.wait_combo.findData(to_name)
            if idx >= 0:
                self.wait_combo.setCurrentIndex(idx)
        wait = self.wait_combo.currentData() or self.wait_combo.currentText() or "?"
        QMessageBox.information(
            self,
            t("edit_queue_from_server"),
            t(
                "edit_queue_from_server_loaded",
                n=len(slots),
                player=wait,
                filename=last.get("filename") or "?",
            ),
        )

    def _rebuild_selected_name(self):
        row = self._selected_row()
        if row < 0:
            return
        slots = self._read_slots()
        slot = slots[row]
        slot["filename"] = self.game.managed_save_filename(
            slot["seq"], slot["turn_number"], slot["from_name"], slot["to_name"],
        )
        self._replace_table(slots, select=row)
        self._maybe_sync_wait()

    def _set_row_current(self):
        row = self._selected_row()
        if row < 0:
            return
        slots = self._read_slots()
        chosen = slots.pop(row)
        slots.append(chosen)
        self._replace_table(slots, select=len(slots) - 1)
        to_name = chosen.get("to_name") or ""
        if to_name:
            idx = self.wait_combo.findData(to_name)
            if idx >= 0:
                self.wait_combo.setCurrentIndex(idx)
        max_seq = max((int(s.get("seq") or 0) for s in slots), default=-1)
        self.seq_spin.setValue(max_seq + 1)

    def _on_route_changed(self):
        self._apply_table_colors()
        self._maybe_sync_wait()

    def _maybe_sync_wait(self):
        if not self.chk_sync_wait.isChecked():
            return
        if self.table.rowCount() <= 0:
            return
        last = self._read_slot(self.table.rowCount() - 1)
        to_name = last.get("to_name") or ""
        if not to_name:
            return
        idx = self.wait_combo.findData(to_name)
        if idx >= 0:
            self.wait_combo.setCurrentIndex(idx)

    def _save(self):
        slots = self._read_slots()
        if self.chk_sync_wait.isChecked() and slots:
            to_name = slots[-1].get("to_name") or ""
            if to_name:
                idx = self.wait_combo.findData(to_name)
                if idx >= 0:
                    self.wait_combo.setCurrentIndex(idx)
        wait = self.wait_combo.currentData() or self.wait_combo.currentText()
        last = (slots[-1].get("filename") if slots else "") or ""
        reply = QMessageBox.question(
            self,
            t("edit_queue_title", name=self.game.name),
            t(
                "edit_queue_confirm",
                player=wait or "?",
                turn=int(self.turn_spin.value()),
                seq=int(self.seq_spin.value()),
                n=len(slots),
                filename=last,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        err = self.game.apply_manual_queue(
            self._order_names(),
            slots,
            wait,
            int(self.turn_spin.value()),
            int(self.seq_spin.value()),
        )
        if err:
            QMessageBox.warning(self, t("error"), t(err))
            return
        # Last save on disk is the source of truth for whose turn it is
        if slots:
            latest = slots[-1].get("filename") or ""
            if latest:
                self.game.sync_current_player_from_save(latest)
        self._publish = self.chk_publish.isChecked()
        self.accept()
