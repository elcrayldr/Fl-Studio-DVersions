"""Generador de archivos SINTÉTICOS con estructura FLhd/FLdt. NO son proyectos reales de FL Studio."""
from __future__ import annotations

import struct

from cray_flp_analyzer.flp.semantics import encode_text
from cray_flp_analyzer.flp.writer import build_event

MARK = "SINTÉTICO - no es un proyecto real de FL Studio"


def ev_byte(i, v): return build_event(i, bytes([v]))
def ev_word(i, v): return build_event(i, struct.pack("<H", v))
def ev_dword(i, v): return build_event(i, struct.pack("<I", v))
def ev_text(i, s, enc): return build_event(i, encode_text(s, enc))


def build_flp(version="20.8.3.2304", tempo=140.0, channels=("Kick", "Bass"), patterns=("P1",),
              samples=(), plugins=(), unknown=(), blob=b"\x01\x02\x03\x04", ppq=96, declared_extra=0,
              trailing=b"") -> bytes:
    vt = tuple(int(x) for x in version.split("."))
    enc = "utf-16le" if vt >= (11, 5) else "cp1252"
    evs = [build_event(199, version.encode("ascii") + b"\x00"), ev_text(194, MARK, enc),
           ev_dword(156, int(tempo * 1000))]
    for n in channels:
        evs += [ev_word(64, 0), ev_text(192, n, enc)]
    for n in patterns:
        evs += [ev_word(65, 1), ev_text(193, n, enc), build_event(224, blob)]
    for s in samples:
        evs.append(ev_text(196, s, enc))
    for p in plugins:
        evs.append(ev_text(203, p, enc))
    for uid, payload in unknown:
        evs.append(build_event(uid, payload))
    evs.append(build_event(233, blob * 3))
    body = b"".join(evs)
    return (b"FLhd" + struct.pack("<I", 6) + struct.pack("<hHH", 0, len(channels), ppq)
            + b"FLdt" + struct.pack("<I", len(body) + declared_extra) + body + trailing)
