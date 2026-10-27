# Limitaciones conocidas (v0.2.0 alfa)
**Implementado y probado con datos sintéticos:** lectura estructural tolerante, detección de vacío/no-FLP/cabecera incompleta/truncado/bytes sobrantes/eventos desconocidos, diagnóstico con confianza, copia de trabajo + hash SHA-256, salida con nombre nuevo, registro de operaciones (JSONL), recorte de cola truncada, reemplazo confirmado de rutas de sample, comparación antes/después por eventos y datos, validación niveles A y B, informes JSON/Markdown, CLI.

**Parcial / sin probar en el entorno:** GUI tkinter (compila; falta prueba manual en Windows), arrastrar y soltar (requiere `tkinterdnd2` opcional), detección de FL Studio instalado (por nombre de carpeta, inferido), apertura manual en FL Studio.

**No implementado:** conversión real entre versiones; interpretación semántica de notas, playlist, automatizaciones, mixer y estado de plugins; validación automática en FL Studio (nivel C) o de audio; instalador y portable compilados; icono/logo.

**Otras:** el mapeo de ids de evento es inferido y puede ser incorrecto para algunas versiones; versiones de FL no validadas con proyectos reales: todas, incluida la 26.
