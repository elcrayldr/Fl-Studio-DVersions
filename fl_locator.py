"""Localización de FL Studio instalado y apertura manual de proyectos (sin verificación automática)."""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class FlInstall:
    folder: str
    exe: str
    label: str
    major_guess: int | None     # inferido del nombre de carpeta, no verificado


def _guess_major(label: str) -> int | None:
    m = re.search(r"(\d{2,4})", label)
    if not m:
        return None
    v = int(m.group(1))
    if v >= 2000:           # p.ej. "FL Studio 2025" -> 25
        v -= 2000
    return v if 10 <= v <= 99 else None


def find_installs() -> list[FlInstall]:
    if sys.platform != "win32":
        return []
    bases = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")]
    out: list[FlInstall] = []
    for b in filter(None, bases):
        for folder in glob.glob(os.path.join(b, "Image-Line", "FL Studio*")):
            for exe_name in ("FL64.exe", "FL.exe"):
                exe = os.path.join(folder, exe_name)
                if os.path.isfile(exe):
                    label = os.path.basename(folder)
                    out.append(FlInstall(folder, exe, label, _guess_major(label)))
                    break
    return sorted(out, key=lambda i: (i.major_guess or 0), reverse=True)


def open_in_fl(project: str, exe: str | None = None) -> str:
    """Abre el proyecto en FL Studio. Devuelve cómo se lanzó. NO verifica que cargue correctamente."""
    if exe and os.path.isfile(exe):
        subprocess.Popen([exe, project], shell=False)  # noqa: S603 - argumentos sin shell
        return "exe"
    if sys.platform == "win32":
        os.startfile(project)  # type: ignore[attr-defined]  # noqa: S606
        return "asociacion"
    raise OSError("La apertura automática solo está disponible en Windows.")
