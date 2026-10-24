"""Consumer -2 UI safety regression without Tk window creation."""
from __future__ import annotations
import unittest
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch
from folder_desktop_app import FolderDesktop

ROOT = Path(__file__).resolve().parents[1]

class FakeVariable:
    def __init__(self):
        self.value = None
    def set(self, value):
        self.value = value
    def get(self):
        return self.value or ""

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

    def test_picker_rejects_outside_folder_and_links(self):
        with TemporaryDirectory() as d:
            base = Path(d)
            root = base / "root"
            outsider = base / "outside"
            root.mkdir()
            outsider.mkdir()
            model = SimpleNamespace(
                busy=False, watch_active=False, root=None,
                root_path=FakeVariable(), input_folder=FakeVariable(),
                output_folder=FakeVariable(), status=FakeVariable(),
                preview_revision="approved",
                preview_input_snapshot=("before",),
                t=lambda ja, en: en,
            )
            model.root_path.set(str(root))
            model.input_folder.set("inbox")
            model.output_folder.set("processed")
            with patch("folder_desktop_app.filedialog.askdirectory", return_value=str(outsider)):
                with patch("folder_desktop_app.messagebox.showerror") as showerror:
                    FolderDesktop._choose_child_folder(model, for_input=True)
            self.assertTrue(showerror.called)
            self.assertEqual(model.input_folder.get(), "inbox")
            self.assertEqual(model.preview_revision, "approved")

    def test_browsed_folders_revoke_approved_preview(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "inbox").mkdir()
            (root / "processed").mkdir()
            model = SimpleNamespace(
                busy=False, watch_active=False, root=None,
                root_path=FakeVariable(), input_folder=FakeVariable(),
                output_folder=FakeVariable(), status=FakeVariable(),
                preview_revision="approved",
                preview_input_snapshot=("before",),
                t=lambda ja, en: en,
            )
            model.root_path.set(str(root))
            model.input_folder.set("original")
            model.output_folder.set("processed")
            with patch("folder_desktop_app.filedialog.askdirectory", return_value=str(root / "inbox")):
                FolderDesktop._choose_child_folder(model, for_input=True)
            self.assertEqual(model.input_folder.get(), "inbox")
            self.assertIsNone(model.preview_revision)
            self.assertIsNone(model.preview_input_snapshot)
            self.assertIn("Preview again", model.status.get())

    def test_destination_cannot_equal_source(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "inbox").mkdir()
            model = SimpleNamespace(
                busy=False, watch_active=False, root=None,
                root_path=FakeVariable(), input_folder=FakeVariable(),
                output_folder=FakeVariable(), status=FakeVariable(),
                preview_revision="approved",
                preview_input_snapshot=("before",),
                t=lambda ja, en: en,
            )
            model.root_path.set(str(root))
            model.input_folder.set("inbox")
            model.output_folder.set("out")
            with patch("folder_desktop_app.filedialog.askdirectory", return_value=str(root / "inbox")):
                with patch("folder_desktop_app.messagebox.showerror") as showerror:
                    FolderDesktop._choose_child_folder(model, for_input=False)
            self.assertTrue(showerror.called)
            self.assertEqual(model.output_folder.get(), "out")
            self.assertEqual(model.preview_revision, "approved")

if __name__ == "__main__":
    unittest.main()
