"""Tests for save-folder watchdog settle / ignore behaviour."""
from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.gui import file_watcher as fw


class FileStableTests(unittest.TestCase):
    def test_stable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.CivBeyondSwordSave"
            p.write_bytes(b"x" * 1000)
            self.assertTrue(fw._file_size_stable(str(p), checks=2, interval_s=0.05))

    def test_missing_file(self):
        self.assertFalse(
            fw._file_size_stable(str(Path("nope_missing.CivBeyondSwordSave")), checks=2, interval_s=0.01),
        )


class IgnoreAndSettleTests(unittest.TestCase):
    def test_ignore_by_name_survives_multiple_events(self):
        callback = MagicMock()
        lock = threading.Lock()
        ignore_paths: set[str] = set()
        ignore_path_until: dict = {}
        ignore_names: set[str] = set()
        ignore_name_until: dict = {}
        handler = fw._SaveFileHandler(
            callback,
            ignore_paths,
            ignore_path_until,
            ignore_names,
            ignore_name_until,
            lock,
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Kuzyny_BC-3760_to_Frederick.CivBeyondSwordSave"
            p.write_bytes(b"y" * 500)
            # Simulate ignore_next semantics
            until = time.time() + 30
            ignore_paths.add(str(p.resolve()))
            ignore_path_until[str(p.resolve())] = until
            ignore_names.add(p.name.lower())
            ignore_name_until[p.name.lower()] = until

            handler._notify(str(p))
            handler._notify(str(p))
            time.sleep(fw._SETTLE_S + 0.3)
            callback.assert_not_called()

    def test_settle_emits_once(self):
        callback = MagicMock()
        lock = threading.Lock()
        handler = fw._SaveFileHandler(
            callback, set(), {}, set(), {}, lock,
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Kuzyny_BC-3760_to_Frederick.CivBeyondSwordSave"
            p.write_bytes(b"z" * 800)
            handler._notify(str(p))
            handler._notify(str(p))  # modified burst
            time.sleep(fw._SETTLE_S + 1.5)
            self.assertEqual(callback.call_count, 1)


if __name__ == "__main__":
    unittest.main()
