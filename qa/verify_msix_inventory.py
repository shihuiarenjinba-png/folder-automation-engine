"""Verify that a built MSIX matches the staged package SHA256 inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote
from zipfile import ZipFile

ALLOWED_MAKEAPPX_EXTRAS = {"AppxBlockMap.xml", "[Content_Types].xml"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(msix_path: Path, inventory_path: Path) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    items = {item["path"].replace("\\", "/"): item for item in inventory["files"]}
    with ZipFile(msix_path) as archive:
        decoded_names: dict[str, str] = {}
        for stored in archive.namelist():
            decoded = unquote(stored)
            if decoded in decoded_names:
                raise ValueError(f"Duplicate logical MSIX path after URI decoding: {decoded}")
            decoded_names[decoded] = stored

        missing = sorted(set(items) - set(decoded_names))
        extras = sorted(set(decoded_names) - set(items))
        unexpected_extras = [name for name in extras if name not in ALLOWED_MAKEAPPX_EXTRAS]
        mismatches = []
        for logical, item in items.items():
            stored = decoded_names.get(logical)
            if stored is None:
                continue
            data = archive.read(stored)
            actual = {"size": len(data), "sha256": _sha256(data)}
            if actual["size"] != item["size"] or actual["sha256"] != item["sha256"]:
                mismatches.append({"path": logical, "expected": item, "actual": actual})

    result = {
        "inventory_count": len(items),
        "missing": missing,
        "unexpected_extras": unexpected_extras,
        "makeappx_generated_extras": sorted(set(extras) & ALLOWED_MAKEAPPX_EXTRAS),
        "mismatches": mismatches,
    }
    if missing or unexpected_extras or mismatches:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("msix", type=Path)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    result = verify(args.msix, args.inventory)
    print(json.dumps({"status": "PASS", **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
