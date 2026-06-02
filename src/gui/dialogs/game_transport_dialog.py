"""
GameTransportDialog — per-game transport configuration dialog.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox, QGroupBox,
    QPushButton, QDialogButtonBox, QMessageBox, QCheckBox,
    QScrollArea, QFrame, QApplication,
)
from PyQt5.QtCore import Qt

from src.config import AppConfig
from src.models.game import Game
from src.i18n import t
from src.gui.styles import get_style_for_theme


class GameTransportDialog(QDialog):
    """Per-game transport configuration dialog.

    Allows configuring transport for individual games with option to
    copy settings from defaults (global config) or from another game.
    """

    def __init__(self, config: AppConfig, game: Game, all_games: list, parent=None):
        super().__init__(parent)
        self.config = config
        self.game = game
        self.all_games = all_games
        self.setWindowTitle(f"Transport: {game.name}")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(560, 500)
        self.resize(600, 560)
        self.setStyleSheet(get_style_for_theme(self.config.get("dark_mode", True)))
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Copy from section
        copy_group = QGroupBox(t("game_transport_copy_group"))
        copy_layout = QHBoxLayout(copy_group)

        btn_copy_defaults = QPushButton(t("copy_defaults"))
        btn_copy_defaults.clicked.connect(self._copy_from_defaults)
        copy_layout.addWidget(btn_copy_defaults)

        self.copy_game_combo = QComboBox()
        self.copy_game_combo.addItem("-- " + t("copy_from") + " --")
        for g in self.all_games:
            if g.name != self.game.name and g.transport_config:
                self.copy_game_combo.addItem(g.name)
        copy_layout.addWidget(self.copy_game_combo)

        btn_copy_game = QPushButton(t("copy_from"))
        btn_copy_game.clicked.connect(self._copy_from_game)
        copy_layout.addWidget(btn_copy_game)

        layout.addWidget(copy_group)

        # Transport config (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        from PyQt5.QtWidgets import QWidget
        content = QWidget()
        form_layout = QVBoxLayout(content)

        tc = self.game.transport_config or {}

        # Type
        type_group = QGroupBox(t("transport_method"))
        type_form = QFormLayout(type_group)
        self.transport_type = QComboBox()
        self.transport_type.addItems(["ftp", "sftp", "webdav", "email"])
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.transport_type.currentTextChanged.connect(self._on_type_changed)
        type_form.addRow(t("transport_type_label"), self.transport_type)

        self.ssl_ignore_check = QCheckBox(t("ssl_ignore"))
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        type_form.addRow(self.ssl_ignore_check)
        form_layout.addWidget(type_group)

        # File-based (FTP/SFTP/WebDAV)
        self.file_group = QGroupBox(t("file_transport_group"))
        file_form = QFormLayout(self.file_group)
        self.t_host = QLineEdit(tc.get("host", ""))
        file_form.addRow(t("field_host"), self.t_host)
        self.t_port = QSpinBox()
        self.t_port.setRange(1, 65535)
        self.t_port.setValue(tc.get("port", 21))
        file_form.addRow(t("field_port"), self.t_port)
        self.t_user = QLineEdit(tc.get("username", ""))
        file_form.addRow(t("field_login"), self.t_user)
        self.t_pass = QLineEdit(tc.get("password", ""))
        self.t_pass.setEchoMode(QLineEdit.Password)
        file_form.addRow(t("field_password"), self.t_pass)
        self.t_dir = QLineEdit(tc.get("remote_dir", "/civ4pbem"))
        file_form.addRow(t("field_remote_dir"), self.t_dir)
        form_layout.addWidget(self.file_group)

        # Email
        self.email_group = QGroupBox(t("email_transport_group"))
        email_form = QFormLayout(self.email_group)
        ec = tc.get("email", {})
        self.e_mode = QComboBox()
        self.e_mode.addItems(["shared", "individual"])
        self.e_mode.setCurrentText(ec.get("mode", "shared"))
        email_form.addRow(t("field_mode"), self.e_mode)
        self.e_shared = QLineEdit(ec.get("shared_email", ""))
        email_form.addRow(t("field_shared_mailbox"), self.e_shared)
        self.e_smtp_host = QLineEdit(ec.get("smtp_host", ""))
        email_form.addRow("SMTP host:", self.e_smtp_host)
        self.e_smtp_port = QSpinBox()
        self.e_smtp_port.setRange(1, 65535)
        self.e_smtp_port.setValue(ec.get("smtp_port", 587))
        email_form.addRow("SMTP port:", self.e_smtp_port)
        self.e_smtp_user = QLineEdit(ec.get("smtp_user", ""))
        email_form.addRow("SMTP login:", self.e_smtp_user)
        self.e_smtp_pass = QLineEdit(ec.get("smtp_password", ""))
        self.e_smtp_pass.setEchoMode(QLineEdit.Password)
        email_form.addRow("SMTP " + t("field_password"), self.e_smtp_pass)
        self.e_imap_host = QLineEdit(ec.get("imap_host", ""))
        email_form.addRow("IMAP host:", self.e_imap_host)
        self.e_imap_port = QSpinBox()
        self.e_imap_port.setRange(1, 65535)
        self.e_imap_port.setValue(ec.get("imap_port", 993))
        email_form.addRow("IMAP port:", self.e_imap_port)
        self.e_imap_user = QLineEdit(ec.get("imap_user", ""))
        email_form.addRow("IMAP login:", self.e_imap_user)
        self.e_imap_pass = QLineEdit(ec.get("imap_password", ""))
        self.e_imap_pass.setEchoMode(QLineEdit.Password)
        email_form.addRow("IMAP " + t("field_password"), self.e_imap_pass)
        self.e_from = QLineEdit(ec.get("from_address", ""))
        email_form.addRow(t("field_from"), self.e_from)

        email_warning = QLabel(f"⚠ {t('email_warning')}")
        email_warning.setWordWrap(True)
        email_warning.setStyleSheet("color: #ff9800; font-size: 9pt; padding: 4px;")
        email_form.addRow(email_warning)

        form_layout.addWidget(self.email_group)

        form_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Show/hide panels
        self._on_type_changed(self.transport_type.currentText())

        # Test connection button
        btn_test = QPushButton(t("transport_test_btn"))
        btn_test.clicked.connect(self._test_connection)
        layout.addWidget(btn_test)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _test_connection(self):
        """Test the transport connection with current form values."""
        from src.gui.app_controller import AppController
        from src.models.game import Game as _Game

        # Build a temporary game with current form config
        tc = self.get_transport_config()
        temp_game = _Game(name="__test__", transport_config=tc)

        # Use a temporary controller to test
        transport = AppController._create_transport_for_game(None, temp_game)
        if not transport:
            QMessageBox.warning(self, t("test_connection"), t("transport_not_configured_short"))
            return

        QApplication.processEvents()
        success = transport.connect()
        if success:
            transport.disconnect()
            QMessageBox.information(self, t("test_connection"), t("connection_ok"))
        else:
            QMessageBox.warning(self, t("test_connection"), t("connection_failed"))

    def _on_type_changed(self, transport_type: str):
        self.file_group.setVisible(transport_type in ("ftp", "sftp", "webdav"))
        self.email_group.setVisible(transport_type == "email")

    def _copy_from_defaults(self):
        """Copy transport config from global defaults."""
        tc = self.config.transport_config
        self._apply_config(tc)

    def _copy_from_game(self):
        """Copy transport config from another game."""
        game_name = self.copy_game_combo.currentText()
        if game_name == "-- wybierz gre --":
            return
        for g in self.all_games:
            if g.name == game_name and g.transport_config:
                self._apply_config(g.transport_config)
                break

    def _apply_config(self, tc: dict):
        """Apply a transport config dict to the form fields."""
        self.transport_type.setCurrentText(tc.get("type", "ftp"))
        self.ssl_ignore_check.setChecked(tc.get("ignore_ssl_errors", True))
        self.t_host.setText(tc.get("host", ""))
        self.t_port.setValue(tc.get("port", 21))
        self.t_user.setText(tc.get("username", ""))
        self.t_pass.setText(tc.get("password", ""))
        self.t_dir.setText(tc.get("remote_dir", "/civ4pbem"))

        ec = tc.get("email", {})
        self.e_mode.setCurrentText(ec.get("mode", "shared"))
        self.e_shared.setText(ec.get("shared_email", ""))
        self.e_smtp_host.setText(ec.get("smtp_host", ""))
        self.e_smtp_port.setValue(ec.get("smtp_port", 587))
        self.e_smtp_user.setText(ec.get("smtp_user", ""))
        self.e_smtp_pass.setText(ec.get("smtp_password", ""))
        self.e_imap_host.setText(ec.get("imap_host", ""))
        self.e_imap_port.setValue(ec.get("imap_port", 993))
        self.e_imap_user.setText(ec.get("imap_user", ""))
        self.e_imap_pass.setText(ec.get("imap_password", ""))
        self.e_from.setText(ec.get("from_address", ""))

    def get_transport_config(self) -> dict:
        """Build transport config dict from form fields."""
        return {
            "type": self.transport_type.currentText(),
            "ignore_ssl_errors": self.ssl_ignore_check.isChecked(),
            "host": self.t_host.text().strip(),
            "port": self.t_port.value(),
            "username": self.t_user.text().strip(),
            "password": self.t_pass.text(),
            "remote_dir": self.t_dir.text().strip(),
            "email": {
                "mode": self.e_mode.currentText(),
                "shared_email": self.e_shared.text().strip(),
                "smtp_host": self.e_smtp_host.text().strip(),
                "smtp_port": self.e_smtp_port.value(),
                "smtp_user": self.e_smtp_user.text().strip(),
                "smtp_password": self.e_smtp_pass.text(),
                "smtp_use_tls": True,
                "imap_host": self.e_imap_host.text().strip(),
                "imap_port": self.e_imap_port.value(),
                "imap_user": self.e_imap_user.text().strip(),
                "imap_password": self.e_imap_pass.text(),
                "imap_use_ssl": True,
                "from_address": self.e_from.text().strip(),
            },
        }
