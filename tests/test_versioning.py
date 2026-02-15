from mcworldmgr.world.versioning import assert_supported_data_version


def test_version_supported() -> None:
    assert_supported_data_version(3465)


def test_version_unsupported() -> None:
    try:
        assert_supported_data_version(3000)
    except ValueError:
        return
    raise AssertionError("Expected ValueError for unsupported version")
