#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_backup.py — Backup y limpieza de un proyecto

Crea un ZIP con todos los archivos generados en deprecated/ y luego
limpia el proyecto para empezar un nuevo video.

Conserva siempre: original_speech.md, video_config.yaml, ai_config.yaml,
                  código fuente (pipeline/, core/, scripts *.py)

Uso:
  python 00_backup.py -p 01           # Backup del proyecto 01
  python 00_backup.py -p 01 -nb       # Solo backup, sin limpiar
"""

import os
import shutil
import zipfile
import glob
from datetime import datetime
from pathlib import Path
import yaml
import argparse
import sys


def format_size(size_bytes):
    if size_bytes == 0: return "0 B"
    names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(names) - 1:
        size_bytes /= 1024.0; i += 1
    return f"{size_bytes:.1f} {names[i]}"


def get_files_recursive(folder_path):
    archivos = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            archivos.append(os.path.join(root, f))
    return archivos


def empty_folder(folder_path):
    """Vacía una carpeta manteniendo su estructura. Retorna nº de archivos eliminados."""
    count = 0
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            for r, _, files in os.walk(item_path):
                count += len(files)
            shutil.rmtree(item_path)
        else:
            count += 1
            os.remove(item_path)
    return count


def get_project_root(proyecto: str) -> Path:
    """Retorna la ruta absoluta del proyecto indicado."""
    base = Path(__file__).parent / "proyectos"
    project_root = base / proyecto
    if not project_root.exists():
        print(f"❌ El proyecto '{proyecto}' no existe: {project_root}")
        sys.exit(1)
    return project_root


def main():
    parser = argparse.ArgumentParser(description="Backup y limpieza del proyecto")
    parser.add_argument('-p', '--proyecto', required=True,
                        metavar='NUM', help='Número o nombre del proyecto (ej: 01, 02)')
    parser.add_argument('-nb', '--no-borrar', action='store_true',
                        help='Hacer backup sin limpiar ni borrar archivos del proyecto')
    args = parser.parse_args()

    project_root = get_project_root(args.proyecto)
    repo_root    = Path(__file__).parent

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deprecated_dir = repo_root / "deprecated"
    deprecated_dir.mkdir(exist_ok=True)
    backup_name = f"backup_p{args.proyecto}_{timestamp}.zip"
    backup_path = deprecated_dir / backup_name

    print(f"🚀 BACKUP Y LIMPIEZA — Proyecto: {args.proyecto}")
    print("=" * 55)
    print(f"   📂 {project_root}")

    archivos_para_backup = []

    # ── Analizar output/ (artefactos generados) ──────────────────────────────
    print("\n📂 Analizando output/...")
    output_path = project_root / "output"
    if output_path.exists():
        for subfolder in sorted(output_path.iterdir()):
            if subfolder.is_dir():
                files = get_files_recursive(subfolder)
                for f in files:
                    rel = os.path.relpath(f, project_root)
                    archivos_para_backup.append((f, rel))
                print(f"   📁 {subfolder.name}/ — {len(files)} archivos")
    else:
        print("   ⚠️  output/ no existe")

    # ── Analizar Configuración Base (ADN del video) ──────────────────────────
    print("\n📂 Analizando configuración base...")
    for f_name in ['original_speech.md', 'video_config.yaml']:
        f_path = project_root / f_name
        if f_path.exists():
            archivos_para_backup.append((str(f_path), f"snapshot_config/{f_name}"))
            print(f"   📄 {f_name} (copia de seguridad para ADN)")
    # ai_config.yaml es compartido en la raíz del repo
    ai_config = repo_root / 'ai_config.yaml'
    if ai_config.exists():
        archivos_para_backup.append((str(ai_config), "snapshot_config/ai_config.yaml"))
        print(f"   📄 ai_config.yaml (compartido)")

    # ── Analizar Audio Principal y recursos (assets) ─────────────────────────
    print("\n📂 Analizando recursos (Audio, Imágenes, Videos)...")
    audio_path = None
    try:
        with open(project_root / 'video_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            audio = config.get('MAIN_AUDIO')
            files_folder = config.get('FILES_FOLDER', 'assets')
            if audio:
                if not os.path.isabs(audio):
                    if files_folder and not (audio.startswith(files_folder + os.sep) or audio.startswith(files_folder + "/")):
                        audio_path = project_root / files_folder / audio
                    else:
                        audio_path = project_root / audio
                else:
                    audio_path = Path(audio)

                if audio_path and audio_path.exists() and audio_path.is_file():
                    archivos_para_backup.append((str(audio_path), os.path.relpath(audio_path, project_root)))
                    print(f"   🎵 Audio detectado: {audio_path.name}")
    except Exception as e:
        print(f"   ⚠️  No se pudo incluir AUDIO específico: {e}")

    # Respaldar el resto de los assets del proyecto
    for folder in ['images', 'videos', 'AUDIO']:
        folder_path = project_root / "assets" / folder
        if folder_path.exists():
            files = get_files_recursive(folder_path)
            for f in files:
                if audio_path and os.path.abspath(f) == os.path.abspath(str(audio_path)):
                    continue
                rel = os.path.relpath(f, project_root)
                archivos_para_backup.append((f, rel))
            print(f"   📁 assets/{folder}/ — {len(files)} archivos")

    # Analizar assets/MANIM/*.py del proyecto
    manim_path = project_root / "assets" / "MANIM"
    manim_py = list(manim_path.glob("*.py")) if manim_path.exists() else []
    if manim_py:
        for f in manim_py:
            archivos_para_backup.append((str(f), os.path.relpath(f, project_root)))
        print(f"   📁 assets/MANIM/*.py — {len(manim_py)} scripts")

    # Analizar video_final.mp4 del proyecto
    for mp4 in project_root.glob("*.mp4"):
        archivos_para_backup.append((str(mp4), os.path.relpath(mp4, project_root)))
        print(f"\n📄 {mp4.name}")

    # ── Resumen ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    total_size = sum(os.path.getsize(f) for f, _ in archivos_para_backup if os.path.exists(f))
    print(f"📊 Total archivos a respaldar: {len(archivos_para_backup)}")
    print(f"💾 Tamaño aproximado:          {format_size(total_size)}")
    print(f"📍 Destino backup:             deprecated/{backup_name}")

    skip_backup = False
    if not archivos_para_backup:
        print("\n⚠️  No hay archivos para respaldar. El proyecto parece limpio.")
        if not args.no_borrar:
            respuesta = input("¿Continuar con la limpieza de todos modos? (s/N): ")
            if respuesta.lower() != 's':
                print("❌ Cancelado"); return
            skip_backup = True
        else:
            print("❌ Cancelado. No hay nada para respaldar y se pidió no borrar (-nb activo)."); return
    else:
        print("\n" + "⚠️  " * 15)
        print("ATENCIÓN: Este proceso:")
        print("  1. 📦 Crea un backup ZIP con recursos y 'ADN' del video actual (guión, config)")
        if not args.no_borrar:
            print("  2. 🧹 Vacía output/, assets/images/, assets/videos/ y el audio principal")
            print("  3. 🗑️  Elimina video_final.mp4 y scripts MANIM de assets/MANIM/")
            print("  4. 🔒 CONSERVA ÍNTEGROS: original_speech.md, video_config.yaml, fuentes y código")
        else:
            print("  2. 🔒 (MODO -nb) Mantiene TODOS los archivos en el proyecto INTACTOS.")
        print("⚠️  " * 15)
        respuesta = input("\n¿Proceder? (s/N): ")
        if respuesta.lower() != 's':
            print("❌ Cancelado"); return

    try:
        # ── Crear backup ─────────────────────────────────────────────────────
        if not skip_backup:
            print(f"\n📦 CREANDO BACKUP...")
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, (file_path, zip_path) in enumerate(archivos_para_backup, 1):
                    try:
                        zipf.write(file_path, zip_path)
                        print(f"   ✅ [{i:3d}/{len(archivos_para_backup)}] {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"   ❌ Error: {os.path.basename(file_path)}: {e}")
            print(f"\n✅ Backup creado: {backup_name}")

        # ── Limpiar ───────────────────────────────────────────────────────────
        if not args.no_borrar:
            print("\n🧹 LIMPIANDO...")

            # Vaciar subcarpetas de output/
            if output_path.exists():
                for subfolder in output_path.iterdir():
                    if subfolder.is_dir():
                        n = empty_folder(subfolder)
                        print(f"   🧹 output/{subfolder.name}/ — {n} archivos eliminados")

            # Vaciar assets/images, assets/videos y assets/AUDIO del proyecto
            for folder in ['images', 'videos', 'AUDIO']:
                folder_path = project_root / "assets" / folder
                if folder_path.exists():
                    n = empty_folder(folder_path)
                    if n > 0:
                        print(f"   🧹 assets/{folder}/ — {n} archivos eliminados")

            # Eliminar el archivo de audio principal
            if audio_path and audio_path.exists() and audio_path.is_file():
                try:
                    os.remove(audio_path)
                    print(f"   🧹 Audio principal eliminado: {audio_path.name}")
                except Exception:
                    pass

            # Eliminar scripts MANIM del proyecto
            for f in manim_py:
                os.remove(f)
                print(f"   🗑️  {f.name} eliminado")

            # Eliminar videos finales del proyecto
            for mp4 in project_root.glob("*.mp4"):
                os.remove(mp4)
                print(f"   🗑️  {mp4.name} eliminado")

            # Eliminar tmp de MANIM si existe
            manim_media = project_root / "assets" / "MANIM" / "media"
            if manim_media.exists():
                shutil.rmtree(manim_media)
                print("   🗑️  assets/MANIM/media/ eliminada")

            print("\n🎉 ¡LISTO! Proyecto limpio para nuevo video.")
        else:
            print("\n🎉 ¡LISTO! Backup completado. No se eliminaron archivos (-nb activo).")
        print(f"📦 Backup en: deprecated/{backup_name}")
        print("🔒 original_speech.md y video_config.yaml conservados en el proyecto.")

    except Exception as e:
        print(f"❌ Error durante la operación: {e}")


if __name__ == "__main__":
    main()
