#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_preparacion.py — Pipeline completo de preparación de video

Fases automáticas (con caché inteligente):
  1. Transcripción local con WhisperX
  2. Corrección ortográfica con OpenAI (spell checker)
  3a. Alineación de segmentos + generación de guion base
  3b. Enriquecimiento visual con OpenAI (Visual Orchestrator)
  3c. Generación automática de recursos dummy

Uso:
  python 01_preparacion.py -p 01                  # Proyecto 01, pipeline completo
  python 01_preparacion.py -p 01 --desde-fase 2   # Saltar Whisper
  python 01_preparacion.py -p 01 --desde-fase 3   # Solo guion + visuales + dummies
  python 01_preparacion.py -p 01 --forzar         # Ignorar caché, re-ejecutar todo
"""

import os
import sys
import re
import yaml
import argparse
from pathlib import Path


def get_project_root(proyecto: str) -> Path:
    """Retorna la ruta absoluta de la carpeta del proyecto indicado."""
    base = Path(__file__).parent / "proyectos"
    project_root = base / proyecto
    if not project_root.exists():
        print(f"❌ El proyecto '{proyecto}' no existe: {project_root}")
        print(f"   Crea la carpeta y coloca original_speech.md y video_config.yaml dentro.")
        sys.exit(1)
    return project_root


# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_bloques(filepath: Path):
    """Lee un archivo de subtítulos con timestamps y retorna lista de bloques."""
    bloques = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r"\[(\d+\.\d+)\s*-\s*(\d+\.\d+)\]:\s*(.+)$", line.strip())
            if m:
                bloques.append({
                    "start": float(m.group(1)),
                    "end":   float(m.group(2)),
                    "text":  m.group(3).strip()
                })
    return bloques


def crear_dirs(root: Path, out_transcripcion, out_correccion, out_guion):
    for d in [out_transcripcion, out_correccion, out_guion]:
        d.mkdir(parents=True, exist_ok=True)


def cargar_audio(root: Path):
    """Lee el audio principal de video_config.yaml de forma robusta."""
    config_path = root / 'video_config.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        audio = config.get('MAIN_AUDIO')
        files_folder = config.get('FILES_FOLDER', 'assets')

        if not audio:
            print("❌ MAIN_AUDIO no encontrado en video_config.yaml")
            sys.exit(1)

        # Resolver ruta relativa al root del proyecto
        if not os.path.isabs(audio):
            # Evitar duplicados como assets/assets/
            if files_folder and not (audio.startswith(files_folder + os.sep) or audio.startswith(files_folder + "/")):
                audio_path = root / files_folder / audio
            else:
                audio_path = root / audio
        else:
            audio_path = Path(audio)

        return str(audio_path)
    except Exception as e:
        print(f"❌ Error leyendo video_config.yaml: {e}")
        sys.exit(1)


# ── Pipeline ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Pipeline de preparación de video")
    parser.add_argument('-p', '--proyecto', required=True,
                        metavar='NUM', help='Número o nombre del proyecto (ej: 01, 02)')
    parser.add_argument('--desde-fase', type=int, default=1, choices=[1, 2, 3],
                        metavar='N', help='Empezar desde fase N (1=Whisper, 2=Corrección, 3=Guion)')
    parser.add_argument('--forzar', action='store_true',
                        help='Ignorar caché y re-ejecutar todo desde la fase indicada')
    args = parser.parse_args()

    PROJECT_ROOT = get_project_root(args.proyecto)

    # ── Rutas de output ──────────────────────────────────────────────────────
    OUT_TRANSCRIPCION  = PROJECT_ROOT / "output/01_transcripcion"
    OUT_CORRECCION     = PROJECT_ROOT / "output/02_correccion"
    OUT_GUION          = PROJECT_ROOT / "output/03_guion"
    SUBTITULOS_CRUDO   = OUT_TRANSCRIPCION / "subtitulos_formato_personalizado.txt"
    SUBTITULOS_CORREGIDO = OUT_CORRECCION  / "subtitulos_corregido.txt"
    GUION_BASE         = OUT_GUION / "guion_base.txt"
    GUION_CONSOLIDADO  = OUT_GUION / "guion_consolidado.txt"
    ORIGINAL_SPEECH    = PROJECT_ROOT / "original_speech.md"

    print("=" * 60)
    print(f"🚀  PIPELINE DE PREPARACIÓN — Proyecto: {args.proyecto}")
    print(f"   📂 {PROJECT_ROOT}")
    print("=" * 60)

    crear_dirs(PROJECT_ROOT, OUT_TRANSCRIPCION, OUT_CORRECCION, OUT_GUION)

    if not ORIGINAL_SPEECH.exists():
        print(f"❌ '{ORIGINAL_SPEECH}' no encontrado. Colócalo en proyectos/{args.proyecto}/")
        sys.exit(1)

    audio_file = cargar_audio(PROJECT_ROOT)
    bloques_corregidos = []

    # Cambiar directorio de trabajo al proyecto para imports relativos
    original_cwd = os.getcwd()
    os.chdir(PROJECT_ROOT)

    try:
        # ── FASE 1: Transcripción (WhisperX) ──────────────────────────────────
        fase1_hecha = SUBTITULOS_CRUDO.exists() and not args.forzar
        if args.desde_fase <= 1 and not fase1_hecha:
            print("\n🎙️  FASE 1: Transcripción con WhisperX...")
            os.chdir(original_cwd)
            from pipeline.whisper_engine import WhisperAnalyzer
            os.chdir(PROJECT_ROOT)
            bloques_crudos = WhisperAnalyzer().transcribir(audio_file, output_dir=str(OUT_TRANSCRIPCION))
        elif SUBTITULOS_CRUDO.exists():
            print("\n⚡ [CACHÉ] Fase 1 — Texto crudo encontrado, cargando desde disco.")
            bloques_crudos = parse_bloques(SUBTITULOS_CRUDO)
        else:
            print("❌ No hay texto crudo. Ejecuta desde --desde-fase 1")
            sys.exit(1)

        # ── FASE 2: Corrección ortográfica (OpenAI) ───────────────────────────
        fase2_hecha = SUBTITULOS_CORREGIDO.exists() and not args.forzar
        if args.desde_fase <= 2 and not fase2_hecha:
            print("\n✏️  FASE 2: Corrección ortográfica (OpenAI)...")
            os.chdir(original_cwd)
            from pipeline.spell_checker import CorrectorOrtografia
            os.chdir(PROJECT_ROOT)
            bloques_corregidos = CorrectorOrtografia().corregir_memoria(
                bloques_crudos, str(ORIGINAL_SPEECH), output_dir=str(OUT_CORRECCION)
            )
        elif SUBTITULOS_CORREGIDO.exists():
            print("\n⚡ [CACHÉ] Fase 2 — Texto corregido encontrado, cargando desde disco.")
            bloques_corregidos = parse_bloques(SUBTITULOS_CORREGIDO)
        else:
            print("❌ No hay texto corregido. Ejecuta desde --desde-fase 2 o 1")
            sys.exit(1)

        # ── FASE 3a: Alineación + Guion Base ──────────────────────────────────
        print("\n🔍 FASE 3a: Alineando segmentos con guion original...")
        os.chdir(original_cwd)
        from pipeline.aligner import SegmentAligner
        from pipeline.formatter import GuionFormatter
        os.chdir(PROJECT_ROOT)
        with open(ORIGINAL_SPEECH, 'r', encoding='utf-8') as f:
            original_text = f.read()
        segmentos = SegmentAligner().alinear(bloques_corregidos, original_text)
        GuionFormatter().exportar(segmentos, str(GUION_BASE))

        # ── FASE 3b: Enriquecimiento Visual (OpenAI) ──────────────────────────
        print("\n🧠 FASE 3b: Generando arquitectura visual (OpenAI)...")
        os.chdir(original_cwd)
        from pipeline.visual_orchestrator import VisualOrchestrator
        os.chdir(PROJECT_ROOT)
        VisualOrchestrator(
            input_file=str(GUION_BASE),
            output_dir=str(OUT_GUION),
            project_root=str(PROJECT_ROOT)
        ).procesar_guion()

        # ── FASE 3c: Recursos Dummy ────────────────────────────────────────────
        print("\n🎬 FASE 3c: Generando recursos dummy...")
        os.chdir(original_cwd)
        from pipeline.dummy_builder import crear_recursos_dummies
        os.chdir(PROJECT_ROOT)
        crear_recursos_dummies(
            json_path=OUT_GUION / "recursos_visuales.json",
            assets_root=str(PROJECT_ROOT / "assets")
        )

    finally:
        os.chdir(original_cwd)

    print("\n" + "=" * 60)
    print("✅  PREPARACIÓN COMPLETA")
    print(f"   Guion consolidado → {GUION_CONSOLIDADO}")
    print(f"   Ahora ejecuta: python 02_generar_video.py -p {args.proyecto}")
    print("=" * 60)


if __name__ == "__main__":
    main()
