# Manual de Uso Rápido - Creador de Videos

Este manual describe cómo crear y gestionar múltiples proyectos de video de forma independiente, cada uno en su propia carpeta numerada dentro de `proyectos/`.

---

## 0. Activar el Entorno Virtual

Antes de ejecutar cualquier script, activa el entorno virtual:

```bash
source venv/bin/activate
```

*(Verás `(venv)` al inicio de tu línea de comandos cuando esté activo).*

---

## 1. Flujo Completo (4 Scripts, en Orden)

El flujo de trabajo se compone de **4 scripts numerados**. Todos requieren el flag `-p` para indicar el proyecto:

```
00_crear_proyecto.py   →   01_preparacion.py   →   02_generar_video.py   →   00_backup.py
       ↑                          ↑                         ↑                      ↑
  Crear el proyecto         IA + Whisper             Render FFmpeg         Archivar y limpiar
```

---

## 2. Crear un Proyecto Nuevo

Antes de empezar, crea la estructura de carpetas con:

```bash
python 00_crear_proyecto.py
```

Esto detecta automáticamente el siguiente número disponible (01, 02, 03...) y genera:
- `proyectos/02/video_config.yaml` — configuración de ese video (título, audio, colores)
- `proyectos/02/original_speech.md` — plantilla de guion con ejemplos de etiquetas
- Todas las carpetas necesarias (`assets/AUDIO/`, `assets/images/`, `output/`, etc.)

Para forzar un número o nombre específico:
```bash
python 00_crear_proyecto.py -p 03
python 00_crear_proyecto.py -p clase_marketing
```

### Archivos que debes editar antes de continuar:
1. **`proyectos/NN/video_config.yaml`** — cambia `TITLE`, `MAIN_AUDIO`, colores, etc.
2. **`proyectos/NN/original_speech.md`** — escribe tu guion con las etiquetas de escena.
3. Copia tu **audio** a `proyectos/NN/assets/AUDIO/`.

> [!TIP]
> Si usas un archivo **.WAV de alta calidad (44.1kHz o más)**, WhisperX puede consumir mucha RAM. Para mayor estabilidad en audios largos, usa **MP3** o **WAV a 16000 Hz**.

---

## 3. Preparación con IA (Transcripción, Corrección, Guion Visual)

```bash
python 01_preparacion.py -p 01
```

**Flags opcionales:**
- `--desde-fase 2` — Salta WhisperX, usa transcripción cacheada.
- `--desde-fase 3` — Salta Whisper y corrección, regenera solo el guion visual.
- `--forzar` — Ignora todo el caché y re-ejecuta desde la fase indicada.

**¿Cuándo saltar fases?**

| Situción | Comando |
|---|---|
| Modificar etiquetas `<!-- type:... -->` en el guion | `--desde-fase 3` |
| Re-corregir texto sin re-transcribir | `--desde-fase 2` |
| Transcripción nueva de audio | (sin flags, fase 1) |

> [!TIP]
> **Al copiar transcripciones de otro proyecto:** Si copiaste `01_transcripcion/` para ahorrar tiempo, elimina manualmente `02_correccion/` y `03_guion/` antes de correr desde la fase 2.

---

## 4. Generar el Video Final

```bash
python 02_generar_video.py -p 01
python 02_generar_video.py -p 01 --debug   # activa timestamps en pantalla
```

El video se guarda en: `proyectos/01/video_final.mp4`

---

## 5. Backup y Limpieza

Cuando termines un video, respalda y limpia el proyecto para el siguiente:

```bash
# Backup + limpieza (vacía output/, assets/, elimina video_final.mp4)
python 00_backup.py -p 01

# Solo backup, sin borrar nada (-nb = no borrar)
python 00_backup.py -p 01 -nb
```

El ZIP se guarda en `deprecated/backup_p01_TIMESTAMP.zip`.  
Se conservan siempre: `original_speech.md` y `video_config.yaml` (el ADN del proyecto).

---

## 6. Restaurar un Proyecto Archivado

Si necesitas hacer cambios en un video que ya fue archivado:

```bash
python 00_restaurar_proyecto.py -z backup_p01_TIMESTAMP.zip -p 01_recuperado
```

Esto creará la carpeta `proyectos/01_recuperado/` con todo su contenido original listo para volver a renderizar.

---

## 7. Estructura de un Proyecto

```
proyectos/
└── 01/
    ├── original_speech.md        ← guion con etiquetas de escena
    ├── video_config.yaml         ← configuración del video
    ├── video_final.mp4           ← resultado final (ignorado por git)
    ├── assets/
    │   ├── AUDIO/                ← tu locución (.mp3/.wav)
    │   ├── images/               ← imágenes generadas por IA
    │   ├── videos/               ← videos de fondo / portada
    │   └── MANIM/                ← animaciones Manim (opcional)
    └── output/
        ├── 01_transcripcion/     ← WhisperX crudo
        ├── 02_correccion/        ← texto corregido por IA
        ├── 03_guion/             ← guion consolidado + JSON visuales
        └── 04_render/            ← temporales de FFmpeg
```

Archivos compartidos en la raíz (todos los proyectos los usan):
- `ai_config.yaml` — prompts de IA (Visual Orchestrator, SpellChecker)
- `fonts/` — tipografías compartidas
- `pipeline/`, `core/` — código fuente del motor

---

## 8. Preguntas Frecuentes (Q&A)

**P: ¿Cómo modifico solo una etiqueta visual sin re-transcribir todo?**

**R:** Edita la etiqueta en `original_speech.md` y corre:
```bash
python 01_preparacion.py -p 01 --desde-fase 3
python 02_generar_video.py -p 01
```

---

**P: ¿Cómo creo el proyecto 02 mientras el 01 sigue activo?**

**R:** Los proyectos son independientes. Simplemente crea el nuevo:
```bash
python 00_crear_proyecto.py        # detecta que el siguiente es 02
python 01_preparacion.py -p 02
python 02_generar_video.py -p 02
```

---

**P: ¿Hay riesgo de que un proyecto pise a otro?**

**R:** No. Cada proyecto tiene su propio `output/`, `assets/` y `video_final.mp4`. Los scripts nunca tocan otro proyecto.
