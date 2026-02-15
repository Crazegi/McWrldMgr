from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

ConfirmFn = Callable[[str], bool]
ProgressFn = Callable[[int, int, str], None]


def backups_dir(world_path: Path) -> Path:
    return world_path / ".mcworldmgr_backups"


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        if ".mcworldmgr_backups" in item.parts:
            continue
        files.append(item)
    return files


def _copy_tree_with_progress(source: Path, target: Path, progress: ProgressFn | None = None) -> None:
    files = _iter_files(source)
    total = len(files)
    copied = 0
    target.mkdir(parents=True, exist_ok=True)

    for file_path in files:
        relative = file_path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)
        copied += 1
        if progress:
            progress(copied, total, str(relative))


def create_backup(world_path: Path, progress: ProgressFn | None = None) -> Path:
    target_root = backups_dir(world_path)
    target_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = target_root / f"backup-{stamp}"
    _copy_tree_with_progress(world_path, target, progress)
    return target


def list_backups(world_path: Path) -> list[Path]:
    root = backups_dir(world_path)
    if not root.exists():
        return []
    return sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)


def restore_backup(world_path: Path, backup_name: str, progress: ProgressFn | None = None) -> None:
    source = backups_dir(world_path) / backup_name
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Backup not found: {backup_name}")

    for child in world_path.iterdir():
        if child.name == ".mcworldmgr_backups":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink(missing_ok=True)

    _copy_tree_with_progress(source, world_path, progress)


def _default_confirm(message: str) -> bool:
    answer = input(message).strip().lower()
    return answer in {"y", "yes"}


def prompt_backup_decision(confirm: ConfirmFn | None = None) -> bool:
    confirmer = confirm or _default_confirm
    return confirmer("Create backup before write? [y/N]: ")


def maybe_prompt_backup(
    world_path: Path,
    confirm: ConfirmFn | None = None,
    progress: ProgressFn | None = None,
) -> Path | None:
    if prompt_backup_decision(confirm=confirm):
        path = create_backup(world_path, progress=progress)
        print(f"Backup created: {path}")
        return path
    return None
