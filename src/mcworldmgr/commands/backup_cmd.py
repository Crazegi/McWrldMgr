from __future__ import annotations

import argparse

from mcworldmgr.services.operations import (
    create_backup_for_world,
    list_backups_for_world,
    restore_backup_for_world,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("backup", help="Manage world backups")
    backup_sub = parser.add_subparsers(dest="backup_command", required=True)

    create_parser = backup_sub.add_parser("create", help="Create backup")
    create_parser.add_argument("--world", required=True)
    create_parser.set_defaults(handler=handle_create)

    list_parser = backup_sub.add_parser("list", help="List backups")
    list_parser.add_argument("--world", required=True)
    list_parser.set_defaults(handler=handle_list)

    restore_parser = backup_sub.add_parser("restore", help="Restore backup")
    restore_parser.add_argument("--world", required=True)
    restore_parser.add_argument("--name", required=True, help="Backup folder name")
    restore_parser.set_defaults(handler=handle_restore)


def handle_create(args: argparse.Namespace) -> int:
    backup_path = create_backup_for_world(args.world, args.saves_dir)
    print(f"Backup created: {backup_path}")
    return 0


def handle_list(args: argparse.Namespace) -> int:
    backups = list_backups_for_world(args.world, args.saves_dir)
    if not backups:
        print("No backups found.")
        return 0
    for item in backups:
        print(f"- {item}")
    return 0


def handle_restore(args: argparse.Namespace) -> int:
    restore_backup_for_world(args.world, args.name, args.saves_dir)
    print(f"Backup restored: {args.name}")
    return 0
