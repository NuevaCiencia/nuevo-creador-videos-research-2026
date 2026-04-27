# 🎬 Creador de Videos (IA Pipeline)

Este repositorio aloja un **motor avanzado y completamente automatizado de inteligencia artificial** diseñado para transformar una locución de audio cruda y un archivo de guion (en Markdown) en un video educativo profesional, dinámico y listo para producción — todo sin tocar Premiere o After Effects.

El sistema soporta **múltiples proyectos independientes** organizados en `proyectos/01/`, `proyectos/02/`, etc. Cada uno con su propio audio, guion y configuración.

---

## 🚀 Flujo de Trabajo

```
00_crear_proyecto.py  →  01_preparacion.py  →  02_generar_video.py  →  00_backup.py
                                                      (opcional)   ↘  00_restaurar_proyecto.py
```

Todos los scripts reciben el flag `-p NUM` para indicar el proyecto activo.

### Paso 0: Crear un proyecto nuevo
```bash
python 00_crear_proyecto.py          # detecta automáticamente el siguiente número
python 00_crear_proyecto.py -p 03    # o fuerza un número/nombre específico
```
Genera la estructura de carpetas, un `video_config.yaml` y un `original_speech.md` de plantilla.

### Paso 1: Preparación con IA
Transcripción (WhisperX), corrección ortográfica y diseño visual automatizado:
```bash
python 01_preparacion.py -p 01
```
Flags de control:
- `--desde-fase 2` — Salta WhisperX, usa transcripción cacheada.
- `--desde-fase 3` — Solo regenera el guion visual (útil al editar etiquetas).
- `--forzar` — Ignora el caché y re-ejecuta desde la fase indicada.

### Paso 2: Renderizado
Construye el video con FFmpeg:
```bash
python 02_generar_video.py -p 01
```
El resultado aparece en `proyectos/01/video_final.mp4`.

### Paso 3: Backup y limpieza
```bash
python 00_backup.py -p 01       # backup + limpiar el proyecto
python 00_backup.py -p 01 -nb   # solo backup, sin borrar nada
```

### Paso 4: Restaurar un proyecto (Opcional)
Si necesitas recuperar un video archivado para hacer cambios:
```bash
python 00_restaurar_proyecto.py -z backup_p01_TIMESTAMP.zip -p 01_recuperado
```

---

## 💡 Etiquetas de Escena (`original_speech.md`)

El motor visual lee las etiquetas HTML que intercalas en tu guion para decidir qué mostrar en cada segmento:

### Etiquetas estáticas (usan imágenes o texto)
| Etiqueta | Resultado |
|---|---|
| `<!-- type:TEXT -->` | Fondo sólido + frase clave generada por IA |
| `<!-- type:FULL_IMAGE -->` | Imagen generada por IA a pantalla completa |
| `<!-- type:SPLIT_LEFT -->` | Imagen izquierda, texto derecha |
| `<!-- type:SPLIT_RIGHT -->` | Texto izquierda, imagen derecha |
| `<!-- type:VIDEO -->` | Video de fondo (B-roll) |

### Etiquetas dinámicas animadas (sincronizadas al audio)
Cada elemento aparece **exactamente en el milisegundo en que se pronuncia** gracias a WhisperX.

```
<!-- type:CONCEPT // Término a definir // Definición larga aquí -->
```
Perfecto para pantallas de glosario. El título aparece al decir el término; la definición al hablar de ella.

```
<!-- type:LIST // @ Título Fantasma // Elemento 1 // Elemento 2 [Nota] // Elemento 3 -->
```
Lista secuencial animada. Cada ítem aparece al ser mencionado. El prefijo `@` en el primer parámetro crea un "título fantasma" sutil que aparece desde el inicio. Lo que va entre `[...]` se muestra como nota aclaratoria pequeña.

---

## 7. Estructura de un Proyecto

```
creador-videos-mac-investigacion/
│
├── 00_crear_proyecto.py     ← crea un proyecto nuevo
├── 00_restaurar_proyecto.py  ← recupera un backup (-z ZIP -p DEST)
├── 00_backup.py             ← backup y limpieza  (-p NUM)
├── 01_preparacion.py        ← pipeline de IA     (-p NUM)
├── 02_generar_video.py      ← render con FFmpeg  (-p NUM)
│
├── ai_config.yaml          ← prompts de IA (compartido)
├── fonts/                  ← tipografías compartidas
├── pipeline/               ← módulos de IA (Whisper, Aligner, etc.)
├── core/                   ← motor de render (FFmpeg, ASS, utils)
│
└── proyectos/
    ├── 01/
    │   ├── original_speech.md    ← guion con etiquetas
    │   ├── video_config.yaml     ← título, audio, colores, FPS...
    │   ├── assets/AUDIO/         ← tu locución
    │   ├── assets/images/        ← imágenes generadas por IA
    │   ├── assets/videos/        ← videos de fondo / portada
    │   └── output/               ← todo lo generado automáticamente
    └── 02/
        └── ...
```

---

## 🧠 Cómo Funciona

1. **Transcripción Milimétrica** — WhisperX registra en qué milisegundo exacto se pronuncia cada palabra.
2. **Corrección y Alineación** — GPT-4o-mini limpia el texto transcrito y lo alinea con el guion original.
3. **Dirección de Arte Automática** — La IA lee las etiquetas de tu guion y genera prompts profundos para imágenes y frases clave.
4. **Animación y Renderizado** — FFmpeg inyecta imágenes, videos, transiciones y tipografía sincronizada con el audio.
5. **Caché Inteligente** — Si solo cambias una etiqueta, el motor reutiliza las fases pesadas ya calculadas.

---

## 🛠 Instalación

```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Dependencias del sistema (Homebrew en macOS)
brew install ffmpeg
```

> Requiere `ffmpeg` con soporte para `libass`. WhisperX requiere `torch` (instalado vía `requirements.txt`).

## 💾 Consejos Ninja

- **Dummies automáticos:** Si la IA sugiere `S001.png` y no existe, se genera un placeholder gris automáticamente para prototipar rápido.
- **Ajustar el estilo de la IA:** Edita los prompts en `ai_config.yaml`. No toques el código Python.
- **Reutilizar transcripciones:** Copia la carpeta `output/01_transcripcion/` de un proyecto anterior y corre `--desde-fase 2` para ahorrar tiempo de Whisper.

---

## 8. Preguntas Frecuentes (Q&A)

**P: ¿Cómo modifico solo una etiqueta visual sin re-transcribir todo?**

**R:** Edita la etiqueta en `original_speech.md` y corre:
```bash
python 01_preparacion.py -p 01 --desde-fase 3
python 02_generar_video.py -p 01
```

**P: ¿Cómo creo el proyecto 02 mientras el 01 sigue activo?**

**R:** Los proyectos son independientes. Simplemente crea el nuevo con `python 00_crear_proyecto.py`.