"""Tests for exact MSIX package inventory verification."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import hashlib

from qa.verify_msix_inventory import verify


class MsixInventoryVerifierTests(unittest.TestCase):
    def test_uri_encoded_plus_and_makeappx_metadata_are_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "app.msix"
            expected = b"timezone"
            with ZipFile(package, "w", ZIP_DEFLATED) as z:
                z.writestr("_internal/tzdata/GMT%2B1", expected)
                z.writestr("AppxBlockMap.xml", b"block")
                z.writestr("[Content_Types].xml", b"types")
            inventory = {
                "source_commit": "a" * 40,
                "version": "1.0.0.0",
                "file_count": 1,
                "files": [{
                    "path": "_internal/tzdata/GMT+1",
                    "size": len(expected),
                    "sha256": hashlib.sha256(expected).hexdigest(),
                }],
            }
            inv = root / "inventory.json"
            inv.write_text(json.dumps(inventory), encoding="utf-8")
            result = verify(package, inv)
            self.assertEqual(result["inventory_count"], 1)
            self.assertEqual(result["missing"], [])
            self.assertEqual(result["mismatches"], [])

    def test_changed_bytes_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "app.msix"
            with ZipFile(package, "w", ZIP_DEFLATED) as z:
                z.writestr("file.txt", b"changed")
            inv = root / "inventory.json"
            inv.write_text(json.dumps({
                "file_count": 1,
                "files": [{"path": "file.txt", "size": 4,
                           "sha256": hashlib.sha256(b"safe").hexdigest()}],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify(package, inv)

    def test_unexpected_package_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "app.msix"
            data = b"safe"
            with ZipFile(package, "w", ZIP_DEFLATED) as z:
                z.writestr("file.txt", data)
                z.writestr("unexpected.bin", b"x")
            inv = root / "inventory.json"
            inv.write_text(json.dumps({
                "file_count": 1,
                "files": [{"path": "file.txt", "size": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()}],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify(package, inv)


if __name__ == "__main__":
    unittest.main()
