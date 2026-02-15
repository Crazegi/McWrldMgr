from __future__ import annotations

from pathlib import Path
from typing import Any

import nbtlib

from mcworldmgr.safety.backup import ProgressFn, create_backup, list_backups, restore_backup
from mcworldmgr.safety.locks import ConfirmFn, prompt_if_locked
from mcworldmgr.world.discovery import WorldRef, list_worlds, resolve_world
from mcworldmgr.world.nbt_io import read_nbt, write_nbt_atomic
from mcworldmgr.world.versioning import assert_supported_data_version

DIFFICULTY_MAP = {"peaceful": 0, "easy": 1, "normal": 2, "hard": 3}
GAMEMODE_MAP = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}


def _region_name_for_chunk(chunk_x: int, chunk_z: int) -> str:
    rx = chunk_x // 32
    rz = chunk_z // 32
    return f"r.{rx}.{rz}.mca"


def list_world_refs(saves_dir: str | None = None) -> list[WorldRef]:
    return list_worlds(saves_dir)


def get_world_inspect_info(world_arg: str, saves_dir: str | None = None) -> dict[str, Any]:
    world = resolve_world(world_arg, saves_dir)
    level = read_nbt(world.path / "level.dat")
    data = level["Data"]

    player_data_dir = world.path / "playerdata"
    players = list(player_data_dir.glob("*.dat")) if player_data_dir.exists() else []

    region_dir = world.path / "region"
    regions = list(region_dir.glob("r.*.*.mca")) if region_dir.exists() else []

    entities_dir = world.path / "entities"
    entity_regions = list(entities_dir.glob("r.*.*.mca")) if entities_dir.exists() else []

    return {
        "world_name": world.name,
        "path": str(world.path),
        "data_version": int(data.get("DataVersion", 0)),
        "level_name": str(data.get("LevelName", world.name)),
        "difficulty": int(data.get("Difficulty", 0)),
        "gametype": int(data.get("GameType", 0)),
        "time": int(data.get("Time", 0)),
        "gamerules_count": len(data.get("GameRules", {})),
        "players_count": len(players),
        "regions_count": len(regions),
        "entity_regions_count": len(entity_regions),
    }


def create_backup_for_world(
    world_arg: str,
    saves_dir: str | None = None,
    confirm: ConfirmFn | None = None,
    progress: ProgressFn | None = None,
) -> Path:
    world = resolve_world(world_arg, saves_dir)
    prompt_if_locked(world.path, confirm=confirm)
    return create_backup(world.path, progress=progress)


def list_backups_for_world(world_arg: str, saves_dir: str | None = None) -> list[str]:
    world = resolve_world(world_arg, saves_dir)
    return [item.name for item in list_backups(world.path)]


def restore_backup_for_world(
    world_arg: str,
    backup_name: str,
    saves_dir: str | None = None,
    confirm: ConfirmFn | None = None,
    progress: ProgressFn | None = None,
) -> None:
    world = resolve_world(world_arg, saves_dir)
    prompt_if_locked(world.path, confirm=confirm)
    restore_backup(world.path, backup_name, progress=progress)


def _maybe_backup(world_path: Path, backup_before_write: bool, progress: ProgressFn | None = None) -> Path | None:
    if backup_before_write:
        return create_backup(world_path, progress=progress)
    return None


def set_world_metadata(
    world_arg: str,
    saves_dir: str | None = None,
    *,
    name: str | None = None,
    difficulty: str | None = None,
    gamemode: str | None = None,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    if name is None and difficulty is None and gamemode is None:
        raise ValueError("Provide at least one change: name, difficulty, or gamemode")

    world = resolve_world(world_arg, saves_dir)
    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)

    level_path = world.path / "level.dat"
    level = read_nbt(level_path)
    data = level["Data"]
    assert_supported_data_version(int(data.get("DataVersion", 0)))

    if name is not None:
        data["LevelName"] = nbtlib.String(name)
    if difficulty is not None:
        data["Difficulty"] = nbtlib.Byte(DIFFICULTY_MAP[difficulty])
    if gamemode is not None:
        data["GameType"] = nbtlib.Int(GAMEMODE_MAP[gamemode])

    write_nbt_atomic(level_path, level)


def set_world_advanced(
    world_arg: str,
    saves_dir: str | None = None,
    *,
    time_value: int | None = None,
    weather: str | None = None,
    weather_duration: int | None = None,
    spawn_x: int | None = None,
    spawn_y: int | None = None,
    spawn_z: int | None = None,
    border_center_x: float | None = None,
    border_center_z: float | None = None,
    border_size: float | None = None,
    hardcore: bool | None = None,
    allow_commands: bool | None = None,
    seed: int | None = None,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    if all(
        value is None
        for value in [
            time_value,
            weather,
            weather_duration,
            spawn_x,
            spawn_y,
            spawn_z,
            border_center_x,
            border_center_z,
            border_size,
            hardcore,
            allow_commands,
            seed,
        ]
    ):
        raise ValueError("No advanced world fields provided to update.")

    world = resolve_world(world_arg, saves_dir)
    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)

    level_path = world.path / "level.dat"
    level = read_nbt(level_path)
    data = level["Data"]
    assert_supported_data_version(int(data.get("DataVersion", 0)))

    if time_value is not None:
        data["Time"] = nbtlib.Long(time_value)
        data["DayTime"] = nbtlib.Long(time_value)

    if weather is not None:
        duration = weather_duration if weather_duration is not None else 6000
        if weather == "clear":
            data["raining"] = nbtlib.Byte(0)
            data["thundering"] = nbtlib.Byte(0)
            data["clearWeatherTime"] = nbtlib.Int(duration)
            data["rainTime"] = nbtlib.Int(0)
            data["thunderTime"] = nbtlib.Int(0)
        elif weather == "rain":
            data["raining"] = nbtlib.Byte(1)
            data["thundering"] = nbtlib.Byte(0)
            data["rainTime"] = nbtlib.Int(duration)
            data["thunderTime"] = nbtlib.Int(0)
            data["clearWeatherTime"] = nbtlib.Int(0)
        elif weather == "thunder":
            data["raining"] = nbtlib.Byte(1)
            data["thundering"] = nbtlib.Byte(1)
            data["rainTime"] = nbtlib.Int(duration)
            data["thunderTime"] = nbtlib.Int(duration)
            data["clearWeatherTime"] = nbtlib.Int(0)
        else:
            raise ValueError("weather must be one of: clear, rain, thunder")

    if spawn_x is not None:
        data["SpawnX"] = nbtlib.Int(spawn_x)
    if spawn_y is not None:
        data["SpawnY"] = nbtlib.Int(spawn_y)
    if spawn_z is not None:
        data["SpawnZ"] = nbtlib.Int(spawn_z)

    if border_center_x is not None:
        data["BorderCenterX"] = nbtlib.Double(border_center_x)
    if border_center_z is not None:
        data["BorderCenterZ"] = nbtlib.Double(border_center_z)
    if border_size is not None:
        data["BorderSize"] = nbtlib.Double(border_size)

    if hardcore is not None:
        data["hardcore"] = nbtlib.Byte(1 if hardcore else 0)

    if allow_commands is not None:
        data["allowCommands"] = nbtlib.Byte(1 if allow_commands else 0)

    if seed is not None:
        world_gen = data.get("WorldGenSettings")
        if world_gen is not None and isinstance(world_gen, nbtlib.Compound):
            world_gen["seed"] = nbtlib.Long(seed)
        else:
            data["RandomSeed"] = nbtlib.Long(seed)

    write_nbt_atomic(level_path, level)


def set_gamerule(
    world_arg: str,
    rule: str,
    value: str,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    world = resolve_world(world_arg, saves_dir)
    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)

    level_path = world.path / "level.dat"
    level = read_nbt(level_path)
    data = level["Data"]
    assert_supported_data_version(int(data.get("DataVersion", 0)))

    game_rules = data.get("GameRules")
    if game_rules is None:
        game_rules = nbtlib.Compound()
        data["GameRules"] = game_rules

    game_rules[rule] = nbtlib.String(value)
    write_nbt_atomic(level_path, level)


def list_player_uuids(world_arg: str, saves_dir: str | None = None) -> list[str]:
    world = resolve_world(world_arg, saves_dir)
    player_dir = world.path / "playerdata"
    if not player_dir.exists():
        return []
    return [file.stem for file in sorted(player_dir.glob("*.dat"))]


def set_player(
    world_arg: str,
    player_uuid: str,
    saves_dir: str | None = None,
    *,
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
    health: float | None = None,
    hunger: int | None = None,
    slot: int | None = None,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    world = resolve_world(world_arg, saves_dir)
    target = world.path / "playerdata" / f"{player_uuid}.dat"
    if not target.exists():
        raise FileNotFoundError(f"Player file not found: {target}")

    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)

    player = read_nbt(target)
    changed = False

    if x is not None or y is not None or z is not None:
        pos = player.get("Pos")
        if pos is None:
            pos = nbtlib.List[nbtlib.Double]([nbtlib.Double(0), nbtlib.Double(64), nbtlib.Double(0)])
        nx = x if x is not None else float(pos[0])
        ny = y if y is not None else float(pos[1])
        nz = z if z is not None else float(pos[2])
        player["Pos"] = nbtlib.List[nbtlib.Double]([nbtlib.Double(nx), nbtlib.Double(ny), nbtlib.Double(nz)])
        changed = True

    if health is not None:
        player["Health"] = nbtlib.Float(health)
        changed = True

    if hunger is not None:
        player["foodLevel"] = nbtlib.Int(hunger)
        changed = True

    if slot is not None:
        player["SelectedItemSlot"] = nbtlib.Int(slot)
        changed = True

    if not changed:
        raise ValueError("No player fields provided to update.")

    write_nbt_atomic(target, player)


def kill_player(
    world_arg: str,
    player_uuid: str,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    set_player(
        world_arg,
        player_uuid,
        saves_dir,
        health=0.0,
        confirm=confirm,
        backup_before_write=backup_before_write,
    )


def delete_player(
    world_arg: str,
    player_uuid: str,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    world = resolve_world(world_arg, saves_dir)
    target = world.path / "playerdata" / f"{player_uuid}.dat"
    if not target.exists():
        raise FileNotFoundError(f"Player file not found: {target}")

    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)
    target.unlink()


def list_entity_regions(world_arg: str, saves_dir: str | None = None) -> list[str]:
    world = resolve_world(world_arg, saves_dir)
    entities_dir = world.path / "entities"
    if not entities_dir.exists():
        return []
    return [file.name for file in sorted(entities_dir.glob("r.*.*.mca"))]


def delete_entity_region(
    world_arg: str,
    region_name: str,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    world = resolve_world(world_arg, saves_dir)
    target = world.path / "entities" / region_name
    if not target.exists() or target.suffix.lower() != ".mca":
        raise FileNotFoundError(f"Entity region file not found: {region_name}")

    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)
    target.unlink()


def delete_all_entity_regions(
    world_arg: str,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> int:
    world = resolve_world(world_arg, saves_dir)
    entities_dir = world.path / "entities"
    if not entities_dir.exists():
        return 0

    files = sorted(entities_dir.glob("r.*.*.mca"))
    if not files:
        return 0

    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)
    for file in files:
        file.unlink()
    return len(files)


def queue_command(
    world_arg: str,
    command: str,
    saves_dir: str | None = None,
    *,
    backup_before_write: bool = False,
    confirm: ConfirmFn | None = None,
) -> Path:
    world = resolve_world(world_arg, saves_dir)
    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)

    command_dir = world.path / "mcworldmgr_commands"
    command_dir.mkdir(parents=True, exist_ok=True)
    command_file = command_dir / "queued_commands.mcfunction"
    with command_file.open("a", encoding="utf-8") as handle:
        handle.write(command.strip())
        handle.write("\n")
    return command_file


def queue_summon_entity(
    world_arg: str,
    entity_id: str,
    x: float,
    y: float,
    z: float,
    nbt_suffix: str | None = None,
    saves_dir: str | None = None,
    *,
    backup_before_write: bool = False,
    confirm: ConfirmFn | None = None,
) -> Path:
    command = f"summon {entity_id} {x} {y} {z}"
    if nbt_suffix:
        command = f"{command} {nbt_suffix.strip()}"
    return queue_command(
        world_arg,
        command,
        saves_dir,
        backup_before_write=backup_before_write,
        confirm=confirm,
    )


def queue_kill_entities(
    world_arg: str,
    selector: str,
    saves_dir: str | None = None,
    *,
    backup_before_write: bool = False,
    confirm: ConfirmFn | None = None,
) -> Path:
    return queue_command(
        world_arg,
        f"kill {selector.strip()}",
        saves_dir,
        backup_before_write=backup_before_write,
        confirm=confirm,
    )


def list_region_files(world_arg: str, saves_dir: str | None = None) -> list[str]:
    world = resolve_world(world_arg, saves_dir)
    region_dir = world.path / "region"
    if not region_dir.exists():
        return []
    return [file.name for file in sorted(region_dir.glob("r.*.*.mca"))]


def delete_region(
    world_arg: str,
    region_name: str,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> None:
    world = resolve_world(world_arg, saves_dir)
    target = world.path / "region" / region_name
    if not target.exists() or target.suffix.lower() != ".mca":
        raise FileNotFoundError(f"Region not found: {region_name}")

    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)
    target.unlink()


def reset_chunk(
    world_arg: str,
    chunk_x: int,
    chunk_z: int,
    saves_dir: str | None = None,
    *,
    confirm: ConfirmFn | None = None,
    backup_before_write: bool = False,
) -> str:
    world = resolve_world(world_arg, saves_dir)
    region_name = _region_name_for_chunk(chunk_x, chunk_z)
    target = world.path / "region" / region_name
    if not target.exists():
        raise FileNotFoundError(f"Chunk parent region does not exist: {region_name}. Nothing to reset.")

    prompt_if_locked(world.path, confirm=confirm)
    _maybe_backup(world.path, backup_before_write)
    target.unlink()
    return region_name
