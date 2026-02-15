from pathlib import Path

from mcworldmgr.world.discovery import list_worlds, resolve_world


def test_list_worlds(tmp_path: Path) -> None:
    saves = tmp_path / "saves"
    world_ok = saves / "WorldA"
    world_ok.mkdir(parents=True)
    (world_ok / "level.dat").write_bytes(b"x")

    world_bad = saves / "NotAWorld"
    world_bad.mkdir(parents=True)

    worlds = list_worlds(str(saves))
    assert len(worlds) == 1
    assert worlds[0].name == "WorldA"


def test_resolve_world_by_name(tmp_path: Path) -> None:
    saves = tmp_path / "saves"
    world = saves / "WorldB"
    world.mkdir(parents=True)
    (world / "level.dat").write_bytes(b"x")

    resolved = resolve_world("WorldB", str(saves))
    assert resolved.path == world.resolve()
