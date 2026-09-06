"""
EditGameDialog — dialog for editing an existing game's settings.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QGroupBox,
    QDialogButtonBox, QPushButton, QColorDialog, QFileDialog, QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.config import AppConfig
from src.models.game import Game
from src.i18n import t
from src.gui.styles import get_style_for_theme
from src.civ4_save_info import (
    Civ4SaveInfo, parse_civ4_save, find_latest_game_save, normalize_leader_key,
)
from src.saves import iter_save_dirs

# Default color palette for players
DEFAULT_COLORS = ["#66bb6a", "#42a5f5", "#ffa726", "#ab47bc", "#ef5350", "#26c6da", "#ec407a", "#8d6e63"]


def confirm_player_claim(parent, game: Game, player_name: str, install_id: str) -> bool:
    """True if this install may claim the roster slot (no conflict, or user steals)."""
    other = game.other_install_claim(player_name, install_id)
    if not other:
        return True
    other_nick = (other.get("local_name") or "").strip() or "?"
    reply = QMessageBox.warning(
        parent,
        t("alias_claimed_title"),
        t("alias_claimed_body", player=player_name, other=other_nick),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes


class EditGameDialog(QDialog):
    """Dialog for editing an existing game's settings (players, emails, speed, alias, colors)."""

    def __init__(self, config: AppConfig, game: Game, parent=None):
        super().__init__(parent)
        self.config = config
        self.game = game
        self._save_info: Civ4SaveInfo | None = None
        self.setWindowTitle(t("edit_game_title", name=game.name))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(620, 560)
        self.resize(680, 600)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()
        self._try_autoload_save()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Game speed
        speed_group = QGroupBox(t("game_speed"))
        speed_form = QFormLayout(speed_group)
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("Quick (330)", "quick")
        self.speed_combo.addItem("Normal (500)", "normal")
        self.speed_combo.addItem("Epic (750)", "epic")
        self.speed_combo.addItem("Marathon (1500)", "marathon")
        idx = self.speed_combo.findData(self.game.game_speed)
        if idx >= 0:
            self.speed_combo.setCurrentIndex(idx)
        speed_form.addRow(t("game_speed"), self.speed_combo)
        layout.addWidget(speed_group)

        # Player alias — WHICH player (in this game's roster) are you.
        # No "all / none" wildcard option here: leaving this ambiguous is
        # exactly what caused ghost "your turn" states for the wrong person.
        # If your local nick already matches a roster name exactly, that
        # name is simply pre-selected — but it's still one concrete choice.
        alias_group = QGroupBox(t("edit_alias"))
        alias_form = QFormLayout(alias_group)
        self.alias_combo = QComboBox()
        my_local_name = (self.config.player_name or "").casefold()
        default_idx = 0
        for i, p in enumerate(self.game.players):
            self.alias_combo.addItem(p.name, p.name)
            if p.name.casefold() == my_local_name:
                default_idx = i
        current_alias = self.game.local_player_alias
        if current_alias:
            idx = self.alias_combo.findData(current_alias)
            if idx >= 0:
                default_idx = idx
        self.alias_combo.setCurrentIndex(default_idx)
        alias_form.addRow(t("edit_alias_label"), self.alias_combo)
        layout.addWidget(alias_group)

        winner_group = QGroupBox(t("winner_group"))
        winner_form = QFormLayout(winner_group)
        self.winner_combo = QComboBox()
        self.winner_combo.addItem(t("winner_none"), "")
        for p in self.game.players:
            self.winner_combo.addItem(p.name, p.name)
        widx = self.winner_combo.findData((self.game.winner or "").strip())
        self.winner_combo.setCurrentIndex(widx if widx >= 0 else 0)
        winner_form.addRow(t("winner_label"), self.winner_combo)
        winner_hint = QLabel(t("winner_hint"))
        winner_hint.setWordWrap(True)
        winner_hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        winner_form.addRow(winner_hint)
        layout.addWidget(winner_group)

        # Leaders from save
        leaders_group = QGroupBox(t("civ4_leaders_from_save"))
        leaders_layout = QVBoxLayout(leaders_group)
        self.lbl_save_source = QLabel(t("civ4_leaders_no_save"))
        self.lbl_save_source.setWordWrap(True)
        self.lbl_save_source.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        leaders_layout.addWidget(self.lbl_save_source)
        btn_row = QHBoxLayout()
        self.btn_load_save = QPushButton(t("civ4_leaders_load_save"))
        self.btn_load_save.clicked.connect(self._pick_save)
        btn_row.addWidget(self.btn_load_save)
        btn_row.addStretch()
        leaders_layout.addLayout(btn_row)
        layout.addWidget(leaders_group)

        # Players — editable emails + leader dropdown + color picker
        players_group = QGroupBox(t("edit_players"))
        players_layout = QVBoxLayout(players_group)

        header = QHBoxLayout()
        for text, width in (
            (t("edit_player_nick"), 100),
            ("Email", 0),
            (t("civ4_leader_name"), 0),
            (t("edit_player_status"), 110),
            ("", 28),
        ):
            lab = QLabel(text)
            if width:
                lab.setMinimumWidth(width)
            header.addWidget(lab, 1 if not width else 0)
        players_layout.addLayout(header)

        self._email_edits = []
        self._leader_combos = []
        self._status_combos = []
        self._color_buttons = []
        for i, p in enumerate(self.game.players):
            row = QHBoxLayout()
            name_label = QLabel(f"{p.name}:")
            name_label.setMinimumWidth(100)
            row.addWidget(name_label)

            email_edit = QLineEdit(p.email)
            email_edit.setPlaceholderText("email@example.com")
            row.addWidget(email_edit, 2)

            leader_combo = QComboBox()
            leader_combo.setEditable(True)
            leader_combo.setMinimumWidth(180)
            leader_combo.setToolTip(t("civ4_leader_name"))
            self._fill_leader_combo(leader_combo, p.civ4_leader or "")
            row.addWidget(leader_combo, 2)

            status_combo = QComboBox()
            status_combo.setMinimumWidth(110)
            status_combo.addItem(t("player_status_active"), "active")
            status_combo.addItem(t("player_status_defeated"), "defeated")
            status_combo.addItem(t("player_status_resigned"), "resigned")
            idx = status_combo.findData(p.status or "active")
            status_combo.setCurrentIndex(idx if idx >= 0 else 0)
            status_combo.setToolTip(t("edit_player_status_hint"))
            row.addWidget(status_combo)

            current_color = self.game.player_colors.get(
                p.name, DEFAULT_COLORS[i % len(DEFAULT_COLORS)],
            )
            color_btn = QPushButton("")
            color_btn.setFixedSize(28, 28)
            color_btn.setStyleSheet(
                f"background-color: {current_color}; border: 1px solid #888; border-radius: 4px;"
            )
            color_btn.setToolTip(t("edit_player_color_tooltip"))
            color_btn.clicked.connect(
                lambda checked, btn=color_btn, name=p.name: self._pick_color(btn, name)
            )
            row.addWidget(color_btn)

            self._email_edits.append((p, email_edit))
            self._leader_combos.append((p, leader_combo))
            self._status_combos.append((p, status_combo))
            self._color_buttons.append((p.name, color_btn, current_color))
            players_layout.addLayout(row)

        layout.addWidget(players_group)

        # History color mode
        color_mode_group = QGroupBox(t("edit_color_mode_group"))
        color_mode_layout = QVBoxLayout(color_mode_group)

        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItem(t("color_mode_all"), "all")
        self.color_mode_combo.addItem(t("color_mode_mine"), "mine")
        current_mode = self.game.history_color_mode or "all"
        idx = self.color_mode_combo.findData(current_mode)
        if idx >= 0:
            self.color_mode_combo.setCurrentIndex(idx)
        color_mode_layout.addWidget(self.color_mode_combo)

        mode_hint = QLabel(t("color_mode_hint"))
        mode_hint.setWordWrap(True)
        mode_hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        color_mode_layout.addWidget(mode_hint)

        layout.addWidget(color_mode_group)

        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_leader_combo(self, combo: QComboBox, selected: str):
        combo.blockSignals(True)
        current_text = combo.currentText().strip() if combo.count() else selected
        combo.clear()
        combo.addItem("", "")
        if self._save_info:
            for slot in self._save_info.players:
                if not slot.leader_name:
                    continue
                combo.addItem(slot.label, slot.leader_name)
        # Keep a free-text / previously saved value even if not in save
        want = selected or current_text
        if want:
            found = False
            for i in range(combo.count()):
                if normalize_leader_key(combo.itemData(i) or "") == normalize_leader_key(want):
                    combo.setCurrentIndex(i)
                    found = True
                    break
                if normalize_leader_key(combo.itemText(i)) == normalize_leader_key(want):
                    combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                combo.addItem(want, want)
                combo.setCurrentIndex(combo.count() - 1)
        combo.blockSignals(False)

    def _refresh_all_leader_combos(self):
        for player, combo in self._leader_combos:
            selected = combo.currentData() or combo.currentText() or player.civ4_leader
            self._fill_leader_combo(combo, selected or "")

    def _apply_save_info(self, info: Civ4SaveInfo):
        self._save_info = info
        self.lbl_save_source.setText(
            t("civ4_leaders_loaded", path=str(info.path.name), n=len(info.players))
        )
        self._refresh_all_leader_combos()
        self._auto_match_leaders()

    def _auto_match_leaders(self):
        """If PBEM nick equals a save leader name, select it."""
        if not self._save_info:
            return
        used: set[str] = set()
        for player, combo in self._leader_combos:
            if (combo.currentData() or combo.currentText() or "").strip():
                key = normalize_leader_key(combo.currentData() or combo.currentText())
                if key:
                    used.add(key)
                continue
            for slot in self._save_info.players:
                key = normalize_leader_key(slot.leader_name)
                if key in used:
                    continue
                if normalize_leader_key(player.name) == key:
                    for i in range(combo.count()):
                        if combo.itemData(i) == slot.leader_name:
                            combo.setCurrentIndex(i)
                            used.add(key)
                            break
                    break

    def _try_autoload_save(self):
        dirs = []
        try:
            dirs = list(
                iter_save_dirs(
                    self.config.save_path,
                    self.config.get("civ4_save_path", ""),
                    self.config.get("mirror_saves", True),
                )
            )
        except Exception:
            if self.config.save_path:
                dirs = [Path(self.config.save_path)]
        latest = find_latest_game_save(self.game.name, dirs)
        if not latest:
            return
        info = parse_civ4_save(latest)
        if info:
            self._apply_save_info(info)

    def _pick_save(self):
        start = self.config.save_path or ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("civ4_leaders_pick_save"),
            start,
            t("civ4_saves_filter"),
        )
        if not path:
            return
        info = parse_civ4_save(path)
        if not info or not info.players:
            QMessageBox.warning(self, t("error"), t("civ4_leaders_parse_fail"))
            return
        self._apply_save_info(info)

    def _pick_color(self, btn: QPushButton, player_name: str):
        """Open color picker for a player."""
        current = None
        for name, b, color in self._color_buttons:
            if name == player_name:
                current = color
                break

        color = QColorDialog.getColor(
            QColor(current) if current else QColor("#66bb6a"),
            self,
            t("edit_player_color_title", name=player_name),
        )
        if color.isValid():
            hex_color = color.name()
            btn.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #888; border-radius: 4px;"
            )
            for i, (name, b, _) in enumerate(self._color_buttons):
                if name == player_name:
                    self._color_buttons[i] = (name, b, hex_color)
                    break

    def _confirm_admin_password(self) -> bool:
        """Same admin_password gate as danger-zone actions (main.py's
        _ask_admin_password) — one shared concept, not a second app/UI."""
        if not (self.game.admin_password or "").strip():
            return True
        from src.gui.app_controller import AppController
        pwd, ok = QInputDialog.getText(
            self, t("admin_password_prompt"), t("admin_password_prompt"),
            QLineEdit.Password,
        )
        if not ok:
            return False
        if not AppController.verify_admin_password(self.game, pwd):
            QMessageBox.warning(self, t("error"), t("wrong_password"))
            return False
        return True

    def _save(self):
        """Apply changes to the game object."""
        # Player status (defeated/resigned) changes who the turn queue skips —
        # that's a trust-sensitive action (it can be abused to steal a turn),
        # so it needs the game's admin password just like Danger Zone actions.
        status_changed = any(
            (combo.currentData() or "active") != (player.status or "active")
            for player, combo in self._status_combos
        )
        winner_changed = (
            (self.winner_combo.currentData() or "").strip()
            != (self.game.winner or "").strip()
        )
        if (status_changed or winner_changed) and not self._confirm_admin_password():
            QMessageBox.information(self, t("info"), t("edit_status_needs_admin"))
            return

        self.game.game_speed = self.speed_combo.currentData()

        alias = self.alias_combo.currentData()
        install_id = self.config.install_id
        if alias and not confirm_player_claim(self, self.game, alias, install_id):
            return
        self.game.local_player_alias = alias or ""
        if alias:
            self.game.set_player_claim(alias, install_id, self.config.player_name)

        for player, email_edit in self._email_edits:
            new_email = email_edit.text().strip()
            if new_email:
                player.email = new_email
        for player, leader_combo in self._leader_combos:
            data = leader_combo.currentData()
            text = leader_combo.currentText().strip()
            # Prefer data (leader name without civ label); fall back to typed text
            if data:
                player.civ4_leader = str(data).strip()
            else:
                # Editable combo may show "Leader — Civ"; keep left part if matched
                player.civ4_leader = text.split("—")[0].strip() if "—" in text else text

        for player, status_combo in self._status_combos:
            new_status = status_combo.currentData() or "active"
            self.game.set_player_status(player.name, new_status)

        explicit_winner = (self.winner_combo.currentData() or "").strip()
        if explicit_winner:
            self.game.winner = explicit_winner
        else:
            auto = self.game.maybe_declare_winner()
            if not auto and len(self.game.active_players) != 1:
                self.game.winner = ""

        colors = {}
        for name, btn, color in self._color_buttons:
            colors[name] = color
        self.game.player_colors = colors

        self.game.history_color_mode = self.color_mode_combo.currentData()

        self.accept()
