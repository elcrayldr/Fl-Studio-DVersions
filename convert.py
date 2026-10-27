"""Evaluación de conversión. No se fabrican conversiones: sin método verificado, no se genera archivo."""
from __future__ import annotations

from dataclasses import dataclass

from .diagnose import Diagnosis
from .i18n import t


@dataclass
class ConversionAssessment:
    status: str        # not_needed | needs_repair | downgrade_unsupported | unknown_source | unknown_target | no_method
    explanation: str
    can_generate_file: bool = False


def assess_conversion(diag: Diagnosis, target_major: int | None) -> ConversionAssessment:
    info = diag.info
    if any(i.severity in ("critical", "error") and i.category == "estructura" for i in diag.issues):
        return ConversionAssessment("needs_repair", t("CV.needs_repair"))
    if info.version is None:
        return ConversionAssessment("unknown_source", t("CV.unknown_source"))
    if not target_major:
        return ConversionAssessment("unknown_target", t("CV.unknown_target"))
    if info.version[0] > target_major:
        return ConversionAssessment("downgrade_unsupported",
                                    t("CV.downgrade", src=info.version_text, dst=target_major))
    return ConversionAssessment("not_needed", t("CV.not_needed", src=info.version_text, dst=target_major))
