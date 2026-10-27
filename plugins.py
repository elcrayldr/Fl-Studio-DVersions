"""Comprobación de presencia de plugins. Una coincidencia de nombre NO prueba compatibilidad."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

DEFAULT_SCAN_DIRS_WINDOWS = [
    r"C:\Program Files\Common Files\VST3",
    r"C:\Program Files\Steinberg\VSTPlugins",
    r"C:\Program Files\VSTPlugins",
    r"C:\Program Files (x86)\VSTPlugins",
]
_PLUGIN_EXT = {".dll", ".vst3", ".fst"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def default_scan_dirs() -> list[str]:
    return DEFAULT_SCAN_DIRS_WINDOWS if sys.platform == "win32" else []


def scan_installed(dirs: list[str]) -> dict[str, str]:
    found: dict[str, str] = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, subdirs, files in os.walk(d):
            for name in list(subdirs) + files:
                p = Path(name)
                if p.suffix.lower() in _PLUGIN_EXT:
                    found.setdefault(_norm(p.stem), str(Path(root) / name))
    return found


def presence(name: str, installed: dict[str, str] | None) -> str:
    """'not_checked' | 'candidate_found' | 'not_found_in_scanned_dirs'."""
    if installed is None:
        return "not_checked"
    return "candidate_found" if _norm(name) in installed else "not_found_in_scanned_dirs"
