# Registro de cambios
## 0.2.0 (alfa) — reescritura del prototipo 0.1.0
- Arquitectura modular en `src/cray_flp_analyzer` (lector FLP, diagnóstico, reparación, conversión/evaluación, rutas, plugins, validación, informes, configuración, GUI, CLI).
- Lector estructurado de FLhd/FLdt con tolerancia a truncados y reserialización exacta.
- Protección del original, reparación sobre copia, validación A/B, nivel C pendiente.
- Scripts de PyInstaller e Inno Setup (sin compilar en este entorno).
## 0.1.0 — prototipo de solo lectura (en `prototype_v0_1/`)
