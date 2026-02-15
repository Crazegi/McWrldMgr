from __future__ import annotations

from pathlib import Path
from typing import Callable

ConfirmFn = Callable[[str], bool]


def world_lock_exists(world_path: Path) -> bool:
    return (world_path / "session.lock").exists()


def _default_confirm(message: str) -> bool:
    answer = input(message).strip().lower()
    return answer in {"y", "yes"}


def prompt_if_locked(world_path: Path, confirm: ConfirmFn | None = None) -> None:
    if world_lock_exists(world_path):
        confirmer = confirm or _default_confirm
        if not confirmer("Warning: session.lock exists. Continue anyway? [y/N]: "):
            raise RuntimeError("Aborted due to active world lock.")
