"""Collect exact runtime/build license texts into the packaged app.

Called only from the pinned Windows packaging environment. Fails closed if the
core CPython or PyInstaller license evidence cannot be found.
"""
from __future__ import annotations

import json
import shutil
import sys
from importlib import metadata
from pathlib import Path


def copy_required(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"Required license file missing: {src}")
    shutil.copy2(src, dst)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: collect_runtime_notices.py DESTINATION SUMMARY_FILE")
    destination = Path(sys.argv[1]).resolve()
    summary = Path(sys.argv[2]).resolve()
    destination.mkdir(parents=True, exist_ok=False)

    base = Path(sys.base_prefix)
    python_version = ".".join(map(str, sys.version_info[:3]))
    copied: list[str] = []

    python_license = destination / f"CPython-{python_version}-LICENSE.txt"
    copy_required(base / "LICENSE.txt", python_license)
    copied.append(python_license.name)

    # Official Windows CPython installs include Tcl/Tk license.terms files.
    for component, relative in (
        ("Tcl", Path("tcl") / "tcl8.6" / "license.terms"),
        ("Tk", Path("tcl") / "tk8.6" / "license.terms"),
    ):
        src = base / relative
        if src.is_file():
            dst = destination / f"{component}-8.6-license.terms"
            shutil.copy2(src, dst)
            copied.append(dst.name)

    pyinstaller_dist = metadata.distribution("pyinstaller")
    pyinstaller_version = pyinstaller_dist.version
    pi_licenses: list[Path] = []
    for item in pyinstaller_dist.files or ():
        lowered = item.name.lower()
        if "copying" in lowered or lowered.startswith("license"):
            candidate = Path(pyinstaller_dist.locate_file(item))
            if candidate.is_file():
                pi_licenses.append(candidate)
    if not pi_licenses:
        raise SystemExit("PyInstaller license/COPYING material not found")
    for index, src in enumerate(sorted(set(pi_licenses))):
        dst = destination / f"PyInstaller-{pyinstaller_version}-{index + 1}-{src.name}"
        shutil.copy2(src, dst)
        copied.append(dst.name)

    shutil.copy2(summary, destination / "THIRD_PARTY_NOTICES.md")
    copied.append("THIRD_PARTY_NOTICES.md")

    versions = {
        "python": python_version,
        "pyinstaller": pyinstaller_version,
    }
    for package in (
        "pyinstaller-hooks-contrib", "altgraph", "packaging", "pefile",
        "pywin32-ctypes", "setuptools",
    ):
        versions[package] = metadata.version(package)

    (destination / "BUILD_COMPONENT_VERSIONS.json").write_text(
        json.dumps({"versions": versions, "files": sorted(copied)}, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
