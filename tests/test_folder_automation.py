from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from folder_automation import Engine


class FolderAutomationTests(unittest.TestCase):
    def test_destination_collision_is_not_marked_processed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inbox = root / "inbox"
            dst_dir = root / "processed"
            inbox.mkdir()
            dst_dir.mkdir()
            src = inbox / "sample.pdf"
            src.write_text("new", encoding="utf-8")
            (dst_dir / "sample.pdf").write_text("old", encoding="utf-8")

            engine = Engine({
                "root_dir": str(root),
                "input_dir": "inbox",
                "state_db": ".state/processed.sqlite3",
                "rules": [{"glob": "*.pdf", "action": "move", "destination": "processed", "overwrite": False}],
            })
            signature = engine.signature(src)
            self.assertEqual(engine.scan_once(), 0)
            self.assertTrue(src.exists())
            self.assertFalse(engine.seen(signature))

            (dst_dir / "sample.pdf").unlink()
            self.assertEqual(engine.scan_once(), 1)
            self.assertFalse(src.exists())
            self.assertTrue((dst_dir / "sample.pdf").exists())
            self.assertTrue(engine.seen(signature))

    def test_matching_blocked_rule_does_not_fall_through_to_later_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inbox = root / "inbox"
            inbox.mkdir()
            src = inbox / "x.csv"
            src.write_text("a,b", encoding="utf-8")
            first = root / "first"
            second = root / "second"
            first.mkdir()
            (first / "x.csv").write_text("existing", encoding="utf-8")

            engine = Engine({
                "root_dir": str(root),
                "input_dir": "inbox",
                "state_db": ".state/processed.sqlite3",
                "rules": [
                    {"glob": "*.csv", "action": "move", "destination": "first", "overwrite": False},
                    {"glob": "*.csv", "action": "move", "destination": "second", "overwrite": False},
                ],
            })
            self.assertEqual(engine.scan_once(), 0)
            self.assertTrue(src.exists())
            self.assertFalse((second / "x.csv").exists())


if __name__ == "__main__":
    unittest.main()
