# Informe de pruebas — Cray FLP Analyzer 0.2.0 (alfa)

Fecha: 2026-10-27 · Entorno: Linux x86_64, Python 3.12.3, solo biblioteca estándar (unittest).

```
test_clean_does_not_claim_success (test_all.TestDiagnose.test_clean_does_not_claim_success) ... ok
test_missing_sample_posix (test_all.TestDiagnose.test_missing_sample_posix) ... ok
test_newer_than_target (test_all.TestDiagnose.test_newer_than_target) ... ok
test_no_version (test_all.TestDiagnose.test_no_version) ... ok
test_older_not_converted (test_all.TestDiagnose.test_older_not_converted) ... ok
test_plugins_are_hypothesis_not_culprit (test_all.TestDiagnose.test_plugins_are_hypothesis_not_culprit) ... ok
test_sample_candidates (test_all.TestDiagnose.test_sample_candidates) ... ok
test_windows_path_unverifiable_here_not_missing_claim (test_all.TestDiagnose.test_windows_path_unverifiable_here_not_missing_claim) ... ok
test_empty (test_all.TestReader.test_empty) ... ok
test_incomplete_header (test_all.TestReader.test_incomplete_header) ... ok
test_not_flp (test_all.TestReader.test_not_flp) ... ok
test_old_version_ansi (test_all.TestReader.test_old_version_ansi) ... ok
test_trailing_data (test_all.TestReader.test_trailing_data) ... ok
test_truncated (test_all.TestReader.test_truncated) ... ok
test_truncated_inside_event (test_all.TestReader.test_truncated_inside_event) ... ok
test_unknown_events_preserved_and_reported (test_all.TestReader.test_unknown_events_preserved_and_reported) ... ok
test_valid_roundtrip_exact (test_all.TestReader.test_valid_roundtrip_exact) ... ok
test_not_flp_refused (test_all.TestRepair.test_not_flp_refused) ... ok
test_remap_changes_only_sample_event (test_all.TestRepair.test_remap_changes_only_sample_event) ... ok
test_remap_wrong_old_path_refused (test_all.TestRepair.test_remap_wrong_old_path_refused) ... ok
test_trim_and_original_untouched (test_all.TestRepair.test_trim_and_original_untouched) ... ok
test_trim_refuses_when_not_truncated (test_all.TestRepair.test_trim_refuses_when_not_truncated) ... ok
test_unique_output_never_overwrites (test_all.TestRepair.test_unique_output_never_overwrites) ... ok
test_repair_report_mentions_pending_level_c (test_all.TestReports.test_repair_report_mentions_pending_level_c) ... ok
test_report_no_false_success (test_all.TestReports.test_report_no_false_success) ... ok
test_detects_loss (test_all.TestValidation.test_detects_loss) ... ok
test_never_declares_c_without_manual (test_all.TestValidation.test_never_declares_c_without_manual) ... ok

----------------------------------------------------------------------
Ran 27 tests in 0.017s

OK
```

## Qué NO se ha probado (importante)
- **Ningún proyecto FLP real de FL Studio.** Todas las pruebas usan archivos SINTÉTICOS generados por `tests/synthetic.py` (marcados con «SINTÉTICO» en el título). Pasar estas pruebas demuestra que el lector respeta la estructura FLhd/FLdt que implementa, no que lea cualquier FLP real.
- Ninguna versión de FL Studio (incluida la 26) está validada. El significado de los identificadores de evento es «inferido» de documentación comunitaria.
- La GUI solo se ha comprobado que compila (no hay tkinter ni pantalla en el entorno de desarrollo).
- No se ha compilado PyInstaller ni Inno Setup (entorno Linux sin red): **no existen** `CrayFLPAnalyzer-Setup.exe` ni `CrayFLPAnalyzer-Portable.zip`.
- Rutas con espacios y acentos: probadas en Linux (carpeta temporal «crayáñ test …»); falta probar en Windows.
- Apertura en FL Studio (nivel C): no comprobable aquí.
