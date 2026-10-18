"""Watcher engine only processes explicitly stable input signatures."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from folder_automation import Engine
from folder_desktop_flow import build_config, snapshot_inputs


class WatchEligibilityTests(unittest.TestCase):
    def test_future_file_is_not_automatically_processed_at_first_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_dir = root / "inbox"
            input_dir.mkdir()
            cfg = build_config(root_dir=temp, input_folder="inbox", output_folder="processed",
                               filename_glob="*.pdf", action="copy")
            engine = Engine(cfg, dry_run=False)
            file = input_dir / "new.pdf"
            file.write_bytes(b"incomplete")
            old_snapshot = tuple()
            new_snapshot = snapshot_inputs(cfg)
            stable = {item[0] for item in new_snapshot if item in old_snapshot}
            eligible = {engine.signature(input_dir / item) for item in stable}
            self.assertEqual(engine.scan_once(eligible_signatures=eligible), 0)
            self.assertFalse((root / "processed" / "new.pdf").exists())

            file.write_bytes(b"complete content")
            newer_snapshot = snapshot_inputs(cfg)
            stable = {item[0] for item in newer_snapshot if item in new_snapshot}
            self.assertEqual(stable, set())
            self.assertEqual(engine.scan_once(eligible_signatures=set()), 0)
            newest_snapshot = snapshot_inputs(cfg)
            eligible = {engine.signature(input_dir / item[0])
                        for item in newest_snapshot if item in newer_snapshot}
            self.assertEqual(engine.scan_once(eligible_signatures=eligible), 1)
            self.assertEqual((root / "processed" / "new.pdf").read_bytes(), b"complete content")


if __name__ == "__main__":
    unittest.main()
