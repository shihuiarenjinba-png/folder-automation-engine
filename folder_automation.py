from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from file_ops_safe import FileOperationError, copy_or_move


class ConfigError(RuntimeError):
    pass


class Engine:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.root = Path(config.get("root_dir", ".")).expanduser().resolve()
        self.input_dir = self._path(config.get("input_dir", "inbox"))
        self.interval = max(float(config.get("poll_seconds", 5)), 1.0)
        self.min_stable_seconds = max(float(config.get("min_stable_seconds", 3)), 0.0)
        self.rules = config.get("rules", [])
        if not isinstance(self.rules, list) or not self.rules:
            raise ConfigError("rules must be a non-empty list")
        self.state_db = self._path(config.get("state_db", ".state/processed.sqlite3"))
        if not self.dry_run:
            self.input_dir.mkdir(parents=True, exist_ok=True)
            self.state_db.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()

    def _path(self, value: str) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.root / path
        path = path.resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ConfigError(f"Path is outside root_dir: {path}") from exc
        return path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.state_db)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS processed (signature TEXT PRIMARY KEY, processed_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )

    @staticmethod
    def signature(path: Path) -> str:
        stat = path.stat()
        return f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"

    def seen(self, signature: str) -> bool:
        if self.dry_run:
            return False
        with self._connect() as con:
            row = con.execute("SELECT 1 FROM processed WHERE signature = ?", (signature,)).fetchone()
        return row is not None

    def mark_seen(self, signature: str) -> None:
        if self.dry_run:
            return
        with self._connect() as con:
            con.execute("INSERT OR IGNORE INTO processed(signature) VALUES (?)", (signature,))

    def destination(self, folder: str, src: Path) -> Path:
        dst_dir = self._path(folder)
        return dst_dir / src.name

    def apply_rule(self, src: Path, rule: dict[str, Any]) -> bool:
        pattern = str(rule.get("glob", "*"))
        if not fnmatch.fnmatch(src.name, pattern):
            return False

        action = str(rule.get("action", "")).lower()
        if action not in {"copy", "move"}:
            raise ConfigError(f"Unsupported action: {action}")

        dst = self.destination(str(rule["destination"]), src)
        overwrite = bool(rule.get("overwrite", False))
        print(json.dumps({"file": str(src), "action": action, "destination": str(dst), "dry_run": self.dry_run}, ensure_ascii=False))

        if self.dry_run:
            return True
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not overwrite:
            raise ConfigError(f"Destination already exists; source remains unprocessed: {dst}")
        result = copy_or_move(src, dst, move=(action == "move"), overwrite=overwrite)
        print(json.dumps({"event": "file_committed", "sha256": result["destination_sha256"],
                          "moved": result["moved"]}, ensure_ascii=False))
        return True

    def scan_once(self) -> int:
        if not self.input_dir.exists():
            if self.dry_run:
                print(f"Input directory does not exist yet: {self.input_dir}")
                return 0
            self.input_dir.mkdir(parents=True, exist_ok=True)

        handled = 0
        for path in sorted(self.input_dir.iterdir()):
            # Never follow an external file symlink or a Windows reparse-point file.
            if path.is_symlink():
                continue
            try:
                attributes = getattr(path.lstat(), "st_file_attributes", 0)
            except OSError:
                continue
            if attributes & 0x400:
                continue
            if not path.is_file():
                continue
            # Avoid consuming a file while another application is still writing it.
            if time.time() - path.stat().st_mtime < self.min_stable_seconds:
                continue
            sig = self.signature(path)
            if self.seen(sig):
                continue
            matched = False
            for rule in self.rules:
                if self.apply_rule(path, rule):
                    matched = True
                    handled += 1
                    break
            if matched:
                self.mark_seen(sig)
        return handled


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic folder automation engine")
    parser.add_argument("config", type=Path)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        engine = Engine(config, dry_run=args.dry_run)
        if args.once:
            engine.scan_once()
            return 0
        while True:
            engine.scan_once()
            time.sleep(engine.interval)
    except KeyboardInterrupt:
        return 0
    except (OSError, json.JSONDecodeError, KeyError, ConfigError, FileOperationError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
