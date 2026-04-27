#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_generar_partes_audio.py — Utilidad para extraer las partes de audio exactas 
basadas en la especificación de output/03_guion/videos.md.
"""

import os
import argparse
import re
import yaml
import subprocess
import shutil

def parse_args():
    parser = argparse.ArgumentParser(description="Extrae las secuencias de audio para los clips especificados en videos.md.")
    parser.add_argument("-p", "--proyecto", required=True, help="Nombre del proyecto (ej: 01_final)")
    return parser.parse_args()

def main():
    args = parse_args()
    project_dir = os.path.join("proyectos", args.proyecto)
    
    if not os.path.isdir(project_dir):
        print(f"Error: No se encontró el proyecto en {project_dir}")
        return

    # 1. Leer el archivo de configuración para obtener el audio principal
    config_path = os.path.join(project_dir, "video_config.yaml")
    if not os.path.isfile(config_path):
        print(f"Error: No se encontró {config_path}")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    main_audio_rel = config.get("MAIN_AUDIO", "")
    if not main_audio_rel:
        print("Error: No se definió MAIN_AUDIO en video_config.yaml")
        return
        
    main_audio_path = os.path.join(project_dir, main_audio_rel)
    if not os.path.isfile(main_audio_path):
        print(f"Error: No se encontró el audio principal en {main_audio_path}")
        return
        
    print(f"✅ Audio principal detectado: {main_audio_path}")

    # 2. Leer videos.md para extraer los segmentos
    videos_md_path = os.path.join(project_dir, "output", "03_guion", "videos.md")
    if not os.path.isfile(videos_md_path):
        print(f"Error: No se encontró el archivo de segmentos en {videos_md_path}")
        return

    with open(videos_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'### ', content)[1:]  # Separar por el marcador de titulo
    
    segments = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        title_line = lines[0].strip()
        
        # Omitimos cosas que no sean mp4 si hay, usualmente son V001.mp4 o REM01.mp4
        if not title_line.endswith(".mp4"):
            continue
            
        base_name = title_line.replace(".mp4", "") # ej V001
        
        start_time = None
        duration = None
        
        for line in lines[1:]:
            if "- **Segmento:**" in line:
                match = re.search(r'\[(.*?)\]', line)
                if match:
                    start_time = match.group(1).strip()
            elif "- **Duración:**" in line:
                match = re.search(r'([\d\.]+)\s*segundos', line)
                if match:
                    duration = match.group(1).strip()
                    
        if start_time is not None and duration is not None:
            segments.append({
                "name": base_name,
                "start": start_time,
                "duration": duration
            })
            
    if not segments:
        print("No se extrajeron segmentos de audio de videos.md.")
        return
        
    print(f"📊 Se encontraron {len(segments)} segmentos para extraer.")

    # 3. Extraer partes de audio
    audio_output_dir = os.path.join(project_dir, "assets", "AUDIO")
    os.makedirs(audio_output_dir, exist_ok=True)
    
    # Verificar ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        if os.path.exists("/opt/homebrew/bin/ffmpeg"):
            ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
        else:
            print("❌ Error: no se encontró 'ffmpeg' en el sistema.")
            return

    for i, seg in enumerate(segments):
        output_file = os.path.join(audio_output_dir, f"{seg['name']}.mp3")
        print(f"\n[{i+1}/{len(segments)}] Generando {seg['name']}.mp3 ...")
        print(f"    Inicio: {seg['start']}, Duración: {seg['duration']}s")
        
        cmd = [
            ffmpeg_path, "-y", "-i", main_audio_path,
            "-ss", seg["start"],
            "-t", seg["duration"],
            # Copiar codecs si no hay transcodificacion, sino forzar libmp3lame
            "-c:a", "libmp3lame", 
            "-q:a", "2", # Buena calidad (VBR)
            output_file
        ]
        
        try:
            # Ejecutar silenciosamente
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print(f"    ✅ Guardado: {output_file}")
            else:
                print(f"    ❌ Error al generar {output_file}")
                print(result.stderr)
        except Exception as e:
            print(f"    ❌ Excepción: {e}")

    print("\n🎉 Extracción completada.")

if __name__ == "__main__":
    main()
