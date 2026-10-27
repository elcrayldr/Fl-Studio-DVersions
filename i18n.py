"""Catálogo de mensajes. Para añadir un idioma, crear otro dict y registrarlo en CATALOGS."""
from __future__ import annotations

ES: dict[str, str] = {
    # severidades y confianza
    "sev.critical": "Crítico", "sev.error": "Error", "sev.warning": "Aviso", "sev.info": "Info",
    "conf.confirmed": "Confirmado", "conf.inferred": "Inferido", "conf.hypothesis": "Hipótesis",
    "conf.unknown": "Desconocido",
    # incidencias estructurales
    "EMPTY_FILE": "El archivo está vacío (0 bytes).",
    "TOO_SMALL": "El archivo es demasiado pequeño para ser un FLP ({size} bytes).",
    "BAD_MAGIC": "No empieza por la firma 'FLhd': no parece un proyecto FLP (o está dañado al inicio).",
    "HEADER_TRUNCATED": "La cabecera FLhd está incompleta.",
    "HEADER_SIZE_UNEXPECTED": "El tamaño de cabecera declarado es {size} (se esperaba 6). Variante no documentada.",
    "DATA_CHUNK_MISSING": "No se encuentra el bloque 'FLdt' justo después de la cabecera.",
    "DATA_TRUNCATED": "El bloque de datos declara {declared} bytes pero solo hay {available}: el archivo está truncado ({missing} bytes ausentes).",
    "TRAILING_DATA": "Hay {n} bytes después del final declarado del bloque de datos (no interpretados).",
    "EVENT_INCOMPLETE": "Último evento incompleto en el desplazamiento {at} ({n} bytes sin completar).",
    "EVENT_OVERRUN": "Un evento en el desplazamiento {at} sobrepasa el final declarado del bloque de datos.",
    "VARINT_INVALID": "Longitud de evento inválida en el desplazamiento {at}.",
    "NO_EVENTS": "El bloque de datos no contiene eventos interpretables.",
    # semánticas
    "NO_VERSION": "No se encontró el evento de versión de FL Studio; no se puede determinar la versión de origen.",
    "VERSION_UNPARSEABLE": "El texto de versión '{text}' no tiene el formato esperado.",
    "VERSION_NEWER_THAN_TARGET": "El proyecto se guardó con la versión {src} (posterior a la versión de destino {dst}).",
    "TEMPO_IMPLAUSIBLE": "El tempo leído ({tempo}) está fuera de un rango plausible; interpretación no fiable.",
    "UNINTERPRETED_EVENTS": "{n} de {total} eventos usan identificadores que este analizador no interpreta (se conservan intactos).",
    "SAMPLE_MISSING": "Sample no encontrado: {path}",
    "SAMPLE_UNVERIFIABLE": "Ruta no verificable en este sistema: {path}",
    "SAMPLE_OK": "Sample presente: {path}",
    "PLUGIN_LISTED": "Plugin/instrumento referenciado: {name} (presencia en el sistema: {state}).",
    "NO_STRUCTURAL_PROBLEM": "No se detectaron problemas estructurales con las comprobaciones disponibles. Esto NO garantiza que FL Studio abra el proyecto.",
    # diagnóstico principal
    "DX.not_flp": "El archivo no es un proyecto FLP reconocible.",
    "DX.truncated": "El archivo está truncado o incompleto: se perdió la parte final del proyecto.",
    "DX.damaged": "La estructura del archivo presenta inconsistencias.",
    "DX.newer": "El proyecto procede de una versión de FL Studio más reciente que la de destino.",
    "DX.external": "No se aprecia daño estructural. Las causas más probables a investigar son plugins o samples externos (hipótesis, sin confirmar).",
    "DX.clean": "No se detectaron problemas con las comprobaciones disponibles.",
    "DX.unknown_version": "No se pudo determinar la versión de origen; el diagnóstico es limitado.",
    # reparación y conversión
    "RP.trim_tail": "Descartar el evento final incompleto ({n} bytes) y ajustar el tamaño declarado del bloque de datos.",
    "RP.remap_sample": "Reemplazar la ruta de sample (evento #{index}): '{old}' → '{new}'.",
    "RP.nothing": "No hay reparaciones automáticas seguras para este archivo.",
    "CV.not_needed": "No hace falta convertir: la versión de origen ({src}) no es posterior al destino ({dst}).",
    "CV.downgrade": "El proyecto es de una versión posterior ({src}) a la de destino ({dst}). No existe un método verificado para degradar proyectos; no se genera archivo.",
    "CV.unknown_source": "No se pudo determinar la versión de origen, por lo que no se puede evaluar la conversión.",
    "CV.unknown_target": "No se conoce la versión de destino. Selecciónala manualmente.",
    "CV.needs_repair": "El archivo tiene problemas estructurales. Repara una copia antes de evaluar la conversión.",
    "CV.no_method": "Esta versión no incluye transformaciones de formato verificadas entre versiones de FL Studio.",
    # validación
    "VA.A": "Nivel A — estructural", "VA.B": "Nivel B — contenido", "VA.C": "Nivel C — apertura en FL Studio",
    "VA.C.pending": "PENDIENTE: no se ha comprobado la apertura real en FL Studio. Ábrelo manualmente y confirma.",
    "VA.C.manual": "Confirmado manualmente por el usuario (no verificado automáticamente).",
    "pstate.not_checked": "no comprobado", "pstate.candidate_found": "coincidencia por nombre en carpetas escaneadas",
    "pstate.not_found_in_scanned_dirs": "no localizado en las carpetas escaneadas (no prueba que falte)",
    # GUI
    "gui.title": "CRAY FLP ANALYZER", "gui.subtitle": "Analizador, reparador y conversor de proyectos FL Studio",
    "gui.drop": "Arrastra aquí tus proyectos .flp o pulsa «Seleccionar»",
    "gui.select": "Seleccionar…", "gui.analyze": "Analizar", "gui.repair": "Reparar copia",
    "gui.convert": "Convertir", "gui.compare": "Comparar", "gui.open_fl": "Abrir en FL Studio",
    "gui.save_report": "Guardar informe…", "gui.settings": "Ajustes", "gui.logs": "Registros",
    "gui.no_file": "Ningún archivo seleccionado.", "gui.ready": "Listo.", "gui.working": "Trabajando…",
}

CATALOGS = {"es": ES}
_current = "es"


def set_language(code: str) -> None:
    global _current
    if code in CATALOGS:
        _current = code


def t(key: str, **kw) -> str:
    text = CATALOGS[_current].get(key, key)
    try:
        return text.format(**kw)
    except (KeyError, IndexError, ValueError):
        return text
