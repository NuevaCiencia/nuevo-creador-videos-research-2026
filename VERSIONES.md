# VERSIONES — nuevo-creador-videos-research-2026

Historial de actualizaciones del proyecto. Cada versión corresponde a un bloque
de trabajo coherente sobre la app web (`app/`).

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
