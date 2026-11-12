"""Tests for local Store-MSIX handoff behavior."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from qa.verify_local_msix_handoff import sha256


class LocalMsixHandoffTests(unittest.TestCase):
    def test_sha256_reads_exact_file_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.msix"
            path.write_bytes(b"abc")
            self.assertEqual(sha256(path), hashlib.sha256(b"abc").hexdigest())

    def test_unsigned_candidate_has_no_signature_file_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.msix"
            with ZipFile(path, "w") as z:
                z.writestr("AppxManifest.xml", "<Package/>")
            with ZipFile(path) as z:
                self.assertNotIn("AppxSignature.p7x", z.namelist())


if __name__ == "__main__":
    unittest.main()
