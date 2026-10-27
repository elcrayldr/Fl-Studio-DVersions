"""Configuración y ubicaciones de datos de usuario (sin escribir en la carpeta de instalación)."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .version import APP_NAME

_DIRNAME = "CrayFLPAnalyzer"


def user_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(os.environ.get("CRAY_FLP_HOME", "")) if os.environ.get("CRAY_FLP_HOME") else Path(base) / _DIRNAME


def logs_dir() -> Path:
    return user_data_dir() / "logs"


def default_output_dir() -> Path:
    return Path.home() / "Documents" / APP_NAME


@dataclass
class Settings:
    language: str = "es"
    target_mode: str = "auto"          # "auto" (instalada) o "manual"
    target_major: int = 26             # usado si no se detecta o es manual
    output_dir: str = ""
    sample_search_dirs: list[str] = field(default_factory=list)
    plugin_scan_dirs: list[str] = field(default_factory=list)
    fl_exe: str = ""

    @staticmethod
    def path() -> Path:
        return user_data_dir() / "settings.json"

    @classmethod
    def load(cls) -> "Settings":
        try:
            raw = json.loads(cls.path().read_text(encoding="utf-8"))
            known = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
            return cls(**known)
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self) -> None:
        p = self.path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    def resolved_output_dir(self) -> Path:
        return Path(self.output_dir) if self.output_dir else default_output_dir()
