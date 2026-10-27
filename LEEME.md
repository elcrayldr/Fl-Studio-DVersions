# Cray FLP Analyzer 0.2.0 (alfa) — Cray LDR / La Zeta Music
Analiza y repara copias de proyectos .flp de forma conservadora. **No** es compatible universal ni está validado con proyectos reales de FL Studio.

## Estado honesto
Ver `docs/LIMITACIONES.md` y `docs/INFORME_PRUEBAS.md`. No incluye `.exe`: debes compilarlo en Windows.

## Ejecutar desde el código (Python 3.11+ con tkinter)
`python run_app.py` (GUI) · `python run_app.py analyze samples\synthetic\synthetic_truncado.flp`

## Pruebas
`set PYTHONPATH=src` y `python -m unittest discover -s tests` (Linux: `PYTHONPATH=src python3 -m unittest discover -s tests`)

## Compilar en Windows 10/11 x64
1. Instala Python 3.11+ (con «Add to PATH») e Inno Setup 6.
2. Ejecuta `build_windows.bat`. Genera `release\CrayFLPAnalyzer-Portable.zip` y, si Inno Setup está instalado, `release\CrayFLPAnalyzer-Setup.exe`.
3. Prueba manual recomendada: iniciar desde el menú Inicio, ruta con espacios/acentos, desinstalar y comprobar que tus proyectos siguen ahí.

## Datos de ejemplo
`samples/synthetic/` contiene archivos SINTÉTICOS (no son proyectos reales de FL Studio).
