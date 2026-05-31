"""
Watchdog-based file watcher for detecting new save files in the Civ4 save folder.
When a new .CivBeyondSwordSave file appears, emits a signal to propose upload.

IMPORTANT: Files downloaded by the app itself are excluded via ignore_next().
This prevents the "just downloaded a turn, watchdog asks to re-upload it" loop.
"""
import logging
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

SAVE_EXTENSION = ".CivBeyondSwordSave"


class _SaveFileHandler(FileSystemEventHandler):
    """Watchdog handler that detects new/modified save files."""

    def __init__(self, callback, ignore_set: set):
        super().__init__()
        self._callback = callback
        self._ignore_set = ignore_set
        self._seen: set[str] = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def _notify(self, path: str):
        # Normalize path for consistent comparison
        normalized = str(Path(path).resolve())

        # Skip files that the app itself downloaded
        if normalized in self._ignore_set:
            logger.debug(f"Watchdog ignoring downloaded file: {Path(path).name}")
            self._ignore_set.discard(normalized)
            return

        # Deduplicate rapid events for the same file (5s cooldown)
        if path not in self._seen:
            self._seen.add(path)
            self._callback(path)
            QTimer.singleShot(5000, lambda: self._seen.discard(path))


class SaveFileWatcher(QObject):
    """Watches the save folder for new .CivBeyondSwordSave files.

    Files added to the ignore list (via ignore_next()) will NOT trigger
    the new_save_detected signal. Use this when downloading saves from
    the server to prevent the watchdog from immediately asking to re-upload.

    Signals:
        new_save_detected(str): emitted with the full path to the new save file.
    """

    new_save_detected = pyqtSignal(str)

    def __init__(self, watch_path: str, parent=None):
        super().__init__(parent)
        self._watch_path = watch_path
        self._observer = None
        self._handler = None
        # Set of file paths (resolved) to ignore on next detection
        self._ignore_set: set[str] = set()

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    def ignore_next(self, filepath: str):
        """Mark a file path to be ignored by the watcher.

        Call this BEFORE downloading/writing a save file to the watch folder.
        The file will be silently ignored when watchdog detects it.
        Entry auto-expires after 30 seconds (in case download fails).
        """
        normalized = str(Path(filepath).resolve())
        self._ignore_set.add(normalized)
        # Auto-expire after 30s to prevent stale entries
        QTimer.singleShot(30000, lambda: self._ignore_set.discard(normalized))
        logger.debug(f"Watchdog will ignore: {Path(filepath).name}")

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

        self._handler = _SaveFileHandler(self._on_file_detected, self._ignore_set)
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
