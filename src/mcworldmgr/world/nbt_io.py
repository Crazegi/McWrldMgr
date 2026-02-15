from __future__ import annotations

import os
import tempfile
from pathlib import Path

import nbtlib


def read_nbt(path: Path) -> nbtlib.File:
    return nbtlib.load(path)


def write_nbt_atomic(path: Path, nbt_file: nbtlib.File) -> None:
    path = path.resolve()
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        nbt_file.save(tmp_path)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
