from __future__ import annotations

import argparse

from mcworldmgr.safety.backup import prompt_backup_decision
from mcworldmgr.services.operations import (
    delete_all_entity_regions,
    delete_entity_region,
    list_entity_regions,
    queue_kill_entities,
    queue_summon_entity,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    entity_parser = subparsers.add_parser("entity", help="Entity region operations")
    entity_sub = entity_parser.add_subparsers(dest="entity_command", required=True)

    list_regions = entity_sub.add_parser("list-regions", help="List entity region files")
    list_regions.add_argument("--world", required=True)
    list_regions.set_defaults(handler=handle_list_regions)

    delete_region = entity_sub.add_parser("delete-region", help="Delete one entity region file")
    delete_region.add_argument("--world", required=True)
    delete_region.add_argument("--name", required=True, help="Example: r.0.0.mca")
    delete_region.set_defaults(handler=handle_delete_region)

    delete_all = entity_sub.add_parser("delete-all-regions", help="Delete all entity region files")
    delete_all.add_argument("--world", required=True)
    delete_all.set_defaults(handler=handle_delete_all_regions)

    summon_parser = entity_sub.add_parser(
        "queue-summon", help="Queue summon command in world command file"
    )
    summon_parser.add_argument("--world", required=True)
    summon_parser.add_argument("--entity", required=True, help="Example: minecraft:zombie")
    summon_parser.add_argument("--x", type=float, required=True)
    summon_parser.add_argument("--y", type=float, required=True)
    summon_parser.add_argument("--z", type=float, required=True)
    summon_parser.add_argument("--nbt", help="Optional NBT suffix, example: {CustomName:'\"Boss\"'}")
    summon_parser.set_defaults(handler=handle_queue_summon)

    kill_parser = entity_sub.add_parser(
        "queue-kill", help="Queue kill command in world command file"
    )
    kill_parser.add_argument("--world", required=True)
    kill_parser.add_argument("--selector", required=True, help="Example: @e[type=minecraft:zombie]")
    kill_parser.set_defaults(handler=handle_queue_kill)


def handle_list_regions(args: argparse.Namespace) -> int:
    files = list_entity_regions(args.world, args.saves_dir)
    if not files:
        print("No entity region files found.")
        return 0
    for name in files:
        print(name)
    return 0


def handle_delete_region(args: argparse.Namespace) -> int:
    delete_entity_region(
        args.world,
        args.name,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print(f"Deleted entity region: {args.name}")
    return 0


def handle_delete_all_regions(args: argparse.Namespace) -> int:
    count = delete_all_entity_regions(
        args.world,
        args.saves_dir,
        backup_before_write=prompt_backup_decision(),
    )
    print(f"Deleted {count} entity region file(s).")
    return 0


def handle_queue_summon(args: argparse.Namespace) -> int:
    path = queue_summon_entity(
        args.world,
        args.entity,
        args.x,
        args.y,
        args.z,
        args.nbt,
        args.saves_dir,
        backup_before_write=False,
    )
    print(f"Summon command queued in: {path}")
    return 0


def handle_queue_kill(args: argparse.Namespace) -> int:
    path = queue_kill_entities(
        args.world,
        args.selector,
        args.saves_dir,
        backup_before_write=False,
    )
    print(f"Kill command queued in: {path}")
    return 0
