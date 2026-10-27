# Cray FLP Analyzer — v0.1.0

Aplicación inicial para Windows que analiza archivos `.flp` en modo de solo lectura.

## Qué hace esta versión
- Selecciona un proyecto FLP.
- Comprueba la firma inicial del archivo y algunos campos básicos del encabezado.
- Extrae cadenas legibles como pistas de posibles rutas, samples, presets o nombres de plugins.
- Muestra advertencias y permite guardar un informe JSON.
- Calcula SHA-256 para identificar exactamente el archivo analizado.
- No modifica ni sobrescribe el proyecto original.
- No necesita conexión a Internet para analizar archivos.

## Limitaciones importantes
Esta versión es un prototipo de diagnóstico, no un conversor ni un reparador. El formato FLP es binario y ha cambiado con el tiempo. La búsqueda de cadenas es heurística: puede omitir rutas y plugins, y puede encontrar fragmentos que no representen datos reales. No deduce de forma fiable la versión comercial exacta de FL Studio.

## Cómo probarlo
1. Instala Python 3.11 o posterior desde python.org (marca “Add Python to PATH” durante la instalación).
2. Descomprime esta carpeta.
3. Ejecuta `Cray_FLP_Analyzer.pyw` con doble clic, o ejecuta:
   `python Cray_FLP_Analyzer.pyw`
4. Selecciona una copia de un proyecto `.flp` y pulsa **Analizar**.
5. Guarda el informe JSON si quieres compartir el diagnóstico.

## Cómo generar el EXE en Windows
Abre CMD en esta carpeta y ejecuta:

```bat
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name CrayFLPAnalyzer Cray_FLP_Analyzer.pyw
```

El ejecutable quedará en `dist\CrayFLPAnalyzer.exe`.

PyInstaller debe ejecutarse en Windows para generar un EXE de Windows. El código de la aplicación no requiere paquetes externos.

## Plan de desarrollo realista
### Fase 1 — Analizador seguro (esta versión)
- Lectura de solo lectura, firma, tamaño, hash, pistas de texto e informe.
- Pruebas con proyectos de diferentes versiones y archivos dañados.

### Fase 2 — Parser semántico
- Integrar un parser mantenido y revisar su licencia antes de distribuirlo.
- Extraer tempo, PPQ, canales, patrones, clips, automatizaciones, mixer y plugins donde estén soportados.
- Diferenciar “detectado”, “inferido” y “desconocido”.

### Fase 3 — Diagnóstico de compatibilidad
- Inventario de plugins y rutas de samples.
- Verificación de archivos referenciados en el disco local.
- Informe de posibles plugins ausentes, sin afirmar que se pueden sustituir automáticamente.

### Fase 4 — Reparación sobre copia
- Crear una copia de seguridad verificable.
- Corregir solo rutas u objetos cuyo formato esté confirmado.
- Guardar como archivo nuevo y registrar cada cambio.
- Nunca sobrescribir el original.

### Fase 5 — Conversión experimental y validación
- Crear adaptadores específicos por versión/formato cuando haya evidencia suficiente.
- Validar con proyectos de prueba y abrir los resultados en FL Studio.
- No prometer equivalencia sonora si faltan plugins, presets o samples.

## Seguridad de los proyectos
Los proyectos pueden contener música inédita. Esta app procesa los datos localmente y no los transmite. No uses proyectos únicos como primera prueba: trabaja con copias.
