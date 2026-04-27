#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_crear_proyecto.py — Inicializar un proyecto nuevo

Crea la estructura de carpetas necesaria para un nuevo video y genera
un video_config.yaml y original_speech.md de plantilla listos para editar.

Uso:
  python 00_crear_proyecto.py             # detecta automáticamente el siguiente número
  python 00_crear_proyecto.py -p 03       # fuerza el nombre/número de proyecto
  python 00_crear_proyecto.py -p clase2   # también acepta nombres descriptivos
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


# ── Plantillas ─────────────────────────────────────────────────────────────────

VIDEO_CONFIG_TEMPLATE = """\
# Configuración de video para CREADOR-VIDEOS
# Proyecto: {proyecto}
# Creado:   {fecha}

FILES_FOLDER: assets
TITLE: "Título del video aquí"
MAIN_AUDIO: "assets/AUDIO/mi_audio.mp3"
GUION_COMPLETO: "output/03_guion/guion_consolidado.txt"
FPS: 30
RESOLUTION: "1920x1080"
MAIN_FONT: Inter
BACKGROUND_COLOR: "#fefefe"
MAIN_TEXT_COLOR: "#bd0505"
HIGHLIGHT_TEXT_COLOR: "#e3943b"
COVER_ASSET: "videos/portada.mp4"
COVER_NOTES: "Título cover aquí"

USE_TRANSITIONS: true
TRANSITION_DURATION: 0.5
"""

ORIGINAL_SPEECH_TEMPLATE = """\
# {proyecto} — Guion Original

<!-- type:TEXT -->
Escribe aquí el primer párrafo de tu guion. Este texto se usará como base
para la transcripción y alineación de subtítulos.

<!-- type:TEXT -->
Continúa tu guion aquí. Puedes usar etiquetas para controlar el tipo de
pantalla que se mostrará en cada segmento.

<!-- TIPOS DE ETIQUETAS DISPONIBLES:
  type:TEXT         — Fondo sólido + frase clave generada por IA
  type:FULL_IMAGE   — Imagen generada por IA a pantalla completa
  type:SPLIT_LEFT   — Imagen a la izquierda, texto a la derecha
  type:SPLIT_RIGHT  — Texto a la izquierda, imagen a la derecha
  type:VIDEO        — Video de fondo (B-roll)
  type:CONCEPT // Término // Definición larga — Pantalla de concepto animada
  type:LIST // @ Título Fantasma // Elemento 1 // [Nota] // ... — Lista animada 

  <# COMENTARIOS #>  — Todo entre <# y #> será IGNORADO por el sistema.
                     Útil para notas personales o recordatorios.
-->
"""


def detectar_siguiente_proyecto(base: Path) -> str:
    """Detecta automáticamente el siguiente número disponible (01, 02, 03...)."""
    if not base.exists():
        return "01"
    existing = sorted([
        d.name for d in base.iterdir()
        if d.is_dir() and d.name.isdigit()
    ])
    if not existing:
        return "01"
    ultimo = int(existing[-1])
    return f"{ultimo + 1:02d}"


def main():
    parser = argparse.ArgumentParser(description="Crear un nuevo proyecto de video")
    parser.add_argument('-p', '--proyecto', metavar='NUM',
                        help='Nombre o número del proyecto (ej: 02, clase2). '
                             'Se detecta automáticamente si no se indica.')
    args = parser.parse_args()

    repo_root = Path(__file__).parent
    proyectos_base = repo_root / "proyectos"
    proyectos_base.mkdir(exist_ok=True)

    # Determinar nombre del proyecto
    if args.proyecto:
        nombre = args.proyecto
    else:
        nombre = detectar_siguiente_proyecto(proyectos_base)

    project_root = proyectos_base / nombre

    print()
    print("=" * 60)
    print("🆕  CREAR NUEVO PROYECTO — creador-videos-mac")
    print("=" * 60)
    print(f"\n   📂 Carpeta destino: proyectos/{nombre}/")

    # Verificar si ya existe
    if project_root.exists():
        print(f"\n⚠️  El proyecto '{nombre}' ya existe en: {project_root}")
        respuesta = input("   ¿Sobrescribir estructura? (no toca archivos existentes) (s/N): ")
        if respuesta.lower() != 's':
            print("❌ Cancelado.")
            return

    # ── Crear estructura de carpetas ──────────────────────────────────────────
    carpetas = [
        project_root / "assets" / "AUDIO",
        project_root / "assets" / "images",
        project_root / "assets" / "videos",
        project_root / "assets" / "MANIM",
        project_root / "output" / "01_transcripcion",
        project_root / "output" / "02_correccion",
        project_root / "output" / "03_guion",
        project_root / "output" / "04_render",
    ]

    print("\n📁 Creando estructura de carpetas...")
    for carpeta in carpetas:
        carpeta.mkdir(parents=True, exist_ok=True)
        rel = carpeta.relative_to(repo_root)
        print(f"   ✓ {rel}/")

    # ── Generar archivos de plantilla ─────────────────────────────────────────
    print("\n📄 Generando archivos de plantilla...")
    fecha = datetime.now().strftime("%Y-%m-%d")

    config_path = project_root / "video_config.yaml"
    if not config_path.exists():
        config_path.write_text(
            VIDEO_CONFIG_TEMPLATE.format(proyecto=nombre, fecha=fecha),
            encoding='utf-8'
        )
        print(f"   ✓ proyectos/{nombre}/video_config.yaml")
    else:
        print(f"   ⏭  video_config.yaml ya existe, no se sobreescribió")

    speech_path = project_root / "original_speech.md"
    if not speech_path.exists():
        speech_path.write_text(
            ORIGINAL_SPEECH_TEMPLATE.format(proyecto=nombre),
            encoding='utf-8'
        )
        print(f"   ✓ proyectos/{nombre}/original_speech.md")
    else:
        print(f"   ⏭  original_speech.md ya existe, no se sobreescribió")

    # ── Resumen y siguientes pasos ────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"✅  PROYECTO '{nombre}' LISTO")
    print("=" * 60)
    print(f"""
📋 PRÓXIMOS PASOS:

  1. Copia tu audio a:
     proyectos/{nombre}/assets/AUDIO/mi_audio.mp3

  2. Edita la configuración del video:
     proyectos/{nombre}/video_config.yaml
        → Cambia TITLE, MAIN_AUDIO, COVER_NOTES, colores, etc.

  3. Escribe tu guion en:
     proyectos/{nombre}/original_speech.md
        → Usa las etiquetas <!-- type:... --> para controlar las pantallas.

  4. Cuando todo esté listo, ejecuta:
     python 01_preparacion.py -p {nombre}

  5. Genera el video final:
     python 02_generar_video.py -p {nombre}

  6. Al terminar, haz backup y limpia:
     python 00_backup.py -p {nombre}
""")


if __name__ == "__main__":
    main()
