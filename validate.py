"""Validación por niveles (A estructural, B contenido, C apertura en FL Studio) y comparación."""
from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from .flp import FlpDocument, parse_flp, serialize
from .flp.semantics import interpret
from .i18n import t


@dataclass
class DiffItem:
    category: str
    key: str
    before: object
    after: object
    status: str            # igual | perdido | añadido | modificado
    explained: bool = False
    note: str = ""


@dataclass
class LevelResult:
    level: str
    status: str            # PASS | WARN | FAIL | PENDIENTE | MANUAL
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    A: LevelResult
    B: LevelResult
    C: LevelResult
    diff: list[DiffItem]


def summarize(doc: FlpDocument) -> dict:
    info = interpret(doc)
    payloads = Counter((e.id, hashlib.sha1(e.payload).hexdigest()) for e in doc.events)
    return {
        "version": info.version_text, "tempo": info.tempo, "ppq": doc.ppq, "channels_header": doc.n_channels,
        "event_counts": dict(info.event_counts), "texts": {k: list(v) for k, v in info.texts.items()},
        "samples": [s.path for s in info.samples], "plugins": [p.name for p in info.plugins],
        "payloads": payloads, "tail_bytes": len(doc.tail), "trailing_bytes": len(doc.trailing),
    }


def diff_summaries(before: dict, after: dict, expected_event_ids: set[int] | None = None) -> list[DiffItem]:
    expected = expected_event_ids or set()
    items: list[DiffItem] = []
    for key in ("version", "tempo", "ppq", "channels_header"):
        b, a = before[key], after[key]
        items.append(DiffItem("proyecto", key, b, a, "igual" if b == a else "modificado"))
    ids = sorted(set(before["event_counts"]) | set(after["event_counts"]))
    for i in ids:
        b, a = before["event_counts"].get(i, 0), after["event_counts"].get(i, 0)
        st = "igual" if a == b else ("perdido" if a < b else "añadido")
        items.append(DiffItem("eventos", f"id {i}", b, a, st, explained=(i in expected and st != "igual")))
    lost = before["payloads"] - after["payloads"]
    gained = after["payloads"] - before["payloads"]
    for (eid, _h), n in lost.items():
        items.append(DiffItem("contenido", f"evento id {eid}: datos distintos o ausentes", n, 0,
                              "modificado", explained=(eid in expected)))
    for (eid, _h), n in gained.items():
        items.append(DiffItem("contenido", f"evento id {eid}: datos nuevos", 0, n, "añadido",
                              explained=(eid in expected)))
    if before["tail_bytes"] != after["tail_bytes"]:
        items.append(DiffItem("contenido", "bytes de cola incompleta", before["tail_bytes"], after["tail_bytes"],
                              "perdido", True, "Bytes irrecuperables descartados en la reparación."))
    return items


def validate_pair(original: bytes, result: bytes, expected_event_ids: set[int] | None = None,
                  manual_open_confirmed: bool = False) -> ValidationReport:
    d_before, d_after = parse_flp(original), parse_flp(result)
    a = LevelResult("A", "PASS")
    if len(result) == 0:
        a.status = "FAIL"; a.details.append("El resultado está vacío.")
    if not d_after.structurally_ok:
        a.status = "FAIL"; a.details.append("El resultado no supera la lectura estructural: "
                                           + ", ".join(i.code for i in d_after.issues))
    elif serialize(d_after, keep_trailing=True) != result:
        a.status = "WARN"; a.details.append("La reserialización no es idéntica byte a byte.")
    else:
        a.details.append("El resultado se vuelve a leer sin errores y se reserializa idéntico.")

    diff = diff_summaries(summarize(d_before), summarize(d_after), expected_event_ids)
    unexplained_loss = [d for d in diff if d.status in ("perdido",) and not d.explained]
    unexplained_mod = [d for d in diff if d.status in ("modificado", "añadido") and d.category != "proyecto"
                       and not d.explained]
    b = LevelResult("B", "PASS")
    if unexplained_loss:
        b.status = "FAIL"; b.details.append(f"{len(unexplained_loss)} pérdidas sin justificar.")
    if unexplained_mod:
        b.status = "FAIL" if b.status == "FAIL" else "WARN"
        b.details.append(f"{len(unexplained_mod)} diferencias de contenido no previstas.")
    if b.status == "PASS":
        b.details.append("Los eventos interpretables y sus datos coinciden salvo cambios previstos.")
    b.details.append("No comparable: el significado musical de los blobs binarios (notas, playlist, "
                     "automatizaciones, estado de plugins) no se interpreta; solo se compara que sus bytes se conserven.")
    c = LevelResult("C", "MANUAL" if manual_open_confirmed else "PENDIENTE",
                    [t("VA.C.manual" if manual_open_confirmed else "VA.C.pending"),
                     "No se ha comprobado el audio ni la equivalencia sonora."])
    return ValidationReport(a, b, c, diff)
