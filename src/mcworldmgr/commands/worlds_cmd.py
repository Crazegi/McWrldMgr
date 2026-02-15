from __future__ import annotations

import argparse

from mcworldmgr.world.paths import resolve_saves_dir
from mcworldmgr.services.operations import list_world_refs


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("worlds", help="Discover worlds")
    worlds_sub = parser.add_subparsers(dest="worlds_command", required=True)

    list_parser = worlds_sub.add_parser("list", help="List worlds")
    list_parser.set_defaults(handler=handle_list)


def handle_list(args: argparse.Namespace) -> int:
    saves_dir = resolve_saves_dir(args.saves_dir)
    worlds = list_world_refs(args.saves_dir)
    print(f"Saves dir: {saves_dir}")
    if not worlds:
        print("No worlds found.")
        return 0
    for world in worlds:
        print(f"- {world.name} -> {world.path}")
    return 0
