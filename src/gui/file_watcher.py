"""
Watchdog-based file watcher for detecting new save files in the Civ4 save folder.
When a new .CivBeyondSwordSave file appears, emits a signal to propose upload.
"""
import logging
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

logger = logging.getLogger(__name__)

SAVE_EXTENSION = ".CivBeyondSwordSave"


class _SaveFileHandler(FileSystemEventHandler):
    """Watchdog handler that detects new/modified save files."""

    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._seen: set[str] = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def _notify(self, path: str):
        # Deduplicate rapid events for the same file
        if path not in self._seen:
            self._seen.add(path)
            self._callback(path)
            # Clear after a short delay to allow re-detection
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(5000, lambda: self._seen.discard(path))


class SaveFileWatcher(QObject):
    """Watches the save folder for new .CivBeyondSwordSave files.

    Signals:
        new_save_detected(str): emitted with the full path to the new save file.
    """

    new_save_detected = pyqtSignal(str)

    def __init__(self, watch_path: str, parent=None):
        super().__init__(parent)
        self._watch_path = watch_path
        self._observer = None
        self._handler = None

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    def start(self):
        """Start watching the save folder."""
        watch_dir = Path(self._watch_path)
        if not watch_dir.exists():
            logger.warning(f"Watch directory does not exist: {watch_dir}")
            try:
                watch_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created watch directory: {watch_dir}")
            except Exception as e:
                logger.error(f"Cannot create watch directory: {e}")
                return

        self._handler = _SaveFileHandler(self._on_file_detected)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(watch_dir), recursive=False)
        self._observer.daemon = True
        self._observer.start()
        logger.info(f"File watcher started on: {watch_dir}")

    def stop(self):
        """Stop watching."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)
            logger.info("File watcher stopped")
        self._observer = None

    def restart(self, new_path: str):
        """Restart watcher with a new path."""
        self.stop()
        self._watch_path = new_path
        self.start()

    def _on_file_detected(self, filepath: str):
        """Called by watchdog handler when a new save is detected."""
        logger.info(f"New save detected: {filepath}")
        self.new_save_detected.emit(filepath)
