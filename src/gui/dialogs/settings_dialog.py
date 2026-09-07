"""
SettingsDialog — application settings dialog with tabbed layout.
"""
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QWidget, QLabel, QLineEdit, QSpinBox, QComboBox,
    QGroupBox, QPushButton, QDialogButtonBox, QTextEdit,
    QCheckBox, QFileDialog, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt

from src.config import AppConfig
from src.i18n import t, set_language
from src.gui.styles import get_style_for_theme
from src.launcher import (
    detect_civ4_for_edition, detect_save_path, detect_steam_path,
    resolve_save_layout,
)
from src.gui.dialogs.choose_save_path_dialog import ChooseSavePathDialog

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Application settings dialog with tabbed layout."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(t("settings_title"))
        # Remove the "?" button from title bar (useless, confuses users)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        self.setMinimumSize(580, 560)
        self.resize(640, 620)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        from PySide6.QtWidgets import QTabWidget
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), t("tab_general"))
        tabs.addTab(self._create_transport_tab(), t("tab_transport"))
        tabs.addTab(self._create_notifications_tab(), t("tab_notifications"))
        tabs.addTab(self._create_security_tab(), t("tab_security"))
        layout.addWidget(tabs)

        # Buttons at the bottom (always visible)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --- Tab 1: General ---
    def _create_general_tab(self) -> QWidget:
        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Player info
        player_group = QGroupBox(t("stats_player_name"))
        player_form = QFormLayout(player_group)
        self.player_name_edit = QLineEdit(self.config.player_name)
        player_form.addRow(t("player_name"), self.player_name_edit)
        self.player_email_edit = QLineEdit(self.config.player_email)
        player_form.addRow(t("player_email"), self.player_email_edit)
        layout.addWidget(player_group)

        # Save path
        path_group = QGroupBox(t("save_path"))
        path_box = QVBoxLayout(path_group)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.config.save_path)
        path_layout.addWidget(self.path_edit)
        btn_browse = QPushButton(t("browse_save_folder"))
        btn_browse.clicked.connect(self._browse_path)
        path_layout.addWidget(btn_browse)
        btn_detect_saves = QPushButton(t("detect_civ4"))
        btn_detect_saves.clicked.connect(self._detect_save_path)
        path_layout.addWidget(btn_detect_saves)
        path_box.addLayout(path_layout)

        self.save_path_hint = QLabel(t("save_path_hint"))
        self.save_path_hint.setWordWrap(True)
        self.save_path_hint.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        path_box.addWidget(self.save_path_hint)

        self.mirror_saves_check = QCheckBox(t("mirror_saves"))
        self.mirror_saves_check.setChecked(self.config.get("mirror_saves", True))
        self.mirror_saves_check.toggled.connect(self._on_mirror_toggled)
        path_box.addWidget(self.mirror_saves_check)

        self.mirror_hint = QLabel(t("mirror_saves_hint"))
        self.mirror_hint.setWordWrap(True)
        self.mirror_hint.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        path_box.addWidget(self.mirror_hint)

        civ4_row = QHBoxLayout()
        self.civ4_path_edit = QLineEdit(self.config.get("civ4_save_path", ""))
        self.civ4_path_edit.setPlaceholderText(t("civ4_save_path_placeholder"))
        civ4_row.addWidget(self.civ4_path_edit)
        self.btn_browse_civ4_saves = QPushButton(t("browse_save_folder"))
        self.btn_browse_civ4_saves.clicked.connect(self._browse_civ4_save_path)
        civ4_row.addWidget(self.btn_browse_civ4_saves)
        self.btn_detect_civ4_saves = QPushButton(t("detect_civ4"))
        self.btn_detect_civ4_saves.clicked.connect(self._detect_civ4_save_path)
        civ4_row.addWidget(self.btn_detect_civ4_saves)
        self.btn_use_civ4_as_primary = QPushButton(t("use_civ4_as_primary"))
        self.btn_use_civ4_as_primary.clicked.connect(self._use_civ4_as_primary)
        civ4_row.addWidget(self.btn_use_civ4_as_primary)
        path_box.addLayout(civ4_row)
        layout.addWidget(path_group)
        self._on_mirror_toggled(self.mirror_saves_check.isChecked())

        # Check interval
        interval_group = QGroupBox(t("check_interval"))
        interval_form = QFormLayout(interval_group)
        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 60)
        self.check_interval.setValue(self.config.check_interval_minutes)
        self.check_interval.setSuffix(" min")
        interval_form.addRow(t("check_interval"), self.check_interval)
        layout.addWidget(interval_group)

        # Appearance & Language
        appearance_group = QGroupBox(t("settings_appearance"))
        appearance_form = QFormLayout(appearance_group)
        self.dark_mode_check = QCheckBox(t("dark_mode"))
        self.dark_mode_check.setChecked(self.config.get("dark_mode", True))
        appearance_form.addRow(self.dark_mode_check)

        self.auto_send_check = QCheckBox(t("auto_send"))
        self.auto_send_check.setChecked(self.config.get("auto_send", False))
        appearance_form.addRow(self.auto_send_check)

        self.autostart_check = QCheckBox(t("autostart"))
        self.autostart_check.setChecked(self.config.get("autostart", False))
        appearance_form.addRow(self.autostart_check)
        autostart_hint = QLabel(t("autostart_hint"))
        autostart_hint.setWordWrap(True)
        autostart_hint.setStyleSheet("font-size: 9pt; color: #9e9e9e;")
        appearance_form.addRow(autostart_hint)

        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItem("Polski", "pl")
        self.language_combo.addItem("English", "en")
        current_lang = self.config.language
        idx = 0 if current_lang == "pl" else 1
        self.language_combo.setCurrentIndex(idx)
        appearance_form.addRow(t("language"), self.language_combo)

        self.btn_setup_wizard = QPushButton(t("wizard_rerun"))
        self.btn_setup_wizard.clicked.connect(self._rerun_setup_wizard)
        appearance_form.addRow(self.btn_setup_wizard)

        layout.addWidget(appearance_group)

        # ---- Civ4 BTS installations (multi-edition) ----
        installs_group = QGroupBox(t("civ4_installations_group"))
        installs_layout = QVBoxLayout(installs_group)
        installs_layout.setSpacing(6)

        installs = self.config.civ4_installations
        self._edition_widgets = {}  # edition -> dict of widgets

        EDITION_LABELS = {
            "steam": t("civ4_edition_steam"),
            "gog":   t("civ4_edition_gog"),
            "dvd":   t("civ4_edition_dvd"),
        }

        for edition in ("steam", "gog", "dvd"):
            cfg = installs.get(edition, {})
            ed_group = QGroupBox(EDITION_LABELS[edition])
            ed_form = QFormLayout(ed_group)
            ed_form.setSpacing(4)

            # Enabled checkbox
            enabled_cb = QCheckBox(t("edition_enabled"))
            enabled_cb.setChecked(cfg.get("enabled", False))
            ed_form.addRow(enabled_cb)

            # exe path row -- disabled until checkbox ticked
            exe_layout = QHBoxLayout()
            exe_edit = QLineEdit(cfg.get("exe_path", ""))
            exe_edit.setPlaceholderText("C:\\...\\Civ4BeyondSword.exe")
            exe_edit.setEnabled(cfg.get("enabled", False))
            exe_layout.addWidget(exe_edit)

            btn_browse_ed = QPushButton(t("browse"))
            btn_browse_ed.setEnabled(cfg.get("enabled", False))
            btn_browse_ed.clicked.connect(
                lambda checked, e=exe_edit: self._browse_edition_exe(e))
            exe_layout.addWidget(btn_browse_ed)

            btn_detect_ed = QPushButton(t("detect_for_edition"))
            btn_detect_ed.setEnabled(cfg.get("enabled", False))
            btn_detect_ed.clicked.connect(
                lambda checked, ed=edition, e=exe_edit: self._detect_edition_exe(ed, e))
            exe_layout.addWidget(btn_detect_ed)

            ed_form.addRow(t("edition_exe_path"), exe_layout)

            # Wire checkbox -> enable/disable path fields
            def _toggle_edition(state, e=exe_edit, bb=btn_browse_ed, bd=btn_detect_ed):
                e.setEnabled(bool(state))
                bb.setEnabled(bool(state))
                bd.setEnabled(bool(state))
            enabled_cb.stateChanged.connect(_toggle_edition)

            installs_layout.addWidget(ed_group)

            self._edition_widgets[edition] = {
                "enabled": enabled_cb,
                "exe_edit": exe_edit,
                "direct_cb": None,
                "steam_exe_edit": None,
                "app_id_edit": None,
            }

        # Global direct load checkbox -- applies to all editions
        self.direct_load_global_check = QCheckBox(t("edition_direct_load"))
        self.direct_load_global_check.setChecked(
            self.config.get("direct_load_global", False))
        installs_layout.addWidget(self.direct_load_global_check)

        self.auto_launch_check = QCheckBox(t("auto_launch"))
        self.auto_launch_check.setChecked(self.config.get("auto_launch", False))
        installs_layout.addWidget(self.auto_launch_check)
        auto_launch_hint = QLabel(t("auto_launch_hint"))
        auto_launch_hint.setWordWrap(True)
        auto_launch_hint.setObjectName("hintLabel")
        installs_layout.addWidget(auto_launch_hint)

        # Preferred edition when multiple enabled
        pref_layout = QHBoxLayout()
        pref_layout.addWidget(QLabel(t("preferred_edition")))
        self.preferred_edition_combo = QComboBox()
        self.preferred_edition_combo.addItem(t("preferred_edition_ask"), "")
        self.preferred_edition_combo.addItem(t("civ4_edition_steam"), "steam")
        self.preferred_edition_combo.addItem(t("civ4_edition_gog"), "gog")
        self.preferred_edition_combo.addItem(t("civ4_edition_dvd"), "dvd")
        pref_val = self.config.preferred_edition
        pref_idx = self.preferred_edition_combo.findData(pref_val)
        self.preferred_edition_combo.setCurrentIndex(pref_idx if pref_idx >= 0 else 0)
        pref_layout.addWidget(self.preferred_edition_combo)
        pref_hint = QLabel(t("preferred_edition_hint"))
        pref_hint.setWordWrap(True)
        pref_hint.setObjectName("hintLabel")
        pref_layout.addWidget(pref_hint)
        pref_layout.addStretch()
        installs_layout.addLayout(pref_layout)

        # --- File association ---
        from src.launcher import get_current_file_association
        assoc_group = QGroupBox(t("file_assoc_group"))
        assoc_layout = QVBoxLayout(assoc_group)

        current_assoc = get_current_file_association() or t("file_assoc_none")
        assoc_current_lbl = QLabel(f"{t('file_assoc_current')} {current_assoc}")
        assoc_current_lbl.setWordWrap(True)
        assoc_current_lbl.setStyleSheet("font-size: 8pt; color: #9e9e9e;")
        assoc_layout.addWidget(assoc_current_lbl)

        assoc_hint = QLabel(t("file_assoc_set"))
        assoc_hint.setStyleSheet("font-size: 9pt;")
        assoc_layout.addWidget(assoc_hint)

        assoc_btn_row = QHBoxLayout()
        ASSOC_COLORS = {"steam": "#1b5e20", "gog": "#0d47a1", "dvd": "#4a148c"}
        for ed in ("steam", "gog", "dvd"):
            lbl = EDITION_LABELS[ed]
            btn_a = QPushButton(lbl)
            btn_a.setMinimumHeight(36)
            c = ASSOC_COLORS[ed]
            btn_a.setStyleSheet(
                f"background-color: {c}; color: white; font-weight: bold; border-radius: 4px;")
            btn_a.clicked.connect(
                lambda checked, e=ed: self._set_file_association(e))
            assoc_btn_row.addWidget(btn_a)
        assoc_layout.addLayout(assoc_btn_row)

        installs_layout.addWidget(assoc_group)
        layout.addWidget(installs_group)

        layout.addStretch()
        scroll.setWidget(tab)
        return scroll

    def _browse_edition_exe(self, target_edit):
        """Browse for exe and set into target_edit."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik .exe", target_edit.text(),
            "Executable (*.exe);;All Files (*)"
        )
        if filepath:
            target_edit.setText(filepath)

    def _detect_edition_exe(self, edition: str, target_edit):
        """Auto-detect Civ4 exe for a specific edition."""
        detected = detect_civ4_for_edition(edition)
        if detected:
            target_edit.setText(detected)
            QMessageBox.information(self, "OK", t("civ4_detected", path=detected))
        else:
            QMessageBox.information(self, t("info"), t("civ4_not_detected"))

    def _detect_steam_into_widget(self):
        """Auto-detect Steam.exe and fill into Steam edition's steam_exe field."""
        detected = detect_steam_path()
        if detected:
            widgets = self._edition_widgets.get("steam", {})
            if widgets.get("steam_exe_edit"):
                widgets["steam_exe_edit"].setText(detected)
            QMessageBox.information(self, "OK", t("steam_detected", path=detected))
        else:
            QMessageBox.information(self, t("info"), t("steam_not_detected"))

    def _set_file_association(self, edition: str):
        """Set Windows file association for .CivBeyondSwordSave for the given edition."""
        from src.launcher import set_file_association, get_current_file_association

        widgets = self._edition_widgets.get(edition, {})
        exe_path = widgets["exe_edit"].text().strip() if widgets.get("exe_edit") else ""
        steam_exe = ""
        app_id = "8800"
        if edition == "steam":
            steam_exe = widgets["steam_exe_edit"].text().strip() if widgets.get("steam_exe_edit") else ""
            app_id = widgets["app_id_edit"].text().strip() if widgets.get("app_id_edit") else "8800"
        success, result = set_file_association(
            edition=edition,
            exe_path=exe_path,
            steam_path=steam_exe,
            steam_app_id=app_id or "8800",
        )
        if success:
            QMessageBox.information(self, "OK", t("file_assoc_ok", cmd=result))
        else:
            msg = t(result) if result in (
                "civ4_not_found", "steam_not_found",
                "registry_windows_only", "registry_permission_error"
            ) else t("file_assoc_error", error=result)
            QMessageBox.warning(self, t("error"), msg)

    # --- Tab 2: Transport ---
    def _create_transport_tab(self) -> QWidget:
        from PySide6.QtWidgets import QScrollArea

        # If config is locked, show lock message instead of form
        if not self.config.is_unlocked:
            locked_tab = QWidget()
            locked_layout = QVBoxLayout(locked_tab)
            locked_layout.addStretch()
            lock_label = QLabel(f"\U0001f512 {t('transport_locked')}")
            lock_label.setAlignment(Qt.AlignCenter)
            lock_label.setStyleSheet("font-size: 11pt; color: #ff9800; padding: 40px;")
            locked_layout.addWidget(lock_label)
            locked_layout.addStretch()
            return locked_tab

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        tc = self.config.transport_config

        # Transport type selector
        type_group = QGroupBox(t("transport_method"))
        type_form = QFormLayout(type_group)
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.transport_type.currentTextChanged.connect(self._on_transport_type_changed)
        type_form.addRow(t("transport_type_label"), self.transport_type)

        self.ssl_ignore_check = QCheckBox(t("ssl_ignore"))
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", False))
        type_form.addRow(self.ssl_ignore_check)

        layout.addWidget(type_group)

        # File-based transport settings (FTP/SFTP/WebDAV)
        self.file_transport_group = QGroupBox(t("file_transport_group"))
        file_form = QFormLayout(self.file_transport_group)

        self.transport_host = QLineEdit(tc.get("host", ""))
        self.transport_host.setPlaceholderText("np. ftp.mojserwer.pl")
        file_form.addRow(t("field_host"), self.transport_host)

        self.transport_port = QSpinBox()
        self.transport_port.setRange(1, 65535)
        self.transport_port.setValue(tc.get("port", 21))
        file_form.addRow(t("field_port"), self.transport_port)

        self.transport_user = QLineEdit(tc.get("username", ""))
        file_form.addRow(t("field_login"), self.transport_user)

        self.transport_pass = QLineEdit(tc.get("password", ""))
        self.transport_pass.setEchoMode(QLineEdit.Password)
        file_form.addRow(t("field_password"), self.transport_pass)

        self.transport_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        file_form.addRow(t("field_remote_dir"), self.transport_dir)

        layout.addWidget(self.file_transport_group)

        # Email transport settings (SMTP + IMAP/POP3)
        self.email_transport_group = QGroupBox(t("email_transport_group"))
        email_layout = QVBoxLayout(self.email_transport_group)
        email_layout.setSpacing(8)

        ec = tc.get("email", {})

        # --- Autodiscover ---
        autodiscover_group = QGroupBox(t("email_autodiscover"))
        ad_layout = QHBoxLayout(autodiscover_group)
        self.et_autodiscover_email = QLineEdit()
        self.et_autodiscover_email.setPlaceholderText("twoj@email.com")
        ad_layout.addWidget(self.et_autodiscover_email)
        btn_autodiscover = QPushButton(t("email_autodiscover_btn"))
        btn_autodiscover.clicked.connect(self._run_autodiscover)
        ad_layout.addWidget(btn_autodiscover)
        email_layout.addWidget(autodiscover_group)

        # Autodiscover status label
        self.et_autodiscover_status = QLabel("")
        self.et_autodiscover_status.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        self.et_autodiscover_status.setWordWrap(True)
        email_layout.addWidget(self.et_autodiscover_status)

        # --- Preset selector ---
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel(t("email_preset")))
        self.et_preset_combo = QComboBox()
        self.et_preset_combo.addItem(t("email_preset_custom"), "")
        self.et_preset_combo.addItem("Gmail", "gmail")
        self.et_preset_combo.addItem("Outlook / Hotmail / Live", "outlook")
        self.et_preset_combo.addItem("Yahoo Mail", "yahoo")
        self.et_preset_combo.addItem("iCloud Mail", "icloud")
        self.et_preset_combo.currentIndexChanged.connect(self._apply_email_preset)
        preset_layout.addWidget(self.et_preset_combo)
        preset_layout.addStretch()
        email_layout.addLayout(preset_layout)

        # App password hint
        self.et_apppwd_hint = QLabel(t("email_app_password_hint"))
        self.et_apppwd_hint.setWordWrap(True)
        self.et_apppwd_hint.setStyleSheet("color: #ff9800; font-size: 8pt;")
        self.et_apppwd_hint.setVisible(False)
        email_layout.addWidget(self.et_apppwd_hint)

        # --- Mode & shared mailbox ---
        mode_form = QFormLayout()
        mode_form.setSpacing(6)

        self.et_mode = QComboBox()
        self.et_mode.addItems(["shared", "individual"])
        self.et_mode.setCurrentText(ec.get("mode", "shared"))
        mode_form.addRow(t("field_mode"), self.et_mode)

        self.et_shared_email = QLineEdit(ec.get("shared_email", ""))
        self.et_shared_email.setPlaceholderText("civ4pbem@example.com")
        mode_form.addRow(t("field_shared_mailbox"), self.et_shared_email)

        self.et_from_address = QLineEdit(ec.get("from_address", ""))
        self.et_from_address.setPlaceholderText(t("notification_empty_hint"))
        mode_form.addRow(t("field_from"), self.et_from_address)

        email_layout.addLayout(mode_form)

        # --- SMTP ---
        smtp_box = QGroupBox("SMTP")
        smtp_form = QFormLayout(smtp_box)
        smtp_form.setSpacing(5)

        self.et_smtp_host = QLineEdit(ec.get("smtp_host", ""))
        self.et_smtp_host.setPlaceholderText("smtp.gmail.com")
        smtp_form.addRow(t("field_host"), self.et_smtp_host)

        smtp_port_sec = QHBoxLayout()
        self.et_smtp_port = QSpinBox()
        self.et_smtp_port.setRange(1, 65535)
        self.et_smtp_port.setValue(ec.get("smtp_port", 587))
        smtp_port_sec.addWidget(self.et_smtp_port)
        self.et_smtp_security = QComboBox()
        self.et_smtp_security.addItems(["STARTTLS", "SSL", t("security_none")])
        self.et_smtp_security.setCurrentText(ec.get("smtp_security", "STARTTLS"))
        smtp_port_sec.addWidget(self.et_smtp_security)
        smtp_form.addRow(t("field_port") + " / " + t("security_label"), smtp_port_sec)

        self.et_smtp_user = QLineEdit(ec.get("smtp_user", ""))
        smtp_form.addRow(t("field_login"), self.et_smtp_user)

        self.et_smtp_pass = QLineEdit(ec.get("smtp_password", ""))
        self.et_smtp_pass.setEchoMode(QLineEdit.Password)
        smtp_form.addRow(t("field_password"), self.et_smtp_pass)

        email_layout.addWidget(smtp_box)

        # --- Incoming: IMAP or POP3 ---
        incoming_box = QGroupBox(t("email_incoming"))
        incoming_layout = QVBoxLayout(incoming_box)

        # Protocol selector
        proto_layout = QHBoxLayout()
        proto_layout.addWidget(QLabel(t("email_protocol")))
        self.et_incoming_proto = QComboBox()
        self.et_incoming_proto.addItem("IMAP " + t("email_imap_recommended"), "imap")
        self.et_incoming_proto.addItem("POP3", "pop3")
        proto = ec.get("incoming_protocol", "imap")
        self.et_incoming_proto.setCurrentIndex(0 if proto == "imap" else 1)
        self.et_incoming_proto.currentIndexChanged.connect(self._on_incoming_proto_changed)
        proto_layout.addWidget(self.et_incoming_proto)
        proto_layout.addStretch()
        incoming_layout.addLayout(proto_layout)

        # IMAP fields
        self.et_imap_widget = QWidget()
        imap_form = QFormLayout(self.et_imap_widget)
        imap_form.setSpacing(5)
        imap_form.setContentsMargins(0, 0, 0, 0)

        self.et_imap_host = QLineEdit(ec.get("imap_host", ""))
        self.et_imap_host.setPlaceholderText("imap.gmail.com")
        imap_form.addRow(t("field_host"), self.et_imap_host)

        imap_port_sec = QHBoxLayout()
        self.et_imap_port = QSpinBox()
        self.et_imap_port.setRange(1, 65535)
        self.et_imap_port.setValue(ec.get("imap_port", 993))
        imap_port_sec.addWidget(self.et_imap_port)
        self.et_imap_security = QComboBox()
        self.et_imap_security.addItems(["SSL", "STARTTLS", t("security_none")])
        self.et_imap_security.setCurrentText(ec.get("imap_security", "SSL"))
        imap_port_sec.addWidget(self.et_imap_security)
        imap_form.addRow(t("field_port") + " / " + t("security_label"), imap_port_sec)

        self.et_imap_user = QLineEdit(ec.get("imap_user", ""))
        imap_form.addRow(t("field_login"), self.et_imap_user)

        self.et_imap_pass = QLineEdit(ec.get("imap_password", ""))
        self.et_imap_pass.setEchoMode(QLineEdit.Password)
        imap_form.addRow(t("field_password"), self.et_imap_pass)

        incoming_layout.addWidget(self.et_imap_widget)

        # POP3 fields
        self.et_pop3_widget = QWidget()
        pop3_form = QFormLayout(self.et_pop3_widget)
        pop3_form.setSpacing(5)
        pop3_form.setContentsMargins(0, 0, 0, 0)

        self.et_pop3_host = QLineEdit(ec.get("pop3_host", ""))
        self.et_pop3_host.setPlaceholderText("pop3.example.com")
        pop3_form.addRow(t("field_host"), self.et_pop3_host)

        pop3_port_sec = QHBoxLayout()
        self.et_pop3_port = QSpinBox()
        self.et_pop3_port.setRange(1, 65535)
        self.et_pop3_port.setValue(ec.get("pop3_port", 995))
        pop3_port_sec.addWidget(self.et_pop3_port)
        self.et_pop3_security = QComboBox()
        self.et_pop3_security.addItems(["SSL", "STARTTLS", t("security_none")])
        self.et_pop3_security.setCurrentText(ec.get("pop3_security", "SSL"))
        pop3_port_sec.addWidget(self.et_pop3_security)
        pop3_form.addRow(t("field_port") + " / " + t("security_label"), pop3_port_sec)

        incoming_layout.addWidget(self.et_pop3_widget)

        # Delete after download
        self.et_delete_after_download = QCheckBox(t("email_delete_after_download"))
        self.et_delete_after_download.setChecked(ec.get("delete_after_download", False))
        incoming_layout.addWidget(self.et_delete_after_download)

        email_layout.addWidget(incoming_box)

        # Init protocol visibility
        self._on_incoming_proto_changed(self.et_incoming_proto.currentIndex())

        et_warning = QLabel(f"\u26a0 {t('email_warning')}")
        et_warning.setStyleSheet("color: #ff9800; font-size: 9pt;")
        email_layout.addWidget(et_warning)

        layout.addWidget(self.email_transport_group)

        # Show/hide based on current type
        self._on_transport_type_changed(self.transport_type.currentText())

        layout.addStretch()
        scroll.setWidget(tab)
        return scroll

    # --- Tab 3: Notifications ---
    def _create_notifications_tab(self) -> QWidget:
        # If config is locked, show lock message
        if not self.config.is_unlocked:
            locked_tab = QWidget()
            locked_layout = QVBoxLayout(locked_tab)
            locked_layout.addStretch()
            lock_label = QLabel(f"\U0001f512 {t('smtp_locked')}")
            lock_label.setAlignment(Qt.AlignCenter)
            lock_label.setStyleSheet("font-size: 11pt; color: #ff9800; padding: 40px;")
            locked_layout.addWidget(lock_label)
            locked_layout.addStretch()
            return locked_tab

        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        sc = self.config.smtp_config

        # --- Master switch ---
        self.notifications_enabled_check = QCheckBox(t("notifications_master_switch"))
        self.notifications_enabled_check.setChecked(
            self.config.get("notifications_enabled", True))
        self.notifications_enabled_check.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(self.notifications_enabled_check)

        # Container that gets enabled/disabled by master switch
        notif_container = QWidget()
        notif_layout = QVBoxLayout(notif_container)
        notif_layout.setContentsMargins(0, 0, 0, 0)
        notif_layout.setSpacing(10)

        # --- Channels ---
        channels_group = QGroupBox(t("tab_notifications"))
        channels_layout = QVBoxLayout(channels_group)

        self.notify_via_smtp_check = QCheckBox(t("notify_via_smtp"))
        self.notify_via_smtp_check.setChecked(self.config.get("notify_via_smtp", False))
        channels_layout.addWidget(self.notify_via_smtp_check)

        self.notify_via_app_check = QCheckBox(t("notify_via_app"))
        self.notify_via_app_check.setChecked(self.config.get("notify_via_app", True))
        channels_layout.addWidget(self.notify_via_app_check)

        app_hint = QLabel(f"  \u2139 {t('notify_via_app_hint')}")
        app_hint.setWordWrap(True)
        app_hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        channels_layout.addWidget(app_hint)

        notif_layout.addWidget(channels_group)

        # --- SMTP settings (shown only when SMTP channel enabled) ---
        self.smtp_settings_group = QGroupBox(t("notifications_group"))
        smtp_layout = QVBoxLayout(self.smtp_settings_group)
        smtp_layout.setSpacing(8)

        # Source selector: same as transport email OR custom SMTP
        self.smtp_source_combo = QComboBox()
        self.smtp_source_combo.addItem(t("notif_smtp_same_as_transport"), "transport")
        self.smtp_source_combo.addItem(t("notif_smtp_custom"), "custom")
        # Determine current source: if smtp host is set and differs from transport, it's custom
        tc = self.config.transport_config
        ec = tc.get("email", {})
        current_smtp_host = sc.get("host", "")
        transport_smtp_host = ec.get("smtp_host", "")
        is_custom = bool(current_smtp_host and current_smtp_host != transport_smtp_host)
        self.smtp_source_combo.setCurrentIndex(1 if is_custom else 0)
        smtp_layout.addWidget(self.smtp_source_combo)

        # Hint for "same as transport" mode
        self.smtp_same_hint = QLabel(f"  \u2139 {t('notif_smtp_same_hint')}")
        self.smtp_same_hint.setWordWrap(True)
        self.smtp_same_hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
        smtp_layout.addWidget(self.smtp_same_hint)

        # Custom SMTP fields (hidden when using transport)
        self.smtp_custom_widget = QWidget()
        smtp_form = QFormLayout(self.smtp_custom_widget)
        smtp_form.setSpacing(8)
        smtp_form.setContentsMargins(0, 8, 0, 0)

        self.smtp_host = QLineEdit(sc.get("host", ""))
        self.smtp_host.setPlaceholderText("np. smtp.gmail.com")
        smtp_form.addRow("Host SMTP:", self.smtp_host)

        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(sc.get("port", 587))
        smtp_form.addRow(t("field_port"), self.smtp_port)

        self.smtp_user = QLineEdit(sc.get("username", ""))
        self.smtp_user.setPlaceholderText(t("notification_empty_hint"))
        smtp_form.addRow(t("field_login"), self.smtp_user)

        self.smtp_pass = QLineEdit(sc.get("password", ""))
        self.smtp_pass.setEchoMode(QLineEdit.Password)
        self.smtp_pass.setPlaceholderText(t("notification_empty_hint"))
        smtp_form.addRow(t("field_password"), self.smtp_pass)

        self.smtp_from = QLineEdit(sc.get("from_address", ""))
        self.smtp_from.setPlaceholderText(t("notification_empty_hint"))
        smtp_form.addRow(t("field_from"), self.smtp_from)

        smtp_layout.addWidget(self.smtp_custom_widget)

        notif_layout.addWidget(self.smtp_settings_group)

        # Wire source combo -> show/hide custom fields
        def _toggle_smtp_source(index):
            is_transport = self.smtp_source_combo.currentData() == "transport"
            self.smtp_custom_widget.setVisible(not is_transport)
            self.smtp_same_hint.setVisible(is_transport)
        self.smtp_source_combo.currentIndexChanged.connect(_toggle_smtp_source)
        _toggle_smtp_source(self.smtp_source_combo.currentIndex())

        # --- Message templates ---
        templates_group = QGroupBox(t("notif_templates_group"))
        tpl_layout = QVBoxLayout(templates_group)
        tpl_layout.setSpacing(8)

        VARS = ["{game}", "{turn}", "{from_player}", "{to_player}"]

        def _make_var_buttons(target_widget):
            """Return a row of variable-insert buttons for a QLineEdit or QTextEdit."""
            row = QHBoxLayout()
            hint = QLabel(t("notif_template_hint"))
            hint.setStyleSheet("color: #9e9e9e; font-size: 8pt;")
            row.addWidget(hint)
            for var in VARS:
                btn = QPushButton(var)
                btn.setMaximumWidth(90)
                btn.setStyleSheet("font-size: 8pt; padding: 2px 4px;")
                if isinstance(target_widget, QTextEdit):
                    btn.clicked.connect(
                        lambda checked, v=var, w=target_widget:
                        w.insertPlainText(v))
                else:
                    btn.clicked.connect(
                        lambda checked, v=var, w=target_widget:
                        w.insert(v))
                row.addWidget(btn)
            row.addStretch()
            return row

        # Turn subject
        tpl_layout.addWidget(QLabel(t("notif_subject_template")))
        self.smtp_subject_template = QLineEdit(sc.get("subject_template", ""))
        self.smtp_subject_template.setPlaceholderText(
            "[Civ4 PBEM] {game} - Your turn! (Turn {turn})")
        tpl_layout.addWidget(self.smtp_subject_template)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_subject_template))

        # Turn body
        tpl_layout.addWidget(QLabel(t("notif_body_template")))
        self.smtp_body_template = QTextEdit()
        self.smtp_body_template.setPlainText(sc.get("body_template", ""))
        self.smtp_body_template.setPlaceholderText(
            "Hi {to_player}!\n\n{from_player} finished turn {turn} in {game}.\nYour turn!")
        self.smtp_body_template.setFixedHeight(80)
        tpl_layout.addWidget(self.smtp_body_template)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_body_template))

        # Reminder subject
        tpl_layout.addWidget(QLabel(t("notif_reminder_subject_template")))
        self.smtp_reminder_subject = QLineEdit(sc.get("reminder_subject_template", ""))
        self.smtp_reminder_subject.setPlaceholderText(
            "[Civ4 PBEM] {game} - Reminder: your turn! (Turn {turn})")
        tpl_layout.addWidget(self.smtp_reminder_subject)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_reminder_subject))

        # Reminder body
        tpl_layout.addWidget(QLabel(t("notif_reminder_body_template")))
        self.smtp_reminder_body = QTextEdit()
        self.smtp_reminder_body.setPlainText(sc.get("reminder_body_template", ""))
        self.smtp_reminder_body.setPlaceholderText(
            "Hi {to_player}!\n\nJust a reminder -- it's your turn in {game}!\nTurn: {turn}")
        self.smtp_reminder_body.setFixedHeight(80)
        tpl_layout.addWidget(self.smtp_reminder_body)
        tpl_layout.addLayout(_make_var_buttons(self.smtp_reminder_body))

        notif_layout.addWidget(templates_group)

        # --- Auto-reminder ---
        reminder_group = QGroupBox(t("reminder_auto_group"))
        reminder_form = QFormLayout(reminder_group)
        reminder_form.setSpacing(8)

        self.reminder_auto_check = QCheckBox(t("reminder_auto_enabled"))
        self.reminder_auto_check.setChecked(self.config.get("reminder_auto_enabled", False))
        reminder_form.addRow(self.reminder_auto_check)

        self.reminder_auto_days = QSpinBox()
        self.reminder_auto_days.setRange(1, 30)
        self.reminder_auto_days.setValue(self.config.get("reminder_auto_days", 2))
        self.reminder_auto_days.setSuffix(
            " dni" if self.config.language == "pl" else " days")
        reminder_form.addRow(t("reminder_auto_days"), self.reminder_auto_days)

        notif_layout.addWidget(reminder_group)
        notif_layout.addStretch()

        layout.addWidget(notif_container)

        # Wire master switch -> enable/disable container
        def _toggle_notif(state):
            notif_container.setEnabled(bool(state))
        self.notifications_enabled_check.stateChanged.connect(_toggle_notif)
        notif_container.setEnabled(self.notifications_enabled_check.isChecked())

        # Wire SMTP channel -> show/hide SMTP settings + templates
        def _toggle_smtp(state):
            self.smtp_settings_group.setVisible(bool(state))
            templates_group.setVisible(bool(state))
        self.notify_via_smtp_check.stateChanged.connect(_toggle_smtp)
        _toggle_smtp(self.notify_via_smtp_check.isChecked())

        scroll.setWidget(tab)
        return scroll

    # --- Tab 4: Security ---
    def _create_security_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Status
        status_group = QGroupBox(t("tab_security"))
        status_layout = QVBoxLayout(status_group)

        if self.config.has_master_password:
            if self.config.is_unlocked:
                status_label = QLabel(f"\U0001f513 {t('security_status_unlocked')}")
                status_label.setStyleSheet("color: #66bb6a; font-size: 10pt;")
            else:
                status_label = QLabel(f"\U0001f512 {t('security_status_locked')}")
                status_label.setStyleSheet("color: #ff9800; font-size: 10pt;")
        else:
            status_label = QLabel(f"\u26a0 {t('security_no_password')}")
            status_label.setStyleSheet("color: #ef5350; font-size: 10pt;")

        status_layout.addWidget(status_label)
        layout.addWidget(status_group)

        # Set / Change password
        password_group = QGroupBox(t("master_password_group"))
        password_form = QFormLayout(password_group)

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText(t("new_password_placeholder"))
        password_form.addRow(t("new_password"), self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText(t("confirm_password_placeholder"))
        password_form.addRow(t("confirm_password"), self.confirm_password_edit)

        btn_set_password = QPushButton(t("set_password_btn"))
        btn_set_password.setStyleSheet("color: #ff9800; border-color: #ff9800; font-weight: bold;")
        btn_set_password.clicked.connect(self._on_set_master_password)
        password_form.addRow(btn_set_password)

        layout.addWidget(password_group)

        # Info
        info_label = QLabel(t("security_info"))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #9e9e9e; font-size: 9pt; padding: 8px;")
        layout.addWidget(info_label)

        layout.addStretch()
        return tab

    def _on_set_master_password(self):
        """Set or change the master password."""
        new_pass = self.new_password_edit.text()
        confirm = self.confirm_password_edit.text()

        if not new_pass:
            QMessageBox.warning(self, t("error"), t("password_empty"))
            return

        if new_pass != confirm:
            QMessageBox.warning(self, t("error"), t("password_mismatch"))
            return

        if self.config.has_master_password and not self.config.is_unlocked:
            QMessageBox.warning(self, t("error"), t("password_locked_error"))
            return

        self.config.set_master_password(new_pass)
        QMessageBox.information(self, "OK", t("password_set_ok"))
        self.new_password_edit.clear()
        self.confirm_password_edit.clear()

    # --- Logic ---
    def _on_transport_type_changed(self, transport_type: str):
        """Show/hide transport panels based on selected type."""
        self.file_transport_group.setVisible(transport_type in ("ftp", "sftp", "webdav"))
        self.email_transport_group.setVisible(transport_type == "email")

    def _on_incoming_proto_changed(self, index: int):
        """Show IMAP or POP3 fields based on selected protocol."""
        is_imap = (self.et_incoming_proto.currentData() == "imap")
        self.et_imap_widget.setVisible(is_imap)
        self.et_pop3_widget.setVisible(not is_imap)

    def _run_autodiscover(self):
        """Run autodiscovery for the entered email address."""
        from src.transport.autodiscover import discover
        from PySide6.QtWidgets import QApplication
        email_addr = self.et_autodiscover_email.text().strip()
        if not email_addr or "@" not in email_addr:
            self.et_autodiscover_status.setText(t("email_autodiscover_invalid"))
            return

        self.et_autodiscover_status.setText(t("email_autodiscover_searching"))
        QApplication.processEvents()

        result = discover(email_addr)
        if result and result.is_complete:
            # Fill SMTP fields
            self.et_smtp_host.setText(result.smtp.host)
            self.et_smtp_port.setValue(result.smtp.port)
            sec_idx = self.et_smtp_security.findText(result.smtp.security)
            if sec_idx >= 0:
                self.et_smtp_security.setCurrentIndex(sec_idx)

            # Fill IMAP fields
            self.et_imap_host.setText(result.imap.host)
            self.et_imap_port.setValue(result.imap.port)
            sec_idx = self.et_imap_security.findText(result.imap.security)
            if sec_idx >= 0:
                self.et_imap_security.setCurrentIndex(sec_idx)

            # Set IMAP protocol
            self.et_incoming_proto.setCurrentIndex(0)
            self._on_incoming_proto_changed(0)

            self.et_autodiscover_status.setText(
                t("email_autodiscover_ok", source=result.source,
                  smtp=str(result.smtp), imap=str(result.imap)))
            self.et_autodiscover_status.setStyleSheet("color: #66bb6a; font-size: 8pt;")
        elif result:
            # Partial result
            if result.smtp:
                self.et_smtp_host.setText(result.smtp.host)
                self.et_smtp_port.setValue(result.smtp.port)
            if result.imap:
                self.et_imap_host.setText(result.imap.host)
                self.et_imap_port.setValue(result.imap.port)
            self.et_autodiscover_status.setText(
                t("email_autodiscover_partial", source=result.source))
            self.et_autodiscover_status.setStyleSheet("color: #ff9800; font-size: 8pt;")
        else:
            self.et_autodiscover_status.setText(t("email_autodiscover_failed"))
            self.et_autodiscover_status.setStyleSheet("color: #ef5350; font-size: 8pt;")

    # Preset data: smtp_host, smtp_port, smtp_security, imap_host, imap_port, imap_security
    _EMAIL_PRESETS = {
        "gmail": ("smtp.gmail.com", 587, "STARTTLS", "imap.gmail.com", 993, "SSL"),
        "outlook": ("smtp-mail.outlook.com", 587, "STARTTLS", "imap-mail.outlook.com", 993, "SSL"),
        "yahoo": ("smtp.mail.yahoo.com", 587, "STARTTLS", "imap.mail.yahoo.com", 993, "SSL"),
        "icloud": ("smtp.mail.me.com", 587, "STARTTLS", "imap.mail.me.com", 993, "SSL"),
    }
    _APP_PASSWORD_PROVIDERS = {"gmail", "yahoo", "icloud"}

    def _apply_email_preset(self, index: int):
        """Fill SMTP/IMAP fields from selected preset."""
        key = self.et_preset_combo.currentData()
        if not key or key not in self._EMAIL_PRESETS:
            self.et_apppwd_hint.setVisible(False)
            return
        sh, sp, ss, ih, ip, is_ = self._EMAIL_PRESETS[key]
        self.et_smtp_host.setText(sh)
        self.et_smtp_port.setValue(sp)
        idx = self.et_smtp_security.findText(ss)
        if idx >= 0:
            self.et_smtp_security.setCurrentIndex(idx)
        self.et_imap_host.setText(ih)
        self.et_imap_port.setValue(ip)
        idx = self.et_imap_security.findText(is_)
        if idx >= 0:
            self.et_imap_security.setCurrentIndex(idx)
        # Show app password hint for providers that require it
        self.et_apppwd_hint.setVisible(key in self._APP_PASSWORD_PROVIDERS)

    def _civ4_exe_paths(self) -> list[str]:
        paths: list[str] = []
        for cfg in (self.config.civ4_installations or {}).values():
            exe = (cfg or {}).get("exe_path") or ""
            if exe:
                paths.append(exe)
        legacy = self.config.get("civ4_path") or ""
        if legacy:
            paths.append(legacy)
        return paths

    def _civ4_exe_paths_for_detection(self) -> list[str]:
        return self.config.civ4_exe_paths_for_save_detection() or self._civ4_exe_paths()

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, t("save_path"), self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)

    def _browse_civ4_save_path(self):
        start = self.civ4_path_edit.text() or self.path_edit.text()
        path = QFileDialog.getExistingDirectory(
            self, t("civ4_save_path"), start
        )
        if path:
            self.civ4_path_edit.setText(path)

    def _on_mirror_toggled(self, checked: bool):
        self.civ4_path_edit.setEnabled(checked)
        self.btn_browse_civ4_saves.setEnabled(checked)
        self.btn_detect_civ4_saves.setEnabled(checked)
        self.btn_use_civ4_as_primary.setEnabled(checked)
        self.mirror_hint.setEnabled(checked)

    def _use_civ4_as_primary(self):
        civ4 = self.civ4_path_edit.text().strip()
        if not civ4:
            detected = detect_save_path(self._civ4_exe_paths_for_detection())
            if detected:
                civ4 = detected
                self.civ4_path_edit.setText(civ4)
        if civ4:
            self.path_edit.setText(civ4)

    def _apply_save_layout(self, path: str) -> str:
        pbem, mirror = resolve_save_layout(path, create=True)
        self.path_edit.setText(pbem)
        if self.mirror_saves_check.isChecked():
            self.civ4_path_edit.setText(mirror)
        return pbem

    def _detect_save_path(self):
        """Read Civ4's own save location; user picks from detected folders."""
        path = ChooseSavePathDialog.pick(
            self, self._civ4_exe_paths(), current=self.path_edit.text().strip(),
        )
        if path:
            self._apply_save_layout(path)

    def _detect_civ4_save_path(self):
        path = ChooseSavePathDialog.pick(
            self,
            self._civ4_exe_paths(),
            current=self.civ4_path_edit.text().strip() or self.path_edit.text().strip(),
        )
        if path:
            self._apply_save_layout(path)

    def _rerun_setup_wizard(self):
        """Re-open the first-run wizard from Settings."""
        from src.gui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(self.config, self)
        if wizard.exec() == QDialog.Accepted:
            self.player_name_edit.setText(self.config.player_name)
            self.player_email_edit.setText(self.config.get("player_email", ""))
            self.path_edit.setText(self.config.save_path)
            self.civ4_path_edit.setText(self.config.get("civ4_save_path", ""))
            self.mirror_saves_check.setChecked(self.config.get("mirror_saves", True))
            self.direct_load_global_check.setChecked(
                self.config.get("direct_load_global", False)
            )
            self.auto_launch_check.setChecked(self.config.get("auto_launch", False))
            installs = self.config.civ4_installations
            for edition in ("steam", "gog", "dvd"):
                widgets = self._edition_widgets.get(edition, {})
                cfg = installs.get(edition, {})
                if widgets.get("enabled"):
                    widgets["enabled"].setChecked(bool(cfg.get("enabled")))
                if widgets.get("exe_edit"):
                    widgets["exe_edit"].setText(cfg.get("exe_path", ""))
            pref = self.config.preferred_edition
            idx = self.preferred_edition_combo.findData(pref)
            if idx >= 0:
                self.preferred_edition_combo.setCurrentIndex(idx)
            lang = self.config.language
            lang_idx = self.language_combo.findData(lang)
            if lang_idx >= 0:
                self.language_combo.setCurrentIndex(lang_idx)

    def _browse_civ4_path(self):
        """Legacy stub -- replaced by per-edition browse."""
        pass

    def _detect_civ4(self):
        """Legacy stub -- replaced by per-edition detect."""
        pass

    def _browse_steam_path(self):
        """Legacy stub -- replaced by per-edition browse."""
        pass

    def _detect_steam(self):
        """Legacy stub -- replaced by _detect_steam_into_widget."""
        pass

    def _on_edition_changed(self, index: int):
        """Legacy stub -- no longer used (multi-edition UI replaced single dropdown)."""
        pass

    def _save_settings(self):
        name = self.player_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, t("error"), t("wizard_name_required"))
            return
        self.config.player_name = name
        self.config.set("player_email", self.player_email_edit.text().strip())
        self.config.save_path = self.path_edit.text().strip()
        self.config.set("mirror_saves", self.mirror_saves_check.isChecked())
        self.config.set("civ4_save_path", self.civ4_path_edit.text().strip())
        self.config.set("check_interval_minutes", self.check_interval.value())
        self.config.set("dark_mode", self.dark_mode_check.isChecked())
        self.config.set("auto_send", self.auto_send_check.isChecked())

        from src.autostart import is_autostart_enabled, set_autostart
        want_autostart = self.autostart_check.isChecked()
        self.config.set("autostart", want_autostart)
        if want_autostart != is_autostart_enabled():
            ok, msg = set_autostart(want_autostart)
            if not ok:
                QMessageBox.warning(
                    self, t("error"), t("autostart_failed", msg=msg),
                )

        # Language
        new_lang = self.language_combo.currentData()
        self.config.language = new_lang
        set_language(new_lang)

        # Civ4 installations (multi-edition)
        installs = {}
        for edition in ("steam", "gog", "dvd"):
            w = self._edition_widgets.get(edition, {})
            installs[edition] = {
                "enabled": w["enabled"].isChecked() if w.get("enabled") else False,
                "exe_path": w["exe_edit"].text().strip() if w.get("exe_edit") else "",
            }
        self.config.set("civ4_installations", installs)
        self.config.set("direct_load_global", self.direct_load_global_check.isChecked())
        self.config.set("auto_launch", self.auto_launch_check.isChecked())
        self.config.set("preferred_edition", self.preferred_edition_combo.currentData())

        transport_data = {
            "type": self.transport_type.currentText(),
            "ignore_ssl_errors": self.ssl_ignore_check.isChecked(),
            "use_tls": False,
            "host": self.transport_host.text().strip(),
            "port": self.transport_port.value(),
            "username": self.transport_user.text().strip(),
            "password": self.transport_pass.text(),
            "remote_dir": self.transport_dir.text().strip(),
            "email": {
                "smtp_host": self.et_smtp_host.text().strip(),
                "smtp_port": self.et_smtp_port.value(),
                "smtp_security": self.et_smtp_security.currentText(),
                "smtp_user": self.et_smtp_user.text().strip(),
                "smtp_password": self.et_smtp_pass.text(),
                "incoming_protocol": self.et_incoming_proto.currentData(),
                "imap_host": self.et_imap_host.text().strip(),
                "imap_port": self.et_imap_port.value(),
                "imap_security": self.et_imap_security.currentText(),
                "imap_user": self.et_imap_user.text().strip(),
                "imap_password": self.et_imap_pass.text(),
                "pop3_host": self.et_pop3_host.text().strip(),
                "pop3_port": self.et_pop3_port.value(),
                "pop3_security": self.et_pop3_security.currentText(),
                "delete_after_download": self.et_delete_after_download.isChecked(),
                "mode": self.et_mode.currentText(),
                "shared_email": self.et_shared_email.text().strip(),
                "from_address": self.et_from_address.text().strip(),
            },
        }
        self.config.set("transport", transport_data)

        # SMTP notification config — depends on source selection
        smtp_source = self.smtp_source_combo.currentData() if hasattr(self, 'smtp_source_combo') else "custom"
        if smtp_source == "transport":
            # Clear custom SMTP — controller will fallback to transport email credentials
            self.config.set("smtp", {
                "host": "",
                "port": 587,
                "username": "",
                "password": "",
                "use_tls": True,
                "from_address": "",
                "subject_template": self.smtp_subject_template.text().strip(),
                "body_template": self.smtp_body_template.toPlainText().strip(),
                "reminder_subject_template": self.smtp_reminder_subject.text().strip(),
                "reminder_body_template": self.smtp_reminder_body.toPlainText().strip(),
            })
        else:
            self.config.set("smtp", {
                "host": self.smtp_host.text().strip(),
                "port": self.smtp_port.value(),
                "username": self.smtp_user.text().strip(),
                "password": self.smtp_pass.text(),
                "use_tls": True,
                "from_address": self.smtp_from.text().strip(),
                "subject_template": self.smtp_subject_template.text().strip(),
                "body_template": self.smtp_body_template.toPlainText().strip(),
                "reminder_subject_template": self.smtp_reminder_subject.text().strip(),
                "reminder_body_template": self.smtp_reminder_body.toPlainText().strip(),
            })

        # Notification channels + auto-reminder
        self.config.set("notifications_enabled",
                        self.notifications_enabled_check.isChecked())
        self.config.set("notify_via_smtp", self.notify_via_smtp_check.isChecked())
        self.config.set("notify_via_app", self.notify_via_app_check.isChecked())
        self.config.set("reminder_auto_enabled", self.reminder_auto_check.isChecked())
        self.config.set("reminder_auto_days", self.reminder_auto_days.value())

        if self.mirror_saves_check.isChecked():
            from src.launcher import copy_missing_pbem_saves
            from src.saves import iter_save_dirs
            primary = self.config.save_path
            for dest in iter_save_dirs(
                primary,
                self.config.get("civ4_save_path", ""),
                True,
            ):
                copy_missing_pbem_saves(primary, str(dest))

        # Apply theme change immediately to parent window
        parent = self.parent()
        if parent and hasattr(parent, 'apply_theme'):
            parent.apply_theme()

        self.accept()
