"""
Watchdog-based file watcher for detecting new save files in the Civ4 save folder.
When a new .CivBeyondSwordSave file appears, emits a signal to propose upload.

IMPORTANT: Files downloaded by the app itself are excluded via ignore_next().
This prevents the "just downloaded a turn, watchdog asks to re-upload it" loop.
"""
import logging
import time
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

SAVE_EXTENSION = ".CivBeyondSwordSave"


class _SaveFileHandler(FileSystemEventHandler):
    """Watchdog handler that detects new/modified save files."""

    def __init__(
        self,
        callback,
        ignore_set: set,
        ignore_until: dict,
        lock: threading.Lock,
    ):
        super().__init__()
        self._callback = callback
        self._ignore_set = ignore_set
        self._ignore_until = ignore_until
        self._lock = lock
        self._seen_until: dict[str, float] = {}

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def _notify(self, path: str):
        lower = path.replace("/", "\\").lower()
        for skip in ("\\auto\\", "\\pitboss\\", "\\pithoss\\"):
            if skip in lower:
                logger.debug("Watchdog ignoring %s save: %s", skip.strip("\\"), path)
                return

        # Normalize path for consistent comparison
        normalized = str(Path(path).resolve())

        with self._lock:
            if normalized in self._ignore_set:
                expires = self._ignore_until.get(normalized, 0)
                self._ignore_set.discard(normalized)
                self._ignore_until.pop(normalized, None)
                if time.time() <= expires:
                    logger.debug(
                        f"Watchdog ignoring downloaded file: {Path(path).name}",
                    )
                    return

            now = time.time()
            if self._seen_until.get(path, 0) > now:
                return
            self._seen_until[path] = now + 5

        self._callback(path)


class SaveFileWatcher(QObject):
    """Watches one or more save folders for new .CivBeyondSwordSave files.

    Files added to the ignore list (via ignore_next()) will NOT trigger
    the new_save_detected signal. Use this when downloading saves from
    the server to prevent the watchdog from immediately asking to re-upload.

    Signals:
        new_save_detected(str): emitted with the full path to the new save file.
    """

    new_save_detected = Signal(str)

    def __init__(self, watch_path, parent=None):
        super().__init__(parent)
        self._watch_paths = self._normalize_paths(watch_path)
        self._observer = None
        self._handler = None
        # Lock for thread-safe access to ignore_set and seen set
        self._lock = threading.Lock()
        # Set of file paths (resolved) to ignore on next detection
        self._ignore_set: set[str] = set()
        self._ignore_until: dict[str, float] = {}

    @staticmethod
    def _normalize_paths(watch_path) -> list[str]:
        if not watch_path:
            return []
        if isinstance(watch_path, (list, tuple)):
            return [str(p) for p in watch_path if p]
        return [str(watch_path)]

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    def ignore_next(self, filepath: str):
        """Mark a file path to be ignored by the watcher.

        Call this BEFORE downloading/writing a save file to the watch folder.
        The file will be silently ignored when watchdog detects it.
        Entry auto-expires after 30 seconds (in case download fails).
        Thread-safe (no Qt calls).
        """
        normalized = str(Path(filepath).resolve())
        with self._lock:
            self._ignore_set.add(normalized)
            self._ignore_until[normalized] = time.time() + 30
        logger.debug(f"Watchdog will ignore: {Path(filepath).name}")

    def start(self):
        """Start watching the save folder(s)."""
        dirs: list[Path] = []
        for raw in self._watch_paths:
            watch_dir = Path(raw)
            if not watch_dir.exists():
                logger.warning(f"Watch directory does not exist: {watch_dir}")
                try:
                    watch_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created watch directory: {watch_dir}")
                except Exception as e:
                    logger.error(f"Cannot create watch directory: {e}")
                    continue
            dirs.append(watch_dir)

        if not dirs:
            logger.warning("File watcher has no directories to watch")
            return

        self._handler = _SaveFileHandler(
            self._on_file_detected, self._ignore_set, self._ignore_until, self._lock,
        )
        self._observer = Observer()
        seen: set[str] = set()
        for watch_dir in dirs:
            key = str(watch_dir.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            self._observer.schedule(self._handler, str(watch_dir), recursive=True)
            logger.info(f"File watcher started on: {watch_dir}")
        self._observer.daemon = True
        self._observer.start()

    def stop(self):
        """Stop watching."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)
            logger.info("File watcher stopped")
        self._observer = None

    def restart(self, new_path):
        """Restart watcher with a new path or list of paths."""
        self.stop()
        self._watch_paths = self._normalize_paths(new_path)
        self.start()

    def _on_file_detected(self, filepath: str):
        """Called by watchdog handler when a new save is detected."""
        logger.info(f"New save detected: {filepath}")
        self.new_save_detected.emit(filepath)
