"""Offline read-only backup verification and isolated restore-test extension.

Runs independently of folder_automation.py (no changes to existing copy/move
rules). Snapshot the trusted source BEFORE backup; then verify backup against
that manifest. A manifest generated from a bad backup cannot prove recovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

FORMAT = "local_backup_manifest_v1"
MAX_FILES = 100000


def filehash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unsafe(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _relative_parts(value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("Invalid relative manifest path")
    p = PurePosixPath(value)
    if p.is_absolute() or not p.parts or any(x in ("..", ".") for x in value.split("/")):
        raise ValueError(f"Unsafe manifest path: {value!r}")
    if ":" in value or "//" in value:
        raise ValueError(f"Unsupported manifest path: {value!r}")
    return p.parts


def inventory(root: Path) -> list[dict]:
    root = root.expanduser().resolve()
    if not root.is_dir() or _unsafe(root):
        raise ValueError("Root must be an ordinary directory")
    items: list[dict] = []
    seen_casefold: set[str] = set()
    for base, directories, files in os.walk(root, topdown=True, followlinks=False):
        folder = Path(base)
        for dirname in directories:
            if _unsafe(folder / dirname):
                raise ValueError(f"Symlink/junction directory prohibited: {folder / dirname}")
        for filename in sorted(files):
            p = folder / filename
            if _unsafe(p) or not p.is_file():
                raise ValueError(f"Symlink or non-file prohibited: {p}")
            rel = p.relative_to(root).as_posix()
            _relative_parts(rel)
            if rel.casefold() in seen_casefold:
                raise ValueError(f"Case-insensitive file collision: {rel}")
            seen_casefold.add(rel.casefold())
            before = p.stat()
            digest = filehash(p)
            after = p.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError(f"Source changed while reading: {p}")
            items.append({"path": rel, "size": after.st_size, "sha256": digest})
            if len(items) > MAX_FILES:
                raise ValueError("Too many files for MVP verifier")
    return sorted(items, key=lambda r: r["path"])


def snapshot(source_dir: str | Path, manifest_file: str | Path) -> Path:
    source = Path(source_dir).expanduser().resolve()
    target = Path(manifest_file).expanduser().resolve()
    if target.is_relative_to(source):
        raise ValueError("Manifest must be outside the source tree")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite manifest: {target}")
    files = inventory(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "format": FORMAT,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source),
        "file_count": len(files),
        "files": files,
        "limitations": ["This is a snapshot, not an authenticated signature.",
                        "Keep the manifest in trusted storage separately from the backup."],
    }
    # Atomic no-overwrite file creation; never alter the source.
    with target.open("x", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
    return target


def _read_manifest(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if len(raw) > 32 * 1024 * 1024:
        raise ValueError("Manifest too large")
    data = json.loads(raw)
    if data.get("format") != FORMAT or not isinstance(data.get("files"), list):
        raise ValueError("Unsupported manifest")
    files = data["files"]
    if len(files) > MAX_FILES or len(files) != data.get("file_count"):
        raise ValueError("Invalid file count")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("Malformed manifest item")
        rel = item["path"]
        _relative_parts(rel)
        if rel.casefold() in seen:
            raise ValueError("Duplicate/case-colliding manifest path")
        seen.add(rel.casefold())
        if type(item.get("size")) is not int or item["size"] < 0:
            raise ValueError("Invalid file size")
        digest = item.get("sha256", "")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid sha256")
    return files


def verify(backup_dir: str | Path, manifest_file: str | Path,
           report_parent: str | Path, *, restore_test_max_bytes: int = 100_000_000) -> Path:
    """Hash every manifest entry, list extras, and restore a bounded sample."""
    if restore_test_max_bytes < 0:
        raise ValueError("restore_test_max_bytes cannot be negative")
    root = Path(backup_dir).expanduser().resolve()
    if not root.is_dir() or _unsafe(root):
        raise ValueError("Backup must be an ordinary directory")
    manifest = Path(manifest_file).expanduser().resolve()
    if manifest.is_relative_to(root):
        raise ValueError("Store manifest outside backup root to avoid circular verification")
    expected = _read_manifest(manifest)
    findings: list[dict] = []
    verified: list[tuple[Path, str, int, str]] = []
    def issue(code: str, path: str) -> None:
        findings.append({"code": code, "path": path})
    actual_paths: set[str] = set()
    # Listing backup can fail on unsafe links rather than silently following them.
    for base, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        for name in directories:
            if _unsafe(Path(base) / name):
                raise ValueError("Backup contains symlink/junction directory")
        for name in filenames:
            p = Path(base) / name
            if _unsafe(p):
                raise ValueError("Backup contains symlink file")
            actual_paths.add(p.relative_to(root).as_posix())
    expected_paths = {e["path"] for e in expected}
    for rel in sorted(actual_paths - expected_paths):
        issue("unexpected_backup_file", rel)
    for item in expected:
        rel = item["path"]
        path = root.joinpath(*_relative_parts(rel))
        if not path.is_file() or _unsafe(path) or not path.resolve().is_relative_to(root):
            issue("missing_or_unsafe_file", rel)
            continue
        before = path.stat()
        if before.st_size != item["size"]:
            issue("size_mismatch", rel)
            continue
        actual_sha = filehash(path)
        after = path.stat()
        if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
            issue("changed_during_verification", rel)
            continue
        if actual_sha != item["sha256"]:
            issue("hash_mismatch", rel)
            continue
        verified.append((path, rel, item["size"], item["sha256"]))
    restore_bytes = 0
    restored_count = 0
    restore_skipped_count = 0
    if restore_test_max_bytes > 0:
        with tempfile.TemporaryDirectory(prefix="backup_restore_probe_") as tmp:
            temp_root = Path(tmp)
            for source, rel, size, expected_digest in verified:
                if restore_bytes + size > restore_test_max_bytes:
                    restore_skipped_count += 1
                    continue
                dest = temp_root.joinpath(*_relative_parts(rel))
                dest.parent.mkdir(parents=True, exist_ok=True)
                with source.open("rb") as src, dest.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                if filehash(dest) != expected_digest:
                    issue("restore_copy_mismatch", rel)
                else:
                    restored_count += 1
                    restore_bytes += size
    output = Path(report_parent).expanduser().resolve()
    if output.is_relative_to(root):
        raise ValueError("Report output must be outside backup directory")
    output.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="backup_verify_", dir=output))
    report = {
        "mode": FORMAT,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": filehash(manifest),
        "status": "REVIEW" if findings else ("RESTORE_SAMPLE_INCOMPLETE" if restore_skipped_count else ("HASH_CHECKED_RESTORE_SAMPLE" if restore_test_max_bytes > 0 else "HASH_CHECKED_ONLY")),
        "summary": {"expected": len(expected), "verified": len(verified),
                    "findings": len(findings), "sample_restored": restored_count,
                    "sample_restore_bytes": restore_bytes, "restore_skipped": restore_skipped_count},
        "findings": findings,
        "limitations": [
            "SHA-256 verifies bytes against the manifest, not manifest authenticity.",
            "Restore copy test is a bounded sample, not full application-level recovery.",
            "No cloud API or filesystem ACL/ADS consistency checks.",
            "No file deletion, overwrite, or permanent restore is performed.",
        ],
    }
    (run / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return run


def main() -> None:
    p = argparse.ArgumentParser(description="Backup snapshot and read-only verification")
    sub = p.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("source")
    snap.add_argument("manifest")
    val = sub.add_parser("verify")
    val.add_argument("backup")
    val.add_argument("manifest")
    val.add_argument("reports")
    val.add_argument("--restore-test-max-mb", type=int, default=100)
    args = p.parse_args()
    if args.command == "snapshot":
        print(snapshot(args.source, args.manifest))
    else:
        print(verify(args.backup, args.manifest, args.reports,
                     restore_test_max_bytes=args.restore_test_max_mb * 1000000))


if __name__ == "__main__":
    main()
