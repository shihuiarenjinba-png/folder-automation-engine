"""Usability regressions without opening Windows or touching real files."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from folder_desktop_app import FolderDesktop, action_label, preview_count


class ConsumerUIHelpersTests(unittest.TestCase):
    def test_localized_actions_preserve_engine_codes(self):
        self.assertEqual(action_label("copy", "日本語"), "コピー（元を残す）")
        self.assertEqual(action_label("move", "English"), "Move (remove original)")
        for action in ("delete", "", "COPY"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                action_label(action, "日本語")

    def test_preview_count_from_worker_header_only(self):
        self.assertEqual(preview_count("0 file(s)\n"), 0)
        self.assertEqual(preview_count("13 file(s)\n{\"dry_run\": true}"), 13)
        for message in ("", "errors=10", "Error 2 file(s)", "3 files", "3 file(s) text"):
            with self.subTest(message=message):
                self.assertIsNone(preview_count(message))

    def _app(self, root):
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = False
        app.closing = False
        app.root = Mock()
        app.root_path = Mock(get=Mock(return_value=str(root)))
        app.t = lambda ja, en: en
        return app

    def test_child_picker_refuses_no_parent_without_dialog(self):
        app = self._app("")
        target = Mock()
        with patch("folder_desktop_app.filedialog.askdirectory") as choose, \
             patch("folder_desktop_app.messagebox.showwarning") as warning:
            app.choose_child_folder(target)
        choose.assert_not_called()
        target.set.assert_not_called()
        warning.assert_called_once()

    def test_child_picker_accepts_existing_direct_child(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            source = parent / "inbox"
            source.mkdir()
            app = self._app(parent)
            target = Mock()
            with patch("folder_desktop_app.filedialog.askdirectory", return_value=str(source)), \
                 patch("folder_desktop_app.messagebox.showwarning") as warning:
                app.choose_child_folder(target)
            target.set.assert_called_once_with("inbox")
            warning.assert_not_called()

    def test_child_picker_rejects_nested_and_outside(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            nested = parent / "inbox" / "sub"
            nested.mkdir(parents=True)
            outside = parent.parent
            app = self._app(parent)
            for bad in (nested, outside):
                with self.subTest(bad=bad), \
                     patch("folder_desktop_app.filedialog.askdirectory", return_value=str(bad)), \
                     patch("folder_desktop_app.messagebox.showwarning") as warning:
                    target = Mock()
                    app.choose_child_folder(target)
                    target.set.assert_not_called()
                    warning.assert_called_once()

    def test_field_edit_revokes_old_preview_and_does_not_touch_files(self):
        app = FolderDesktop.__new__(FolderDesktop)
        app.preview_revision = "old-approved"
        app.preview_input_snapshot = ("old-data",)
        app.preview_summary = Mock()
        app.run_btn = None
        app.t = lambda ja, en: en
        app._invalidate_preview_on_edit()
        self.assertIsNone(app.preview_revision)
        self.assertIsNone(app.preview_input_snapshot)
        app.preview_summary.set.assert_called_once()

    def test_action_selection_writes_only_copy_or_move(self):
        app = FolderDesktop.__new__(FolderDesktop)
        app.lang = Mock(get=Mock(return_value="日本語"))
        app.action_display = Mock(get=Mock(return_value="移動（元を移す）"))
        app.action = Mock()
        app.on_action_selected()
        app.action.set.assert_called_once_with("move")
        app.action_display.get.return_value = "delete"
        app.action.reset_mock()
        app.on_action_selected()
        app.action.set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
