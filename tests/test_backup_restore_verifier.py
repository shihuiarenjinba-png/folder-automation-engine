"""Backup integrity + isolated restore regression tests (stdlib only)."""
import json
import tempfile
import unittest
from pathlib import Path

from backup_restore_verifier import snapshot, verify


class BackupVerificationTest(unittest.TestCase):
    def test_identical_backup_and_detect_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            source, backup = p / "source", p / "backup"
            (source / "nested").mkdir(parents=True)
            (backup / "nested").mkdir(parents=True)
            original = b"important content 123"
            (source / "nested" / "a.txt").write_bytes(original)
            (backup / "nested" / "a.txt").write_bytes(original)
            manifest = snapshot(source, p / "trusted_manifest.json")
            ok_dir = verify(backup, manifest, p / "report_a", restore_test_max_bytes=1024)
            ok = json.loads((ok_dir / "verification.json").read_text(encoding="utf-8"))
            self.assertEqual(ok["summary"]["verified"], 1)
            self.assertEqual(ok["summary"]["sample_restored"], 1)
            self.assertEqual(ok["summary"]["findings"], 0)
            self.assertEqual((backup / "nested" / "a.txt").read_bytes(), original)
            (backup / "nested" / "a.txt").write_bytes(b"corrupted")
            failed_dir = verify(backup, manifest, p / "report_b", restore_test_max_bytes=1024)
            failed = json.loads((failed_dir / "verification.json").read_text(encoding="utf-8"))
            self.assertEqual(failed["status"], "REVIEW")
            self.assertIn("size_mismatch", {f["code"] for f in failed["findings"]})

    def test_extra_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            source, backup = p / "src", p / "bk"
            source.mkdir()
            backup.mkdir()
            (source / "a").write_text("a", encoding="utf-8")
            (backup / "a").write_text("a", encoding="utf-8")
            (backup / "extra").write_text("extra", encoding="utf-8")
            m = snapshot(source, p / "m.json")
            out = verify(backup, m, p / "reports", restore_test_max_bytes=0)
            report = json.loads((out / "verification.json").read_text(encoding="utf-8"))
            self.assertIn("unexpected_backup_file", {f["code"] for f in report["findings"]})

    def test_traversal_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            backup = p / "bk"
            backup.mkdir()
            m = p / "malicious.json"
            m.write_text(json.dumps({"format": "local_backup_manifest_v1", "file_count": 1,
                                     "files": [{"path": "../escape", "size": 0, "sha256": "0" * 64}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify(backup, m, p / "reports")

    def test_manifest_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            source = p / "src"
            source.mkdir()
            m = snapshot(source, p / "m.json")
            with self.assertRaises(FileExistsError):
                snapshot(source, m)


if __name__ == "__main__":
    unittest.main()
