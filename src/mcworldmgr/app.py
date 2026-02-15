from __future__ import annotations

import argparse

from mcworldmgr.commands import backup_cmd, edit_entity, edit_player, edit_world, inspect_cmd, regions_cmd, worlds_cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcworldmgr", description="Minecraft Java world manager")
    parser.add_argument("--saves-dir", help="Override Minecraft saves directory")

    subparsers = parser.add_subparsers(dest="command", required=True)
    worlds_cmd.register(subparsers)
    inspect_cmd.register(subparsers)
    backup_cmd.register(subparsers)
    edit_world.register(subparsers)
    edit_player.register(subparsers)
    edit_entity.register(subparsers)
    regions_cmd.register(subparsers)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    return int(handler(args) or 0)
