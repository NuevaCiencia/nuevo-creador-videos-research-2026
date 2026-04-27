# PARA_CLAUDE.md — Contexto completo del proyecto

## Qué estamos construyendo

Pipeline de producción de videos educativos animados con **Remotion** (React + TypeScript). El objetivo es tener un catálogo de pantallas educativas reutilizables que un LLM pueda instanciar con contenido para generar videos de cursos automáticamente.

Cada pantalla es un **template Remotion** independiente: recibe props con el contenido, tiene animaciones determinísticas, y sigue un estilo visual consistente.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Templates animados | Remotion 4.x + React + TypeScript |
| Orquestador | Python 3.14 + typer + pyyaml |
| Composición final | FFmpeg |
| Runtime | Node.js 24 |

### Estructura de carpetas
```
remotion/
├── pipeline/
│   ├── remotion/
│   │   ├── src/
│   │   │   ├── index.tsx              ← registro de todas las composiciones
│   │   │   ├── components/
│   │   │   └── templates/             ← un archivo por pantalla
│   │   └── package.json
│   ├── pipeline.py
│   ├── requirements.txt
│   └── inputs/
├── venv/                              ← entorno virtual Python
├── Blueprint.md
└── README.md
```

---

## Convenciones de cada template

1. **CONFIG object** al tope del archivo con todas las variables visuales explícitas:
   - `bg` — color de fondo
   - `fontFamily` — siempre `"Inter, system-ui, sans-serif"`
   - tamaños, pesos y colores de cada elemento de texto
   - colores de acento

2. **Fondo blanco** por defecto (`#FFFFFF`). Las pantallas de impacto/cierre pueden usar gradiente oscuro.

3. **Sin `word_cues`** — los templates nuevos no dependen del componente `Subtitles`.

4. **Animaciones determinísticas** — solo `useCurrentFrame()`, `spring()`, `interpolate()`. Sin `Math.random()`.

5. **IDs de composición** con prefijo de categoría:
   - `COVER-` → apertura y cierre
   - `CLOSE-` → cierres
   - `DEF-` → conceptos y definiciones
   - `CLASS-` → clasificaciones y estructuras
   - `FLOW-` → procesos y flujos
   - `DATA-` → datos y evidencia
   - `NAR-` → narrativa y contexto
   - `FX-` → transiciones y ritmo

---

## Cómo ver un template

Con el studio corriendo (`npx remotion studio src/index.tsx` en `pipeline/remotion/`), abrir directamente:

```
http://localhost:3000/[ID-de-composición]
```

---

## Catálogo completo de pantallas

### APERTURA Y CIERRE

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `COVER-MainCover` | MainCover | Portada principal — título grande, subtítulo, tag de episodio, fondo blanco |
| ✅ | `COVER-SectionCover` | SectionCover | Portada de sección — fondo gris `#F1F5F9`, título y subtítulo alineados a la izquierda |
| ✅ | `CLOSE-Keywords` | ClosingKeywords | Cierre con palabras clave — 4-6 palabras vuelan desde distintas direcciones |
| ✅ | `CLOSE-Quote` | ClosingQuote | Cierre con frase — palabras aparecen una a una, gradiente oscuro índigo→cyan |
| ✅ | `CLOSE-Credits` | Credits | Créditos / Fuentes — bullets con label y texto, aparecen uno a uno |

### CONCEPTOS Y DEFINICIONES

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `DEF-Central` | CentralDefinition | Definición central — término arriba, comilla decorativa, texto grande centrado |
| ✅ | `DEF-ProgressiveReveal` | ProgressiveReveal | Revelado progresivo — título + items numerados que aparecen por `t_trigger` |
| ✅ | `DEF-ImpactTerm` | ImpactTerm | Término con post-it — palabra grande + definición en caja amarilla tipo post-it |
| ✅ | `DEF-RhetoricalQuestion` | RhetoricalQuestion | Pregunta retórica — pregunta grande sobre gradiente oscuro con signo `?` decorativo |
| ✅ | `DEF-VisualAnalogy` | VisualAnalogy | Analogía visual — dos columnas: lo conocido (gris) → concepto nuevo (lila) |

### CLASIFICACIONES Y ESTRUCTURAS

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `CLASS-FourBoxes` | FourBoxes | 4 cajas — grid 2×2 con ícono emoji, título y descripción, stagger de entrada |
| ✅ | `CLASS-TwoColumns` | TwoColumns | 2 columnas comparación — headers de color, items con check ✅ o cruz ❌ |
| ✅ | `CLASS-PyramidLevels` | PyramidLevels | Pirámide de niveles — capas SVG de abajo hacia arriba, etiquetas a la derecha |
| ✅ | `CLASS-MatrixGrid` | MatrixGrid | Matriz 2×2 — cuatro cuadrantes con ejes X/Y etiquetados |
| ✅ | `CLASS-FlipCards` | FlipCards | Cartas que voltean — 4 cartas CSS 3D, frente=ícono, reverso=concepto |
| ✅ | `CLASS-HexGrid` | HexGrid | Panal de conceptos — hexágonos que se revelan en ola desde el centro |
| ✅ | `CLASS-VennDiagram` | VennDiagram | Diagrama Venn — dos círculos con solapamiento, listas en cada zona |
| ✅ | `CLASS-MosaicReveal` | MosaicReveal | Mosaico de términos — celdas que estallan en ola, título encima |

### PROCESOS Y FLUJOS

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `FLOW-LinearSteps` | LinearSteps | Pasos lineales — 4 tarjetas en fila con flechas que se dibujan |
| ✅ | `FLOW-CycleLoop` | CycleLoop | Ciclo / Loop — 4 nodos en diamante con flechas curvas, nodo central |
| ✅ | `FLOW-Funnel` | Funnel | Embudo — capas que se van estrechando con números animados |
| ✅ | `FLOW-OrgChart` | OrgChart | Árbol jerárquico — nodos conectados con líneas SVG de arriba hacia abajo |
| ✅ | `FLOW-MindMap` | MindMap | Mapa mental — post-its distribuidos en toda la pantalla con líneas desde el centro |
| ✅ | `FLOW-SketchDiagram` | SketchDiagram | Flujo en pizarrón — trazo tembloroso tipo dibujo a mano, fondo papel |

### DATOS Y EVIDENCIA

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `DATA-StatCounter` | StatCounter | Cifras impactantes — 3 números que cuentan desde cero |
| ✅ | `DATA-HorizontalBars` | HorizontalBars | Barras horizontales — ranking con barras que crecen y valores animados |
| ✅ | `DATA-PieDonut` | PieDonut | Gráfico de rosca — donut que se dibuja segmento a segmento |
| ✅ | `DATA-RadarChart` | RadarChart | Gráfico araña — polígono que se llena sobre red de ejes |
| ✅ | `DATA-CircleStats` | CircleStats | Medidores circulares — 3-4 arcos SVG con porcentaje animado |
| ✅ | `DATA-WaveTrend` | WaveTrend | Onda de tendencia — curva que se dibuja con etiquetas en puntos clave |

### NARRATIVA Y CONTEXTO

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `NAR-Timeline` | Timeline | Línea de tiempo — línea horizontal con eventos alternando arriba/abajo |
| ✅ | `NAR-Spotlight` | Spotlight | Spotlight de conceptos — foco de luz que viaja entre términos sobre fondo negro |
| ✅ | `NAR-TypeWriter-Hacker` | TypeWriter | Terminal de código — texto que se escribe letra a letra, fuente monospace |
| ✅ | `NAR-ParticleNetwork` | ParticleNetwork | Red de partículas — nodos que orbitan y se conectan, texto encima |
| ❌ | `NAR-Globe3D` | Globe3D | **Descartado** — depende de @remotion/three, no carga |

### TRANSICIONES Y RITMO

| Estado | ID | Template | Descripción |
|---|---|---|---|
| ✅ | `FX-KineticWords` | KineticWords | Palabras cinéticas — palabras vuelan y se ensamblan (versión educativa blanca) |
| ✅ | `FX-RotatingCube` | RotatingCube | Cubo rotando — cubo 3D CSS, cada cara un concepto distinto |
| ✅ | `FX-WaveOrb` | WaveOrb | Radar de percepción — orbe con ondas de radar expandiéndose |
| ✅ | `FX-GlitchReveal` | GlitchReveal | Glitch — texto con falla digital, RGB split |
| ✅ | `FX-GradientTitle` | GradientTitle | Gradiente vibrante — texto blanco sobre gradiente con formas geométricas |

---

## Progreso

- **Completadas:** 39 de 39 pantallas (1 descartada: Globe3D)
- **Pendientes:** 0 pantallas

---

## Notas importantes para Claude

- El studio debe estar corriendo antes de trabajar: `cd pipeline/remotion && npx remotion studio src/index.tsx`
- El entorno Python se activa con: `source venv/bin/activate`
- Cada template nuevo se registra en `pipeline/remotion/src/index.tsx`
- Los `defaultProps` en `index.tsx` son el contenido de prueba — no van en el template
- El usuario aprueba cada pantalla visualmente antes de pasar a la siguiente
- Trabajar de a **una pantalla a la vez**
