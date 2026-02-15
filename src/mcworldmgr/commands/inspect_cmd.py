from __future__ import annotations

import argparse

from mcworldmgr.services.operations import get_world_inspect_info


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("inspect", help="Inspect world")
    parser.add_argument("--world", required=True, help="World name or path")
    parser.set_defaults(handler=handle_inspect)


def handle_inspect(args: argparse.Namespace) -> int:
    info = get_world_inspect_info(args.world, args.saves_dir)
    print(f"World: {info['world_name']}")
    print(f"Path: {info['path']}")
    print(f"DataVersion: {info['data_version']}")
    print(f"LevelName: {info['level_name']}")
    print(f"Difficulty: {info['difficulty']}")
    print(f"GameType: {info['gametype']}")
    print(f"Time: {info['time']}")
    print(f"GameRules: {info['gamerules_count']}")
    print(f"Players: {info['players_count']}")
    print(f"Regions: {info['regions_count']}")
    print(f"Entity regions: {info['entity_regions_count']}")
    return 0
