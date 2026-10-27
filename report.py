"""Generación de informes (dict/JSON y texto Markdown en español)."""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path

from .convert import ConversionAssessment
from .diagnose import Diagnosis
from .i18n import t
from .session import OperationResult, sha256_file
from .validate import ValidationReport
from .version import APP_NAME, APP_STAGE, APP_VERSION


def build_report(path: Path, diag: Diagnosis, conversion: ConversionAssessment | None = None,
                 operation: OperationResult | None = None, validation: ValidationReport | None = None) -> dict:
    info = diag.info
    rep = {
        "aplicacion": f"{APP_NAME} {APP_VERSION} ({APP_STAGE})",
        "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
        "archivo": str(path), "sha256": sha256_file(path), "tamano_bytes": path.stat().st_size,
        "diagnostico": {"codigo": diag.primary_code, "texto": diag.primary_text,
                        "confianza": diag.primary_confidence},
        "confirmado": {"ppq": info.ppq, "canales_cabecera": info.channels_header,
                       "eventos_totales": info.total_events},
        "inferido": {"version_fl": info.version_text, "tempo": info.tempo, "titulo": info.title,
                     "codificacion_texto": info.text_encoding},
        "desconocido": {"eventos_sin_interpretar": info.uninterpreted_events, "ids_desconocidos": info.unknown_ids},
        "incidencias": [asdict(i) for i in diag.issues],
        "samples": diag.samples, "plugins": diag.plugins, "limitaciones": diag.limitations,
    }
    if conversion:
        rep["conversion"] = asdict(conversion)
    if operation:
        rep["operacion"] = asdict(operation)
    if validation:
        rep["validacion"] = {"A": asdict(validation.A), "B": asdict(validation.B), "C": asdict(validation.C),
                             "diferencias": [asdict(d) for d in validation.diff if d.status != "igual"]}
    return rep


def to_json(rep: dict) -> str:
    return json.dumps(rep, ensure_ascii=False, indent=2, default=str)


def to_markdown(rep: dict) -> str:
    L: list[str] = [f"# Informe — {rep['aplicacion']}", "",
                    f"- Archivo: `{rep['archivo']}`", f"- SHA-256: `{rep['sha256']}`",
                    f"- Fecha: {rep['fecha']}", "",
                    "## Diagnóstico principal", "",
                    f"{rep['diagnostico']['texto']}  ",
                    f"**Confianza:** {t('conf.' + rep['diagnostico']['confianza'])}", "",
                    "## Datos", ""]
    c, i, u = rep["confirmado"], rep["inferido"], rep["desconocido"]
    L += [f"- (Confirmado) PPQ={c['ppq']}, canales en cabecera={c['canales_cabecera']}, eventos={c['eventos_totales']}",
          f"- (Inferido) Versión FL={i['version_fl']}, tempo={i['tempo']}, título={i['titulo']}",
          f"- (Desconocido) {u['eventos_sin_interpretar']} eventos sin interpretar", "",
          "## Incidencias", ""]
    for x in rep["incidencias"]:
        L.append(f"- [{t('sev.' + x['severity'])} · {t('conf.' + x['confidence'])}] {x['message']}")
    if rep.get("conversion"):
        L += ["", "## Conversión", "", rep["conversion"]["explanation"]]
    if rep.get("operacion"):
        o = rep["operacion"]
        L += ["", "## Operación", "", f"- Tipo: {o['operation']}", f"- Salida: `{o['output']}`",
              f"- Original intacto: {'sí' if o['original_untouched'] else 'NO'}"]
        L += [f"- Cambio: {ch}" for ch in o["changes"]]
    if rep.get("validacion"):
        v = rep["validacion"]
        L += ["", "## Validación", ""]
        for k in ("A", "B", "C"):
            L.append(f"- **{t('VA.' + k)}: {v[k]['status']}**")
            L += [f"  - {d}" for d in v[k]["details"]]
        L += ["", "### Diferencias antes/después", ""]
        L += [f"- {d['category']} · {d['key']}: {d['before']} → {d['after']} ({d['status']}"
              f"{', previsto' if d['explained'] else ''})" for d in v["diferencias"]] or ["- Ninguna."]
    L += ["", "## Limitaciones", ""] + [f"- {x}" for x in rep["limitaciones"]]
    return "\n".join(L) + "\n"


def save_report(rep: dict, directory: Path, stem: str) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    j, m = directory / f"{stem}_informe.json", directory / f"{stem}_informe.md"
    j.write_text(to_json(rep), encoding="utf-8")
    m.write_text(to_markdown(rep), encoding="utf-8")
    return j, m
