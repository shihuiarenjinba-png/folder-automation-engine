import json
import tempfile
import unittest
from pathlib import Path
from folder_automation import Engine


class StableFileTests(unittest.TestCase):
    def test_recent_file_is_not_moved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "inbox"
            incoming.mkdir()
            (incoming / "report.csv").write_text("id\n1\n", encoding="utf-8")
            config = {
                "root_dir": str(root),
                "input_dir": "inbox",
                "state_db": ".state/processed.sqlite3",
                "min_stable_seconds": 3600,
                "rules": [{"glob": "*.csv", "action": "move",
                           "destination": "output", "overwrite": False}],
            }
            engine = Engine(config)
            self.assertEqual(engine.scan_once(), 0)
            self.assertTrue((incoming / "report.csv").exists())
            self.assertFalse((root / "output" / "report.csv").exists())


if __name__ == "__main__":
    unittest.main()
