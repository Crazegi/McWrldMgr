from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcworldmgr.world.paths import resolve_saves_dir


@dataclass(frozen=True)
class WorldRef:
    name: str
    path: Path


def list_worlds(saves_dir_override: str | None = None) -> list[WorldRef]:
    saves_dir = resolve_saves_dir(saves_dir_override)
    if not saves_dir.exists():
        return []
    worlds: list[WorldRef] = []
    for child in sorted(saves_dir.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if (child / "level.dat").exists():
            worlds.append(WorldRef(name=child.name, path=child))
    return worlds


def resolve_world(world_arg: str, saves_dir_override: str | None = None) -> WorldRef:
    candidate = Path(world_arg).expanduser()
    if candidate.exists() and candidate.is_dir() and (candidate / "level.dat").exists():
        return WorldRef(name=candidate.name, path=candidate.resolve())

    saves_dir = resolve_saves_dir(saves_dir_override)
    world_path = (saves_dir / world_arg).resolve()
    if world_path.exists() and (world_path / "level.dat").exists():
        return WorldRef(name=world_path.name, path=world_path)

    raise FileNotFoundError(f"World not found: {world_arg}")
