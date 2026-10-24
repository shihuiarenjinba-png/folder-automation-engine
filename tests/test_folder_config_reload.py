"""Pure config and no-window restore tests for the standard Folder GUI."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from folder_automation import ConfigError
from folder_desktop_flow import build_multi_config, revision
from folder_desktop_app import FolderDesktop, validate_saved_config


class SafeSavedConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "inbox").mkdir()
        self.cfg = build_multi_config(
            root_dir=str(self.root), input_folder="inbox", output_folder="processed",
            filename_glob="*.pdf", action="copy",
            extra_rules=[{"glob": "*.csv", "destination": "out-csv", "action": "move"}],
        )

    def test_valid_export_can_be_reopened_without_changing_anything(self):
        path = self.root / "saved.json"
        path.write_text(json.dumps(self.cfg), encoding="utf-8")
        saved_bytes = path.read_bytes()
        loaded = validate_saved_config(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(loaded, self.cfg)
        self.assertEqual(revision(loaded), revision(self.cfg))
        self.assertEqual(path.read_bytes(), saved_bytes)
        self.assertFalse((self.root / "processed").exists())
        self.assertFalse((self.root / "out-csv").exists())

    def test_reject_corrupted_or_extra_fields(self):
        for changed in [
            [],
            {"rules": []},
            {**self.cfg, "unexpected_command": "cmd.exe"},
            {**self.cfg, "rules": [{**self.cfg["rules"][0], "overwrite": True}, self.cfg["rules"][1]]},
            {**self.cfg, "state_db": "../outside.db"},
            {**self.cfg, "rules": [{**self.cfg["rules"][0], "action": "delete"}, self.cfg["rules"][1]]},
        ]:
            with self.subTest(changed=changed), self.assertRaises((ConfigError, ValueError)):
                validate_saved_config(changed)

    def test_load_saved_config_changes_only_ui_fields_and_invalidates_preview(self):
        path = self.root / "saved.json"
        path.write_text(json.dumps(self.cfg), encoding="utf-8")
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = False
        app.lang = Mock()
        app.lang.get.return_value = "English"
        app.root = Mock()
        app.root_path = Mock()
        app.input_folder = Mock()
        app.output_folder = Mock()
        app.pattern = Mock()
        app.action = Mock()
        app.status = Mock()
        app.preview_revision = "old-revision"
        app.preview_input_snapshot = ("old-file",)
        with patch("folder_desktop_app.filedialog.askopenfilename", return_value=str(path)), \
             patch("folder_desktop_app.Engine") as engine:
            app.load_config()
        app.root_path.set.assert_called_once_with(str(self.root.resolve()))
        app.input_folder.set.assert_called_once_with("inbox")
        app.output_folder.set.assert_called_once_with("processed")
        app.pattern.set.assert_called_once_with("*.pdf")
        app.action.set.assert_called_once_with("copy")
        self.assertEqual(app.extra_rules, [{"destination": "out-csv", "glob": "*.csv", "action": "move"}])
        self.assertIsNone(app.preview_revision)
        self.assertIsNone(app.preview_input_snapshot)
        engine.assert_not_called()

    def test_invalid_json_is_rejected_without_modifying_form(self):
        path = self.root / "invalid.json"
        path.write_text('{"rules":[{"action":"delete"}]}', encoding="utf-8")
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = False
        app.lang = Mock()
        app.lang.get.return_value = "日本語"
        app.root = Mock()
        app.root_path = Mock()
        app.status = Mock()
        app.preview_revision = "good"
        app.preview_input_snapshot = ("kept",)
        with patch("folder_desktop_app.filedialog.askopenfilename", return_value=str(path)), \
             patch("folder_desktop_app.messagebox.showerror") as error:
            app.load_config()
        app.root_path.set.assert_not_called()
        self.assertEqual(app.preview_revision, "good")
        self.assertEqual(app.preview_input_snapshot, ("kept",))
        error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
