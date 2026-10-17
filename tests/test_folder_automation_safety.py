"""Safety regression tests for the folder automation engine (stdlib only)."""
from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from folder_automation import ConfigError, Engine


def make_engine(root: Path, *, destination: str = "processed", action: str = "move",
                overwrite: bool = False, dry_run: bool = False) -> Engine:
    return Engine({
        "root_dir": str(root),
        "input_dir": "inbox",
        "state_db": ".state/processed.sqlite3",
        "rules": [{"glob": "*.txt", "action": action, "destination": destination,
                   "overwrite": overwrite}],
    }, dry_run=dry_run)


class FolderAutomationSafetyTests(unittest.TestCase):
    def test_collision_remains_unprocessed_and_retries_when_freed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            (root / "processed").mkdir()
            src = root / "inbox" / "a.txt"
            dst = root / "processed" / "a.txt"
            src.write_text("new", encoding="utf-8")
            dst.write_text("old", encoding="utf-8")
            engine = make_engine(root)
            sig = engine.signature(src)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.scan_once(), 0)
            self.assertFalse(engine.seen(sig))
            self.assertEqual(dst.read_text(encoding="utf-8"), "old")
            dst.unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.scan_once(), 1)
            self.assertTrue(engine.seen(sig))
            self.assertFalse(src.exists())
            self.assertEqual(dst.read_text(encoding="utf-8"), "new")

    def test_same_folder_move_never_deletes_source_even_with_overwrite(self) -> None:
        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "inbox").mkdir()
                src = root / "inbox" / "a.txt"
                src.write_text("important", encoding="utf-8")
                engine = make_engine(root, destination="inbox", overwrite=True, dry_run=dry_run)
                with self.assertRaisesRegex(ConfigError, "same file"):
                    engine.scan_once()
                self.assertEqual(src.read_text(encoding="utf-8"), "important")

    def test_blocked_rule_never_falls_through_to_second_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sub in ("inbox", "first", "second"):
                (root / sub).mkdir()
            (root / "inbox" / "a.txt").write_text("new", encoding="utf-8")
            (root / "first" / "a.txt").write_text("old", encoding="utf-8")
            engine = Engine({
                "root_dir": str(root), "input_dir": "inbox",
                "rules": [
                    {"glob": "*.txt", "action": "move", "destination": "first"},
                    {"glob": "*.txt", "action": "move", "destination": "second"},
                ],
            })
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.scan_once(), 0)
            self.assertFalse((root / "second" / "a.txt").exists())
            self.assertTrue((root / "inbox" / "a.txt").exists())

    def test_dry_run_reports_blocked_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            (root / "processed").mkdir()
            (root / "inbox" / "a.txt").write_text("new", encoding="utf-8")
            (root / "processed" / "a.txt").write_text("old", encoding="utf-8")
            engine = make_engine(root, dry_run=True)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(engine.scan_once(), 0)
            self.assertIn("BLOCKED", out.getvalue())
            self.assertFalse((root / ".state").exists())

    def test_symlink_input_is_never_processed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            external = root.parent / (root.name + "-external-file.txt")
            external.write_text("external", encoding="utf-8")
            try:
                (root / "inbox" / "a.txt").symlink_to(external)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            try:
                engine = make_engine(root)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(engine.scan_once(), 0)
                self.assertEqual(external.read_text(encoding="utf-8"), "external")
                self.assertFalse((root / "processed" / "a.txt").exists())
            finally:
                external.unlink(missing_ok=True)

    def test_destination_symlink_is_rejected_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            (root / "processed").mkdir()
            src = root / "inbox" / "a.txt"
            src.write_text("new", encoding="utf-8")
            target = root / "original.txt"
            target.write_text("original", encoding="utf-8")
            try:
                (root / "processed" / "a.txt").symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            engine = make_engine(root, overwrite=True)
            with self.assertRaises(ConfigError):
                engine.scan_once()
            self.assertEqual(src.read_text(encoding="utf-8"), "new")
            self.assertEqual(target.read_text(encoding="utf-8"), "original")

    def test_replace_copy_failure_preserves_old_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            (root / "processed").mkdir()
            src = root / "inbox" / "a.txt"
            dst = root / "processed" / "a.txt"
            src.write_text("new", encoding="utf-8")
            dst.write_text("old", encoding="utf-8")
            engine = make_engine(root, overwrite=True)
            with patch("folder_automation.shutil.copy2", side_effect=OSError("simulated disk error")):
                with self.assertRaisesRegex(OSError, "simulated"):
                    engine.scan_once()
            self.assertEqual(src.read_text(encoding="utf-8"), "new")
            self.assertEqual(dst.read_text(encoding="utf-8"), "old")
            self.assertEqual(list((root / "processed").glob(".folder-automation-*.tmp")), [])

    def test_move_with_explicit_overwrite_replaces_after_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            (root / "processed").mkdir()
            src = root / "inbox" / "a.txt"
            dst = root / "processed" / "a.txt"
            src.write_text("new", encoding="utf-8")
            dst.write_text("old", encoding="utf-8")
            engine = make_engine(root, overwrite=True)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(engine.scan_once(), 1)
            self.assertFalse(src.exists())
            self.assertEqual(dst.read_text(encoding="utf-8"), "new")


if __name__ == "__main__":
    unittest.main()
