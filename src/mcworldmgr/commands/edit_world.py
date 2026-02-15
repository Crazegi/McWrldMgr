from __future__ import annotations

import argparse

from mcworldmgr.safety.backup import prompt_backup_decision
from mcworldmgr.services.operations import set_gamerule, set_world_advanced, set_world_metadata

DIFFICULTY_MAP = {"peaceful": 0, "easy": 1, "normal": 2, "hard": 3}
GAMEMODE_MAP = {"survival": 0, "creative": 1, "adventure": 2, "spectator": 3}


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    world_parser = subparsers.add_parser("world", help="Edit world metadata")
    world_sub = world_parser.add_subparsers(dest="world_command", required=True)

    set_parser = world_sub.add_parser("set", help="Set world metadata")
    set_parser.add_argument("--world", required=True)
    set_parser.add_argument("--name")
    set_parser.add_argument("--difficulty", choices=list(DIFFICULTY_MAP.keys()))
    set_parser.add_argument("--gamemode", choices=list(GAMEMODE_MAP.keys()))
    set_parser.set_defaults(handler=handle_world_set)

    advanced_parser = world_sub.add_parser("advanced-set", help="Set advanced world values")
    advanced_parser.add_argument("--world", required=True)
    advanced_parser.add_argument("--time", type=int)
    advanced_parser.add_argument("--weather", choices=["clear", "rain", "thunder"])
    advanced_parser.add_argument("--weather-duration", type=int)
    advanced_parser.add_argument("--spawn-x", type=int)
    advanced_parser.add_argument("--spawn-y", type=int)
    advanced_parser.add_argument("--spawn-z", type=int)
    advanced_parser.add_argument("--border-center-x", type=float)
    advanced_parser.add_argument("--border-center-z", type=float)
    advanced_parser.add_argument("--border-size", type=float)
    advanced_parser.add_argument("--hardcore", choices=["true", "false"])
    advanced_parser.add_argument("--allow-commands", choices=["true", "false"])
    advanced_parser.add_argument("--seed", type=int)
    advanced_parser.set_defaults(handler=handle_world_advanced_set)

    gamerule_parser = subparsers.add_parser("gamerule", help="Edit world gamerules")
    gamerule_sub = gamerule_parser.add_subparsers(dest="gamerule_command", required=True)

    gamerule_set = gamerule_sub.add_parser("set", help="Set gamerule")
    gamerule_set.add_argument("--world", required=True)
    gamerule_set.add_argument("--rule", required=True)
    gamerule_set.add_argument("--value", required=True)
    gamerule_set.set_defaults(handler=handle_gamerule_set)


def handle_world_set(args: argparse.Namespace) -> int:
    if args.name is None and args.difficulty is None and args.gamemode is None:
        raise ValueError("Provide at least one change: --name, --difficulty, or --gamemode")

    set_world_metadata(
        args.world,
        args.saves_dir,
        name=args.name,
        difficulty=args.difficulty,
        gamemode=args.gamemode,
        backup_before_write=prompt_backup_decision(),
    )
    print("World metadata updated.")
    return 0


def handle_gamerule_set(args: argparse.Namespace) -> int:
    set_gamerule(
        args.world,
        args.rule,
        args.value,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print(f"Gamerule updated: {args.rule}={args.value}")
    return 0


def handle_world_advanced_set(args: argparse.Namespace) -> int:
    to_bool = lambda value: None if value is None else value.lower() == "true"
    set_world_advanced(
        args.world,
        args.saves_dir,
        time_value=args.time,
        weather=args.weather,
        weather_duration=args.weather_duration,
        spawn_x=args.spawn_x,
        spawn_y=args.spawn_y,
        spawn_z=args.spawn_z,
        border_center_x=args.border_center_x,
        border_center_z=args.border_center_z,
        border_size=args.border_size,
        hardcore=to_bool(args.hardcore),
        allow_commands=to_bool(args.allow_commands),
        seed=args.seed,
        backup_before_write=prompt_backup_decision(),
    )
    print("Advanced world settings updated.")
    return 0
