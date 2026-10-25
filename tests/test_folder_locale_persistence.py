"""No-window regression tests for persisted Folder GUI language."""
import unittest
from unittest.mock import Mock, patch

from folder_desktop_app import FolderDesktop, load_gui_language, save_gui_language


class LanguagePreferenceTests(unittest.TestCase):
    @patch("folder_desktop_app.load_preferences", return_value={"locale": "English"})
    def test_restore_english_after_restart(self, getter):
        self.assertEqual(load_gui_language(), "English")
        getter.assert_called_once_with("FolderAutomationEngine", ("locale",))

    @patch("folder_desktop_app.load_preferences", return_value={"locale": "unexpected"})
    def test_unsupported_saved_locale_falls_back_to_japanese(self, _getter):
        self.assertEqual(load_gui_language(), "日本語")

    @patch("folder_desktop_app.load_preferences", side_effect=ValueError("damaged"))
    def test_corrupt_preferences_fail_closed_without_overwrite(self, _getter):
        self.assertEqual(load_gui_language(), "日本語")

    @patch("folder_desktop_app.save_preferences")
    def test_language_save_is_allowlisted(self, setter):
        save_gui_language("English")
        setter.assert_called_once_with("FolderAutomationEngine", {"locale": "English"}, ("locale",))
        with self.assertRaises(ValueError):
            save_gui_language("unsupported")
        setter.assert_called_once()

    @patch("folder_desktop_app.save_gui_language")
    def test_switch_language_persists_before_rebuild(self, setter):
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = False
        app.displayed_language = "日本語"
        app.lang = Mock()
        app.lang.get.return_value = "English"
        app.build = Mock()
        app.change_language()
        setter.assert_called_once_with("English")
        app.build.assert_called_once()

    @patch("folder_desktop_app.save_gui_language", side_effect=OSError("read-only"))
    @patch("folder_desktop_app.messagebox.showerror")
    def test_failed_save_rolls_back_language_and_reports_error(self, showerror, _setter):
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = False
        app.displayed_language = "日本語"
        app.lang = Mock()
        app.lang.get.return_value = "English"
        app.root = Mock()
        app.build = Mock()
        app.change_language()
        app.lang.set.assert_called_once_with("日本語")
        app.build.assert_not_called()
        showerror.assert_called_once()

    @patch("folder_desktop_app.save_gui_language")
    def test_switch_is_blocked_during_watching(self, setter):
        app = FolderDesktop.__new__(FolderDesktop)
        app.busy = False
        app.watch_active = True
        app.displayed_language = "日本語"
        app.lang = Mock()
        app.build = Mock()
        app.change_language()
        app.lang.set.assert_called_once_with("日本語")
        setter.assert_not_called()
        app.build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
