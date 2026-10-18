"""Validated UI form conversion for a local, no-overwrite folder rule."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath

from folder_automation import ConfigError


def _child_name(value: str, label: str) -> str:
    result = str(value).strip()
    if not result or result in {".", ".."} or "/" in result or "\\" in result:
        raise ConfigError(f"{label}: enter one folder name inside the selected root")
    if result.endswith((" ", ".")) or ":" in result or PureWindowsPath(result).is_absolute():
        raise ConfigError(f"{label}: unsupported Windows folder name")
    if result.lower() in {".state", "con", "prn", "aux", "nul"}:
        raise ConfigError(f"{label}: reserved folder name")
    return result


def build_config(
    *,
    root_dir: str,
    input_folder: str,
    output_folder: str,
    filename_glob: str,
    action: str,
) -> dict:
    root_text = str(root_dir).strip()
    if not root_text:
        raise ConfigError("Select the main folder / ルートフォルダーを選択してください")
    root = Path(root_text).expanduser().resolve()
    if not root.is_dir():
        raise ConfigError("Selected root must be an existing directory / 存在するフォルダーを選択してください")
    source = _child_name(input_folder, "Input folder")
    destination = _child_name(output_folder, "Output folder")
    if source.casefold() == destination.casefold():
        raise ConfigError("Input and output must be different folders / 入出力フォルダーは別々にしてください")
    glob = str(filename_glob).strip()
    if not glob or "/" in glob or "\\" in glob or glob in {".", ".."}:
        raise ConfigError("Enter a filename pattern such as *.pdf / *.pdfなどのファイル名を指定")
    action = str(action).lower().strip()
    if action not in {"copy", "move"}:
        raise ConfigError("Action must be copy or move")
    return {
        "root_dir": str(root),
        "input_dir": source,
        "state_db": ".state/processed.sqlite3",
        "poll_seconds": 5,
        "rules": [{
            "glob": glob,
            "action": action,
            "destination": destination,
            "overwrite": False,
        }],
    }


def revision(config: dict) -> str:
    stable = json.dumps(config, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def snapshot_inputs(config: dict) -> tuple:
    """Capture visible regular-file metadata without writing or following links.

    An unexpected change between Dry Run and the approved live run forces
    another preview. The worker rechecks before scanning. This is not an
    atomic transaction against concurrent writers; Engine protects writes.
    """
    source = Path(config["root_dir"]) / str(config["input_dir"])
    if source.is_symlink():
        raise ConfigError("Input folder is a symbolic link / 入力先のリンクは利用できません")
    if not source.exists():
        return ("MISSING",)
    if not source.is_dir():
        raise ConfigError("Input path must be a directory / 入力先はフォルダーにしてください")
    result = []
    for path in sorted(source.iterdir(), key=lambda x: x.name):
        if path.is_symlink() or not path.is_file():
            continue
        info = path.stat()
        result.append((path.name, info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns))
    return tuple(result)


def format_activity(raw: str, *, japanese: bool) -> str:
    """Show file decisions in plain language; do not modify the original log."""
    lines = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            lines.append(line)
            continue
        if not isinstance(event, dict) or not {"file", "action", "destination"} <= event.keys():
            lines.append(line)
            continue
        source_name = Path(str(event["file"])).name
        destination = str(event["destination"])
        action = str(event["action"])
        if japanese:
            verb = "コピー予定" if action == "copy" else "移動予定"
            if not event.get("dry_run", False):
                verb = "コピー処理" if action == "copy" else "移動処理"
            lines.append(f"• {source_name} → {destination}（{verb}）")
        else:
            verb = "would copy" if action == "copy" else "would move"
            if not event.get("dry_run", False):
                verb = "copy attempted" if action == "copy" else "move attempted"
            lines.append(f"• {source_name} → {destination} ({verb})")
    return "\n".join(lines)
