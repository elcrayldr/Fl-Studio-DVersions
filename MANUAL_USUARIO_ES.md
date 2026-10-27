# Manual de usuario — Cray FLP Analyzer 0.2.0 (alfa)
1. **Seleccionar:** pulsa «Seleccionar…» (o arrastra archivos si `tkinterdnd2` está instalado). Admite varios .flp.
2. **Analizar:** solo lectura. La tabla muestra el diagnóstico principal y su confianza; en «Incidencias» ves cada hallazgo (Confirmado / Inferido / Hipótesis).
3. **Interpretar:** *Confirmado* = comprobado en la estructura. *Inferido* = deducido del significado habitual de un identificador. *Hipótesis* = posible causa sin evidencia (p. ej. un plugin listado). Un diagnóstico «sin problemas» **no garantiza** que FL Studio abra el proyecto.
4. **Reparar copia:** el programa propone solo acciones con base estructural (recortar cola truncada; sustituir una ruta de sample que tú confirmes). Genera un archivo nuevo `…_cray_reparado.flp`; el original no se toca (se verifica con SHA-256).
5. **Comparar / antes y después:** pestaña «Antes / después» con pérdidas y cambios previstos.
6. **Convertir:** evalúa si hace falta. En esta versión no hay conversión entre versiones; verás el motivo y no se crea ningún archivo.
7. **Abrir en FL Studio:** lanza FL Studio con el resultado. La validación nivel C queda **PENDIENTE** hasta que compruebes tú la apertura y el sonido.
8. **Informes:** se guardan junto a la copia reparada (JSON y Markdown); también con «Guardar informe…». Registros: botón «Registros» (carpeta `%APPDATA%\CrayFLPAnalyzer\logs`).
Línea de comandos: `python run_app.py analyze archivo.flp`, `repair archivo.flp --out carpeta --trim-tail`, `compare a.flp b.flp`.
