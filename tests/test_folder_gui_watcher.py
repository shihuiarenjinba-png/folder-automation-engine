"""Safe state transitions for opt-in folder watcher (no real writes)."""
from __future__ import annotations

import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from folder_desktop_app import FolderDesktop
from folder_desktop_flow import build_config, revision, snapshot_inputs


class FolderWatcherGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "inbox").mkdir()
        (root / "inbox" / "sample.pdf").write_bytes(b"sample")
        self.cfg = build_config(root_dir=str(root), input_folder="inbox",
                                output_folder="processed", filename_glob="*.pdf",
                                action="copy")
        self.app = FolderDesktop.__new__(FolderDesktop)
        self.app.root = None
        self.app.t = lambda ja, en: ja
        self.app.busy = False
        self.app.watch_active = False
        self.app.watch_stop = threading.Event()
        self.app.watch_seconds = Mock(get=Mock(return_value="60"))
        self.app.get_config = Mock(return_value=self.cfg)
        self.app.status = Mock()
        self.app.set_busy = Mock()
        self.app.preview_revision = None
        self.app.preview_input_snapshot = None

    def test_no_watch_without_successful_preview(self):
        with patch("folder_desktop_app.messagebox.showwarning") as warning, \
             patch("folder_desktop_app.Engine") as engine:
            self.app.start_watch()
            warning.assert_called_once()
            engine.assert_not_called()
        self.assertFalse(self.app.watch_active)

    def test_changed_config_refuses_watch(self):
        self.app.preview_revision = "old sha"
        self.app.preview_input_snapshot = snapshot_inputs(self.cfg)
        with patch("folder_desktop_app.messagebox.showwarning") as warning:
            self.app.start_watch()
            warning.assert_called_once()
        self.assertFalse(self.app.watch_active)

    def test_reject_confirmation_keeps_preview_and_files(self):
        self.app.preview_revision = revision(self.cfg)
        self.app.preview_input_snapshot = snapshot_inputs(self.cfg)
        with patch("folder_desktop_app.messagebox.askyesno", return_value=False):
            self.app.start_watch()
        self.assertFalse(self.app.watch_active)
        self.assertEqual(self.app.preview_revision, revision(self.cfg))
        self.assertFalse((Path(self.temp.name) / "processed").exists())

    def test_interval_limit_enforced(self):
        self.app.preview_revision = revision(self.cfg)
        self.app.preview_input_snapshot = snapshot_inputs(self.cfg)
        for interval in ("0", "9", "3601", "abc"):
            self.app.watch_seconds.get.return_value = interval
            with self.subTest(interval=interval), \
                 patch("folder_desktop_app.messagebox.showwarning") as warning:
                self.app.start_watch()
                warning.assert_called_once()
                self.assertFalse(self.app.watch_active)

    def test_stop_watch_signals_without_running_any_actions(self):
        self.app.watch_active = True
        self.app.stop_watch()
        self.assertTrue(self.app.watch_stop.is_set())


if __name__ == "__main__":
    unittest.main()
