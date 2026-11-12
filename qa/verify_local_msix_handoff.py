"""Validate a local handoff for an unsigned Store MSIX without installing it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from qa.verify_msix_inventory import verify as verify_inventory


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--msix", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--expected-source-commit", required=True)
    args = parser.parse_args()

    report = json.loads(args.validation.read_text(encoding="utf-8-sig"))
    inventory = json.loads(args.inventory.read_text(encoding="utf-8-sig"))
    actual_msix = sha256(args.msix)

    failures = []
    if report.get("source_commit") != args.expected_source_commit:
        failures.append("validation source_commit mismatch")
    if inventory.get("source_commit") != args.expected_source_commit:
        failures.append("inventory source_commit mismatch")
    if report.get("msix_sha256") != actual_msix:
        failures.append("MSIX SHA256 mismatch")
    if report.get("signed") is not False:
        failures.append("Store engineering candidate must be recorded as unsigned")
    if report.get("manifest_identity_verified") is not True:
        failures.append("manifest identity not verified")
    if report.get("third_party_notices_verified") is not True:
        failures.append("third-party notice evidence missing")
    try:
        inventory_result = verify_inventory(args.msix, args.inventory)
    except Exception as exc:
        failures.append(f"MSIX inventory mismatch: {exc}")
        inventory_result = None

    with ZipFile(args.msix) as archive:
        appx_signature_present = "AppxSignature.p7x" in archive.namelist()
    if appx_signature_present:
        failures.append("unexpected AppxSignature.p7x in unsigned engineering candidate")

    output = {
        "status": "PASS" if not failures else "FAIL",
        "mode": "STATIC_VALIDATION_ONLY",
        "install_authorized": False,
        "source_commit": args.expected_source_commit,
        "msix_sha256": actual_msix,
        "inventory": inventory_result,
        "failures": failures,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
