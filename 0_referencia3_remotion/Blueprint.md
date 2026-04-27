# Stack Tecnológico — Pipeline de Videos Educativos

## Resumen del stack

| Capa | Tecnología | Versión recomendada |
|---|---|---|
| Orquestador | Python | 3.11+ |
| Selector de plantilla | LLM externo (a definir) | — |
| Renderizado visual | Remotion | 4.x |
| Lenguaje de plantillas | TypeScript + React | TS 5.x / React 18 |
| Composición de video | FFmpeg | 6.x |
| Formato intermedio | JSON | — |
| Runtime Node.js | Node.js | 20 LTS |

---

## Lo que el pipeline recibe (ya resuelto externamente)

- Transcripción con timestamps — lista
- Guión por pantallas — listo
- Alineación de cues con tiempos locales — resuelta
- Selección de plantilla y JSON intermedio — producidos por LLM externo

El pipeline arranca desde el **JSON intermedio por pantalla** y se encarga exclusivamente de renderizar y componer.

---

## Capa 1 — Orquestador: Python

### Por qué Python
Conecta todas las capas. Llama a Remotion y FFmpeg como subprocesos, lee los JSONs intermedios y gestiona los artefactos de salida.

### Dependencias

```bash
pip install pyyaml python-dotenv typer rich
```

### requirements.txt

```
pyyaml>=6.0
python-dotenv>=1.0.0
typer>=0.12.0
rich>=13.7.0
```

### Esqueleto del orquestador

```python
# pipeline.py

import typer
import json
from pathlib import Path
from rich.console import Console
from rich.progress import track

app = typer.Typer()
console = Console()

@app.command()
def run(
    intermediate_dir: Path = typer.Option(..., help="Directorio con los JSON por pantalla"),
    audio:            Path = typer.Option(..., help="Ruta al audio original"),
    output_dir:       Path = typer.Option("./output", help="Directorio de salida"),
):
    screens = sorted(intermediate_dir.glob("*.json"))

    for screen_path in track(screens, description="Procesando pantallas..."):
        screen_json = json.loads(screen_path.read_text())

        # Paso 1: renderizar video mudo con Remotion
        render_remotion(screen_json, output_dir)

        # Paso 2: extraer segmento de audio y componer video final
        compose_final(screen_json, audio, output_dir)

if __name__ == "__main__":
    app()
```

---

## Capa 2 — Selector de plantilla: LLM externo

Fuera del scope del pipeline actual. El LLM recibe el contenido de cada pantalla y devuelve el JSON intermedio con la plantilla elegida y los datos estructurados.

El pipeline asume que esos JSONs ya existen en `intermediate/` y los consume directamente.

---

## Capa 3 — Renderizado visual: Remotion

### Por qué Remotion
- Animaciones en React + TypeScript: predecible para generación con IA
- Timing basado en frames: `useCurrentFrame()` permite sincronización exacta al audio
- Renderiza a MP4 desde línea de comandos recibiendo props como JSON externo
- Soporte nativo para fuentes, SVG, Canvas

### Instalación

```bash
cd pipeline/remotion
npm create video@latest .
# elegir: blank template, TypeScript
npm install
npm install @remotion/google-fonts
```

### Estructura de una plantilla

```tsx
// src/templates/BulletList.tsx

import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

export type BulletListProps = {
  title: string;
  items: {
    text: string;
    t_trigger: number; // segundos desde el inicio de la pantalla
  }[];
};

export const BulletList: React.FC<BulletListProps> = ({ title, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ background: "#0f0e13", padding: 64 }}>
      {items.map((item, i) => {
        const triggerFrame = item.t_trigger * fps; // segundos → frames
        const localFrame   = frame - triggerFrame;

        const opacity = interpolate(localFrame, [0, 20], [0, 1], {
          extrapolateLeft:  "clamp",
          extrapolateRight: "clamp",
        });

        const x = spring({
          frame: localFrame,
          fps,
          config: { damping: 18, stiffness: 200 },
          from: -30,
          to: 0,
        });

        return (
          <div key={i} style={{ opacity, transform: `translateX(${x}px)` }}>
            {item.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
```

### Registro de composiciones

```tsx
// src/index.ts

import { Composition } from "remotion";
import { BulletList }   from "./templates/BulletList";
import { SmartDiagram } from "./templates/SmartDiagram";
import { ConceptCard }  from "./templates/ConceptCard";

export const RemotionRoot = () => (
  <>
    <Composition
      id="BulletList"
      component={BulletList}
      durationInFrames={9000}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{ title: "", items: [] }}
    />
    <Composition
      id="SmartDiagram"
      component={SmartDiagram}
      durationInFrames={9000}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{ title: "", diagram_type: "process", nodes: [], edges: [] }}
    />
    <Composition
      id="ConceptCard"
      component={ConceptCard}
      durationInFrames={9000}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{ label: "", term: "", definition: "" }}
    />
  </>
);
```

### Render desde Python

```python
import subprocess
import json
from pathlib import Path

def render_remotion(screen_json: dict, output_dir: Path):
    template    = screen_json["template"]
    duration_f  = int(screen_json["duration_local"] * 30)  # segundos → frames
    screen_id   = screen_json["screen_id"]

    props_path  = output_dir / f"{screen_id}_props.json"
    output_path = output_dir / f"{screen_id}_video.mp4"

    props_path.write_text(json.dumps(screen_json["content"]))

    subprocess.run([
        "npx", "remotion", "render",
        "src/index.ts",
        template,
        "--props",  str(props_path),
        "--frames", f"0-{duration_f}",
        "--output", str(output_path),
    ], cwd="./remotion", check=True)
```

---

## Capa 4 — Composición final: FFmpeg

### Por qué FFmpeg
Estándar universal para procesamiento de video y audio. Exacto al frame, rápido y scripteable desde Python.

### Instalación

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows — descargar binario en https://ffmpeg.org/download.html
```

### Flujo en Python

```python
import subprocess
from pathlib import Path

def compose_final(screen_json: dict, source_audio: Path, output_dir: Path):
    screen_id  = screen_json["screen_id"]
    t_start    = screen_json["t_global"]["start"]
    t_end      = screen_json["t_global"]["end"]

    audio_clip = output_dir / f"{screen_id}_audio.wav"
    video_mute = output_dir / f"{screen_id}_video.mp4"
    final_out  = output_dir / f"{screen_id}_final.mp4"

    # Extraer segmento de audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i",  str(source_audio),
        "-ss", str(t_start),
        "-to", str(t_end),
        "-c",  "copy",
        str(audio_clip),
    ], check=True)

    # Mezclar video + audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_mute),
        "-i", str(audio_clip),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(final_out),
    ], check=True)
```

### Comandos útiles adicionales

```bash
# Verificar duración de un video
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 screen_03_final.mp4

# Concatenar todos los videos finales en uno solo (opcional)
ls output/*_final.mp4 | sed "s/^/file '/" | sed "s/$/'/" > lista.txt
ffmpeg -f concat -safe 0 -i lista.txt -c copy video_completo.mp4
```

---

## Variables de entorno

```bash
# .env
REMOTION_DIR=./remotion
OUTPUT_DIR=./output
INTERMEDIATE_DIR=./intermediate
FPS=30
RESOLUTION_W=1920
RESOLUTION_H=1080
```

---

## Versiones y compatibilidad

| Tecnología | Versión mínima | Notas |
|---|---|---|
| Python | 3.11 | — |
| Node.js | 20 LTS | requerido por Remotion 4.x |
| Remotion | 4.0 | soporte `--props` estable |
| FFmpeg | 5.0 | suficiente; 6.x recomendado |

---

## Diagrama de dependencias

```
JSON intermedio por pantalla   ← entra aquí, ya procesado
          │
          ▼
     pipeline.py
          │
          ├── subprocess → Node.js
          │     └── remotion CLI          → MP4 mudo
          │           └── React / TypeScript
          │                 ├── BulletList.tsx
          │                 ├── SmartDiagram.tsx
          │                 └── ConceptCard.tsx
          │
          └── subprocess → FFmpeg
                ├── extrae segmento de audio
                └── mezcla video + audio  → screen_XX_final.mp4
```

---

## Estructura de carpetas

```
pipeline/
├── inputs/
│   └── locucion_completa.wav     # audio fuente original
│
├── intermediate/
│   ├── screen_01.json            # JSONs producidos externamente
│   ├── screen_02.json
│   └── screen_03.json
│
├── remotion/
│   ├── src/
│   │   ├── templates/
│   │   │   ├── BulletList.tsx
│   │   │   ├── SmartDiagram.tsx
│   │   │   └── ConceptCard.tsx
│   │   └── index.ts
│   └── package.json
│
├── output/
│   ├── screen_01_final.mp4
│   ├── screen_02_final.mp4
│   └── screen_03_final.mp4
│
├── pipeline.py
├── requirements.txt
└── .env
```

---

## Instalación completa desde cero

```bash
# 1. Crear el proyecto
mkdir pipeline-educativo && cd pipeline-educativo

# 2. Entorno Python
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install pyyaml python-dotenv typer rich

# 3. Proyecto Remotion
mkdir remotion && cd remotion
npm create video@latest .       # elegir: blank, TypeScript
npm install @remotion/google-fonts
cd ..

# 4. FFmpeg (macOS)
brew install ffmpeg

# 5. Variables de entorno
cp .env.example .env

# 6. Verificar
python -c "import typer; print('Python OK')"
node -e "console.log('Node OK')"
ffmpeg -version | head -1
```

---

## Costos

Todo el stack es open source y corre local. Costo por video: **$0.00**.