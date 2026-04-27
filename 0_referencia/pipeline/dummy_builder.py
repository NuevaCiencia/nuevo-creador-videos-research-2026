#!/usr/bin/env python3
"""
dummy_builder.py — Generador de recursos dummy/placeholder

Crea archivos placeholder (imágenes y videos etiquetados) para pruebas
del sistema automatizado de videos. Lee la lista de recursos del JSON
generado por visual_orchestrator.py.
"""

import json
import os
import subprocess
from pathlib import Path

from core.font_resolver import get_resolver


def _get_root():
    return Path(__file__).parent.parent


def _crear_frame_pillow(w, h, texto, font_size, output_path):
    """Genera un frame PNG con texto centrado usando Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    root = _get_root()
    fr = get_resolver(base_dir=str(root))
    font_path = fr.get_font_path("regular")

    img = Image.new("RGB", (w, h), color=(180, 180, 180))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    try:
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(texto, font=font)

    x = (w - tw) // 2
    y = (h - th) // 2
    draw.text((x, y), texto, fill=(51, 51, 51), font=font)
    img.save(str(output_path))
    return True


def _generar_dummy(tipo, nombre, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_str = str(output_path)

    if tipo == "imagen_split":
        return _crear_frame_pillow(960, 1080, f"960x1080  {nombre}", 60, output_path)

    elif tipo == "imagen_completa":
        return _crear_frame_pillow(1920, 1080, f"1920x1080  {nombre}", 100, output_path)

    elif tipo in ("video", "portada"):
        if tipo == "portada":
            texto = "PORTADA"
        elif nombre.startswith("REM"):
            texto = f"REMOTION  {nombre}"
        else:
            texto = f"VIDEO  {nombre}"
        frame_tmp = output_path.parent / f"_tmp_frame_{nombre}.png"
        try:
            if not _crear_frame_pillow(1920, 1080, texto, 100, frame_tmp):
                return False
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(frame_tmp),
                "-t", "10", "-r", "1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                out_str
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception as e:
            print(f"❌ ERROR generando dummy '{nombre}' con FFmpeg: {e}")
            return False
        finally:
            if frame_tmp.exists():
                frame_tmp.unlink()
    else:
        return False


def crear_recursos_dummies(json_path=None, assets_root=None):
    print("🎬 CREADOR DE RECURSOS DUMMIES (GENERADOR DINÁMICO INTELIGENTE)")
    print("=" * 50)

    root = _get_root()
    if json_path is None:
        json_path = root / "output" / "03_guion" / "recursos_visuales.json"
    json_path = Path(json_path)

    # assets_root: carpeta assets/ del proyecto activo
    # Si no se indica, fallback a la raíz del repo
    if assets_root is not None:
        assets_path = Path(assets_root)
    else:
        assets_path = root / "assets"

    images_path  = assets_path / "images"
    videos_path  = assets_path / "videos"
    images_path.mkdir(parents=True, exist_ok=True)
    videos_path.mkdir(parents=True, exist_ok=True)

    print("⚙️  Generando Dummies etiquetados...")

    # Portada siempre generada
    portada_destino = videos_path / "portada.mp4"
    if _generar_dummy("portada", "portada.mp4", portada_destino):
        print("🎬 PORTADA | portada.mp4 <- Generada | [COVER]")

    if not json_path.exists():
        print(f"❌ No se encontró {json_path}")
        print("💡 Solo se inyectó la Portada obligatoria.")
        return False

    print(f"📂 Extrayendo recursos de: {json_path}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        recursos = data.get('recursos', [])
        print(f"📊 Total de recursos a poblar: {len(recursos)}\n")

        imagenes_split = imagenes_full = videos_creados = errores = 0

        for recurso in recursos:
            nombre = recurso.get('nombre', '')
            tipo   = recurso.get('tipo', '')
            segmento = recurso.get('segmento', '')

            if tipo == 'imagen_split':
                if _generar_dummy(tipo, nombre, images_path / nombre):
                    print(f"🖼️  SPLIT   | {nombre} (960x1080) | [{segmento}]")
                    imagenes_split += 1
                else:
                    errores += 1
            elif tipo == 'imagen_completa':
                if _generar_dummy(tipo, nombre, images_path / nombre):
                    print(f"🖼️  FULL    | {nombre} (1920x1080) | [{segmento}]")
                    imagenes_full += 1
                else:
                    errores += 1
            elif tipo == 'video':
                if _generar_dummy(tipo, nombre, videos_path / nombre):
                    print(f"🎥 VIDEO   | {nombre} | [{segmento}]")
                    videos_creados += 1
                else:
                    errores += 1
            else:
                print(f"⚠️  DESCONOCIDO: {nombre} (tipo: {tipo})")

        print("\n📈 RESUMEN:")
        print(f"   🖼️  Imágenes Split: {imagenes_split}")
        print(f"   🖼️  Imágenes Full:  {imagenes_full}")
        print(f"   🎥 Videos Dummies:  {videos_creados}")
        print(f"   🎬 Portadas:        1")
        print(f"   ❌ Errores:         {errores}")

        if errores == 0:
            print("\n✅ ¡POBLACIÓN DUMMY COMPLETADA CON ÉXITO!")
            return True
        return False

    except json.JSONDecodeError:
        print("❌ El archivo JSON está malformado")
        return False
    except Exception as e:
        print(f"❌ ERROR GENERAL: {str(e)}")
        return False
