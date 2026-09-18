"""GUI orchestration for GitHub self-update (check → dialog → download → restart)."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QWidget

from src.config import APP_VERSION, version_label
from src.gui.update_worker import UpdateDownloadWorker
from src.i18n import t
from src.updater import (
    ReleaseInfo,
    current_exe_path,
    fetch_latest_release,
    is_frozen_exe,
    schedule_replace_and_restart,
    should_offer_update,
    truncate_release_notes,
)

if TYPE_CHECKING:
    from src.config import AppConfig

logger = logging.getLogger(__name__)

# After Settings closes, leftover click/key can dismiss the next QMessageBox.
_RESULT_DIALOG_DELAY_MS = 280
# Hard UI unblock if a result never arrives.
_CHECK_UI_TIMEOUT_MS = 15000


class _CheckBridge(QObject):
    """Receives worker-thread results on the GUI thread (QueuedConnection)."""

    update_available = Signal(object)
    up_to_date = Signal()
    failed = Signal(str)


class UpdateFlow:
    """Owns update check/download; parent widget must outlive the flow."""

    def __init__(self, parent: QWidget, config: "AppConfig"):
        self._parent = parent
        self._config = config
        self._thread: Optional[QThread] = None
        self._worker = None
        self._manual = False
        self._busy = False
        self._msg_parent: Optional[QWidget] = None
        self._check_gen = 0
        self._status_mine = False
        self._result_shown = False
        self._bridge = _CheckBridge(parent)
        self._bridge.update_available.connect(self._on_available)
        self._bridge.up_to_date.connect(self._on_up_to_date)
        self._bridge.failed.connect(self._on_check_failed)

    @property
    def busy(self) -> bool:
        return self._busy

    def _ui_parent(self) -> QWidget:
        p = self._msg_parent
        if p is not None:
            try:
                if p.isVisible():
                    return p
            except RuntimeError:
                pass
        return self._parent

    def _set_status(self, text: str) -> None:
        label = getattr(self._parent, "status_label", None)
        if label is None:
            return
        try:
            label.setText(text)
            self._status_mine = True
        except RuntimeError:
            pass

    def _clear_status(self) -> None:
        if not self._status_mine:
            return
        self._status_mine = False
        label = getattr(self._parent, "status_label", None)
        if label is None:
            return
        try:
            label.setText(t("ready"))
        except RuntimeError:
            pass

    def _present_box(self, box: QMessageBox) -> int:
        box.setWindowModality(Qt.ApplicationModal)
        box.setMinimumWidth(360)
        box.show()
        box.raise_()
        box.activateWindow()
        return box.exec()

    def start_check(
        self,
        *,
        manual: bool = False,
        dialog_parent: Optional[QWidget] = None,
    ) -> None:
        if self._busy:
            return
        self._msg_parent = dialog_parent
        if manual and not is_frozen_exe():
            QMessageBox.information(
                self._ui_parent(), t("auto_update_group"), t("auto_update_dev_only"),
            )
            return
        if not is_frozen_exe():
            return

        self._manual = manual
        self._busy = True
        self._result_shown = False
        self._check_gen += 1
        gen = self._check_gen
        if manual:
            self._set_status(t("auto_update_checking"))
        QTimer.singleShot(_CHECK_UI_TIMEOUT_MS, lambda: self._on_check_ui_timeout(gen))

        skipped = "" if manual else str(self._config.get("skipped_update_version", "") or "")
        bridge = self._bridge

        def work() -> None:
            try:
                logger.info("UpdateCheckWorker: fetching latest release (gen=%s)", gen)
                info = fetch_latest_release()
                logger.info("UpdateCheckWorker: latest=%s (gen=%s)", info.tag, gen)
                if should_offer_update(info, APP_VERSION, skipped):
                    bridge.update_available.emit(info)
                else:
                    bridge.up_to_date.emit()
            except Exception as e:
                logger.info("Update check failed (gen=%s): %s", gen, e)
                bridge.failed.emit(str(e))

        threading.Thread(target=work, name=f"update-check-{gen}", daemon=True).start()

    def _finish_check(self, gen: int) -> bool:
        """Mark this generation done. True if caller should show UI."""
        if gen != self._check_gen:
            return False
        self._busy = False
        self._clear_status()
        if self._result_shown:
            return False
        self._result_shown = True
        return True

    def _on_check_ui_timeout(self, gen: int) -> None:
        if gen != self._check_gen:
            return
        if self._result_shown:
            self._clear_status()
            return
        # Worker finished without delivering UI, or still hung.
        logger.warning(
            "Update check UI timeout (gen=%s, busy=%s, manual=%s)",
            gen, self._busy, self._manual,
        )
        self._busy = False
        self._clear_status()
        if not self._manual:
            self._result_shown = True
            return
        self._result_shown = True
        self._check_gen += 1  # ignore a late worker result
        box = QMessageBox(self._ui_parent())
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(t("auto_update_group"))
        box.setText(t("auto_update_timeout"))
        box.setStandardButtons(QMessageBox.Ok)
        self._present_box(box)

    @Slot()
    def _on_up_to_date(self) -> None:
        gen = self._check_gen
        if not self._finish_check(gen):
            return
        if not self._manual:
            return

        def _show() -> None:
            try:
                box = QMessageBox(self._ui_parent())
                box.setIcon(QMessageBox.Information)
                box.setWindowTitle(t("auto_update_group"))
                box.setText(t("auto_update_up_to_date", version=version_label()))
                box.setStandardButtons(QMessageBox.Ok)
                box.setDefaultButton(QMessageBox.Ok)
                self._present_box(box)
            except Exception:
                logger.exception("up-to-date dialog failed")

        QTimer.singleShot(_RESULT_DIALOG_DELAY_MS, _show)

    @Slot(str)
    def _on_check_failed(self, error: str) -> None:
        gen = self._check_gen
        if not self._finish_check(gen):
            return
        if not self._manual:
            logger.info("Silent update check failed: %s", error)
            return

        def _show() -> None:
            try:
                box = QMessageBox(self._ui_parent())
                box.setIcon(QMessageBox.Warning)
                box.setWindowTitle(t("auto_update_group"))
                box.setText(t("auto_update_failed", error=error or "?"))
                box.setStandardButtons(QMessageBox.Ok)
                box.setDefaultButton(QMessageBox.Ok)
                self._present_box(box)
            except Exception:
                logger.exception("update-failed dialog failed")

        QTimer.singleShot(_RESULT_DIALOG_DELAY_MS, _show)

    @Slot(object)
    def _on_available(self, info: object) -> None:
        gen = self._check_gen
        if not self._finish_check(gen):
            return
        if not isinstance(info, ReleaseInfo):
            return
        release = info

        def _show() -> None:
            try:
                notes = truncate_release_notes(release.body)
                box = QMessageBox(self._ui_parent())
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
                box.setDefaultButton(btn_dl)
                self._present_box(box)
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
            except Exception:
                logger.exception("update-available dialog failed")

        QTimer.singleShot(_RESULT_DIALOG_DELAY_MS, _show)

    def _start_download(self, release: ReleaseInfo) -> None:
        if self._busy:
            return
        self._busy = True
        progress = QProgressDialog(
            t("auto_update_downloading"), None, 0, 0, self._ui_parent(),
        )
        progress.setWindowTitle(t("auto_update_group"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()
        progress.raise_()
        progress.activateWindow()

        thread = QThread(self._parent)
        worker = UpdateDownloadWorker(release)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        def _ok(path: str) -> None:
            progress.close()
            QTimer.singleShot(0, lambda: self._apply_update(Path(path)))

        def _fail(err: str) -> None:
            progress.close()

            def _show() -> None:
                box = QMessageBox(self._ui_parent())
                box.setIcon(QMessageBox.Warning)
                box.setWindowTitle(t("auto_update_group"))
                box.setText(t("auto_update_download_failed", error=err))
                box.setStandardButtons(QMessageBox.Ok)
                self._present_box(box)

            QTimer.singleShot(_RESULT_DIALOG_DELAY_MS, _show)

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
                self._ui_parent(), t("auto_update_group"), t("auto_update_dev_only"),
            )
            return
        try:
            schedule_replace_and_restart(cur, new_exe)
        except Exception as e:
            logger.exception("schedule_replace_and_restart failed")
            QMessageBox.warning(
                self._ui_parent(),
                t("auto_update_group"),
                t("auto_update_download_failed", error=str(e)),
            )
            return
        self._config.set("skipped_update_version", "")
        self._config.save()
        box = QMessageBox(self._ui_parent())
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle(t("auto_update_group"))
        box.setText(t("auto_update_restarting"))
        box.setStandardButtons(QMessageBox.Ok)
        self._present_box(box)
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.quit()
