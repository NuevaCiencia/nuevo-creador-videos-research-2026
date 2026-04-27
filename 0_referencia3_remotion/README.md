# Remotion Animation Pipeline

Pipeline de producción de videos educativos animados con **Remotion** (React + TypeScript).  
39 templates tipo SmartArt/infografía listos para usar. Se alimentan con un YAML simple y escupen un MP4.

---

## Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| Node.js | 18+ |
| Python | 3.9+ |
| FFmpeg | cualquiera reciente |
| Git | cualquiera |

---

## Instalación

### 1. Clonar

```bash
git clone https://github.com/NuevaCiencia/remotion.git
cd remotion
```

### 2. Dependencias Node (Remotion)

```bash
cd pipeline/remotion
npm install
```

### 3. Entorno virtual Python

```bash
cd pipeline
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## Generar un video

### Paso 1 — Escribir el guion en YAML

Crea un archivo en `pipeline/inputs/mi_video.yaml`:

```yaml
fps: 30   # opcional, default 30

scenes:
  - id: portada
    template: COVER-MainCover
    duration: 7              # segundos exactos de esta escena
    props:
      tag: "Clase 01"
      title: "Agentes de IA"
      subtitle: "Qué son y cómo funcionan"

  - id: definicion
    template: DEF-Central
    duration: 8
    props:
      term: "Agente inteligente"
      definition: "Sistema que percibe su entorno y actúa sobre él de forma autónoma."

  - id: cierre
    template: CLOSE-Keywords
    duration: 5
    props:
      words: ["Autonomía", "Percepción", "Acción"]
      subtitle: "Lo que aprendiste hoy"
```

La duración total del video es la **suma de todos los `duration`**.

### Paso 2 — Renderizar

```bash
cd pipeline
source venv/bin/activate   # Windows: venv\Scripts\activate

python render.py inputs/mi_video.yaml
```

### Paso 3 — Recoger el MP4

```
pipeline/output/video_final.mp4
```

---

## Opciones del comando render

```bash
# Ruta de salida personalizada
python render.py inputs/mi_video.yaml --output ./output/clase_01.mp4

# Con audio (se mezcla automáticamente)
python render.py inputs/mi_video.yaml --audio inputs/locucion.wav

# Solo renderizar una escena (útil para revisar antes de todo)
python render.py inputs/mi_video.yaml --only portada

# No concatenar — deja los clips individuales en output/_tmp/
python render.py inputs/mi_video.yaml --no-concat

# Conservar archivos temporales (clips individuales + props JSON)
python render.py inputs/mi_video.yaml --keep-tmp

# Ayuda
python render.py --help
```

---

## Ejemplo incluido — 45 segundos

```bash
python render.py inputs/ejemplo_45s.yaml
```

Genera `pipeline/output/video_final.mp4` con exactamente **45 segundos** y 7 escenas:

| Escena | Template | Duración |
|---|---|---|
| portada | COVER-MainCover | 7s |
| pregunta | DEF-RhetoricalQuestion | 5s |
| definicion | DEF-Central | 8s |
| propiedades | CLASS-FourBoxes | 7s |
| ciclo | FLOW-CycleLoop | 6s |
| datos | DATA-StatCounter | 6s |
| cierre | CLOSE-Keywords | 6s |
| **TOTAL** | | **45s** |

---

## Ver templates en el studio

```bash
cd pipeline/remotion
npx remotion studio src/index.tsx
```

Abre **http://localhost:3000** y navega por las composiciones en el panel izquierdo.

---

## Catálogo completo de templates

### Apertura y cierre

| ID | Descripción |
|---|---|
| `COVER-MainCover` | Portada principal — título grande, subtítulo, tag de episodio |
| `COVER-SectionCover` | Portada de sección — fondo gris, alineado a la izquierda |
| `CLOSE-Keywords` | Cierre con palabras clave que vuelan desde distintas direcciones |
| `CLOSE-Quote` | Cierre con frase — gradiente oscuro índigo→cyan |
| `CLOSE-Credits` | Créditos / fuentes — bullets que aparecen uno a uno |

### Conceptos y definiciones

| ID | Descripción |
|---|---|
| `DEF-Central` | Término arriba, comilla decorativa, definición centrada grande |
| `DEF-ProgressiveReveal` | Título + items numerados que aparecen por tiempo |
| `DEF-ImpactTerm` | Palabra grande + definición en caja tipo post-it |
| `DEF-RhetoricalQuestion` | Pregunta grande sobre gradiente oscuro |
| `DEF-VisualAnalogy` | Dos columnas: lo conocido → concepto nuevo |

### Clasificaciones y estructuras

| ID | Descripción |
|---|---|
| `CLASS-FourBoxes` | Grid 2×2 con ícono emoji, título y descripción |
| `CLASS-TwoColumns` | Comparación con checks ✅ y cruces ❌ |
| `CLASS-PyramidLevels` | Capas SVG de abajo hacia arriba |
| `CLASS-MatrixGrid` | Matriz 2×2 con ejes X/Y etiquetados |
| `CLASS-FlipCards` | 4 cartas CSS 3D que voltean |
| `CLASS-HexGrid` | Panal de hexágonos que se revelan en ola |
| `CLASS-VennDiagram` | Dos círculos con solapamiento y listas |
| `CLASS-MosaicReveal` | Celdas que estallan en ola desde el centro |

### Procesos y flujos

| ID | Descripción |
|---|---|
| `FLOW-LinearSteps` | 4 tarjetas en fila con flechas que se dibujan |
| `FLOW-CycleLoop` | 4 nodos en elipse con flechas curvas |
| `FLOW-Funnel` | Embudo de capas trapezoidales con valores animados |
| `FLOW-OrgChart` | Árbol jerárquico con líneas SVG |
| `FLOW-MindMap` | Post-its distribuidos en la pantalla con líneas desde el centro |
| `FLOW-SketchDiagram` | Flujo estilo pizarrón, trazo tembloroso, fondo papel |

### Datos y evidencia

| ID | Descripción |
|---|---|
| `DATA-StatCounter` | 3 números grandes que cuentan desde cero |
| `DATA-HorizontalBars` | Barras horizontales tipo ranking |
| `DATA-PieDonut` | Gráfico de rosca que se dibuja segmento a segmento |
| `DATA-RadarChart` | Gráfico araña que se llena sobre red de ejes |
| `DATA-CircleStats` | Arcos SVG circulares con porcentaje animado |
| `DATA-WaveTrend` | Curva suave que se dibuja con etiquetas flotantes |

### Narrativa y contexto

| ID | Descripción |
|---|---|
| `NAR-Timeline` | Línea de tiempo horizontal con eventos alternando arriba/abajo |
| `NAR-Spotlight` | Foco de luz que viaja entre términos activándolos con color |
| `NAR-TypeWriter-Hacker` | Terminal de código — texto que se escribe letra a letra |
| `NAR-ParticleNetwork` | Red neuronal de partículas que orbitan y se conectan |

### Transiciones y efectos

| ID | Descripción |
|---|---|
| `FX-KineticWords` | Palabras que vuelan desde distintas direcciones y se ensamblan |
| `FX-RotatingCube` | Cubo 3D CSS, cada cara un concepto distinto |
| `FX-WaveOrb` | Orbe con ondas de radar expandiéndose |
| `FX-GlitchReveal` | Texto con falla digital RGB split |
| `FX-GradientTitle` | Título blanco sobre gradiente vibrante con formas geométricas |

---

## Estructura del proyecto

```
remotion/
├── pipeline/
│   ├── remotion/
│   │   └── src/
│   │       ├── index.tsx          # Registro de todas las composiciones
│   │       ├── components/        # Subtitles, PlaceholderAsset
│   │       └── templates/         # 39 templates animados (uno por archivo)
│   ├── render.py                  # ← Script principal: YAML → MP4
│   ├── inputs/
│   │   └── ejemplo_45s.yaml       # Ejemplo de guion de 45 segundos
│   ├── output/                    # El MP4 final aparece aquí
│   │   └── video_final.mp4
│   ├── pipeline.py                # Pipeline legacy (para referencia)
│   ├── guion_parser.py            # Parser legacy (para referencia)
│   └── requirements.txt
├── PARA_CLAUDE.md                 # Contexto del proyecto para Claude
└── README.md
```

---

## Convenciones de los templates

- **Fondo blanco** `#FFFFFF` por defecto (FX y NAR oscuros pueden usar gradiente)
- **CONFIG object** al tope de cada template con todos los valores visuales editables
- **Sin `Math.random()`** — todo determinístico con `useCurrentFrame()`, `spring()`, `interpolate()`
- Resolución: **1920×1080 @ 30fps**
- Fuente: **Inter** en todos los templates de fondo blanco

---

## Agregar un template propio

1. Crear `pipeline/remotion/src/templates/MiTemplate.tsx` con un `const CONFIG = { ... }` al tope
2. Registrar en `pipeline/remotion/src/index.tsx` con un ID con prefijo de categoría
3. Usarlo en el YAML con `template: MI-ID`
