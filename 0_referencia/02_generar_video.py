#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_generar_video.py — Render final del video con FFmpeg

Lee el guion consolidado de output/03_guion/ dentro del proyecto indicado
y genera video_final.mp4 en la carpeta de ese proyecto.

Uso:
  python 02_generar_video.py -p 01
  python 02_generar_video.py -p 01 --debug
"""

import os
import sys
import shutil
import yaml
import argparse
from pathlib import Path

# ── Importar módulos del core (siempre relativos a la raíz del repo) ──────────
sys.path.insert(0, str(Path(__file__).parent))
from core.utils import (inicializar_carpeta_temporal, parsear_guion_nuevo,
                        get_audio_sample_rate, get_audio_channels,
                        verificar_recursos_pre_render)
from core.ass_builder import generar_subtitulos_ass
from core.video_engine import crear_video_mixto, procesar_portada


def get_project_root(proyecto: str) -> Path:
    """Retorna la ruta absoluta del proyecto indicado."""
    base = Path(__file__).parent / "proyectos"
    project_root = base / proyecto
    if not project_root.exists():
        print(f"❌ El proyecto '{proyecto}' no existe: {project_root}")
        print(f"   Crea la carpeta y coloca original_speech.md y video_config.yaml dentro.")
        sys.exit(1)
    return project_root


def main():
    parser = argparse.ArgumentParser(description="Generador de video final")
    parser.add_argument('-p', '--proyecto', required=True,
                        metavar='NUM', help='Número o nombre del proyecto (ej: 01, 02)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Activa modo debug (tiempos en pantalla)')
    args = parser.parse_args()

    PROJECT_ROOT = get_project_root(args.proyecto)

    # Rutas relativas al proyecto
    GUION_CONSOLIDADO_DEFAULT = str(PROJECT_ROOT / "output/03_guion/guion_consolidado.txt")
    TMP_DIR_NAME              = str(PROJECT_ROOT / "output/04_render")
    OUTPUT_FINAL              = str(PROJECT_ROOT / "video_final.mp4")

    if args.debug:
        print("=" * 50 + "\n⚠  MODO DEBUG ACTIVADO\n" + "=" * 50)

    print("=" * 60)
    print(f"🎬  GENERANDO VIDEO FINAL — Proyecto: {args.proyecto}")
    print(f"   📂 {PROJECT_ROOT}")
    print("=" * 60)

    # ── Cargar configuración ──────────────────────────────────────────────────
    print("\n📁 Cargando configuración...")
    config_path = PROJECT_ROOT / 'video_config.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            video_config = yaml.safe_load(f)
        print("✓ video_config.yaml cargado")
    except Exception as e:
        print(f"❌ Error cargando {config_path}: {e}")
        sys.exit(1)

    TMP_DIR = inicializar_carpeta_temporal(TMP_DIR_NAME)

    # ── Guion ─────────────────────────────────────────────────────────────────
    guion_from_config = video_config.get('GUION_COMPLETO')
    if guion_from_config and not os.path.isabs(guion_from_config):
        RUTA_GUION = str(PROJECT_ROOT / guion_from_config)
    elif guion_from_config:
        RUTA_GUION = guion_from_config
    else:
        RUTA_GUION = GUION_CONSOLIDADO_DEFAULT

    if not os.path.exists(RUTA_GUION):
        if os.path.exists(GUION_CONSOLIDADO_DEFAULT):
            RUTA_GUION = GUION_CONSOLIDADO_DEFAULT
        else:
            print(f"❌ Guion no encontrado: {RUTA_GUION}")
            print(f"   Ejecuta primero: python 01_preparacion.py -p {args.proyecto}")
            sys.exit(1)
    print(f"📝 Guion: {RUTA_GUION}")

    # ── Audio ─────────────────────────────────────────────────────────────────
    AUDIO_RAW = video_config.get('MAIN_AUDIO')
    if not AUDIO_RAW:
        print("❌ MAIN_AUDIO no encontrado en video_config.yaml")
        sys.exit(1)

    # Resolver ruta del audio relativa al proyecto
    files_folder = video_config.get('FILES_FOLDER', 'assets')
    if not os.path.isabs(AUDIO_RAW):
        if files_folder and not (AUDIO_RAW.startswith(files_folder + os.sep) or AUDIO_RAW.startswith(files_folder + "/")):
            AUDIO_MP3 = str(PROJECT_ROOT / files_folder / AUDIO_RAW)
        else:
            AUDIO_MP3 = str(PROJECT_ROOT / AUDIO_RAW)
    else:
        AUDIO_MP3 = AUDIO_RAW
    print(f"🎵 Audio: {AUDIO_MP3}")

    meta, styles, cover, segs = parsear_guion_nuevo(RUTA_GUION)

    # FILES_FOLDER resuelto como absoluto para el render
    meta_files_folder = meta.get("FILES_FOLDER", files_folder)
    if meta_files_folder and not os.path.isabs(meta_files_folder):
        abs_files_folder = str(PROJECT_ROOT / meta_files_folder)
    else:
        abs_files_folder = meta_files_folder or str(PROJECT_ROOT / "assets")

    print("\n🔍 Check Pre-Render de recursos...")
    cover_file = cover.get("ASSET")
    if not verificar_recursos_pre_render(AUDIO_MP3, cover_file, segs, abs_files_folder):
        sys.exit(1)
    print("✅ Check superado.")

    sample_rate = get_audio_sample_rate(AUDIO_MP3)
    channels    = get_audio_channels(AUDIO_MP3)

    if cover_file:
        meta["FILE"] = cover_file

    cfg = {
        "FPS":               meta.get("FPS", "30"),
        "RESOLUTION":        meta.get("RESOLUTION", "1920x1080"),
        "MAIN_FONT":         meta.get("MAIN_FONT", "Helvetica"),
        "BACKGROUND_COLOR":  meta.get("BACKGROUND_COLOR", "#FFFFFF"),
        "MAIN_TEXT_COLOR":   meta.get("MAIN_TEXT_COLOR", "#000000"),
        "FILES_FOLDER":      abs_files_folder,
        "USE_TRANSITIONS":   str(meta.get("USE_TRANSITIONS",
                                 video_config.get("USE_TRANSITIONS", False))).lower() in ('true','1','yes'),
        "TRANSITION_DURATION": float(meta.get("TRANSITION_DURATION",
                                     video_config.get("TRANSITION_DURATION", 0.5)))
    }

    # Cambiar al directorio del proyecto para que las rutas relativas en el core funcionen
    original_cwd = os.getcwd()
    os.chdir(PROJECT_ROOT)

    OUT_ASS   = "output/04_render/subtitulos.ass"
    OUT_VIDEO = "output/04_render/video_sin_portada.mp4"

    try:
        generar_subtitulos_ass(meta, styles, segs, OUT_ASS, debug_mode=args.debug)
        crear_video_mixto(AUDIO_MP3, OUT_ASS, segs, cfg, OUT_VIDEO, sample_rate, channels, TMP_DIR)
        raw_final = procesar_portada(meta, OUT_VIDEO, cfg, sample_rate, channels, TMP_DIR, debug_mode=args.debug)

        # ── Renombrar y mover output mientras estamos en PROJECT_ROOT ──────────
        if raw_final and os.path.exists(raw_final):
            # Si el nombre es distinto al final deseado, lo movemos/renombramos
            if os.path.abspath(raw_final) != os.path.abspath(str(Path(OUTPUT_FINAL).name)):
                shutil.move(raw_final, Path(OUTPUT_FINAL).name)
            final_path = os.path.abspath(Path(OUTPUT_FINAL).name)
        else:
            final_path = raw_final
    finally:
        os.chdir(original_cwd)

    print(f"\n{'='*60}")
    print(f"✅ VIDEO LISTO: {final_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
