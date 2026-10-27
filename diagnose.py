"""Diagnóstico: separa lo confirmado de lo inferido y de las hipótesis."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import paths as pathmod
from . import plugins as plugmod
from .flp import FlpDocument, parse_flp
from .flp.semantics import ProjectInfo, interpret
from .i18n import t

SEV_ORDER = {"critical": 0, "error": 1, "warning": 2, "info": 3}


@dataclass
class Issue:
    code: str
    severity: str
    confidence: str           # confirmed | inferred | hypothesis | unknown
    message: str
    category: str = "estructura"
    offset: int | None = None
    event_index: int | None = None
    remedies: list[str] = field(default_factory=list)


@dataclass
class Diagnosis:
    primary_code: str
    primary_text: str
    primary_confidence: str
    issues: list[Issue]
    info: ProjectInfo
    samples: list[dict]
    plugins: list[dict]
    limitations: list[str]


STRUCT_CONFIDENCE = "confirmed"


def diagnose(doc: FlpDocument, target_major: int | None = None, sample_dirs: list[str] | None = None,
             plugin_dirs: list[str] | None = None, scan_plugins: bool = False) -> Diagnosis:
    info = interpret(doc)
    issues: list[Issue] = []
    for si in doc.issues:
        issues.append(Issue(si.code, si.severity, STRUCT_CONFIDENCE, t(si.code, **si.p()),
                            "estructura", si.offset))

    limitations = [
        "El significado de los identificadores de evento procede de documentación comunitaria y no está "
        "verificado contra proyectos reales en esta versión (confianza 'inferido').",
        "Los datos binarios de plugins, notas, playlist y automatizaciones no se interpretan: se conservan "
        "intactos pero no se pueden comparar semánticamente.",
    ]

    if doc.recognized and doc.structurally_ok or (doc.recognized and doc.events):
        if info.version_text is None:
            issues.append(Issue("NO_VERSION", "warning", "inferred", t("NO_VERSION"), "versión"))
        elif info.version is None:
            issues.append(Issue("VERSION_UNPARSEABLE", "warning", "inferred",
                                t("VERSION_UNPARSEABLE", text=info.version_issue), "versión"))
        if info.tempo is not None and not (10 <= info.tempo <= 999):
            issues.append(Issue("TEMPO_IMPLAUSIBLE", "warning", "inferred",
                                t("TEMPO_IMPLAUSIBLE", tempo=info.tempo), "contenido"))
        if info.uninterpreted_events:
            issues.append(Issue("UNINTERPRETED_EVENTS", "info", "confirmed",
                                t("UNINTERPRETED_EVENTS", n=info.uninterpreted_events, total=info.total_events),
                                "contenido"))
        if info.version and target_major and info.version[0] > target_major:
            issues.append(Issue("VERSION_NEWER_THAN_TARGET", "error", "inferred",
                                t("VERSION_NEWER_THAN_TARGET", src=info.version_text, dst=target_major),
                                "versión", remedies=["open_in_newer_fl"]))

    # samples
    sample_rows: list[dict] = []
    idx = pathmod.index_folders(sample_dirs) if sample_dirs else None
    for s in info.samples:
        state = pathmod.check_exists(s.path)
        cands = [c.path for c in pathmod.find_candidates(s.path, idx)] if (idx is not None and state != "exists") else []
        sample_rows.append({"event_index": s.event_index, "path": s.path, "state": state,
                            "style": pathmod.path_style(s.path), "candidates": cands})
        if state == "missing":
            issues.append(Issue("SAMPLE_MISSING", "warning", "confirmed", t("SAMPLE_MISSING", path=s.path),
                                "samples", event_index=s.event_index, remedies=["remap_sample"]))
        elif state == "unverifiable":
            issues.append(Issue("SAMPLE_UNVERIFIABLE", "info", "unknown", t("SAMPLE_UNVERIFIABLE", path=s.path),
                                "samples", event_index=s.event_index))

    # plugins
    installed = plugmod.scan_installed(plugin_dirs if plugin_dirs is not None else plugmod.default_scan_dirs()) \
        if scan_plugins else None
    plugin_rows: list[dict] = []
    for p in info.plugins:
        state = plugmod.presence(p.name, installed)
        plugin_rows.append({"event_index": p.event_index, "name": p.name, "state": state,
                            "name_source": "inferido (evento %d)" % p.source_id})
        issues.append(Issue("PLUGIN_LISTED", "info", "hypothesis",
                            t("PLUGIN_LISTED", name=p.name, state=t("pstate." + state)), "plugins", event_index=p.event_index))
    if plugin_rows:
        limitations.append("La presencia de un plugin se estima solo por nombre de archivo en carpetas "
                           "escaneadas; 'no encontrado' no prueba que falte ni que sea la causa de un cierre.")

    issues.sort(key=lambda i: (SEV_ORDER.get(i.severity, 9), i.category))

    code, conf = _primary(doc, info, issues)
    if not any(i.severity in ("critical", "error", "warning") for i in issues) and code == "clean":
        issues.append(Issue("NO_STRUCTURAL_PROBLEM", "info", "inferred", t("NO_STRUCTURAL_PROBLEM"), "estructura"))
    return Diagnosis(code, t("DX." + code), conf, issues, info, sample_rows, plugin_rows, limitations)


def _primary(doc: FlpDocument, info: ProjectInfo, issues: list[Issue]) -> tuple[str, str]:
    if not doc.recognized:
        return "not_flp", "confirmed"
    if doc.truncated:
        return "truncated", "confirmed"
    if any(i.severity in ("critical", "error") and i.category == "estructura" for i in issues):
        return "damaged", "confirmed"
    if any(i.code == "VERSION_NEWER_THAN_TARGET" for i in issues):
        return "newer", "inferred"
    if info.version is None:
        return "unknown_version", "inferred"
    if any(i.code == "SAMPLE_MISSING" for i in issues) or info.plugins:
        return "external", "hypothesis"
    return "clean", "inferred"


def analyze_bytes(data: bytes, **kw) -> tuple[FlpDocument, Diagnosis]:
    doc = parse_flp(data)
    return doc, diagnose(doc, **kw)
