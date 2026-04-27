import os
import re
import shutil
import colorsys
import subprocess
from pymediainfo import MediaInfo

def segundos_a_srt(segundos: float) -> str:
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    ms = int(round((segundos - int(segundos)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def segundos_a_ass(segundos: float) -> str:
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    cs = int(round((segundos - int(segundos)) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def segundos_a_mmss(segundos: float) -> str:
    m = int(segundos // 60)
    s = segundos % 60
    return f"{m:02d}:{s:05.2f}"

def redondear_tiempo(segundos: float) -> float:
    return round(segundos, 2)

def generar_color_por_intensidad(i, total, base_hue=0.6):
    inten = 0.2 + 0.5 * (i / total)
    sat   = 0.6 + 0.3 * (i / total)
    r, g, b = colorsys.hsv_to_rgb(base_hue, sat, inten)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def hex_a_ass_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"
    return "&H00000000"

def limpiar_override(text):
    return re.sub(r"^(?:\{[^}]*\})+", "", text).strip()

def wrap_text(text, max_chars):
    words = text.split()
    if not words:
        return text
    lines, cur = [], words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= max_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return "\\N".join(lines)

def inicializar_carpeta_temporal(nombre="tmp_vid"):
    if os.path.exists(nombre):
        shutil.rmtree(nombre)
    os.makedirs(nombre, exist_ok=True)
    return nombre

def normalizar_ruta_ffmpeg(ruta):
    return ruta.replace('\\', '/')

def get_audio_sample_rate(path: str) -> int:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "default=nokey=1:noprint_wrappers=1", path]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else 44100

def get_audio_channels(path: str) -> int:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "default=nokey=1:noprint_wrappers=1", path]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else 2

def get_audio_duration(path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration", "-of", "default=nokey=1:noprint_wrappers=1", path]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    return float(out) if out else 180.0

def get_video_duration(path: str) -> float:
    info = MediaInfo.parse(path)
    for t in info.tracks:
        if t.track_type == "Video":
            return (t.duration or 0) / 1000
    return 0.0

def parsear_guion_nuevo(ruta_guion):
    meta, styles, cover, segments = {}, {}, {}, []
    cur_section, cur_seg = None, None
    if not os.path.exists(ruta_guion):
        raise FileNotFoundError(f"El guion '{ruta_guion}' no existe")
    with open(ruta_guion, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(("###", "///")):
                continue
            up = line.upper()
            if up.startswith("#META"):
                cur_section = "META";  continue
            if up.startswith("#STYLES"):
                cur_section = "STYLES"; continue
            if up.startswith("#COVER"):
                cur_section = "COVER";  continue
            if up.startswith("#SEGMENT"):
                cur_section = "SEGMENT"
                m = re.search(r"\[(\d+):(\d+)(?:\.(\d+))?\]", line)
                if m:
                    minutes, seconds = int(m.group(1)), int(m.group(2))
                    decimal_part = m.group(3)
                    if decimal_part:
                        seconds += float(f"0.{decimal_part}")
                    start = redondear_tiempo(minutes * 60 + seconds)
                else:
                    start = 0
                cur_seg = {"tiempo_inicio": start}
                segments.append(cur_seg)
                continue
            if '=' not in line: continue
            k, v = map(str.strip, line.split('=', 1))
            if cur_section == "META": meta[k.upper()] = v
            elif cur_section == "STYLES": styles[k.upper()] = v.strip('{}')
            elif cur_section == "COVER": cover[k.upper()] = v
            elif cur_section == "SEGMENT" and cur_seg is not None: cur_seg[k.upper()] = v
    return meta, styles, cover, segments

def verificar_recursos_pre_render(audio_path, cover_file, segments, files_folder):
    faltantes = []
    if audio_path and not os.path.exists(audio_path):
        faltantes.append(f"[AUDIO_MP3]: {audio_path}")
        
    if cover_file:
        ruta_cover = cover_file
        if files_folder and not os.path.isabs(ruta_cover):
            ruta_cover = os.path.join(files_folder, ruta_cover)
        if not os.path.exists(ruta_cover):
            faltantes.append(f"[COVER]: {ruta_cover}")
            
    for seg in segments:
        asset = seg.get("ASSET")
        if not asset or seg.get("TYPE", "").upper() == "COVER" or asset == "DYNAMIC_GENERATED": continue
        ruta_asset = asset
        if files_folder and not os.path.isabs(ruta_asset):
            ruta_asset = os.path.join(files_folder, ruta_asset)
        if not os.path.exists(ruta_asset):
            faltantes.append(f"[SEGMENT {seg.get('tiempo_inicio', '0.0')}s]: {ruta_asset}")
            
    if faltantes:
        print("\n" + "="*50)
        print("❌ ERROR DE PRERENDER: ARCHIVOS FALTANTES")
        print("="*50)
        print("El motor ha detenido la ejecución porque los siguientes recursos no se encuentran en disco:\n")
        for f in faltantes:
            print(f"  - {f}")
        print("\nPor favor, asegúrate de que existen o corrige los nombres en el guion antes de continuar.")
        return False
    return True
