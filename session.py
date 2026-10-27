"""Protección del original: hash, copia de trabajo, salida nueva, registro de operaciones."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

log = logging.getLogger("cray.session")


class OriginalModifiedError(RuntimeError):
    pass


class UnsafeOutputError(ValueError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unique_output_path(directory: Path, stem: str, suffix: str, ext: str = ".flp") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    cand = directory / f"{stem}_cray_{suffix}{ext}"
    n = 2
    while cand.exists():
        cand = directory / f"{stem}_cray_{suffix}_{n}{ext}"
        n += 1
    return cand


@dataclass
class OperationResult:
    operation: str
    original: str
    original_sha256: str
    output: str | None
    output_sha256: str | None
    original_untouched: bool
    changes: list[str] = field(default_factory=list)
    started: str = ""
    extra: dict = field(default_factory=dict)


def append_oplog(directory: Path, entry: dict) -> None:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / "cray_operaciones.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        log.warning("No se pudo escribir el registro de operaciones", exc_info=True)


def run_safe_operation(original: Path, output_dir: Path, operation: str, suffix: str,
                       transform: Callable[[bytes], tuple[bytes, list[str]]]) -> OperationResult:
    """transform(bytes_de_la_copia) -> (bytes_nuevos, lista_de_cambios). El original nunca se abre en escritura."""
    original = Path(original).resolve()
    output_dir = Path(output_dir).resolve()
    sha_before = sha256_file(original)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with tempfile.TemporaryDirectory(prefix="cray_work_") as tmp:
        work = Path(tmp) / original.name
        shutil.copyfile(original, work)
        if sha256_file(work) != sha_before:
            raise OriginalModifiedError("La copia de trabajo no coincide con el original.")
        new_bytes, changes = transform(work.read_bytes())
    out = unique_output_path(output_dir, original.stem, suffix, original.suffix or ".flp")
    if out.resolve() == original:
        raise UnsafeOutputError("La salida coincidiría con el original.")
    fd, tmp_out = tempfile.mkstemp(dir=output_dir, prefix=".cray_", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(new_bytes)
        os.replace(tmp_out, out)
    finally:
        if os.path.exists(tmp_out):
            os.remove(tmp_out)
    sha_after = sha256_file(original)
    untouched = sha_after == sha_before
    res = OperationResult(operation, str(original), sha_before, str(out), sha256_file(out), untouched,
                          changes, started)
    append_oplog(output_dir, {"ts": started, "operation": operation, "original": str(original),
                              "original_sha256": sha_before, "output": str(out),
                              "output_sha256": res.output_sha256, "original_untouched": untouched,
                              "changes": changes})
    if not untouched:
        raise OriginalModifiedError("¡El original cambió durante la operación!")
    return res
