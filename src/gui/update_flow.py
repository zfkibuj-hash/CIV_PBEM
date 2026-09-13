"""GUI orchestration for GitHub self-update (check → dialog → download → restart)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import QUrl

from src.config import APP_VERSION, version_label
from src.gui.update_worker import UpdateCheckWorker, UpdateDownloadWorker
from src.i18n import t
from src.updater import (
    ReleaseInfo,
    current_exe_path,
    is_frozen_exe,
    schedule_replace_and_restart,
    truncate_release_notes,
)

if TYPE_CHECKING:
    from src.config import AppConfig
    from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class UpdateFlow:
    """Owns QThreads for update check/download; parent widget must outlive the flow."""

    def __init__(self, parent: "QWidget", config: "AppConfig"):
        self._parent = parent
        self._config = config
        self._thread: Optional[QThread] = None
        self._worker = None
        self._manual = False
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start_check(self, *, manual: bool = False) -> None:
        if self._busy:
            return
        if manual and not is_frozen_exe():
            QMessageBox.information(
                self._parent, t("auto_update_group"), t("auto_update_dev_only"),
            )
            return
        if not is_frozen_exe():
            return

        self._manual = manual
        self._busy = True
        skipped = "" if manual else str(self._config.get("skipped_update_version", "") or "")
        thread = QThread(self._parent)
        worker = UpdateCheckWorker(skipped_version=skipped)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.update_available.connect(self._on_available)
        worker.up_to_date.connect(self._on_up_to_date)
        worker.failed.connect(self._on_check_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_check_thread_done)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_check_thread_done(self) -> None:
        self._busy = False
        self._thread = None
        self._worker = None

    def _on_up_to_date(self) -> None:
        if self._manual:
            QMessageBox.information(
                self._parent,
                t("auto_update_group"),
                t("auto_update_up_to_date", version=version_label()),
            )

    def _on_check_failed(self, error: str) -> None:
        if self._manual:
            QMessageBox.warning(
                self._parent,
                t("auto_update_group"),
                t("auto_update_failed", error=error),
            )
        else:
            logger.info("Silent update check failed: %s", error)

    def _on_available(self, info: object) -> None:
        release = info  # ReleaseInfo
        assert isinstance(release, ReleaseInfo)
        notes = truncate_release_notes(release.body)
        box = QMessageBox(self._parent)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle(t("auto_update_available_title"))
        box.setText(
            t(
                "auto_update_available_text",
                local=version_label(),
                remote=release.tag,
                notes=notes or release.name,
            )
        )
        btn_dl = box.addButton(t("auto_update_download"), QMessageBox.AcceptRole)
        btn_skip = box.addButton(t("auto_update_skip"), QMessageBox.RejectRole)
        btn_web = box.addButton(t("auto_update_open_browser"), QMessageBox.ActionRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_web:
            QDesktopServices.openUrl(QUrl(release.html_url))
            return
        if clicked is btn_skip or clicked is None:
            self._config.set("skipped_update_version", release.version)
            self._config.save()
            return
        if clicked is btn_dl:
            self._start_download(release)

    def _start_download(self, release: ReleaseInfo) -> None:
        if self._busy:
            return
        self._busy = True
        progress = QProgressDialog(
            t("auto_update_downloading"), None, 0, 0, self._parent,
        )
        progress.setWindowTitle(t("auto_update_group"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()

        thread = QThread(self._parent)
        worker = UpdateDownloadWorker(release)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        def _ok(path: str) -> None:
            progress.close()
            self._apply_update(Path(path))

        def _fail(err: str) -> None:
            progress.close()
            QMessageBox.warning(
                self._parent,
                t("auto_update_group"),
                t("auto_update_download_failed", error=err),
            )

        def _done() -> None:
            self._busy = False
            self._thread = None
            self._worker = None

        worker.succeeded.connect(_ok)
        worker.failed.connect(_fail)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(_done)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _apply_update(self, new_exe: Path) -> None:
        cur = current_exe_path()
        if not cur:
            QMessageBox.information(
                self._parent, t("auto_update_group"), t("auto_update_dev_only"),
            )
            return
        try:
            schedule_replace_and_restart(cur, new_exe)
        except Exception as e:
            logger.exception("schedule_replace_and_restart failed")
            QMessageBox.warning(
                self._parent,
                t("auto_update_group"),
                t("auto_update_download_failed", error=str(e)),
            )
            return
        # Clear skip so we don't suppress after failed restart edge cases
        self._config.set("skipped_update_version", "")
        self._config.save()
        QMessageBox.information(
            self._parent,
            t("auto_update_group"),
            t("auto_update_restarting"),
        )
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.quit()
