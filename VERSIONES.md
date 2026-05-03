# VERSIONES — nuevo-creador-videos-research-2026

Historial de actualizaciones del proyecto. Cada versión corresponde a un bloque
de trabajo coherente sobre la app web (`app/`).

---

## v1.14 — UX: Consistencia y Sincronización de la Fase Visual · `(pending)`

### Feat — Rediseño de "CARGA RECURSOS" (Pestaña Visuales)
- **Sincronización Total**: El botón **↺ Recargar** ahora fuerza una sincronización real con la base de datos de Pantallas. Si cambias la estructura en el editor, la pestaña de recursos se actualiza al instante para reflejar el nuevo número de elementos.
- **Numeración Correlativa por Tipo**: Implementado sistema de nombres determinista y ordenado:
  - **S001, S002...** para Imágenes (Split/Full).
  - **V001, V002...** para Videos.
  - **REM001, REM002...** para Remotion (unificado a 3 dígitos).
  - Se eliminan los "saltos" de numeración; cada categoría empieza en 001 independientemente de su posición en el guion.
- **Filtrado Inteligente**: Las pantallas de tipo `TEXT`, `CONCEPT` y `LIST` ya no aparecen en la lista de recursos, ya que se generan automáticamente y no requieren assets externos. Esto limpia la interfaz y evita confusiones con archivos innecesarios (ej. `T001.png`).
- **Consistencia del Sistema**: La nueva nomenclatura se ha "reafirmado" en todo el pipeline: desde la generación del Agente Visual hasta el motor de renderizado de video.

### UX — Acceso Premium a Archivos Locales
- **Botón 📂 Abrir**: Cada tarjeta de recurso cuenta ahora con un botón explícito para abrir el archivo local directamente en el sistema operativo (Mac/Windows).
- **Doble Click**: Soporte para abrir archivos mediante doble click en la miniatura de la tarjeta, agilizando la revisión de assets.
- **Robustez**: Mejorado el manejo de rutas para evitar bloqueos de la UI cuando faltan rutas en la base de datos.

### Fix — Sincronización de Contadores
- Corregida la discrepancia entre las pestañas "Visuales" y "Carga Recursos". Ahora ambas muestran el mismo conteo total (Pantallas + Portada) y el desglose de assets es idéntico.

---

## v1.13 — Feat: duración y sistema en render completado · `a71bac5`

### Feat — Estadísticas de Pantallas (Guion)
- Añadido un botón de estadísticas (📊) en el panel de Pantallas de la pestaña Guion.
- Muestra un modal elegante con el conteo total de pantallas y un desglose ordenado por tipo de pantalla, incluyendo porcentajes y barras de progreso visuales para verificar el equilibrio del guion.

### Feat — Prompts Consolidados y Carga de Lote Unidos (Split 16:9)
- **Prompts Consolidados**: Añadido botón en "Img Prompts" que agrupa programáticamente las pantallas divididas (`S`) en pares. Genera un prompt maestro unificado con formato de lienzo 16:9 para Midjourney/DALL-E. Si hay pantallas impares, replica el prompt para obtener dos variaciones en la misma imagen.
- **Carga Lote Unidos**: Nuevo botón en "Carga Recursos" que recibe imágenes dobles (ej. `S001_S002_midjourney.png`), extrae las etiquetas del nombre, y corta la imagen por la mitad en el backend mediante Pillow.
- Cada mitad cortada pasa automáticamente por el flujo `_procesar_imagen_asset`, reescalando o añadiendo letterbox para asegurar que encaje perfectamente en la resolución 1920x1080 del video.

### Feat — Edición "en caliente" de Texto en Pantalla
- Añadido soporte para editar el valor `TEXT=` (Texto en Pantalla) desde la pestaña Pantallas para todos los tipos de pantalla.
- La edición guarda directamente en el archivo `guion_consolidado.txt` mediante el nuevo endpoint `PUT /api/segments/{segment_id}/text` sin invalidar el pipeline (el estado de la fase Visual no cambia a `stale`).
- Esto permite hacer correcciones finales de ortografía o ajustes en los textos de los overlays justo antes de renderizar, tal como se hacía en `0_referencia`.

### Fix — Cortes abruptos en transiciones de video
- Añadido el filtro `tpad=stop=-1:stop_mode=clone` antes del `trim` en `ffmpeg_builder.py` para asegurar que los videos (como CONCEPT, LIST o los renderizados por Remotion) siempre tengan fotogramas suficientes para que el filtro `fade` pueda completar su transición hasta el 0% de opacidad sin congelarse ni cortarse abruptamente debido a diferencias de milisegundos en la duración.

### Feat — Tiempo de render y sistema mostrados al terminar
- Al completar el render se guardan `duration_s` (segundos de wall-clock) y
  `system_info` ("macOS (Apple M2 Pro)") en la tabla `class_renders`.
- El card de Render Final muestra duración formateada (ej. "2m 34s") como stat
  junto al número de assets, y el sistema justo debajo.
- `_get_system_info()` en `render_agent.py`: detecta OS + CPU vía `sysctl` en Mac,
  `wmic` en Windows, `/proc/cpuinfo` en Linux.
- Migración no-destructiva en `database.py` para las dos columnas nuevas.

---

## v1.12 — UX: Estructura bloqueada cuando el pipeline ya avanzó · `(pending)`

### Feat — Bloqueo automático de la pestaña Estructura
- Una vez que se ejecuta la Alineación (`guion_base` en estado `done`), la pestaña
  Estructura pasa a modo solo lectura automáticamente.
- Banner ámbar con texto "🔒 Estructura bloqueada — el pipeline ya avanzó".
- Todos los controles (drag-drop, selects de tipo, botones + y ×) quedan deshabilitados.
- Botón "⚠ Editar arquitectura" muestra diálogo de confirmación; al confirmar,
  desbloquea la sesión actual sin recargar (`_estUnlocked = true`).
- Al guardar tras desbloquear, el PUT envía `force: true` y el backend procede
  marcando `guion_base` y `guion_consolidado` como stale en cascada.
- Backend: `GET /estructura` incluye campo `locked`; `PUT /estructura` devuelve
  HTTP 423 si el pipeline avanzó y no se envía `force: true`.

---

## v1.11 — Fix: transiciones en VIDEO/CONCEPT/LIST (overlay alpha) · `(pending)`

### Fix — Transiciones no visibles en clips de video/CONCEPT/LIST
- El filtro `overlay` de FFmpeg usa `format=yuv420` por defecto, que descarta el canal
  alpha antes de componer. El `fade=alpha=1` producía transparencia en RGBA pero
  el overlay la ignoraba → todos los clips aparecían/desaparecían con corte abrupto.
- Fix: añadido `:format=auto` en todos los `overlay` de `ffmpeg_builder.py`.
  FFmpeg negocia automáticamente YUVA420P/RGBA y respeta el alpha del fade.
- Aplica a todos los tipos (img y video); el encoder libx264 recibe yuv420p
  automáticamente vía conversión de formato que FFmpeg inserta al final de la cadena.

---

## v1.10 — Fix: paths multiplataforma Windows → Mac en render · `79a6448`

### Fix — FileNotFoundError al renderizar en Mac con paths guardados desde Windows
- `_resolve_path` en `render_agent.py` ahora normaliza backslashes (`\` → `/`) antes
  de procesar el path, evitando que rutas como `assets\2\audio\original.mp3`
  se traten como un único nombre de archivo en macOS/Linux.
- Causa: `os.path.relpath()` en Windows genera separadores `\` que se almacenan en DB;
  al leer en Mac, `pathlib.Path` no los interpreta como separadores de directorio.

---

## v1.9 — Debug dynamic_animator: error visible en UI + pantallas huérfanas ocultas · `09ab7a9`

### Fix — Pantallas fantasma en tab Pantallas
- El visualizador ahora muestra `min(ScreenSegments, guion_consolidado)` — los segmentos
  huérfanos que quedan en DB tras fusionar pantallas en Estructura ya no aparecen.

### Debug — Error dynamic_animator visible en UI
- Si `dynamic_animator` falla, el error completo (con traceback) ahora se propaga
  y aparece en rojo en la UI del render. Antes fallaba silenciosamente.

---

## v1.8 — Botón 🤖 Rellenar con IA en tab Pantallas (CONCEPT y LIST) · `44d17d5`

### Feat — AI fill para CONCEPT y LIST
- Botón **🤖 Rellenar con IA** junto a "✎ Editar Contenido" solo para tipos CONCEPT y LIST.
- Endpoint `POST /api/segments/{id}/ai-fill` — guarda en DB y marca guiones como stale.

---

## v1.7 — Dynamic Animator (CONCEPT/LIST animados) + Transiciones en config · `538a00a`

### Feat — `dynamic_animator.py`
- CONCEPT: término aparece con fade-in sincronizado al audio; definición aparece escalonada.
- LIST: fondo verde pizarrón, bullets aparecen en sincronía; ghost title con opacidad baja.
- Fuentes desde `app/fonts/` (Montserrat-Bold/Regular) — no depende del SO.

### Feat — Transiciones en Configuración de Proyecto
- Campos `use_transitions` y `transition_duration` en `Course`.
- Modal "Editar Proyecto": nueva sección 🎬 Transiciones.

---

## Historial comprimido (v0.0 – v1.6)

| Versión | Hash | Resumen |
|---|---|---|
| v1.6 | `61da1df` | Fix FFmpeg: backslashes en fontsdir/ass path en Windows |
| v1.5 | `f967000` | Modal Meta-Prompt: botones Copy + scroll + cierre fijo + botón P&Loc |
| v1.4 | `373cbec` | Meta-prompt migrado a DB (tabla `meta_prompts`) |
| v1.3 | `39ab2cb` | Img Prompts: textarea más grande, Copy por fila, Configurar IA |
| v1.2 | `85ed7f9` | Carga Recursos: grid de cards, carga en lote, validaciones |
| v1.1 | — | Pestaña Carga Recursos + procesado automático fit/fill de imágenes |
| v1.0 | `76cfd14` | Estructura DnD + Img Prompts + Fixes de assets por clase + backup DB |
| v0.9 | `bfce334` | Integración Remotion + Dummies en assets/ + Reorden de tabs |
| v0.8.1 | `96b617f` | Visualizador de Pantallas: tipos dinámicos desde DB + fixes scroll |
| v0.8 | `ed9134c` | Fase Video + Fonts & Colors + Visualizador de Pantallas |
| v0.7 | — | Robustez pipeline: distribución pantallas, assets deterministas, cascade invalidation |
| v0.6 | `af9b8b4` | Fase Visuales completa (visual_agent + guion_consolidado) |
| v0.5 | `7617dba` | Configuración de video por curso (fps, resolución, fuente, colores) |
| v0.4 | `5f1e4ed` | Fase Audio: Whisper + corrección ortográfica + alineación |
| v0.3 | `6b2fde3` | Modal AI bloqueante + Panel de estadísticas |
| v0.2 | `e96e078` | Lock del guion + modo edición |
| v0.1 | `0b52970` | Pipeline completo inicial (Guion + Audio + Gestores globales) |
| v0.0 | `08d8ec7` | UI base: sidebar, tabs, glassmorphism, CRUD cursos/secciones/clases |
