# Análisis técnico de DAW Converter para CrayFLPAnalyzer
Fecha: 2026-10-27

## Alcance
Este documento registra lo que anuncia públicamente DAW Converter. No implica que hayamos probado su conversión ni que sus resultados sean correctos para todos los proyectos.

Referencias públicas consultadas:
- https://www.dawconverter.com/tools/flp
- https://www.dawconverter.com/tools/flp/downgrade
- https://www.dawconverter.com/alternatives/fl-studio-downgrade

## Funciones anunciadas
La página del visor anuncia detección de versión, BPM, compás, número de canales/patrones, lista de plugins, rutas de samples, exportación MIDI y downgrade. Las funciones Pro pueden requerir pago/créditos.

La página anuncia rutas modernas como FL Studio 26 → 25/24/21, FL Studio 25 → 24/21 y FL Studio 24 → 21; también describe destinos antiguos como 20/12/11/9/8/7. Estas son afirmaciones del proveedor y no están verificadas independientemente por este repositorio.

## Método que el proveedor describe
El proveedor afirma que:
1. Lee la cabecera FLhd y los eventos del bloque FLdt.
2. Reescribe los metadatos de versión.
3. Mapea algunos eventos o registros de versiones nuevas a formatos anteriores.
4. Elimina o convierte características que el destino no soporta.

Esto es más que cambiar únicamente un byte de versión. Sin embargo, la web no publica el código fuente ni una tabla completa y verificable de las transformaciones por versión; no debemos asumir que conocemos sus mapeos internos.

## Riesgos y límites anunciados
El proveedor indica que algunas funciones nuevas, plugins nativos, automatizaciones avanzadas y estados/rutas complejas del mezclador pueden perderse. La compatibilidad de plugins depende de que existan también en la versión de destino. La presencia de un archivo convertido no demuestra que FL Studio lo abra ni que el proyecto conserve su comportamiento musical.

## Decisiones para CrayFLPAnalyzer
- No copiar código propietario ni intentar reproducir transformaciones no documentadas como si estuvieran verificadas.
- No hacer un parche ciego del byte de versión ni eliminar eventos desconocidos indiscriminadamente.
- Preservar los bytes/eventos desconocidos cuando sea posible y emitir un informe explícito de incertidumbre.
- Mantener el original intacto y escribir siempre una copia de salida.
- Implementar cada conversión de versión como una transformación identificada, versionada y respaldada por fixtures reales con permiso para probarlos.
- Validar tres niveles: lectura/escritura sin cambios; comparación estructural antes/después; apertura manual en la versión de FL Studio objetivo.
- No etiquetar una conversión como «correcta» hasta que la prueba en la versión de destino se haya completado.

## Prueba de referencia pendiente
Para comparar de forma responsable, hacen falta:
1. Un proyecto sencillo creado y guardado en FL Studio 26.
2. Una copia del mismo proyecto convertida por DAW Converter a una versión objetivo compatible.
3. El archivo original y el convertido, ambos compartidos por el propietario y sin contenido privado que no quiera revelar.
4. La versión exacta de FL Studio de destino para la prueba de apertura.

Con esos archivos podremos comparar cabecera, eventos, patrones/notas, Playlist, automatización, canales y mezclador. Si no se dispone de una instalación de la versión de destino, solo se podrá informar de diferencias estructurales; no se podrá certificar la apertura real.
