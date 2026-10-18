"""Standalone tests for guided Folder Engine UI logic; no Tk display required."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from folder_automation import ConfigError
from folder_desktop_flow import build_config, revision
from folder_desktop_app import FolderDesktop


class FolderFormTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.defaults = dict(
            root_dir=str(self.root), input_folder="inbox", output_folder="processed",
            filename_glob="*.pdf", action="copy",
        )

    def test_safe_usable_config_does_not_enable_overwrite(self):
        cfg = build_config(**self.defaults)
        self.assertEqual(cfg["input_dir"], "inbox")
        self.assertEqual(cfg["rules"][0]["destination"], "processed")
        self.assertEqual(cfg["rules"][0]["action"], "copy")
        self.assertIs(cfg["rules"][0]["overwrite"], False)

    def test_reject_same_folder_and_parent_escape(self):
        for updated in [
            {"output_folder": "inbox"},
            {"output_folder": "INBOX"},
            {"input_folder": "../private"},
            {"output_folder": r"..\\outside"},
            {"output_folder": "C:drive"},
            {"input_folder": ".state"},
            {"filename_glob": "../*.pdf"},
        ]:
            with self.subTest(updated=updated):
                with self.assertRaises(ConfigError):
                    build_config(**{**self.defaults, **updated})

    def test_missing_root_or_unsupported_action_rejected(self):
        with self.assertRaises(ConfigError):
            build_config(**{**self.defaults, "root_dir": ""})
        with self.assertRaises(ConfigError):
            build_config(**{**self.defaults, "action": "delete"})

    def test_revision_changes_on_any_rule_or_mode(self):
        first = build_config(**self.defaults)
        rev = revision(first)
        self.assertEqual(rev, revision(json.loads(json.dumps(first))))
        changed = build_config(**{**self.defaults, "filename_glob": "*.csv"})
        self.assertNotEqual(rev, revision(changed))
        moved = build_config(**{**self.defaults, "action": "move"})
        self.assertNotEqual(rev, revision(moved))


class FolderGuiGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.cfg = build_config(
            root_dir=str(root), input_folder="inbox",
            output_folder="processed", filename_glob="*.pdf", action="copy"
        )
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.preview_revision = None
        app.get_config = Mock(return_value=self.cfg)
        app.root = None
        app.t = lambda ja, en: en
        app.action = Mock()
        app.action.get.return_value = "copy"
        app.start_worker = Mock()
        app.status = Mock()
        self.app = app

    def test_live_needs_same_preview(self):
        with patch("folder_desktop_app.messagebox.showwarning") as warning:
            self.app.run_live()
        warning.assert_called_once()
        self.app.start_worker.assert_not_called()

    def test_declining_confirmation_preserves_preview(self):
        self.app.preview_revision = revision(self.cfg)
        with patch("folder_desktop_app.messagebox.askyesno", return_value=False):
            self.app.run_live()
        self.assertEqual(self.app.preview_revision, revision(self.cfg))
        self.app.start_worker.assert_not_called()

    def test_approved_live_consumes_preview_first(self):
        self.app.preview_revision = revision(self.cfg)
        with patch("folder_desktop_app.messagebox.askyesno", return_value=True):
            self.app.run_live()
        self.app.start_worker.assert_called_once_with("live", self.cfg)
        self.assertIsNone(self.app.preview_revision)

    def test_edit_after_preview_refuses_execution(self):
        self.app.preview_revision = revision(self.cfg)
        self.cfg["rules"][0]["glob"] = "*.exe"
        with patch("folder_desktop_app.messagebox.showwarning") as warning:
            self.app.run_live()
        warning.assert_called_once()
        self.app.start_worker.assert_not_called()

    def test_existing_config_save_cannot_overwrite(self):
        config = Path(self.tmp.name) / "existing.json"
        config.write_text("valuable settings", encoding="utf-8")
        with patch("folder_desktop_app.filedialog.asksaveasfilename", return_value=str(config)), \
             patch("folder_desktop_app.messagebox.showerror") as error:
            self.app.save_config()
        self.assertEqual(config.read_text(encoding="utf-8"), "valuable settings")
        error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
