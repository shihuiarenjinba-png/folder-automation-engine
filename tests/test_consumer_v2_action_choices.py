"""Consumer -2 localized copy/move controls must never silently change to move."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from folder_desktop_app import FolderDesktop


class FakeVariable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def model_for(label, *, busy=False, watch_active=False):
    return SimpleNamespace(
        busy=busy, watch_active=watch_active,
        action=FakeVariable("copy"), action_display=FakeVariable(label),
        preview_revision="approved", preview_input_snapshot=("before",),
        status=FakeVariable(""),
        t=lambda ja, en: ja,
    )


class ActionChoiceTests(unittest.TestCase):
    def test_move_is_only_selected_explicitly(self):
        model = model_for("移動（元から移す）")
        FolderDesktop.change_action(model)
        self.assertEqual(model.action.get(), "move")
        self.assertIsNone(model.preview_revision)
        self.assertIsNone(model.preview_input_snapshot)
        self.assertIn("もう一度試運転", model.status.get())

    def test_unknown_selection_is_not_interpreted_as_move(self):
        model = model_for("unexpected selection")
        FolderDesktop.change_action(model)
        self.assertEqual(model.action.get(), "copy")
        self.assertEqual(model.preview_revision, "approved")
        self.assertEqual(model.preview_input_snapshot, ("before",))

    def test_copy_keeps_old_preview_if_action_unchanged(self):
        model = model_for("コピー（元を残す）")
        FolderDesktop.change_action(model)
        self.assertEqual(model.action.get(), "copy")
        self.assertEqual(model.preview_revision, "approved")

    def test_cannot_change_during_running_or_watching(self):
        for blocked in ("busy", "watch_active"):
            model = model_for("移動（元から移す）", **{blocked: True})
            FolderDesktop.change_action(model)
            self.assertEqual(model.action.get(), "copy")

    def test_root_folder_picker_revokes_stale_preview(self):
        model = model_for("コピー（元を残す）")
        model.root = None
        model.root_path = FakeVariable("")
        with patch("folder_desktop_app.filedialog.askdirectory", return_value="C:/Work"):
            FolderDesktop.choose_folder(model)
        self.assertEqual(model.root_path.get(), "C:/Work")
        self.assertIsNone(model.preview_revision)
        self.assertIsNone(model.preview_input_snapshot)


if __name__ == "__main__":
    unittest.main()
