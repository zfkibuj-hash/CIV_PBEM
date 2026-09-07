"""Manual turn-queue editor: player order, save slots, whose turn."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.config import AppConfig
from src.gui.styles import get_style_for_theme
from src.i18n import t
from src.models.game import Game
from src.saves import iter_save_dirs

COL_SEQ, COL_TURN, COL_FROM, COL_TO, COL_FILE = range(5)


class EditQueueDialog(QDialog):
    """Assign each save to a queue slot and set who plays next."""

    def __init__(self, config: AppConfig, game: Game, parent=None):
        super().__init__(parent)
        self.config = config
        self.game = game
        self._publish = True
        self.setWindowTitle(t("edit_queue_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(860, 620)
        self.resize(960, 680)
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
        self.order_list = QListWidget()
        self.order_list.setSelectionMode(QAbstractItemView.SingleSelection)
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

        pointer = QGroupBox(t("edit_queue_pointer"))
        form = QFormLayout(pointer)
        self.wait_combo = QComboBox()
        self.turn_spin = QSpinBox()
        self.turn_spin.setRange(0, 9999)
        self.seq_spin = QSpinBox()
        self.seq_spin.setRange(0, 99999)
        self.chk_sync_wait = QCheckBox(t("edit_queue_sync_wait"))
        self.chk_sync_wait.setChecked(True)
        form.addRow(t("edit_queue_waiting"), self.wait_combo)
        form.addRow(t("edit_queue_turn"), self.turn_spin)
        form.addRow(t("edit_queue_next_seq"), self.seq_spin)
        form.addRow(self.chk_sync_wait)
        layout.addWidget(pointer)

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
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
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
        self.btn_current = QPushButton(t("edit_queue_set_current"))
        self.btn_current.clicked.connect(self._set_row_current)
        for b in (
            self.btn_add, self.btn_remove, self.btn_up, self.btn_down,
            self.btn_pick, self.btn_rebuild, self.btn_current,
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

    def _load_from_game(self):
        self.order_list.clear()
        for p in self.game.players:
            self.order_list.addItem(QListWidgetItem(p.name))
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

    def _selected_row(self) -> int:
        items = self.table.selectedIndexes()
        if items:
            return items[0].row()
        return self.table.currentRow()

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
        row = self._selected_row()
        if row < 0:
            return
        slots = self._read_slots()
        del slots[row]
        self._replace_table(slots, select=min(row, len(slots) - 1))
        self._maybe_sync_wait()

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
        self._publish = self.chk_publish.isChecked()
        self.accept()
