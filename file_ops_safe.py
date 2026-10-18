"""Fail-closed atomic file copy/move for a local folder automation engine."""
from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path


class FileOperationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def copy_or_move(source: Path, destination: Path, *, move: bool = False, overwrite: bool = False) -> dict:
    """Copy into same-directory temp, verify, then commit without a collision race.

    If move=True, unlink the original only after the destination verifies.
    Existing destinations survive a failed copy even when overwrite=True.
    """
    src, dst = Path(source), Path(destination)
    if src.is_symlink() or dst.is_symlink():
        raise FileOperationError('Symbolic links cannot be used as sources or destinations')
    if not src.is_file() or src.resolve() == dst.resolve():
        raise FileOperationError('Source is unavailable or equals destination')
    if dst.exists() and dst.is_dir():
        raise FileOperationError('Destination is a directory')
    dst.parent.mkdir(parents=True, exist_ok=True)
    prior = src.stat()
    before = _sha256(src)
    fd, name = tempfile.mkstemp(dir=dst.parent, prefix='.'+dst.name+'-pending-', suffix='.tmp')
    os.close(fd)
    temp = Path(name)
    try:
        shutil.copy2(src, temp)
        with temp.open('rb') as f:
            os.fsync(f.fileno())
        current = src.stat()
        if current.st_size != prior.st_size or current.st_mtime_ns != prior.st_mtime_ns:
            raise FileOperationError('Source changed during processing')
        if _sha256(temp) != before or _sha256(src) != before:
            raise FileOperationError('Checksum mismatch: source not removed')
        if overwrite:
            os.replace(temp, dst)
        else:
            try:
                os.link(temp, dst)
            except FileExistsError as exc:
                raise FileOperationError('Destination exists; no output written') from exc
        if _sha256(dst) != before:
            raise FileOperationError('Destination verification failed; source retained')
        if move:
            src.unlink()
        return {'source_sha256':before, 'destination_sha256':_sha256(dst), 'moved':move}
    finally:
        temp.unlink(missing_ok=True)
