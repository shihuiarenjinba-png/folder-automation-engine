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
