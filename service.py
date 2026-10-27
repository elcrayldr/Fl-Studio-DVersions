"""Capa de servicio que usan la CLI y la GUI (sin dependencias de interfaz)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import convert as cv
from . import repair as rp
from .config import Settings
from .diagnose import Diagnosis, diagnose
from .fl_locator import find_installs
from .flp import FlpDocument, parse_flp
from .report import build_report
from .session import OperationResult
from .validate import ValidationReport, validate_pair


def resolve_target_major(settings: Settings) -> tuple[int | None, str]:
    if settings.target_mode == "auto":
        installs = find_installs()
        for i in installs:
            if i.major_guess:
                return i.major_guess, f"instalada: {i.label} (inferido del nombre de carpeta)"
    return settings.target_major, "manual/predeterminada"


@dataclass
class Analysis:
    path: Path
    doc: FlpDocument
    diag: Diagnosis
    conversion: cv.ConversionAssessment
    target_major: int | None
    target_source: str

    def report(self, **kw) -> dict:
        return build_report(self.path, self.diag, self.conversion, **kw)


def analyze_file(path: Path, settings: Settings | None = None, scan_plugins: bool = False) -> Analysis:
    s = settings or Settings()
    data = Path(path).read_bytes()
    target, src = resolve_target_major(s)
    doc = parse_flp(data)
    diag = diagnose(doc, target_major=target, sample_dirs=s.sample_search_dirs or None,
                    plugin_dirs=s.plugin_scan_dirs or None, scan_plugins=scan_plugins)
    return Analysis(Path(path), doc, diag, cv.assess_conversion(diag, target), target, src)


def repair_file(a: Analysis, output_dir: Path, trim_tail: bool,
                remaps: list[rp.SampleRemap]) -> tuple[OperationResult, ValidationReport]:
    res = rp.repair_copy(a.path, output_dir, trim_tail=trim_tail, remaps=remaps)
    expected = {196} if remaps else set()
    val = validate_pair(a.path.read_bytes(), Path(res.output).read_bytes(), expected)
    return res, val
