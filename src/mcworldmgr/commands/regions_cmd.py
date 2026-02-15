from __future__ import annotations

import argparse

from mcworldmgr.safety.backup import prompt_backup_decision
from mcworldmgr.services.operations import delete_region, list_region_files, reset_chunk


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("regions", help="Region operations")
    regions_sub = parser.add_subparsers(dest="regions_command", required=True)

    list_parser = regions_sub.add_parser("list", help="List region files")
    list_parser.add_argument("--world", required=True)
    list_parser.set_defaults(handler=handle_list)

    delete_parser = regions_sub.add_parser("delete", help="Delete one region file")
    delete_parser.add_argument("--world", required=True)
    delete_parser.add_argument("--name", required=True, help="Example: r.0.-1.mca")
    delete_parser.set_defaults(handler=handle_delete)

    reset_chunk_parser = regions_sub.add_parser(
        "reset-chunk", help="Reset a chunk by deleting its parent region file"
    )
    reset_chunk_parser.add_argument("--world", required=True)
    reset_chunk_parser.add_argument("--chunk-x", type=int, required=True)
    reset_chunk_parser.add_argument("--chunk-z", type=int, required=True)
    reset_chunk_parser.set_defaults(handler=handle_reset_chunk)


def _region_name_for_chunk(chunk_x: int, chunk_z: int) -> str:
    rx = chunk_x // 32
    rz = chunk_z // 32
    return f"r.{rx}.{rz}.mca"


def handle_list(args: argparse.Namespace) -> int:
    files = list_region_files(args.world, args.saves_dir)
    if not files:
        print("No region files found.")
        return 0
    for name in files:
        print(name)
    return 0


def handle_delete(args: argparse.Namespace) -> int:
    delete_region(
        args.world,
        args.name,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print(f"Deleted region: {args.name}")
    return 0


def handle_reset_chunk(args: argparse.Namespace) -> int:
    region_name = reset_chunk(
        args.world,
        args.chunk_x,
        args.chunk_z,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print(
        "Reset chunk operation completed by deleting parent region file "
        f"{region_name}."
    )
    return 0
