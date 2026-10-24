"""Regression: do not organize partially downloaded browser files."""
from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from folder_automation import Engine
from folder_desktop_flow import build_config


class IncompleteDownloadSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="folder-v2-download-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input_dir = self.root / "inbox"
        self.input_dir.mkdir()
        self.output_dir = self.root / "processed"

    def config(self, pattern: str = "*.pdf") -> dict:
        return build_config(
            root_dir=str(self.root), input_folder="inbox",
            output_folder="processed", filename_glob=pattern,
            action="copy",
        )

    def scan(self, *, dry_run: bool = False, pattern: str = "*.pdf") -> tuple[int, str]:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            count = Engine(self.config(pattern), dry_run=dry_run).scan_once()
        return count, captured.getvalue()

    def test_pending_chromium_download_blocks_same_name_pdf(self) -> None:
        source = self.input_dir / "report.pdf"
        source.write_bytes(b"not yet complete")
        partial = self.input_dir / "report.pdf.crdownload"
        partial.write_bytes(b"transfer in progress")
        count, output = self.scan()
        self.assertEqual(count, 0)
        self.assertIn("SKIP unfinished download", output)
        self.assertEqual(source.read_bytes(), b"not yet complete")
        self.assertFalse((self.output_dir / source.name).exists())

        # No record is made for a skipped item: a later complete file is eligible.
        partial.unlink()
        source.write_bytes(b"final report")
        count, _ = self.scan()
        self.assertEqual(count, 1)
        self.assertEqual((self.output_dir / source.name).read_bytes(), b"final report")

    def test_firefox_part_blocks_the_corresponding_pdf(self) -> None:
        source = self.input_dir / "monthly.pdf"
        source.write_bytes(b"partial")
        (self.input_dir / "monthly.pdf.PART").write_bytes(b"in progress")
        count, _ = self.scan(dry_run=True)
        self.assertEqual(count, 0)
        self.assertFalse(self.output_dir.exists())

    def test_explicit_partial_filename_glob_cannot_copy_unfinished_file(self) -> None:
        partial = self.input_dir / "monthly.pdf.part"
        partial.write_bytes(b"in progress")
        count, result = self.scan(pattern="*.part")
        self.assertEqual(count, 0)
        self.assertIn("SKIP unfinished download", result)
        self.assertFalse((self.output_dir / partial.name).exists())

    def test_complete_file_still_works_and_dry_run_has_no_side_effects(self) -> None:
        src = self.input_dir / "complete.pdf"
        src.write_bytes(b"ready")
        n, _ = self.scan(dry_run=True)
        self.assertEqual(n, 1)
        self.assertFalse(self.output_dir.exists())
        n, _ = self.scan()
        self.assertEqual(n, 1)
        self.assertTrue(src.exists())
        self.assertEqual((self.output_dir / "complete.pdf").read_bytes(), b"ready")

    def test_other_filename_formats_remain_available(self) -> None:
        tmp = self.input_dir / "data.tmp"
        tmp.write_bytes(b"valid temporary document")
        n, _ = self.scan(pattern="*.tmp")
        self.assertEqual(n, 1)
        self.assertEqual((self.output_dir / "data.tmp").read_bytes(), b"valid temporary document")


if __name__ == "__main__":
    unittest.main()
