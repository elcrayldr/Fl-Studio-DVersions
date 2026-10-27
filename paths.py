"""Clasificación y resolución asistida de rutas de samples. Nunca asigna nada sin confirmación."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_WIN_ABS = re.compile(r"^[A-Za-z]:[\\/]")


def path_style(p: str) -> str:
    if p.startswith("%") or p.startswith("$"):
        return "macro"           # p.ej. %FLStudioFactoryData%: depende de la instalación de FL
    if _WIN_ABS.match(p) or p.startswith("\\\\"):
        return "windows"
    if p.startswith("/"):
        return "posix"
    return "relative"


def check_exists(p: str) -> str:
    """'exists' | 'missing' | 'unverifiable'."""
    style = path_style(p)
    here = "windows" if sys.platform == "win32" else "posix"
    if style in ("macro", "relative"):
        return "unverifiable"
    if style != here:
        return "unverifiable"
    try:
        return "exists" if os.path.isfile(p) else "missing"
    except OSError:
        return "unverifiable"


def basename_any(p: str) -> str:
    return re.split(r"[\\/]", p)[-1]


@dataclass
class Candidate:
    path: str
    criteria: str          # criterios en los que coincide
    exact_name: bool


def index_folders(folders: list[str], extensions: set[str] | None = None, limit: int = 500_000) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = {}
    n = 0
    for folder in folders:
        for root, _dirs, files in os.walk(folder):
            for f in files:
                if extensions and Path(f).suffix.lower() not in extensions:
                    continue
                idx.setdefault(f.lower(), []).append(Path(root) / f)
                n += 1
                if n >= limit:
                    return idx
    return idx


def find_candidates(original_path: str, index: dict[str, list[Path]]) -> list[Candidate]:
    """Coincidencia por nombre de archivo (insensible a mayúsculas). Es una propuesta, no una certeza."""
    name = basename_any(original_path).lower()
    return [Candidate(str(p), "nombre de archivo", True) for p in index.get(name, [])]
