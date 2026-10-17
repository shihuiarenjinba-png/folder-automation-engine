from __future__ import annotations

import argparse
import fnmatch
import json
import os
import tempfile
import shutil
import sqlite3
import sys
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Iterator


class ConfigError(RuntimeError):
    pass


class RuleResult(str, Enum):
    NO_MATCH = "no_match"
    HANDLED = "handled"
    BLOCKED = "blocked"


class Engine:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.root = Path(config.get("root_dir", ".")).expanduser().resolve()
        self.input_dir = self._path(config.get("input_dir", "inbox"))
        self.interval = max(float(config.get("poll_seconds", 5)), 1.0)
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

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.state_db)
        try:
            with con:
                yield con
        finally:
            con.close()

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

    @staticmethod
    def _replace_safely(src: Path, dst: Path, *, move: bool) -> None:
        """Stage the replacement before touching the existing destination."""
        fd, tmp_name = tempfile.mkstemp(prefix=".folder-automation-", suffix=".tmp", dir=dst.parent)
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)
            if move:
                src.unlink()
        finally:
            tmp.unlink(missing_ok=True)

    def apply_rule(self, src: Path, rule: dict[str, Any]) -> RuleResult:
        pattern = str(rule.get("glob", "*"))
        if not fnmatch.fnmatch(src.name, pattern):
            return RuleResult.NO_MATCH

        action = str(rule.get("action", "")).lower()
        if action not in {"copy", "move"}:
            raise ConfigError(f"Unsupported action: {action}")
        if "destination" not in rule:
            raise ConfigError("rule destination is required")

        dst = self.destination(str(rule["destination"]), src)
        # Never operate on the source as its own destination, including with
        # overwrite=true. Resolving also prevents a symlink from escaping root.
        if src.resolve() == dst.resolve() or (dst.exists() and src.samefile(dst)):
            raise ConfigError(f"Source and destination refer to the same file: {src}")
        if dst.is_symlink():
            raise ConfigError(f"Symlink destination is not supported: {dst}")
        self._path(str(dst))
        if dst.exists() and dst.is_dir():
            raise ConfigError(f"Destination is a directory: {dst}")

        overwrite = bool(rule.get("overwrite", False))
        print(json.dumps({"file": str(src), "action": action, "destination": str(dst),
                          "dry_run": self.dry_run, "overwrite": overwrite}, ensure_ascii=False))
        # A blocked match must not be marked seen or fall through to a later
        # rule; check this even in dry-run so the preview is accurate.
        if dst.exists() and not overwrite:
            print(f"BLOCKED destination exists: {dst}")
            return RuleResult.BLOCKED
        if self.dry_run:
            return RuleResult.HANDLED

        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and overwrite:
            self._replace_safely(src, dst, move=(action == "move"))
        elif action == "copy":
            shutil.copy2(src, dst)
        else:
            shutil.move(str(src), str(dst))
        return RuleResult.HANDLED

    def scan_once(self) -> int:
        if not self.input_dir.exists():
            if self.dry_run:
                print(f"Input directory does not exist yet: {self.input_dir}")
                return 0
            self.input_dir.mkdir(parents=True, exist_ok=True)

        handled = 0
        for path in sorted(self.input_dir.iterdir()):
            if path.is_symlink():
                print(f"SKIP symlink source: {path}")
                continue
            if not path.is_file():
                continue
            sig = self.signature(path)
            if self.seen(sig):
                continue
            processed = False
            for rule in self.rules:
                result = self.apply_rule(path, rule)
                if result is RuleResult.NO_MATCH:
                    continue
                if result is RuleResult.HANDLED:
                    processed = True
                    handled += 1
                # A blocked matching rule cannot silently reroute to another destination.
                break
            if processed:
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
    except (OSError, json.JSONDecodeError, KeyError, ConfigError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
