from __future__ import annotations

import argparse
from mcworldmgr.safety.backup import prompt_backup_decision
from mcworldmgr.services.operations import delete_player, kill_player, list_player_uuids, set_player


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    player_parser = subparsers.add_parser("player", help="List/edit player data")
    player_sub = player_parser.add_subparsers(dest="player_command", required=True)

    list_parser = player_sub.add_parser("list", help="List player UUID files")
    list_parser.add_argument("--world", required=True)
    list_parser.set_defaults(handler=handle_player_list)

    set_parser = player_sub.add_parser("set", help="Edit player values")
    set_parser.add_argument("--world", required=True)
    set_parser.add_argument("--uuid", required=True, help="Player UUID filename without .dat")
    set_parser.add_argument("--x", type=float)
    set_parser.add_argument("--y", type=float)
    set_parser.add_argument("--z", type=float)
    set_parser.add_argument("--health", type=float)
    set_parser.add_argument("--hunger", type=int)
    set_parser.add_argument("--slot", type=int, help="Selected inventory slot")
    set_parser.set_defaults(handler=handle_player_set)

    kill_parser = player_sub.add_parser("kill", help="Set player health to 0")
    kill_parser.add_argument("--world", required=True)
    kill_parser.add_argument("--uuid", required=True)
    kill_parser.set_defaults(handler=handle_player_kill)

    delete_parser = player_sub.add_parser("delete", help="Delete player data file")
    delete_parser.add_argument("--world", required=True)
    delete_parser.add_argument("--uuid", required=True)
    delete_parser.set_defaults(handler=handle_player_delete)


def handle_player_list(args: argparse.Namespace) -> int:
    players = list_player_uuids(args.world, args.saves_dir)
    if not players:
        print("No player files found.")
        return 0
    for uuid in players:
        print(uuid)
    return 0


def handle_player_set(args: argparse.Namespace) -> int:
    set_player(
        args.world,
        args.uuid,
        args.saves_dir,
        x=args.x,
        y=args.y,
        z=args.z,
        health=args.health,
        hunger=args.hunger,
        slot=args.slot,
        backup_before_write=prompt_backup_decision(),
    )
    print("Player updated.")
    return 0


def handle_player_kill(args: argparse.Namespace) -> int:
    kill_player(
        args.world,
        args.uuid,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print("Player marked as dead (health=0).")
    return 0


def handle_player_delete(args: argparse.Namespace) -> int:
    delete_player(
        args.world,
        args.uuid,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print("Player data deleted.")
    return 0
