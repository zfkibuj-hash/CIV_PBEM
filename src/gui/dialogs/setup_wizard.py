"""
First-run setup wizard: detect Civ4, save folder, bind .CivBeyondSwordSave
to /fxsload so double-clicking a save loads it in the game.
"""
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QStackedWidget,
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox,
    QFileDialog, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer

from src.config import AppConfig
from src.i18n import t, set_language
from src.gui.styles import get_style_for_theme
from src.launcher import (
    detect_all_editions, ensure_pbem_save_path, set_file_association,
    list_civ4_save_candidates, resolve_save_layout, civ4_exe_paths_for_detection,
)
from src.gui.dialogs.choose_save_path_dialog import ChooseSavePathDialog

logger = logging.getLogger(__name__)

_EDITION_ORDER = ("steam", "gog", "dvd")


class SetupWizard(QDialog):
    """Guided first-run setup. Auto-detects Civ4 and wires /fxsload."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._detected: dict[str, str] = {}
        self._save_path = ""
        self._mirror_path = ""
        self._manual_exes: dict[str, str] = {}
        self._save_prompted = False
        self._post_action = ""

        self.setWindowTitle(t("wizard_title"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setMinimumSize(560, 480)
        self.resize(600, 520)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()
        self._go(0)

    @property
    def post_action(self) -> str:
        """Action requested after wizard: import | new_game | settings | ''."""
        return self._post_action

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.step_label = QLabel()
        self.step_label.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        layout.addWidget(self.step_label)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_welcome())
        self.stack.addWidget(self._page_identity())
        self.stack.addWidget(self._page_detect())
        self.stack.addWidget(self._page_next_steps())
        layout.addWidget(self.stack, 1)

        nav = QHBoxLayout()
        self.btn_skip = QPushButton()
        self.btn_skip.clicked.connect(self._on_skip)
        nav.addWidget(self.btn_skip)
        nav.addStretch()
        self.btn_back = QPushButton()
        self.btn_back.clicked.connect(self._on_back)
        nav.addWidget(self.btn_back)
        self.btn_next = QPushButton()
        self.btn_next.setObjectName("btn_download")
        self.btn_next.setMinimumHeight(36)
        self.btn_next.clicked.connect(self._on_next)
        nav.addWidget(self.btn_next)
        layout.addLayout(nav)

        self._retranslate()

    def _page_welcome(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.welcome_title = QLabel()
        self.welcome_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.welcome_title.setWordWrap(True)
        layout.addWidget(self.welcome_title)

        self.welcome_body = QLabel()
        self.welcome_body.setWordWrap(True)
        layout.addWidget(self.welcome_body)

        form = QFormLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItem("Polski", "pl")
        self.language_combo.addItem("English", "en")
        idx = 0 if self.config.language == "pl" else 1
        self.language_combo.setCurrentIndex(idx)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.lang_label = QLabel()
        form.addRow(self.lang_label, self.language_combo)
        layout.addLayout(form)

        layout.addStretch()
        return page

    def _page_identity(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.identity_title = QLabel()
        self.identity_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.identity_title.setWordWrap(True)
        layout.addWidget(self.identity_title)

        self.identity_hint = QLabel()
        self.identity_hint.setWordWrap(True)
        layout.addWidget(self.identity_hint)

        form = QFormLayout()
        self.name_edit = QLineEdit(self.config.player_name)
        self.name_label = QLabel()
        form.addRow(self.name_label, self.name_edit)
        self.email_edit = QLineEdit(self.config.get("player_email", ""))
        self.email_label = QLabel()
        form.addRow(self.email_label, self.email_edit)
        layout.addLayout(form)

        self.identity_error = QLabel()
        self.identity_error.setStyleSheet("color: #ef5350;")
        self.identity_error.setWordWrap(True)
        self.identity_error.hide()
        layout.addWidget(self.identity_error)

        layout.addStretch()
        return page

    def _page_detect(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        self.detect_title = QLabel()
        self.detect_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.detect_title.setWordWrap(True)
        layout.addWidget(self.detect_title)

        self.detect_hint = QLabel()
        self.detect_hint.setWordWrap(True)
        layout.addWidget(self.detect_hint)

        civ4_row = QHBoxLayout()
        self.btn_detect_civ4 = QPushButton()
        self.btn_detect_civ4.clicked.connect(self._detect_civ4)
        civ4_row.addWidget(self.btn_detect_civ4)
        civ4_row.addStretch()
        layout.addLayout(civ4_row)

        self.edition_labels: dict[str, QLabel] = {}
        self.edition_browse: dict[str, QPushButton] = {}
        for edition in _EDITION_ORDER:
            row = QHBoxLayout()
            lbl = QLabel()
            lbl.setWordWrap(True)
            self.edition_labels[edition] = lbl
            row.addWidget(lbl, 1)
            btn = QPushButton()
            btn.clicked.connect(lambda checked=False, ed=edition: self._browse_exe(ed))
            self.edition_browse[edition] = btn
            row.addWidget(btn)
            layout.addLayout(row)

        pref_row = QHBoxLayout()
        self.preferred_label = QLabel()
        pref_row.addWidget(self.preferred_label)
        self.preferred_combo = QComboBox()
        pref_row.addWidget(self.preferred_combo, 1)
        layout.addLayout(pref_row)
        self.preferred_hint = QLabel()
        self.preferred_hint.setWordWrap(True)
        self.preferred_hint.setObjectName("hintLabel")
        layout.addWidget(self.preferred_hint)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        self.save_section_label = QLabel()
        self.save_section_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.save_section_label)

        self.save_status = QLabel()
        self.save_status.setWordWrap(True)
        layout.addWidget(self.save_status)

        self.save_hint = QLabel()
        self.save_hint.setWordWrap(True)
        self.save_hint.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        layout.addWidget(self.save_hint)

        save_row = QHBoxLayout()
        self.btn_detect_saves = QPushButton()
        self.btn_detect_saves.clicked.connect(self._detect_saves)
        save_row.addWidget(self.btn_detect_saves)
        self.btn_browse_saves = QPushButton()
        self.btn_browse_saves.clicked.connect(self._browse_saves)
        save_row.addWidget(self.btn_browse_saves)
        save_row.addStretch()
        layout.addLayout(save_row)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        self.fxsload_check = QCheckBox()
        self.fxsload_check.setChecked(True)
        layout.addWidget(self.fxsload_check)

        self.assoc_check = QCheckBox()
        self.assoc_check.setChecked(True)
        layout.addWidget(self.assoc_check)

        self.assoc_hint = QLabel()
        self.assoc_hint.setWordWrap(True)
        self.assoc_hint.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        layout.addWidget(self.assoc_hint)

        layout.addStretch()
        return page

    def _page_next_steps(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.done_title = QLabel()
        self.done_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.done_title.setWordWrap(True)
        layout.addWidget(self.done_title)

        self.done_summary = QLabel()
        self.done_summary.setWordWrap(True)
        layout.addWidget(self.done_summary)

        self.done_next = QLabel()
        self.done_next.setWordWrap(True)
        layout.addWidget(self.done_next)

        actions = QVBoxLayout()
        actions.setSpacing(8)

        self.btn_wizard_import = QPushButton()
        self.btn_wizard_import.setObjectName("btn_download")
        self.btn_wizard_import.setMinimumHeight(40)
        self.btn_wizard_import.clicked.connect(lambda: self._finish("import"))
        actions.addWidget(self.btn_wizard_import)

        self.btn_wizard_new_game = QPushButton()
        self.btn_wizard_new_game.setMinimumHeight(40)
        self.btn_wizard_new_game.clicked.connect(lambda: self._finish("new_game"))
        actions.addWidget(self.btn_wizard_new_game)

        self.btn_wizard_settings = QPushButton()
        self.btn_wizard_settings.setMinimumHeight(40)
        self.btn_wizard_settings.clicked.connect(lambda: self._finish("settings"))
        actions.addWidget(self.btn_wizard_settings)

        layout.addLayout(actions)
        layout.addStretch()
        return page

    def _retranslate(self):
        self.setWindowTitle(t("wizard_title"))
        self.btn_skip.setText(t("wizard_skip"))
        self.btn_back.setText(t("wizard_back"))
        self.welcome_title.setText(t("wizard_welcome_title"))
        self.welcome_body.setText(t("wizard_welcome_body"))
        self.lang_label.setText(t("language"))
        self.identity_title.setText(t("wizard_identity_title"))
        self.identity_hint.setText(t("wizard_identity_hint"))
        self.name_label.setText(t("player_name"))
        self.email_label.setText(t("player_email"))
        self.name_edit.setPlaceholderText(t("wizard_name_placeholder"))
        self.email_edit.setPlaceholderText(t("wizard_email_placeholder"))
        self.detect_title.setText(t("wizard_detect_title"))
        self.detect_hint.setText(t("wizard_detect_hint"))
        self.btn_detect_civ4.setText(t("wizard_detect_civ4"))
        self.preferred_label.setText(t("wizard_preferred_edition"))
        self.preferred_hint.setText(t("preferred_edition_hint"))
        self.save_section_label.setText(t("wizard_save_section"))
        self.save_hint.setText(t("wizard_saves_onedrive_hint"))
        self.btn_detect_saves.setText(t("detect_civ4"))
        self.btn_browse_saves.setText(t("wizard_browse_saves"))
        for edition in _EDITION_ORDER:
            self.edition_browse[edition].setText(t("browse"))
        self.fxsload_check.setText(t("wizard_fxsload"))
        self.assoc_check.setText(t("wizard_assoc"))
        self.assoc_hint.setText(t("wizard_assoc_hint"))
        self.done_title.setText(t("wizard_done_title"))
        self.done_next.setText(t("wizard_done_next"))
        self.btn_wizard_import.setText(t("wizard_action_import"))
        self.btn_wizard_new_game.setText(t("wizard_action_new_game"))
        self.btn_wizard_settings.setText(t("wizard_action_settings"))
        self._refresh_detect_labels()
        self._refresh_summary()
        self._refresh_nav()

    def _on_language_changed(self, _index: int):
        lang = self.language_combo.currentData()
        if lang:
            set_language(lang)
            self.config.language = lang
            self._retranslate()

    def _step_count(self) -> int:
        return self.stack.count()

    def _go(self, index: int):
        index = max(0, min(index, self._step_count() - 1))
        self.stack.setCurrentIndex(index)
        if index == 2:
            self._run_detection()
        if index == 3:
            self._refresh_summary()
        self._refresh_nav()

    def _refresh_nav(self):
        i = self.stack.currentIndex()
        n = self._step_count()
        self.step_label.setText(t("wizard_step", current=i + 1, total=n))
        self.btn_back.setEnabled(i > 0)
        self.btn_skip.setVisible(i < n - 1)
        if i >= n - 1:
            self.btn_next.setText(t("wizard_open_app"))
        else:
            self.btn_next.setText(t("wizard_next"))

    def _on_back(self):
        self._go(self.stack.currentIndex() - 1)

    def _on_next(self):
        i = self.stack.currentIndex()
        if i == 1:
            name = self.name_edit.text().strip()
            if not name:
                self.identity_error.setText(t("wizard_name_required"))
                self.identity_error.show()
                return
            self.identity_error.hide()
        if i == 2:
            if not self._save_path.strip():
                QMessageBox.warning(self, t("info"), t("wizard_save_required"))
                return
            editions = self._resolved_editions()
            if not editions:
                reply = QMessageBox.question(
                    self,
                    t("info"),
                    t("wizard_no_civ4_continue"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
        if i >= self._step_count() - 1:
            self._finish("")
            return
        self._go(i + 1)

    def _on_skip(self):
        name = self.name_edit.text().strip()
        if not name:
            self._go(1)
            self.identity_error.setText(t("wizard_name_required"))
            self.identity_error.show()
            return
        self.config.player_name = name
        self.config.set("player_email", self.email_edit.text().strip())
        self.config.set("setup_complete", True)
        self.config.save()
        self.reject()

    def _detect_civ4(self):
        self._detected = detect_all_editions()
        self._refresh_detect_labels()
        has_exe = bool(self._resolved_editions())
        if has_exe:
            self.fxsload_check.setChecked(True)
            self.assoc_check.setChecked(True)

    def _run_detection(self):
        self._detect_civ4()
        if not self._save_path:
            self._save_path = ensure_pbem_save_path(self._save_detection_exes())
            _pbem, self._mirror_path = resolve_save_layout(self._save_path, create=False)
        self._refresh_detect_labels()
        if not self._save_prompted:
            self._save_prompted = True
            ranked = list_civ4_save_candidates(self._civ4_exe_paths(), force=True)
            if len(ranked) > 1:
                QTimer.singleShot(250, self._detect_saves)

    def _civ4_exe_paths(self) -> list[str]:
        return list(self._resolved_editions().values())

    def _save_detection_exes(self) -> list[str]:
        installs = {
            edition: {"exe_path": path, "enabled": True}
            for edition, path in self._resolved_editions().items()
        }
        preferred = self._selected_preferred_edition()
        exes = civ4_exe_paths_for_detection(installs, preferred)
        return exes or self._civ4_exe_paths()

    def _detect_saves(self):
        path = ChooseSavePathDialog.pick(
            self, self._civ4_exe_paths(), current=self._save_path,
        )
        if path:
            pbem, mirror = resolve_save_layout(path, create=True)
            self._save_path = pbem
            self._mirror_path = mirror
            self._refresh_detect_labels()

    def _resolved_editions(self) -> dict[str, str]:
        merged = dict(self._detected)
        merged.update({k: v for k, v in self._manual_exes.items() if v})
        if merged.get("dvd") and merged.get("dvd") in (merged.get("gog"), merged.get("steam")):
            merged.pop("dvd")
        if merged.get("gog") and merged.get("gog") == merged.get("steam"):
            merged.pop("gog")
        return merged

    def _refresh_preferred_combo(self):
        editions = self._resolved_editions()
        names = {
            "steam": t("civ4_edition_steam"),
            "gog": t("civ4_edition_gog"),
            "dvd": t("civ4_edition_dvd"),
        }
        current = self.preferred_combo.currentData()
        self.preferred_combo.blockSignals(True)
        self.preferred_combo.clear()
        for edition in _EDITION_ORDER:
            if edition in editions:
                self.preferred_combo.addItem(names[edition], edition)
        visible = self.preferred_combo.count() > 0
        self.preferred_label.setVisible(visible)
        self.preferred_combo.setVisible(visible)
        if visible:
            idx = self.preferred_combo.findData(current)
            if idx < 0:
                pref = self.config.preferred_edition
                idx = self.preferred_combo.findData(pref)
            self.preferred_combo.setCurrentIndex(max(0, idx))
        self.preferred_combo.blockSignals(False)

    def _refresh_detect_labels(self):
        if self._save_path:
            load_game = self._mirror_path or resolve_save_layout(self._save_path)[1]
            self.save_status.setText(t(
                "wizard_saves_found_layout",
                pbem=self._save_path,
                load_game=load_game,
            ))
        else:
            self.save_status.setText(t("wizard_saves_missing"))
        names = {
            "steam": t("civ4_edition_steam"),
            "gog": t("civ4_edition_gog"),
            "dvd": t("civ4_edition_dvd"),
        }
        resolved = self._resolved_editions()
        for edition in _EDITION_ORDER:
            path = resolved.get(edition, "")
            if path:
                self.edition_labels[edition].setText(
                    t("wizard_edition_found", name=names[edition], path=path)
                )
            else:
                self.edition_labels[edition].setText(
                    t("wizard_edition_missing", name=names[edition])
                )
        self._refresh_preferred_combo()

    def _browse_saves(self):
        folder = QFileDialog.getExistingDirectory(
            self, t("wizard_browse_saves"), self._save_path or str(Path.home())
        )
        if folder:
            self._save_path = folder
            self._mirror_path = resolve_save_layout(folder)[1]
            self._refresh_detect_labels()

    def _browse_exe(self, edition: str):
        start = self._resolved_editions().get(edition, "")
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            t("wizard_browse_exe"),
            start,
            "Civ4BeyondSword.exe (Civ4BeyondSword.exe);;Executable (*.exe);;All Files (*)",
        )
        if filepath:
            self._manual_exes[edition] = filepath
            self._refresh_detect_labels()
            self.fxsload_check.setChecked(True)
            self.assoc_check.setChecked(True)

    def _selected_preferred_edition(self) -> str:
        if self.preferred_combo.count():
            edition = self.preferred_combo.currentData()
            if edition:
                return edition
        editions = self._resolved_editions()
        for edition in _EDITION_ORDER:
            if edition in editions:
                return edition
        return ""

    def _refresh_summary(self):
        if not hasattr(self, "done_summary"):
            return
        lines = [
            t("wizard_summary_name", name=self.name_edit.text().strip() or "—"),
            t("wizard_summary_saves", path=self._save_path or "—"),
        ]
        names = {
            "steam": t("civ4_edition_steam"),
            "gog": t("civ4_edition_gog"),
            "dvd": t("civ4_edition_dvd"),
        }
        editions = self._resolved_editions()
        preferred = self._selected_preferred_edition()
        if editions:
            if preferred and preferred in editions:
                lines.append(t(
                    "wizard_summary_civ4_preferred",
                    edition=names[preferred],
                    path=editions[preferred],
                ))
            else:
                listed = ", ".join(names[e] for e in _EDITION_ORDER if e in editions)
                lines.append(t("wizard_summary_civ4", editions=listed))
        else:
            lines.append(t("wizard_summary_civ4_none"))
        if self.fxsload_check.isChecked():
            lines.append(t("wizard_summary_fxsload"))
        if self.assoc_check.isChecked() and editions:
            lines.append(t("wizard_summary_assoc"))
        self.done_summary.setText("\n".join(lines))

    def _finish(self, post_action: str = ""):
        name = self.name_edit.text().strip()
        if not name:
            self._go(1)
            self.identity_error.setText(t("wizard_name_required"))
            self.identity_error.show()
            return

        self.config.player_name = name
        self.config.set("player_email", self.email_edit.text().strip())
        if self._save_path:
            pbem, mirror = resolve_save_layout(self._save_path, create=True)
            self.config.save_path = pbem
            if self.config.get("mirror_saves", True):
                self.config.set("civ4_save_path", mirror)

        lang = self.language_combo.currentData()
        if lang:
            self.config.language = lang
            set_language(lang)

        editions = self._resolved_editions()
        installs = dict(self.config.civ4_installations)
        for edition in _EDITION_ORDER:
            cfg = dict(installs.get(edition, {}))
            if edition in editions:
                cfg["enabled"] = True
                cfg["exe_path"] = editions[edition]
            installs[edition] = cfg
        self.config.set("civ4_installations", installs)

        preferred = self._selected_preferred_edition()
        if preferred:
            self.config.set("preferred_edition", preferred)
        elif editions:
            enabled = [e for e in _EDITION_ORDER if e in editions]
            self.config.set("preferred_edition", enabled[0])

        self.config.set("direct_load_global", self.fxsload_check.isChecked())

        if self.assoc_check.isChecked() and editions:
            edition = preferred if preferred in editions else next(iter(editions))
            success, result = set_file_association(
                edition=edition,
                exe_path=editions[edition],
            )
            if success:
                logger.info("Wizard set file association: %s", result)
            else:
                logger.warning("Wizard file association failed: %s", result)

        self.config.save()
        self._post_action = post_action
        self.config.set("setup_complete", True)
        self.accept()
