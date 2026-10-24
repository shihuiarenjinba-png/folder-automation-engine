"""Consumer -2 UI safety regression without Tk window creation."""
from __future__ import annotations
import unittest
from pathlib import Path
from types import SimpleNamespace
from folder_desktop_app import FolderDesktop

ROOT = Path(__file__).resolve().parents[1]

class FakeVariable:
    def __init__(self):
        self.value = None
    def set(self, value):
        self.value = value

class ConsumerV2GuiTests(unittest.TestCase):
    def test_folder_location_is_selected_not_typed(self):
        text = (ROOT / "folder_desktop_app.py").read_text(encoding="utf-8")
        self.assertIn('textvariable=self.root_path, state="readonly"', text)
        self.assertIn('entry is self.root_entry else "normal"', text)
        self.assertIn('command=self.choose_folder', text)

    def test_quick_presets_are_optional_not_only_available_types(self):
        text = (ROOT / "folder_desktop_app.py").read_text(encoding="utf-8")
        for pattern in ("*.pdf", "*.docx", "*.xlsx", "*.zip", "*.jpg", "*.png"):
            self.assertIn('"' + pattern + '"', text)
        self.assertIn("Other file types can be entered", text)

    def test_changing_quick_type_revokes_previous_preview(self):
        pattern, status = FakeVariable(), FakeVariable()
        model = SimpleNamespace(
            busy=False, watch_active=False, pattern=pattern,
            preview_revision="old", preview_input_snapshot=("old",),
            status=status, t=lambda ja, en: en,
        )
        FolderDesktop.set_quick_pattern(model, "*.xlsx")
        self.assertEqual(pattern.value, "*.xlsx")
        self.assertIsNone(model.preview_revision)
        self.assertIsNone(model.preview_input_snapshot)
        self.assertIn("Preview again", status.value)

    def test_running_or_watching_cannot_change_preset(self):
        for attr in ("busy", "watch_active"):
            pattern, status = FakeVariable(), FakeVariable()
            model = SimpleNamespace(
                busy=attr=="busy", watch_active=attr=="watch_active",
                pattern=pattern, preview_revision="approved",
                preview_input_snapshot=("before",), status=status,
                t=lambda ja, en: en,
            )
            FolderDesktop.set_quick_pattern(model, "*.pdf")
            self.assertIsNone(pattern.value)
            self.assertEqual(model.preview_revision, "approved")
            self.assertEqual(model.preview_input_snapshot, ("before",))

if __name__ == "__main__":
    unittest.main()
