from mcworldmgr.commands.regions_cmd import _region_name_for_chunk


def test_region_name_for_chunk_positive() -> None:
    assert _region_name_for_chunk(0, 0) == "r.0.0.mca"
    assert _region_name_for_chunk(31, 31) == "r.0.0.mca"
    assert _region_name_for_chunk(32, 0) == "r.1.0.mca"


def test_region_name_for_chunk_negative() -> None:
    assert _region_name_for_chunk(-1, -1) == "r.-1.-1.mca"
    assert _region_name_for_chunk(-33, 0) == "r.-2.0.mca"
