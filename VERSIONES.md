# VERSIONES — nuevo-creador-videos-research-2026

Historial de actualizaciones del proyecto. Cada versión corresponde a un bloque
de trabajo coherente sobre la app web (`app/`).

---

## v1.2 — Carga Recursos: grid de cards + lote + validaciones · `85ed7f9`

### Feat — Grid de cards con preview en Carga Recursos
- Reemplaza la tabla por un grid de tarjetas `auto-fill minmax(160px)`.
- Cada card muestra el preview real de la imagen/video si existe en disco;
  placeholder con ícono del tipo si falta.
- Badge ✓/✗ en la esquina superior derecha de cada card.
- Overlay `⚙️ Formateando…` (animación pulsante) sobre el preview durante el upload.
- Botón **📂 Subir** en el footer de cada card, se pone azul al hover.

### Feat — Carga en lote
- Botón **📦 Carga en lote** en el toolbar: abre selector de múltiples archivos.
- Matching por prefijo: `S003_foto.png` → slot `S003.png`; archivos sin coincidencia se omiten.
- Modal de confirmación con tabla de reconocidos (verde) / no reconocidos (rojo atenuado).
- Progreso via AIModal con mensaje por archivo; distingue "formateando" (imágenes) de "subiendo" (videos).

### Fix — Validación de prefijo en upload individual
- Al subir un archivo en un slot específico, se valida que el nombre del archivo
  empiece con el stem esperado (ej. subir `S004.png` en slot `S003.png` → error con mensaje claro).

### Fix — Visuales: portada en estadísticas y tabla de assets
- Stat row: añade columna **portada** (siempre 1); total calculado como
  `1 + splits + fulls + videos + remotion` en lugar de `total_recursos` del JSON
  (que podía no coincidir con los conteos individuales).
- Tabla Assets Identificados: fila de portada al inicio con badge ámbar y nombre real del archivo.

---

## v1.1 — Pestaña Carga Recursos + procesado automático de imágenes

### Feat — Pestaña 📁 Carga Recursos
- Nueva pestaña entre Img Prompts y Fonts & Colors.
- Tabla con todos los assets esperados de la clase (nombre, tipo, ruta destino, ✓/✗ si existe en disco).
- Barra de progreso superior mostrando cuántos assets están presentes.
- Por fila: botón **📂 Elegir** que abre selector de archivo filtrado por tipo (imágenes o `.mp4`).
- Botón **↺ Recargar** para refrescar el estado desde disco.

### Feat — Procesado automático de imágenes al subir (fit-vs-fill)
- Al subir una imagen, el backend la redimensiona al canvas correcto según el nombre del asset:
  - `S*.png` (SPLIT_LEFT / SPLIT_RIGHT) → **960 × 1080 px**
  - `F*.png` (FULL_IMAGE) → **1920 × 1080 px**
- Lógica **fit-vs-fill** (portada de `0_referencia4_imagenesedit`):
  - Si >90% de los píxeles de borde tienen RGB > 235 → **fit** (letterbox blanco, sin recorte)
  - Si no → **fill** (escala hasta cubrir el canvas, recorta el centro)
- Siempre guarda como `.png` optimizado.
- El frontend muestra `⚙️ Formateando imagen, espere…` (animación pulsante) mientras procesa.
- El toast de confirmación indica el modo aplicado: `subido ✓ — fit (letterbox)` o `fill (recorte)`.
- Videos (`.mp4`) se suben sin procesado.
- `Pillow>=10.0.0` añadido a `requirements.txt`.

---

## v1.0 — Estructura DnD + Img Prompts + Fixes de assets por clase · `76cfd14`

### Feat — Pestaña 🖼️ Img Prompts
- Nueva pestaña entre Visuales y Fonts & Colors con tabla de todos los assets de imagen
  (SPLIT_LEFT, SPLIT_RIGHT, FULL_IMAGE) de la clase.
- Muestra prompt activo (original o editado por IA/usuario), narración colapsable y estado.
- Botón **🤖 Fix** por fila y **Fix All** para mejorar todos los prompts de un tirón.
- Usa `META_PROMPT_ARREGLA_IMAGENES.txt` de `0_referencia` (estructura Scientific American).
- Si no hay prompt original, genera un seed desde la narración antes de refinar.
- Nueva tabla `class_img_prompts`: persiste prompts editados por usuario o IA.
- `visual_agent.py`: ahora guarda `descripcion` en `recursos_json` (antes se descartaba).
- Endpoints: `GET/PUT/DELETE /img-prompts/{asset}` y `POST /img-prompts/{asset}/fix`.

### Feat — Pestaña 🗂️ Estructura (editor drag-and-drop de pantallas)
- Nueva pestaña entre Guion y Audio con editor visual de distribución de pantallas.
- Tags de pantalla arrastrables entre párrafos del guion con drop zones siempre visibles.
- Botón **+** entre párrafos para agregar tags; **×** para eliminar.
- Selector de tipo por tag con colores directamente desde la DB (hex+alpha inline, sin `color-mix()`).
- `PUT /api/classes/{id}/estructura`: reconstruye `screen_segments` desde las nuevas posiciones.
- Guarda y cascade-invalida `guion_base` y `guion_consolidado`.
- Botón Guardar con animación pulse cuando hay cambios pendientes.

### Feat — Confirmación con clave para borrar curso o clase
- `openConfirm` acepta `requirePin:true` — muestra input de clave (1234) antes de confirmar.
- Si la clave es incorrecta: shake + borde rojo + campo vacío.
- `deleteCourse` y `deleteClass` usan `requirePin:true`; Enter en el campo activa el botón.

### Feat — Backup automático de DB al arrancar el server
- `_backup_db()`: copia `video_creator.db` → `video_creator.db.bak` en cada startup.
- Siempre sobreescribe — hay un snapshot del estado al arranque previo.
- `.gitignore` actualizado: agrega `*.db.bak`.

### Fix — Assets per-class: rutas `app/assets/{class_id}/images|videos/`
- `assets_base` en `dummy_builder`, `render_agent` y endpoints de viz ahora apunta a
  `app/assets/{class_id}/` — evita colisión de `S001.png` entre clases distintas.
- `remotion_agent.py`: renderiza en `app/assets/{class_id}/videos/` en vez de directorio global.

### Fix — Cascade invalidation completa
- `PUT /api/classes/{id}`: cambiar `raw_narration` marca `guion_base` y `guion_consolidado` como stale.
- `PUT /api/courses/{id}`: cambiar font/colores/fps/resolución marca `guion_consolidado` de todas
  las clases del curso como stale (los valores se embeben en `#META`).

### Fix — UI de Estructura y Pantallas
- Rewrite de la UI de Estructura: orden correcto slot-separator → tag → párrafo.
- Scrollbar más ancho (10px con hover) en tabs Pantallas y Estructura.

---

## v0.9 — Integración Remotion + Dummies en assets/ + Reorden de tabs · `bfce334`

### Feat — Integración Remotion completa
- **Proyecto `remotion/`** en la raíz del repo: Node.js con 4 templates reales
  (TypeWriter, MindMap, LinearSteps, FlipCards) registrados en `src/index.tsx`.
- **`remotion_agent.py`**: encuentra `npx` vía PATH o nvm automáticamente, instala
  `node_modules` si faltan, renderiza cada `REM*.mp4` con `npx remotion render` y
  actualiza progreso en DB. Siempre sobreescribe (reemplaza dummies).
- **`ClassRemotionRender`**: nueva tabla en DB con `status/progress/phase/error`.
- **Endpoints**: `POST /api/classes/{id}/render/remotion` y `GET .../remotion/status`.
- **Card Remotion en tab Visuales**: aparece solo si hay assets remotion; botón
  "Renderizar N assets Remotion", barra de progreso con poll cada 3s, manejo de errores.
- **`tsconfig.json`** añadido al proyecto Remotion (requerido por Remotion CLI).

### Fix — Schema correcto para TypeWriter
- `data_schema` en DB actualizado: `delay` documentado como entero acumulativo,
  `prefix` con espacio final obligatorio y opciones exactas.
- Prompt de `visual_agent.py` reforzado con reglas explícitas de tipos y fórmula
  de cálculo de delays acumulativos para TypeWriter.

### Fix — Dummies en `app/assets/` (ruta correcta)
- `assets_base` en los endpoints de dummies y check-status cambiado de `app/` a
  `ASSETS_DIR` (`app/assets/`) — alineado con la ruta que sirve el servidor estático.
- `render_agent.py`: `FILES_FOLDER` actualizado a `app/assets/` para consistencia.
- `dummy_builder.py`: infiere tipo por nombre del archivo (S*/F* → imagen, V*/REM* → video)
  en lugar de depender del campo `tipo`, eliminando skips silenciosos en assets sin tipo.

### Feat — Card Assets/Dummies en tab Visuales
- Nuevo card "🏗 Assets / Dummies" en la pestaña Visuales (cuando arquitectura visual completa):
  muestra tabla de assets con ✓/✗, botón "Construir dummies" si hay faltantes,
  barra de progreso con poll independiente, mensaje orientativo si todos presentes.

### Feat — Reorden de pestañas
- Tab Visuales movida a después de Audio (nuevo orden: Guion → Audio → Visuales →
  Fonts & Colors → Pantallas → Video) para reflejar el flujo lógico de producción.

---

## v0.8.1 — Visualizador de Pantallas: conexión con catálogo + fixes · `96b617f`

### Tipos de pantalla dinámicos desde la DB
- El select de tipo en la tab Pantallas ahora carga los tipos del catálogo global (`screen_types`)
  en lugar de un array hardcodeado. Incluye ícono, label y color de cada tipo.
- El botón ✎ Editar Contenido usa el flag `has_params` de la DB.
- El color de la columna izquierda viene del campo `color` del catálogo — cambiarlo en el
  Gestor Global se refleja automáticamente en la tab Pantallas.
- El endpoint `/api/classes/{id}/visualizador` ahora incluye `screen_types` en la respuesta.
- Eliminadas las clases CSS `.vt-*` hardcodeadas; los colores se inyectan via `style` inline
  usando CSS custom properties (`--vt-text`, `--vt-border`).

### Fix — scroll al abrir/cerrar editor de params
- `vizToggleEdit` y `vizUpdateType` guardaban y restauraban el `scrollTop` del `.viz-phase`
  antes/después de reconstruir el HTML, evitando el salto al inicio de la lista.

### Fix — templates REMOTION reducidos a los 4 reales
- `REMOTION_TEMPLATES_SEED` corregido: de 19 a 4 (TypeWriter, MindMap, LinearSteps, FlipCards).
  Los otros 15 eran aspiracionales sin implementación en `0_referencia`.
- `_seed_remotion_templates()` ahora sincroniza: elimina de la DB los templates no válidos
  y agrega los faltantes en cada arranque del servidor.
- Select en `_vizParamsForm` actualizado con los 4 templates reales.

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
