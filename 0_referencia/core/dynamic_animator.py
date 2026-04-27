import os
import re
import subprocess
import textwrap
from core.font_resolver import get_resolver
from core.utils import normalizar_ruta_ffmpeg

def _parse_subtitulos(ruta):
    bloques = []
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.search(r"\[(\d+\.\d+)\s*-\s*(\d+\.\d+)\]:\s*(.+)$", line.strip())
                if m:
                    bloques.append({
                        "start": float(m.group(1)),
                        "end": float(m.group(2)),
                        "text": m.group(3).strip()
                    })
    return bloques

def _find_keyword_abs_time(bloques, search_start, end_time, keyword, max_delay=None):
    """
    Busca el keyword (o su parte más representativa) construyendo una línea de tiempo continua.
    Ignora cualquier match que ocurra antes del search_start, garantizando que
    los elementos secuenciales con inicios similares no colisionen.
    """
    keyword_clean = re.sub(r'[^\w\s]', '', keyword).lower().strip()
    if not keyword_clean:
        return search_start + 0.5
        
    combined_text = ""
    char_times = []
    
    # Construir línea de tiempo de caracteres, ordenados
    for b in sorted(bloques, key=lambda x: x["start"]):
        if b["end"] >= max(0.0, search_start - 2.0) and b["start"] <= end_time + 1.0:
            t_clean = re.sub(r'[^\w\s]', '', b["text"]).lower()
            t_clean = re.sub(r'\s+', ' ', t_clean).strip()
            
            if t_clean:
                if combined_text and not combined_text.endswith(" "):
                    combined_text += " "
                    char_times.append(b["start"])
                
                for i in range(len(t_clean)):
                    ratio = i / max(1, len(t_clean))
                    char_times.append(b["start"] + ratio * (b["end"] - b["start"]))
                
                combined_text += t_clean

    if not combined_text:
        return min(search_start + 0.5, end_time)

    # Buscar el indice de inicio más cercano a search_start (con mini-margen)
    start_char_idx = 0
    for i, t in enumerate(char_times):
        if t >= search_start - 0.2:
            start_char_idx = i
            break

    search_targets = [keyword_clean]
    words = keyword_clean.split()
    if len(words) > 3: search_targets.append(" ".join(words[:3]))
    if len(words) > 1: search_targets.append(" ".join(words[:2]))
    if len(words) > 0:
        sig_words = [w for w in words if w not in ('el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'de', 'del', 'al', 'en', 'por', 'para', 'que', 'con')]
        if sig_words:
            search_targets.append(sig_words[0])
            for w in sig_words:
                if len(w) >= 4 and w not in search_targets:
                    search_targets.append(w)
        else:
            search_targets.append(words[0])

    for target in search_targets:
        idx = combined_text.find(target, start_char_idx)
        if idx != -1 and idx < len(char_times):
            found_t = char_times[idx]
            if max_delay is not None and (found_t - search_start > max_delay):
                pass # El encuentro ocurrió excesivamente tarde respecto al inicio, lo ignoramos para usar triggers por defecto
            else:
                return min(found_t, end_time)

    return min(search_start + 0.5, end_time)

def escape_ff_text(text):
    # escape backslashes first, then other special ffmpeg characters
    return text.replace("\\", "\\\\").replace("'", "'\\\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")

def generate_dynamic_video(segment, cfg, out_path, subtitulos_path, tmp_dir):
    W, H = map(int, cfg["RESOLUTION"].split('x'))
    fps = cfg.get("FPS", 30)
    dur = float(segment.get("TIME", "5"))
    tipo = segment.get("TYPE", "")
    params_str = segment.get("PARAMS", "")
    params = params_str.split('//') if params_str else []

    bloques = _parse_subtitulos(subtitulos_path)
    
    bg_color = cfg.get("BACKGROUND_COLOR", "#FFFFFF").lstrip('#')
    txt_color = cfg.get("MAIN_TEXT_COLOR", "#000000").lstrip('#')
    hl_color = cfg.get("HIGHLIGHT_TEXT_COLOR", "#bd0505").lstrip('#')
    sec_color = "1a1a1a" # Elegant dark gray for secondary text

    color_src = f"color=0x{bg_color}:s={W}x{H}:r={fps}:d={dur}"

    fr = get_resolver()
    font_main = normalizar_ruta_ffmpeg(fr.get_font_path("bold"))
    font_reg = normalizar_ruta_ffmpeg(fr.get_font_path("regular"))

    filters = []

    if tipo == "CONCEPT":
        termino = params[0] if len(params) > 0 else "Concepto"
        definicion = params[1] if len(params) > 1 else ""
        
        # Calcular cuándo se dice exactamente el término (tiempo absoluto) limitando la espera máxima a 3 segundos
        trigger_termino_abs = _find_keyword_abs_time(bloques, segment["tiempo_inicio"], segment["tiempo_inicio"] + dur, termino, max_delay=3.0)
        trigger_termino = max(0.0, trigger_termino_abs - segment["tiempo_inicio"])
        
        # TITULO CONCEPT
        t_text = escape_ff_text(termino)
        y_title = int(H*0.30)
        # Ahora el título aparece SÓLO cuando se nombra el término en el audio (no desde el tiempo 0)
        f_term = (f"drawtext=fontfile='{font_main}':text='{t_text}':"
                  f"fontcolor=0x{txt_color}:fontsize={int(H*0.11)}:x=(w-text_w)/2:y={y_title}:"
                  f"alpha='if(lt(t,{trigger_termino}),0,min(1,(t-{trigger_termino})/0.3))'")
        filters.append(f_term)
        
        # DEFINICION
        if definicion:
            # Calcular cuándo se empieza a leer la definición, limitando demora extra de la definición
            trigger_def_abs = _find_keyword_abs_time(bloques, trigger_termino_abs, segment["tiempo_inicio"] + dur, definicion, max_delay=4.0)
            trigger_definicion = max(0.0, trigger_def_abs - segment["tiempo_inicio"])
            # Para evitar que la definición caiga antes o a la vez que el título
            if trigger_definicion <= trigger_termino:
                trigger_definicion = trigger_termino + 0.5

            lines = textwrap.wrap(definicion, width=42)
            y_base_def = y_title + int(H*0.16)  # Más espaciado entre título y definición
            line_height = int(H*0.065)           # Más interlineado
            
            for i, line in enumerate(lines):
                l_text = escape_ff_text(line)
                y_pos = y_base_def + (i * line_height)
                # La definición obedece a su propio trigger basado en texto dictado o fallback natural
                f_line = (f"drawtext=fontfile='{font_reg}':text='{l_text}':"
                          f"fontcolor=0x{sec_color}:fontsize={int(H*0.052)}:x=(w-text_w)/2:y={y_pos}:"
                          f"alpha='if(lt(t,{trigger_definicion}),0,min(1,(t-{trigger_definicion})/0.4))'")
                filters.append(f_line)

    elif tipo == "LIST":
        # ── Fondo verde pizarrón exclusivo para LIST ──────────────────────────
        list_bg = "2C5F2E"
        color_src = f"color=0x{list_bg}:s={W}x{H}:r={fps}:d={dur}"

        list_bullet_color = "FFFFFF"
        list_sub_color    = "E8D5A3"

        # Detección de Ghost Title (prefijo @)
        ghost_title = ""
        items_to_process = list(params)
        if items_to_process and items_to_process[0].strip().startswith("@"):
            ghost_title = items_to_process.pop(0).strip().lstrip("@").strip()

        n_items = len(items_to_process)
        has_sub = any(re.search(r'\[.*\]', p) for p in items_to_process)

        # Área segura
        area_top = int(H * 0.12)
        area_bot = int(H * 0.88)
        
        # Si hay título, el área de ítems empieza más abajo
        if ghost_title:
            title_fs = int(H * 0.075)
            y_title = int(H * 0.09)
            gt_text = escape_ff_text(ghost_title)
            # Título fantasma: visible desde t=0 con opacidad baja (0.25)
            f_ghost = (f"drawtext=fontfile='{font_main}':text='{gt_text}':"
                       f"fontcolor=0x{list_bullet_color}:fontsize={title_fs}:x=(w-text_w)/2:y={y_title}:"
                       f"alpha=0.25")
            filters.append(f_ghost)
            area_top += int(H * 0.08) # Mover el inicio de la lista hacia abajo

        usable = area_bot - area_top

        # Tamaño de fuente provisional para calcular wrapping
        item_h_max = int(H * 0.155) if has_sub else int(H * 0.115)
        y_offset_prov = min(item_h_max, usable // max(n_items, 1))
        bullet_fs = max(int(H * 0.042), min(int(H * 0.065), int(y_offset_prov * 0.55)))
        sub_fs    = max(int(H * 0.032), min(int(H * 0.048), int(y_offset_prov * 0.40)))

        # Márgenes horizontales y cálculo de caracteres máximos por línea
        x_start  = int(W * 0.06)
        avail_w  = int(W * 0.84)   # margen 6% izquierda, 10% derecha
        max_chars = max(15, int(avail_w / (bullet_fs * 0.52)))  # ~0.52 px/char promedio

        # ── PASADA 1: Pre-calcular wrapping de cada ítem ─────────────────────
        processed = []
        for item in items_to_process:
            element = item
            subtext = ""
            m2 = re.match(r"(.*)\[(.*)\]", item)
            if m2:
                element = m2.group(1).strip()
                subtext = m2.group(2).strip()
            wrapped = textwrap.wrap(f"• {element}", width=max_chars) or [f"• {element}"]
            processed.append((element, subtext, wrapped))

        # Calcular altura real de cada ítem
        line_h = int(bullet_fs * 1.18)
        sub_gap = int(H * 0.012)
        item_gap = int(H * 0.022)

        item_heights = []
        for (el, sub, lines) in processed:
            h = len(lines) * line_h
            if sub:
                h += int(sub_fs * 1.3) + sub_gap
            item_heights.append(h)

        total_block_h = sum(item_heights) + item_gap * max(n_items - 1, 0)

        # Centrar verticalmente el bloque completo
        y_base = area_top + max(0, (usable - total_block_h) // 2)

        # ── PASADA 2: Renderizar línea por línea ──────────────────────────────
        current_search_abs = segment["tiempo_inicio"]
        current_y = y_base

        for (element, subtext, wrapped_lines), item_h in zip(processed, item_heights):
            trigger_abs  = _find_keyword_abs_time(bloques, current_search_abs, segment["tiempo_inicio"] + dur, element)
            trigger_time = max(0.0, trigger_abs - segment["tiempo_inicio"])
            current_search_abs = trigger_abs + 0.5

            # Renderizar cada línea del bullet (con sangrado colgante)
            x_indent = x_start + int(bullet_fs * 1.1)  # alinea con texto post-bullet
            for li, line_text in enumerate(wrapped_lines):
                lt = escape_ff_text(line_text)
                y_line = current_y + (li * line_h)
                x_line = x_start if li == 0 else x_indent
                f_bullet = (f"drawtext=fontfile='{font_main}':text='{lt}':"
                            f"fontcolor=0x{list_bullet_color}:fontsize={bullet_fs}:x={x_line}:y={y_line}:"
                            f"alpha='if(lt(t,{trigger_time}),0,min(1,(t-{trigger_time})/0.3))'")
                filters.append(f_bullet)

            # Subtext debajo de las líneas del bullet
            if subtext:
                st_txt = escape_ff_text(subtext)
                sub_y = current_y + len(wrapped_lines) * line_h + sub_gap
                f_sub = (f"drawtext=fontfile='{font_reg}':text='{st_txt}':"
                         f"fontcolor=0x{list_sub_color}:fontsize={sub_fs}:x={int(W * 0.08)}:y={sub_y}:"
                         f"alpha='if(lt(t,{trigger_time + 0.2}),0,min(1,(t-({trigger_time + 0.2}))/0.3))'")
                filters.append(f_sub)

            current_y += item_h + item_gap



    else:
        filters.append(f"drawtext=fontfile='{font_main}':text='...':fontcolor=0x{txt_color}:fontsize=50:x=(w-text_w)/2:y=(h-text_h)/2")

    filter_txt_path = os.path.join(tmp_dir, f"dynamic_{segment['tiempo_inicio']}.txt")
    with open(filter_txt_path, "w", encoding="utf-8") as f:
        f.write(",\n".join(filters))
        
    cmd = [
        "ffmpeg", "-y", "-v", "warning",
        "-f", "lavfi", "-i", color_src,
        "-filter_complex_script", normalizar_ruta_ffmpeg(filter_txt_path),
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        normalizar_ruta_ffmpeg(out_path)
    ]
    subprocess.run(cmd, check=True)
    return out_path
