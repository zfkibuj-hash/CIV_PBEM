"""Background check / download for GitHub self-update."""
from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from src.config import APP_VERSION
from src.updater import (
    ReleaseInfo,
    download_to,
    default_download_path,
    fetch_latest_release,
    should_offer_update,
)

logger = logging.getLogger(__name__)


class UpdateCheckWorker(QObject):
    """Fetch latest release; emit update_available / up_to_date / failed."""

    update_available = Signal(object)  # ReleaseInfo
    up_to_date = Signal()
    failed = Signal(str)
    finished = Signal()

    def __init__(self, skipped_version: str = "", parent=None):
        super().__init__(parent)
        self._skipped = skipped_version or ""

    @Slot()
    def run(self):
        try:
            logger.info("UpdateCheckWorker: fetching latest release")
            info = fetch_latest_release()
            logger.info("UpdateCheckWorker: latest=%s", info.tag)
            if should_offer_update(info, APP_VERSION, self._skipped):
                self.update_available.emit(info)
            else:
                self.up_to_date.emit()
        except Exception as e:
            logger.info("Update check failed: %s", e)
            self.failed.emit(str(e))
        finally:
            self.finished.emit()


class UpdateDownloadWorker(QObject):
    """Download release exe to a temp path."""

    progress = Signal(str)
    succeeded = Signal(str)  # local path
    failed = Signal(str)
    finished = Signal()

    def __init__(self, release: ReleaseInfo, parent=None):
        super().__init__(parent)
        self._release = release

    @Slot()
    def run(self):
        try:
            dest = default_download_path(self._release.exe_name)
            self.progress.emit(str(dest))
            path = download_to(self._release.exe_url, dest)
            self.succeeded.emit(str(path))
        except Exception as e:
            logger.exception("Update download failed")
            self.failed.emit(str(e))
        finally:
            self.finished.emit()
