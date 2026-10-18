"""Standalone tests for guided Folder Engine UI logic; no Tk display required."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from folder_automation import ConfigError
from folder_desktop_flow import build_config, build_multi_config, revision, snapshot_inputs
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
            {"output_folder": "COM1"},
            {"input_folder": "lpt9"},
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

    def test_multi_rule_builder_orders_rules_and_keeps_no_overwrite(self):
        cfg = build_multi_config(**self.defaults, extra_rules=[
            {"glob": "*.csv", "destination": "tabular", "action": "move"},
            {"glob": "*.png", "destination": "images", "action": "copy"},
        ])
        self.assertEqual(len(cfg["rules"]), 3)
        self.assertEqual([r["glob"] for r in cfg["rules"]],
                         ["*.pdf", "*.csv", "*.png"])
        self.assertEqual([r["destination"] for r in cfg["rules"]],
                         ["processed", "tabular", "images"])
        self.assertEqual([r["action"] for r in cfg["rules"]],
                         ["copy", "move", "copy"])
        self.assertTrue(all(r["overwrite"] is False for r in cfg["rules"]))
        self.assertNotEqual(revision(cfg), revision(build_config(**self.defaults)))

    def test_multi_rule_builder_rejects_unsafe_destination_and_duplicates(self):
        invalid = [
            [{"glob": "*.PDF", "destination": "docs", "action": "copy"}],
            [{"glob": "*.csv", "destination": "../elsewhere", "action": "move"}],
            [{"glob": "*.csv", "destination": "inbox", "action": "copy"}],
            [{"glob": "*.csv", "destination": "tabular", "action": "delete"}],
        ]
        for rules in invalid:
            with self.subTest(rules=rules), self.assertRaises(ConfigError):
                build_multi_config(**self.defaults, extra_rules=rules)

    def test_multi_rule_matches_first_rule_only(self):
        from folder_automation import Engine
        inbox = self.root / "inbox"
        inbox.mkdir()
        (inbox / "report.csv").write_text("1,2\n", encoding="utf-8")
        cfg = build_multi_config(**self.defaults, extra_rules=[
            {"glob": "*.csv", "destination": "one", "action": "copy"},
            {"glob": "report.*", "destination": "two", "action": "copy"},
        ])
        result = Engine(cfg).scan_once()
        self.assertEqual(result, 1)
        self.assertTrue((self.root / "one" / "report.csv").exists())
        self.assertFalse((self.root / "two" / "report.csv").exists())

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
        app.watch_active = False
        app.preview_revision = None
        app.preview_input_snapshot = ()
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

    def test_snapshot_invalidates_preview_when_file_appears(self):
        root = Path(self.tmp.name)
        inbox = root / "inbox"
        inbox.mkdir()
        first = snapshot_inputs(self.cfg)
        (inbox / "new.pdf").write_bytes(b"new PDF")
        self.assertNotEqual(first, snapshot_inputs(self.cfg))

    def test_changed_file_and_removed_file_require_new_preview(self):
        root = Path(self.tmp.name)
        inbox = root / "inbox"
        inbox.mkdir()
        file = inbox / "new.pdf"
        file.write_bytes(b"old")
        original = snapshot_inputs(self.cfg)
        file.write_bytes(b"different size now")
        self.assertNotEqual(original, snapshot_inputs(self.cfg))
        file.unlink()
        self.assertNotEqual(original, snapshot_inputs(self.cfg))

    def test_live_worker_fails_closed_if_files_changed_after_preview(self):
        import queue
        from types import SimpleNamespace
        root = Path(self.tmp.name)
        inbox = root / "inbox"
        inbox.mkdir()
        app = self.app
        app.preview_input_snapshot = snapshot_inputs(self.cfg)
        (inbox / "unexpected.pdf").write_bytes(b"unexpected")
        app.messages = queue.Queue()
        app.set_busy = Mock()
        with patch("folder_desktop_app.threading.Thread",
                   side_effect=lambda target, daemon: SimpleNamespace(start=target)):
            app.start_worker("live", self.cfg)
        event = app.messages.get_nowait()
        self.assertFalse(event[1])
        self.assertIn("Files changed", event[2])
        self.assertTrue((inbox / "unexpected.pdf").exists())
        self.assertFalse((root / "processed").exists())

    def test_symlink_input_folder_is_refused(self):
        root = Path(self.tmp.name)
        external = root / "external"
        external.mkdir()
        try:
            (root / "inbox").symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(str(exc))
        with self.assertRaises(ConfigError):
            snapshot_inputs(self.cfg)


if __name__ == "__main__":
    unittest.main()
