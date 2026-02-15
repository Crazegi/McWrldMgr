from __future__ import annotations

MIN_DATA_VERSION = 3465


def assert_supported_data_version(data_version: int) -> None:
    if data_version < MIN_DATA_VERSION:
        raise ValueError(
            f"Unsupported world DataVersion {data_version}. This build supports 1.20+ worlds."
        )
