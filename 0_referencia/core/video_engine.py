import os
import subprocess
import shutil
from .utils import get_audio_duration, normalizar_ruta_ffmpeg, redondear_tiempo
from .ffmpeg_builder import construir_filtro_ffmpeg
from .font_resolver import get_resolver

def crear_video_mixto(audio_path, ass_path, segments, cfg, out_path, sample_rate, channels, tmp_dir):
    print("Creando video…")
    dur_audio = get_audio_duration(audio_path)
    ass_path_ffmpeg = normalizar_ruta_ffmpeg(ass_path)

    norm_audio = os.path.join(tmp_dir, "audio_normalizado.wav")
    subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary", "-ar", str(sample_rate), "-ac", str(channels), "-acodec", "pcm_s16le", normalizar_ruta_ffmpeg(norm_audio)], check=True)

    bg_color = cfg["BACKGROUND_COLOR"].lstrip('#')
    fondo = os.path.join(tmp_dir, "fondo.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=0x{bg_color}:s={cfg['RESOLUTION']}:r={cfg['FPS']}:d={dur_audio}", "-c:v", "libx264", "-pix_fmt", "yuv420p", normalizar_ruta_ffmpeg(fondo)], check=True)

    recursos = []
    files_folder = cfg.get("FILES_FOLDER", "")
    if files_folder and not os.path.isabs(files_folder): files_folder = os.path.abspath(files_folder)

    for seg in segments:
        asset = seg.get("ASSET")
        if not asset or seg.get("TYPE","").upper()=="COVER": continue
        
        if asset == "DYNAMIC_GENERATED":
            asset = os.path.join(tmp_dir, f"dynamic_{str(seg['tiempo_inicio']).replace('.','_')}.mp4")
            if not os.path.exists(asset): # Avoid regenerating if doing debug loops
                from .dynamic_animator import generate_dynamic_video
                subtitulos_path = "output/01_transcripcion/subtitulos_formato_personalizado.txt"
                generate_dynamic_video(seg, cfg, asset, subtitulos_path, tmp_dir)
        else:
            if files_folder and not os.path.isabs(asset): asset = os.path.join(files_folder, asset)
            if not os.path.exists(asset): raise FileNotFoundError(f"Recurso no encontrado: {asset}")
        
        ini = redondear_tiempo(seg["tiempo_inicio"])
        dur = redondear_tiempo(float(seg.get("TIME", "0")))
        fin = redondear_tiempo(ini + dur)
        recursos.append({
            "ini": ini, "dur": dur, "fin": fin,
            "ruta": asset, "ruta_ffmpeg": normalizar_ruta_ffmpeg(asset),
            "tipo": "video" if (seg.get("TYPE","").upper() in ("VIDEO", "CONCEPT", "LIST") or asset.endswith('.mp4')) else "img",
            "pos": ("COMPLETA" if seg.get("TYPE","").upper() in ("FULL_IMAGE","COVER","CONCEPT","LIST") else "IZQUIERDA" if seg.get("TYPE","").upper()=="SPLIT_LEFT" else "DERECHA")
        })
    recursos.sort(key=lambda r: r["ini"])

    if not recursos:
        # Construir filtro ass con fontsdir para tipografía embebida
        fr = get_resolver()
        ass_filter = f"ass={ass_path_ffmpeg}{fr.get_fontsdir_arg()}"
        subprocess.run(["ffmpeg", "-y", "-i", fondo, "-i", norm_audio, "-vf", ass_filter, "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-shortest", out_path], check=True)
        return True

    filtro_txt = os.path.join(tmp_dir, "filtro.txt")
    filtro_txt_ffmpeg = normalizar_ruta_ffmpeg(filtro_txt)
    W, H = map(int, cfg["RESOLUTION"].split('x'))
    
    construir_filtro_ffmpeg(recursos, W, H, cfg["FPS"], ass_path_ffmpeg, filtro_txt,
                            use_trans=cfg.get("USE_TRANSITIONS", False),
                            dur_t=cfg.get("TRANSITION_DURATION", 0.5),
                            fontsdir_arg=get_resolver().get_fontsdir_arg())

    cmd = ["ffmpeg", "-y", "-i", fondo]
    for r in recursos:
        if r["tipo"] == "img": cmd += ["-loop", "1", "-t", str(r["dur"]), "-i", r["ruta"]]
        else: cmd += ["-i", r["ruta"]]
            
    cmd += ["-i", norm_audio, "-filter_complex_script", filtro_txt_ffmpeg, "-map", "[vout]", "-map", f"{len(recursos)+1}:a", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-vsync", "cfr", "-shortest", out_path]
    subprocess.run(cmd, check=True)
    return True

def procesar_portada(meta, body_path, cfg, sample_rate, channels, tmp_dir, debug_mode=False):
    port_file = meta.get("FILE")
    if not port_file:
        if debug_mode: final_name = "video_final_DEBUG.mp4"; shutil.copy(body_path, final_name); return final_name
        return body_path

    files_folder = cfg.get("FILES_FOLDER", "")
    if files_folder and not os.path.isabs(port_file): files_folder = os.path.abspath(files_folder); port_file = os.path.join(files_folder, port_file)
    if not os.path.exists(port_file): raise FileNotFoundError(f"Portada no encontrada: {port_file}")

    port_duration = redondear_tiempo(float(meta.get("DURATION", "5")))
    silence_wav = os.path.join(tmp_dir, "silence.wav")
    
    channel_layout = "stereo" if channels == 2 else "mono" if channels == 1 else f"{channels}c"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={sample_rate}:cl={channel_layout}:d={port_duration}", "-c:a", "pcm_s16le", silence_wav], check=True)

    port_silent = os.path.join(tmp_dir, "portada_sil.mp4")
    _, extension = os.path.splitext(port_file)
    is_image = extension.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif')
    
    W, H = map(int, cfg["RESOLUTION"].split('x'))
    fps = cfg.get("FPS", 30)
    
    # Filtro para asegurar resolución y aspect ratio
    scale_filter = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1"

    if is_image:
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(port_duration), "-i", normalizar_ruta_ffmpeg(port_file), 
                        "-i", normalizar_ruta_ffmpeg(silence_wav), 
                        "-vf", scale_filter, "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", 
                        "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-ac", str(channels),
                        "-video_track_timescale", "15360", "-vsync", "cfr", normalizar_ruta_ffmpeg(port_silent)], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", normalizar_ruta_ffmpeg(port_file), 
                        "-i", normalizar_ruta_ffmpeg(silence_wav), 
                        "-t", str(port_duration), 
                        "-vf", scale_filter, "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", 
                        "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-ac", str(channels),
                        "-video_track_timescale", "15360", "-map", "0:v:0", "-map", "1:a:0", "-vsync", "cfr", 
                        normalizar_ruta_ffmpeg(port_silent)], check=True)

    final = "video_final_con_portada_DEBUG.mp4" if debug_mode else "video_final_con_portada.mp4"
    concat_filter = os.path.join(tmp_dir, "concat_filter.txt")
    # Usar el filtro concat de forma más segura forzando fps en el mapeo final si fuera necesario
    with open(concat_filter, "w") as f: 
        f.write("[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[vout][aout]")

    subprocess.run(["ffmpeg", "-y", "-i", normalizar_ruta_ffmpeg(port_silent), "-i", normalizar_ruta_ffmpeg(body_path), 
                    "-filter_complex_script", normalizar_ruta_ffmpeg(concat_filter), 
                    "-map", "[vout]", "-map", "[aout]", 
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(sample_rate), "-ac", str(channels),
                    "-vsync", "cfr", final], check=True)
    return final
