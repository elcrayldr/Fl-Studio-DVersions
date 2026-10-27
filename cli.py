"""Interfaz de línea de comandos: analyze | repair | compare | gui."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import service
from .config import Settings
from .logging_setup import setup_logging
from .repair import SampleRemap, plan_repairs
from .report import save_report, to_markdown
from .validate import validate_pair
from .version import APP_NAME, APP_STAGE, APP_VERSION


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cray-flp", description=f"{APP_NAME} {APP_VERSION} ({APP_STAGE})")
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("analyze", help="Analiza uno o varios .flp (solo lectura)")
    a.add_argument("files", nargs="+", type=Path)
    a.add_argument("--out", type=Path, help="Carpeta donde guardar informes")
    a.add_argument("--samples", type=Path, nargs="*", default=[], help="Carpetas donde buscar samples")
    a.add_argument("--target", type=int, help="Versión mayor de FL de destino (p.ej. 26)")
    r = sub.add_parser("repair", help="Repara una COPIA (recorta cola truncada)")
    r.add_argument("file", type=Path)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--trim-tail", action="store_true")
    r.add_argument("--remap", nargs=3, action="append", metavar=("INDICE", "ANTIGUA", "NUEVA"),
                   help="Reemplaza una ruta de sample (confirmada por ti)")
    c = sub.add_parser("compare", help="Compara dos .flp")
    c.add_argument("before", type=Path)
    c.add_argument("after", type=Path)
    sub.add_parser("gui", help="Abre la interfaz gráfica")
    args = ap.parse_args(argv)
    setup_logging()

    if args.cmd in (None, "gui"):
        from .gui.app import run
        return run()

    settings = Settings.load()
    if args.cmd == "analyze":
        if args.target:
            settings.target_mode, settings.target_major = "manual", args.target
        if args.samples:
            settings.sample_search_dirs = [str(p) for p in args.samples]
        rc = 0
        for f in args.files:
            try:
                an = service.analyze_file(f, settings)
            except OSError as e:
                print(f"{f}: no se pudo leer ({e})", file=sys.stderr)
                rc = 2
                continue
            rep = an.report()
            print(to_markdown(rep))
            if args.out:
                save_report(rep, args.out, f.stem)
        return rc
    if args.cmd == "repair":
        an = service.analyze_file(args.file, settings)
        remaps = [SampleRemap(int(i), old, new) for i, old, new in (args.remap or [])]
        if not args.trim_tail and not remaps:
            for act in plan_repairs(an.doc, an.diag) or []:
                print("Posible:", act.description)
            print("Indica --trim-tail o --remap para aplicar algo.")
            return 1
        try:
            res, val = service.repair_file(an, args.out, args.trim_tail, remaps)
        except ValueError as e:
            print(f"No se generó archivo: {e}", file=sys.stderr)
            return 3
        rep = an.report(operation=res, validation=val)
        j, m = save_report(rep, args.out, Path(res.output).stem)
        print(to_markdown(rep))
        return 0
    if args.cmd == "compare":
        val = validate_pair(args.before.read_bytes(), args.after.read_bytes())
        for d in val.diff:
            if d.status != "igual":
                print(f"{d.category} · {d.key}: {d.before} -> {d.after} ({d.status})")
        print(f"A={val.A.status} B={val.B.status} C={val.C.status}")
        return 0
    return 0
