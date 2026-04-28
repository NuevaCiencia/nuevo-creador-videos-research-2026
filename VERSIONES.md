# VERSIONES — nuevo-creador-videos-research-2026

Historial de actualizaciones del proyecto. Cada versión corresponde a un bloque
de trabajo coherente sobre la app web (`app/`).

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
