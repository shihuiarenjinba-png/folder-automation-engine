"""Usability regressions without opening Windows or touching real files."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from folder_desktop_app import (
    FolderDesktop,
    _format_store_capture_activity,
    action_label,
    parse_store_capture_request,
    preview_count,
)


class ConsumerUIHelpersTests(unittest.TestCase):
    def test_store_capture_activity_removes_absolute_local_paths(self):
        raw = (
            '1 file(s)\n'
            '{"file":"D:\\\\TeamArchive\\\\Incoming\\\\Report.pdf",'
            '"action":"copy","destination":"D:\\\\TeamArchive\\\\Documents\\\\Report.pdf",'
            '"dry_run":true}\n'
        )
        displayed = _format_store_capture_activity(raw, japanese=False)
        self.assertIn("Documents/Report.pdf", displayed)
        self.assertNotIn("D:\\", displayed)
        self.assertNotIn("TeamArchive", displayed)

    def test_store_capture_hook_is_fail_closed_outside_disposable_ci(self):
        args = [
            "--store-capture-state", "setup", "--store-capture-root", "TeamArchive",
            "--store-capture-ready", "TeamArchive/.capture-ready-setup",
        ]
        with self.assertRaisesRegex(ValueError, "disposable GitHub-hosted Windows"):
            parse_store_capture_request(args, {})

    def test_normal_launch_does_not_enable_store_capture_hook(self):
        self.assertIsNone(parse_store_capture_request([], {}))

    def test_store_capture_hook_rejects_unknown_state_before_paths(self):
        args = [
            "--store-capture-state", "invented", "--store-capture-root", "TeamArchive",
            "--store-capture-ready", "TeamArchive/.capture-ready-invented",
        ]
        environment = {
            "GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted",
            "OS": "Windows_NT", "FOLDER_STORE_CAPTURE": "EXACT_PACKAGED_UI_V1",
        }
        with self.assertRaisesRegex(ValueError, "Unknown Store capture state"):
            parse_store_capture_request(args, environment)

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

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_child_picker_rejects_junction(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            real = parent / "real"
            junction = parent / "junction"
            real.mkdir()
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(real)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                self.skipTest(f"junction creation unavailable: {result.stderr.strip()}")
            try:
                app = self._app(parent)
                target = Mock()
                with patch("folder_desktop_app.filedialog.askdirectory", return_value=str(junction)), \
                     patch("folder_desktop_app.messagebox.showwarning") as warning:
                    app.choose_child_folder(target)
                target.set.assert_not_called()
                warning.assert_called_once()
            finally:
                if junction.exists():
                    junction.rmdir()

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_parent_picker_rejects_folder_beneath_junction_ancestor(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            real_root = base / "real-root"
            selected = real_root / "selected"
            selected.mkdir(parents=True)
            alias = base / "alias"
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(real_root)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                self.skipTest(f"junction creation unavailable: {result.stderr.strip()}")
            try:
                app = self._app("")
                app.root_path = Mock()
                with patch("folder_desktop_app.filedialog.askdirectory",
                           return_value=str(alias / "selected")), \
                     patch("folder_desktop_app.messagebox.showwarning") as warning:
                    app.choose_folder()
                app.root_path.set.assert_not_called()
                warning.assert_called_once()
            finally:
                if alias.exists():
                    alias.rmdir()

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


    def test_set_busy_uses_only_ttk_button_options(self):
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = False
        app.closing = False
        app.preview_revision = None
        app.entries = [Mock()]
        app.action_combo = Mock()
        app.choose_btn = Mock()
        app.preview_btn = Mock()
        app.save_btn = Mock()
        app.load_btn = Mock()
        app.rules_btn = Mock()
        app.advanced_btn = Mock()
        app.child_browse_buttons = []
        app.run_btn = Mock()
        app.watch_interval_entry = Mock()
        app.watch_start_btn = Mock()
        app.watch_stop_btn = Mock()

        app.set_busy(False)

        options = app.run_btn.configure.call_args.kwargs
        self.assertEqual(options, {"state": "disabled"})
        self.assertNotIn("bg", options)


if __name__ == "__main__":
    unittest.main()

