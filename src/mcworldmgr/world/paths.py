from __future__ import annotations

import os
from pathlib import Path


def detect_default_saves_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidate = Path(appdata) / ".minecraft" / "saves"
        if candidate.exists():
            return candidate
    home_candidate = Path.home() / "AppData" / "Roaming" / ".minecraft" / "saves"
    return home_candidate


def resolve_saves_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return detect_default_saves_dir().resolve()
