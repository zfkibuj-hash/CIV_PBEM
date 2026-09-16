"""
Watchdog-based file watcher for detecting new save files in the Civ4 save folder.
When a new .CivBeyondSwordSave file appears, emits a signal to propose upload.

IMPORTANT: Files downloaded by the app itself are excluded via ignore_next().
This prevents the "just downloaded a turn, watchdog asks to re-upload it" loop.

Civ4 often fires created + several modified events while the save is still being
written. We wait until the file size is stable before emitting, and keep a
per-filename cooldown so the upload prompt appears once.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

SAVE_EXTENSION = ".CivBeyondSwordSave"
# Wait after last FS event before treating the save as finished.
_SETTLE_S = 2.5
# After a prompt/emit, ignore the same filename this long.
_COOLDOWN_S = 60.0
# ignore_next TTL (download / mirror writes)
_IGNORE_TTL_S = 45.0


def _norm_path(path: str) -> str:
    try:
        return str(Path(path).resolve())
    except Exception:
        return str(Path(path))


def _file_size_stable(path: str, *, checks: int = 3, interval_s: float = 0.4) -> bool:
    """True if file exists and size stays the same across a few samples."""
    p = Path(path)
    try:
        prev = p.stat().st_size
    except OSError:
        return False
    if prev <= 0:
        return False
    for _ in range(checks - 1):
        time.sleep(interval_s)
        try:
            cur = p.stat().st_size
        except OSError:
            return False
        if cur != prev or cur <= 0:
            return False
        prev = cur
    return True


class _SaveFileHandler(FileSystemEventHandler):
    """Watchdog handler that detects new/modified save files."""

    def __init__(
        self,
        callback,
        ignore_paths: set,
        ignore_path_until: dict,
        ignore_names: set,
        ignore_name_until: dict,
        lock: threading.Lock,
    ):
        super().__init__()
        self._callback = callback
        self._ignore_paths = ignore_paths
        self._ignore_path_until = ignore_path_until
        self._ignore_names = ignore_names
        self._ignore_name_until = ignore_name_until
        self._lock = lock
        self._seen_until: dict[str, float] = {}
        self._pending_paths: dict[str, str] = {}
        self._pending_timers: dict[str, threading.Timer] = {}

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(SAVE_EXTENSION):
            self._notify(event.src_path)

    def on_moved(self, event):
        # Civ4 / OneDrive sometimes write temp then rename into place.
        dest = getattr(event, "dest_path", None) or ""
        if not event.is_directory and dest.endswith(SAVE_EXTENSION):
            self._notify(dest)

    def _still_ignored(self, normalized: str, name_key: str) -> bool:
        now = time.time()
        path_exp = self._ignore_path_until.get(normalized, 0)
        if normalized in self._ignore_paths and now <= path_exp:
            return True
        if normalized in self._ignore_paths and now > path_exp:
            self._ignore_paths.discard(normalized)
            self._ignore_path_until.pop(normalized, None)

        name_exp = self._ignore_name_until.get(name_key, 0)
        if name_key in self._ignore_names and now <= name_exp:
            return True
        if name_key in self._ignore_names and now > name_exp:
            self._ignore_names.discard(name_key)
            self._ignore_name_until.pop(name_key, None)
        return False

    def _notify(self, path: str):
        lower = path.replace("/", "\\").lower()
        for skip in ("\\auto\\", "\\pitboss\\", "\\pithoss\\"):
            if skip in lower:
                logger.debug("Watchdog ignoring %s save: %s", skip.strip("\\"), path)
                return

        normalized = _norm_path(path)
        name_key = Path(path).name.lower()

        with self._lock:
            if self._still_ignored(normalized, name_key):
                logger.debug(
                    "Watchdog ignoring downloaded/mirrored file: %s",
                    Path(path).name,
                )
                return

            now = time.time()
            if self._seen_until.get(name_key, 0) > now:
                return

            # Coalesce created+modified (+ mirror copies) into one settled emit.
            self._pending_paths[name_key] = path
            old = self._pending_timers.pop(name_key, None)
            if old is not None:
                try:
                    old.cancel()
                except Exception:
                    pass
            timer = threading.Timer(_SETTLE_S, self._fire_settled, args=(name_key,))
            timer.daemon = True
            self._pending_timers[name_key] = timer
            timer.start()

    def _fire_settled(self, name_key: str) -> None:
        with self._lock:
            self._pending_timers.pop(name_key, None)
            path = self._pending_paths.pop(name_key, None)
            if not path:
                return
            normalized = _norm_path(path)
            if self._still_ignored(normalized, name_key):
                return
            now = time.time()
            if self._seen_until.get(name_key, 0) > now:
                return

        # Outside lock: wait for Civ4 / OneDrive to finish writing.
        if not _file_size_stable(path):
            # Still growing — wait once more, then give up or emit if stable.
            time.sleep(_SETTLE_S)
            if not _file_size_stable(path):
                logger.info(
                    "Watchdog: save still unstable, skipping prompt: %s",
                    Path(path).name,
                )
                return

        with self._lock:
            if self._still_ignored(_norm_path(path), name_key):
                return
            if self._seen_until.get(name_key, 0) > time.time():
                return
            self._seen_until[name_key] = time.time() + _COOLDOWN_S

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
        self._lock = threading.Lock()
        self._ignore_paths: set[str] = set()
        self._ignore_path_until: dict[str, float] = {}
        self._ignore_names: set[str] = set()
        self._ignore_name_until: dict[str, float] = {}

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
        """Mark a file path/name to be ignored by the watcher for a short TTL.

        Call this BEFORE downloading/writing a save file to the watch folder.
        Ignore stays active for the whole TTL (multiple FS events), and also
        matches by filename so OneDrive/mirror copies in another folder are
        suppressed. Thread-safe (no Qt calls).
        """
        normalized = _norm_path(filepath)
        name_key = Path(filepath).name.lower()
        until = time.time() + _IGNORE_TTL_S
        with self._lock:
            self._ignore_paths.add(normalized)
            self._ignore_path_until[normalized] = until
            self._ignore_names.add(name_key)
            self._ignore_name_until[name_key] = until
        logger.debug("Watchdog will ignore: %s", Path(filepath).name)

    def start(self):
        """Start watching the save folder(s)."""
        dirs: list[Path] = []
        for raw in self._watch_paths:
            watch_dir = Path(raw)
            if not watch_dir.exists():
                logger.warning("Watch directory does not exist: %s", watch_dir)
                try:
                    watch_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("Created watch directory: %s", watch_dir)
                except Exception as e:
                    logger.error("Cannot create watch directory: %s", e)
                    continue
            dirs.append(watch_dir)

        if not dirs:
            logger.warning("File watcher has no directories to watch")
            return

        self._handler = _SaveFileHandler(
            self._on_file_detected,
            self._ignore_paths,
            self._ignore_path_until,
            self._ignore_names,
            self._ignore_name_until,
            self._lock,
        )
        self._observer = Observer()
        seen: set[str] = set()
        for watch_dir in dirs:
            key = str(watch_dir.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            self._observer.schedule(self._handler, str(watch_dir), recursive=True)
            logger.info("File watcher started on: %s", watch_dir)
        self._observer.daemon = True
        self._observer.start()

    def stop(self):
        """Stop watching."""
        if self._handler is not None:
            with self._lock:
                for timer in list(self._handler._pending_timers.values()):
                    try:
                        timer.cancel()
                    except Exception:
                        pass
                self._handler._pending_timers.clear()
                self._handler._pending_paths.clear()
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
        """Called by watchdog handler when a settled save is detected."""
        logger.info("New save detected: %s", filepath)
        self.new_save_detected.emit(filepath)
