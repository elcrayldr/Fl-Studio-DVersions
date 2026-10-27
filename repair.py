"""Reparación conservadora. Solo se implementan transformaciones con base estructural."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .diagnose import Diagnosis
from .flp import FlpDocument, parse_flp, replaced_event, serialize
from .flp.semantics import encode_text
from .i18n import t
from .session import OperationResult, run_safe_operation


@dataclass
class RepairAction:
    code: str                 # trim_tail | remap_sample
    description: str
    automatic: bool
    needs_confirmation: bool
    risk: str
    event_index: int | None = None
    old: str | None = None
    new: str | None = None


@dataclass
class SampleRemap:
    event_index: int
    old: str
    new: str                  # el llamador debe haberlo confirmado con el usuario


def plan_repairs(doc: FlpDocument, diag: Diagnosis) -> list[RepairAction]:
    actions: list[RepairAction] = []
    if doc.recognized and doc.events and doc.truncated and doc.tail is not None:
        n = len(doc.tail)
        actions.append(RepairAction(
            "trim_tail", t("RP.trim_tail", n=n), True, True,
            "El contenido posterior al corte es irrecuperable; FL Studio puede seguir sin abrir el proyecto."))
    for row in diag.samples:
        if row["state"] == "missing" and row["candidates"]:
            actions.append(RepairAction("remap_sample", t("RP.remap_sample", index=row["event_index"],
                                                         old=row["path"], new=row["candidates"][0]),
                                        False, True, "La coincidencia es solo por nombre; confírmala.",
                                        row["event_index"], row["path"], row["candidates"][0]))
    return actions


def _apply(data: bytes, trim_tail: bool, remaps: list[SampleRemap]) -> tuple[bytes, list[str]]:
    doc = parse_flp(data)
    if not doc.recognized or not doc.events:
        raise ValueError("El archivo no es reparable con seguridad (estructura no reconocida).")
    events = list(doc.events)
    changes: list[str] = []
    if remaps:
        from .flp.semantics import interpret
        info = interpret(doc)
        enc_by_index = {s.event_index: s for s in info.samples}
        for r in remaps:
            ref = enc_by_index.get(r.event_index)
            if ref is None or events[r.event_index].id != 196:
                raise ValueError(f"El evento #{r.event_index} no es una ruta de sample verificable.")
            if ref.path != r.old:
                raise ValueError(f"La ruta actual del evento #{r.event_index} no coincide con la esperada.")
            if info.version is None:
                raise ValueError("Sin versión de origen no se puede fijar la codificación del texto con seguridad.")
            events[r.event_index] = replaced_event(events[r.event_index], encode_text(r.new, ref.encoding))
            changes.append(t("RP.remap_sample", index=r.event_index, old=r.old, new=r.new))
    if trim_tail:
        if not doc.truncated:
            raise ValueError("El archivo no está truncado; no se aplica el recorte.")
        changes.append(t("RP.trim_tail", n=len(doc.tail)))
    elif doc.truncated:
        raise ValueError("El archivo está truncado: hay que recortar la cola incompleta para obtener una estructura válida.")
    out = serialize(doc, events, keep_trailing=True)
    if not parse_flp(out).structurally_ok:
        raise ValueError("El resultado no supera la validación estructural; se descarta.")
    return out, changes


def repair_copy(original: Path, output_dir: Path, trim_tail: bool = False,
                remaps: list[SampleRemap] | None = None) -> OperationResult:
    remaps = remaps or []
    if not trim_tail and not remaps:
        raise ValueError(t("RP.nothing"))
    return run_safe_operation(original, output_dir, "repair", "reparado",
                              lambda b: _apply(b, trim_tail, remaps))
