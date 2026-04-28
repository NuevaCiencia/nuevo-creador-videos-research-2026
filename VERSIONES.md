# VERSIONES — nuevo-creador-videos-research-2026

Historial de actualizaciones del proyecto. Cada versión corresponde a un bloque
de trabajo coherente sobre la app web (`app/`).

---

## v0.8 — Fase Video + Fonts & Colors + Visualizador de Pantallas · `ed9134c`

### Fase Video (tab 🎬 Video)
- **Dummy builder inteligente** — genera videos placeholder para cada asset del guion consolidado
  (imágenes split/full, clips de video) antes del render final; permite probar el timing sin assets reales.
- **Render final FFmpeg** — pipeline completo: carga guion consolidado + audio de la DB,
  parsea `#META/#STYLES/#COVER/#SEGMENT`, genera subtítulos `.ass`, mezcla video con `filter_complex_script`,
  antepone portada y guarda en `renders/clase_{id}_final.mp4`.
- **ClassRender model** — nueva tabla `class_renders` que trackea `status/progress/phase/error/output_path`
  para dummy-build y render por separado; polling en tiempo real desde el frontend.
- **Endpoints nuevos**: `GET/POST /api/classes/{id}/render/build-dummies`, `GET /api/classes/{id}/render/status`,
  `POST /api/classes/{id}/render`, `GET /api/classes/{id}/render/download`.

### Fix — paths de audio portátiles entre máquinas
- Al subir audio se guarda `file_path` relativo a `app/` en lugar de absoluto.
- `_migrate_audio_paths()` en `database.py`: al arrancar convierte automáticamente rutas absolutas rancias
  que no existen en el sistema actual a rutas relativas.
- `_resolve_path()` en `render_agent.py`: fallback en runtime — si la ruta absoluta no existe, busca el
  segmento `assets/` o `renders/` en el path almacenado y reconstruye relativo a `app_dir`.

### Fix — FFmpeg en Windows con paths de ass con letra de unidad
- `ass=C:/path/sub.ass` falla en Windows: FFmpeg interpreta `:` como separador de opción.
- Solución: `filter_complex_script` usa `ass='C\:/path/sub.ass'` (escape con backslash + comillas).
- En `-vf` (argumento de subprocess, no en script): `ass=C\:/path/sub.ass` sin comillas externas.

### Feat — Fonts & Colors (tab 🎨)
- **Biblioteca de fuentes**: grid de tarjetas con preview tipográfico vivo; botón de upload para
  agregar `.ttf/.otf`; botón eliminar por fuente; fuentes bundled (Inter, Montserrat, JetBrainsMono)
  preinstaladas en `app/fonts/` y montadas como estáticas en `/fonts/`.
- **Color pickers**: fondos, texto principal, highlight — con sincronización hex + input de color nativo.
- **Live preview**: panel 16:9 con `container-type:size` y unidades `cqh/cqw`; refleja fuente y colores
  en tiempo real; autosave con debounce 800ms al curso activo.
- **fontsdir en FFmpeg**: `crear_video_mixto()` recibe `fonts_dir` y lo pasa al filtro `ass=` como
  `fontsdir=...` para que libass resuelva fuentes bundled sin instalación en el sistema.

### Feat — Visualizador de Pantallas (tab 🖥️ Pantallas)
- Lista de todas las pantallas de la clase con tarjeta de 3 columnas por pantalla.
- **Columna izquierda coloreada por tipo**: VIDEO=azul, TEXT=rosa/rojo, SPLIT_LEFT=verde,
  SPLIT_RIGHT=teal, LIST=ámbar, FULL_IMAGE=violeta, CONCEPT=lila, REMOTION=esmeralda.
  Implementado con CSS custom properties `--vt-bg/border/text` por clase `.vt-{tipo}`.
- Muestra número de pantalla, timestamp, duración, selector de tipo con cambio en tiempo real.
- **Botón ✎ Editar Contenido**: solo visible para LIST/CONCEPT/REMOTION; toggle abre/cierra el
  formulario de params inplace sin recargar la lista completa (`_vizEditingIdx` state).
- Formulario de params por tipo: LIST → campos título + 7 ítems; CONCEPT → nombre + definición;
  REMOTION → select de los 19 templates. Guardado automático al editar.
- **Preview canvas** por pantalla: renderizado fiel de cada tipo (split 50/50, full image,
  texto centrado, lista con ghost title, concepto, remotion con degradado).
- Cambiar tipo invalida `guion_base` y `guion_consolidado` en cascada.

### Fix — scroll en tab Pantallas
- `.viz-phase` ahora tiene `flex:1; overflow-y:auto` para ser su propio contenedor de scroll.
- `.viz-card` tiene `min-height:180px; flex-shrink:0` para no colapsarse.

### Fix — preview SPLIT descuadrado
- `.viz-preview-canvas` tiene `flex-direction:column` en CSS; SPLIT necesita `row`.
- Se añade `canvas.style.flexDirection = 'row'` para SPLIT y reset a `''` en el bloque de reset
  para que no contamine tipos subsiguientes.

---

## v0.7 — Robustez del pipeline + UX mejoras

### Distribución de pantallas (screen_agent)
- Añadida sección **DISTRIBUCIÓN ESPERADA** al prompt de segmentación: SPLIT/FULL como tipo dominante
  (60-70%), TEXT limitado al 15-20%, cuotas orientativas para VIDEO, REMOTION, LIST y CONCEPT.
- La distribución es orientativa y ajustable por proyecto en el futuro.

### Nombres de assets deterministas (visual_agent)
- Los nombres de archivo (`S001.png`, `F001.png`, `V001.mp4`…) ahora se pre-computan antes de llamar
  a GPT, en orden secuencial estricto por tipo. GPT ya no es responsable de generarlos.
- Eliminado el fallback `S_AUTO_<timestamp>.png` que causaba nombres duplicados cuando dos segmentos
  tenían el mismo timestamp de inicio.
- Prompt actualizado: GPT devuelve siempre `asset_filename=""` — el sistema lo ignora.

### Invalidación en cascada (main.py)
- Al regenerar pantallas (Fase Guion), `guion_base` y `guion_consolidado` pasan automáticamente
  a estado `stale`.
- La Fase Visuales queda bloqueada con aviso específico: *"Pantallas regeneradas — re-ejecuta la Alineación"*.
- Previene que Visuales corra silenciosamente con datos rancios.

### UI — botón Re-generar Visuales (app.js)
- Estado **done**: Re-generar aparece en fila propia como `btn-ghost`, separado de los exports.
- Estado **error**: el botón principal pasa a decir "↻ Re-generar" en lugar de "✨ Generar".

### Bug fix — timestamps duplicados (aligner_agent)
- `corregir_gaps` garantiza duración mínima de 100ms por segmento (`max(0.1, ...)`).
- Corrige el caso en que dos segmentos consecutivos con `inicio=0.0` generaban el mismo timestamp
  acumulado, produciendo nombres de archivo idénticos en el fallback visual.

### Panel de Configuración — modelos IA (index.html + style.css)
- Nueva sección de solo lectura en el settings panel: lista todos los modelos IA usados en el
  pipeline en orden de ejecución (claims, Tavily, segmentación, Whisper, spell, alineación,
  arquitectura visual, Remotion).

### Actualización de modelos
- `spell_agent`: `gpt-4.1-mini-2025-04-14` → `gpt-5.4-nano-2025-04-14`
- Referencias en UI actualizadas en consecuencia.

---

## v0.6 — FASE 3b: Orquestación Visual · `af9b8b4`

**Fase Visuales** implementada de extremo a extremo, replicando exactamente
`0_referencia/pipeline/visual_orchestrator.py`.

### Qué hace
- Lee los prompts directamente desde `0_referencia/ai_config.yaml` y los
  templates Remotion desde `0_referencia/ai_remotion_templates.yaml` en tiempo
  de ejecución — cualquier cambio en esos archivos se refleja automáticamente.
- Separa segmentos en `payload_visual` (VisualAssistant) y `payload_remotion`
  (RemotionAssistant).
- Rellena `TEXT=`, `TEXT_STYLE=`, `ASSET=`, `ASSET_TIPO=`, `ASSET_DESCRIPCION=`
  con el mismo prompt "Scientific American style" de `0_referencia`.
- Para segmentos REMOTION llama a RemotionAssistant con el catálogo de templates
  inyectado dinámicamente.
- Sanitiza prefijos de assets (`S`, `F`, `V`) con la misma lógica del original.
- Genera el header `#META` / `#STYLES` / `#COVER` desde la configuración del
  curso (equivalente a `video_config.yaml`).
- Produce `guion_consolidado.txt` y `recursos_visuales.json` idénticos al
  pipeline CLI de `0_referencia`.

### Archivos nuevos / modificados
- `app/ai_agents/visual_agent.py` — nuevo
- `app/models.py` — nuevo modelo `ClassGuionConsolidado`
- `app/main.py` — endpoints `POST/GET /api/classes/{id}/visual`
- `app/static/app.js` — fase Visuales reemplaza el placeholder
- `app/static/style.css` — estilos fase Visuales

### UI
- Gate de prerequisito (requiere alineación completada)
- Botón + barra de progreso con AIModal bloqueante
- Resumen de assets por tipo (split / full / video / remotion)
- Tabla de todos los assets con tipo, segmento y duración
- Exportar `guion_consolidado.txt`, `recursos_visuales.json`
- Modal "👁 Ver guion" con el contenido completo

---

## v0.5 — Configuración de Video por Curso · `7617dba`

Equivalente a `video_config.yaml` de `0_referencia`, ahora editable desde la
interfaz web.

### Campos añadidos al modelo `Course`
| Campo | Default | Uso |
|---|---|---|
| `fps` | 30 | Velocidad de frames del video final |
| `resolution` | 1920x1080 | Resolución de salida |
| `main_font` | Inter | Fuente principal |
| `background_color` | #fefefe | Color de fondo |
| `main_text_color` | #bd0505 | Color de texto principal |
| `highlight_text_color` | #e3943b | Color de texto highlight |
| `cover_asset` | videos/portada.mp4 | Asset de portada |

### Migración
Migración no-destructiva vía `ALTER TABLE` en `database.py`. No borra la DB.
Los cursos existentes reciben los valores por defecto automáticamente.

### UI
Modal "Editar Proyecto" ampliado con sección **⚙️ Configuración de Video**:
color pickers sincronizados con inputs hex, grid de 3 columnas.

---

## v0.4 — UI Audio: Corrección Ortográfica y Alineación · `5f1e4ed` / `3e5e6f7`

Fase Audio reorganizada con flujo completo de 5 cards secuenciales.

### Flujo Audio completo
1. 🎵 **Archivo de Audio** — upload + player HTML5
2. 🎙️ **Whisper** — selección de modelo + transcripción con progreso en tiempo real
3. 📄 **Transcripción** — resumen compacto (bloques / palabras / duración) +
   botones Copiar / .txt / .srt / 👁 Ver modal
4. ✏️ **Corrección Ortográfica** — `gpt-4.1-mini`, batches de 50 bloques,
   mismos prompts y validación de timestamps que `0_referencia`
5. 🔗 **Alineación y Guion Base** — `SegmentAligner` con difflib (sin IA),
   produce `guion_base.txt` en formato `#SEGMENT` exportable

### Fix CSS `3e5e6f7`
- Eliminado `overflow: hidden` en `.audio-card` que recortaba el contenido
- Reemplazado `height: 48px` fijo en card-head por `min-height` + flex-wrap
- Summary row rediseñado con celdas separadas por bordes verticales
- Añadido `padding-bottom: 40px` en `.audio-phase`

---

## v0.3 — Modal AI Bloqueante + Panel de Estadísticas · `6b2fde3`

### Modal AI (`AIModal`)
Modal global que bloquea toda la UI durante cualquier operación con IA o Tavily.
No se puede interactuar con nada hasta que termine.

**Componentes:**
- Spinner animado → ✅ al terminar → ❌ si hay error
- Log de mensajes en tiempo real (últimas 12 líneas, estilo consola)
- Barra de progreso con shimmer (solo cuando hay % real — Whisper, spell)
- Botón "Cerrar" habilitado solo en error; en éxito se cierra solo a 1.4s

**Operaciones cubiertas:** Tavily research, re-examen, segmentación de pantallas,
Whisper ATT, corrección ortográfica.

### Panel de Estadísticas (botón 📊 en topbar)
- **Vista general** — palabras totales, tiempo de locución (130 wpm), video
  estimado (+15%), secciones, clases, pantallas generadas
- **Pipeline** — barra de progreso por cada etapa con % y conteo X/N
- **Investigación** — breakdown verified/disputed/not_found/error
- **Tipos de pantalla** — barra proporcional por tipo con color/icono del catálogo
- **Detalle por sección** — tabla con palabras, minutos de locución y 5 puntos
  de color indicando etapa del pipeline por clase

---

## v0.2 — Lock del Guion + Modo Edición · `e96e078`

Protección contra edición accidental del guion tras guardarlo.

### Comportamiento
| Estado | Textarea | Botón | Visual |
|---|---|---|---|
| **Guardado** | `readonly` | `✏️ Editar guion` | Badge verde 🔒 |
| **Editando** | Editable | `Guardar Guion` | Banner ámbar informativo |

- Clases nuevas/vacías → editable directo
- Navegar entre clases → siempre bloquea si tiene contenido
- Guardar → bloquea y re-renderiza inmediatamente
- Dots pulsantes en tabs Investigación/Pantallas mientras se edita

---

## v0.1 — Pipeline de Producción Completo · `0b52970`

Implementación inicial de la app web con el pipeline completo adaptado de
`0_referencia`.

### Arquitectura
- **Backend**: FastAPI + SQLAlchemy + SQLite (`app/video_creator.db`)
- **Frontend**: SPA vanilla JS (sin frameworks)
- **Assets**: `app/assets/{class_id}/audio/` — excluidos del repo

### Pipeline implementado

#### Fase Guion
- Editor de locución con auto-save (2s debounce)
- **Verificación Tavily** — extrae claims con GPT, verifica con Tavily en dominios
  `.edu` / `.gov` / científicos, muestra verified/disputed/not_found con %
  de confianza y fuente
- **Re-examinar** — genera query alternativo con filtros de recencia 2023-2025
  para claims disputed/not_found
- **Segmentación de pantallas** — GPT divide el guion asignando el tipo de pantalla
  más adecuado pedagógicamente (`ScreenType` del catálogo global)
- **Export guion etiquetado** — formato `<!-- type:NAME // params -->` + copiar/txt

#### Fase Audio
- Upload de audio (MP3, WAV, M4A, AAC, OGG, FLAC) → guardado en `assets/`
- **Whisper** con `faster-whisper` (compatible Python 3.14, a diferencia de
  `whisperx`); modelos tiny/base/small/medium/large-v3; `reconstruir_bloques(1.0s)`
  idéntico a `0_referencia`; produce bloques `[start.xxx - end.xxx]: text` + SRT
- **Corrección ortográfica** — port exacto de `CorrectorOrtografia`: mismo modelo
  `gpt-4.1-mini-2025-04-14`, mismos prompts, validación de timestamps (3 retries),
  batches de 50 bloques
- **Alineación** — port exacto de `SegmentAligner` (difflib, sin IA) +
  `GuionFormatter`; produce `guion_base.txt` en formato `#SEGMENT`

#### Gestores Globales
- **Screen Types** — catálogo con 8 tipos (layout / dynamic / rendering), con
  color, icono, límites y formato de tag; seeded en DB al arrancar
- **Remotion Templates** — 19 templates en 4 categorías (narrativo / flujo /
  datos / clasificación); misma estructura que `ai_remotion_templates.yaml`

### Modelos DB
| Tabla | Descripción |
|---|---|
| `courses` | Proyectos (equivalente a `proyectos/NN/`) |
| `sections` | Secciones dentro de un curso |
| `classes` | Clases — unidad atómica de trabajo |
| `research_items` | Claims verificados con Tavily |
| `screen_segments` | Pantallas segmentadas por IA |
| `class_audio` | Audio + estado de transcripción Whisper |
| `class_spell_corrections` | Bloques corregidos ortográficamente |
| `class_guion_base` | Output del aligner (guion_base.txt) |
| `class_guion_consolidado` | Output del VisualOrchestrator |
| `screen_types` | Catálogo global de tipos de pantalla |
| `remotion_templates` | Catálogo global de templates Remotion |

---

## v0.0 — UI Base · `08d8ec7` / `587b3b8` / `d0280dc`

Layout tipo desktop app: sidebar + phase tabs + status bar.
Glassmorphism dark/light theme. CRUD de cursos, secciones y clases.
Gestor Maestro de Visuales (Screen Types + Remotion Templates).
