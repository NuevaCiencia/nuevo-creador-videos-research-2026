import os
import re
import subprocess
import textwrap
from core.utils import normalizar_ruta_ffmpeg


# ── Font resolution ────────────────────────────────────────────────────────────

def _escape_ff_path(path: str) -> str:
    """
    Escapes a path for use inside an FFmpeg filter script (fontfile, etc).
    On Windows, the drive letter colon (C:) must be escaped as C\\:
    so FFmpeg's filter parser doesn't treat it as an option separator.
    """
    path = path.replace('\\', '/')
    # Escape Windows drive letter colon: C:/ -> C\:/
    return re.sub(r'^([A-Za-z]):', r'\1\\:', path)


def _resolve_font(fonts_dir: str, variant: str) -> str:
    """Find a font file in fonts_dir. variant: 'bold' or 'regular'"""
    candidates = {
        'bold':    ['Montserrat-Bold.ttf', 'Inter-Bold.ttf', 'NotoSans-Bold.ttf'],
        'regular': ['Montserrat-Regular.ttf', 'Inter-Regular.ttf', 'NotoSans-Regular.ttf'],
    }
    for name in candidates.get(variant, []):
        p = os.path.join(fonts_dir, name)
        if os.path.exists(p):
            return _escape_ff_path(p)
    # Fallback: first .ttf found in fonts_dir
    if os.path.isdir(fonts_dir):
        for f in sorted(os.listdir(fonts_dir)):
            if f.lower().endswith(('.ttf', '.otf')):
                return _escape_ff_path(os.path.join(fonts_dir, f))
    return ""


# ── Subtitles parser ───────────────────────────────────────────────────────────

def _parse_subtitulos(ruta):
    bloques = []
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.search(r"\[(\d+\.\d+)\s*-\s*(\d+\.\d+)\]:\s*(.+)$", line.strip())
                if m:
                    bloques.append({
                        "start": float(m.group(1)),
                        "end":   float(m.group(2)),
                        "text":  m.group(3).strip()
                    })
    return bloques


# ── Keyword timing ─────────────────────────────────────────────────────────────

def _find_keyword_abs_time(bloques, search_start, end_time, keyword, max_delay=None):
    """
    Busca el keyword construyendo una línea de tiempo continua de caracteres.
    Ignora matches anteriores a search_start para evitar colisiones entre ítems.
    """
    keyword_clean = clean(keyword)
    if not keyword_clean:
        return search_start + 0.5

    combined_text = ""
    char_times = []

    for b in sorted(bloques, key=lambda x: x["start"]):
        if b["end"] >= max(0.0, search_start - 2.0) and b["start"] <= end_time + 1.0:
            t_clean = clean(b["text"])
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

    start_char_idx = 0
    for i, t in enumerate(char_times):
        if t >= search_start - 0.2:
            start_char_idx = i
            break

    search_targets = [keyword_clean]
    words = keyword_clean.split()
    if len(words) > 3: search_targets.append(" ".join(words[:3]))
    if len(words) > 1: search_targets.append(" ".join(words[:2]))
    STOPWORDS = {'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'de', 'del', 'al', 'en', 'por', 'para', 'que', 'con'}
    if len(words) > 0:
        sig_words = [w for w in words if w not in STOPWORDS]
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
                pass
            else:
                return min(found_t, end_time)

    return min(search_start + 0.5, end_time)


# ── FFmpeg text escaping ───────────────────────────────────────────────────────

import unicodedata as _ud

def _ascii_safe(text: str) -> str:
    """Strip accents → pure ASCII so the filter script is safe on any OS encoding."""
    return _ud.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def clean(t):
    # Normalize to ASCII and lowercase
    t = _ud.normalize('NFKD', t).encode('ascii', 'ignore').decode('ascii').lower()
    # Strip all non-alphanumeric characters (bullets, colons, etc.) for better matching
    return re.sub(r'[^\w\s]', '', t).strip()

def escape_ff_text(text):
    text = _ascii_safe(text)
    return (text.replace("\\", "\\\\")
                .replace("'", "'\\\\''")
                .replace(":", "\\:")
                .replace("[", "\\[")
                .replace("]", "\\]"))

def _alpha(trigger: float, duration: float = 0.3) -> str:
    """Single-quoted alpha — single quotes protect commas from the graph chain splitter."""
    return f"alpha='if(lt(t,{trigger}),0,min(1,(t-{trigger})/{duration}))'"


# ── Main generator ─────────────────────────────────────────────────────────────

def generate_dynamic_video(segment, cfg, out_path, subtitulos_path, tmp_dir):
    """
    Generates an animated video for CONCEPT or LIST segments, synchronized
    with the audio transcription. Uses fonts from cfg["FONTS_DIR"].
    """
    W, H   = map(int, cfg["RESOLUTION"].split('x'))
    fps    = int(cfg.get("FPS", 30))
    dur    = float(segment.get("TIME", "5"))
    tipo   = segment.get("TYPE", "")
    params_str = segment.get("PARAMS", "")
    params = params_str.split('//') if params_str else []

    bloques   = _parse_subtitulos(subtitulos_path) if subtitulos_path else []

    bg_color  = cfg.get("BACKGROUND_COLOR", "#FFFFFF").lstrip('#')
    txt_color = cfg.get("MAIN_TEXT_COLOR",  "#000000").lstrip('#')
    hl_color  = cfg.get("HIGHLIGHT_TEXT_COLOR", "#bd0505").lstrip('#')
    sec_color = "1a1a1a"

    color_src = f"color=0x{bg_color}:s={W}x{H}:r={fps}:d={dur}"

    fonts_dir  = cfg.get("FONTS_DIR", "")
    font_main  = _resolve_font(fonts_dir, "bold")
    font_reg   = _resolve_font(fonts_dir, "regular")

    filters = []

    if tipo == "CONCEPT":
        termino    = params[0] if len(params) > 0 else "Concepto"
        definicion = params[1] if len(params) > 1 else ""

        trigger_termino_abs = _find_keyword_abs_time(
            bloques, segment["tiempo_inicio"], segment["tiempo_inicio"] + dur,
            termino, max_delay=3.0
        )
        trigger_termino = max(0.0, trigger_termino_abs - segment["tiempo_inicio"])

        t_text = escape_ff_text(termino)
        y_title = int(H * 0.30)
        f_term = (
            f"drawtext=fontfile='{font_main}':text='{t_text}':"
            f"fontcolor=0x{txt_color}:fontsize={int(H*0.11)}:x=(w-text_w)/2:y={y_title}:"
            f"{_alpha(trigger_termino)}"
        )
        filters.append(f_term)

        if definicion:
            trigger_def_abs = _find_keyword_abs_time(
                bloques, trigger_termino_abs, segment["tiempo_inicio"] + dur,
                definicion, max_delay=4.0
            )
            trigger_definicion = max(0.0, trigger_def_abs - segment["tiempo_inicio"])
            if trigger_definicion <= trigger_termino:
                trigger_definicion = trigger_termino + 0.5

            lines       = textwrap.wrap(definicion, width=42)
            y_base_def  = y_title + int(H * 0.16)
            line_height = int(H * 0.065)

            for i, line in enumerate(lines):
                l_text = escape_ff_text(line)
                y_pos  = y_base_def + (i * line_height)
                f_line = (
                    f"drawtext=fontfile='{font_reg}':text='{l_text}':"
                    f"fontcolor=0x{sec_color}:fontsize={int(H*0.052)}:x=(w-text_w)/2:y={y_pos}:"
                    f"{_alpha(trigger_definicion, 0.4)}"
                )
                filters.append(f_line)

    elif tipo == "LIST":
        list_bg           = "2C5F2E"
        color_src         = f"color=0x{list_bg}:s={W}x{H}:r={fps}:d={dur}"
        list_bullet_color = "FFFFFF"
        list_sub_color    = "E8D5A3"

        # Ghost title detection (prefix @)
        ghost_title      = ""
        items_to_process = list(params)
        if items_to_process and items_to_process[0].strip().startswith("@"):
            ghost_title = items_to_process.pop(0).strip().lstrip("@").strip()

        n_items = len(items_to_process)
        has_sub = any(re.search(r'\[.*\]', p) for p in items_to_process)

        area_top = int(H * 0.12)
        area_bot = int(H * 0.88)

        if ghost_title:
            title_fs = int(H * 0.075)
            y_title  = int(H * 0.09)
            gt_text  = escape_ff_text(ghost_title)
            f_ghost  = (
                f"drawtext=fontfile='{font_main}':text='{gt_text}':"
                f"fontcolor=0x{list_bullet_color}:fontsize={title_fs}:x=(w-text_w)/2:y={y_title}:"
                f"alpha=0.25"
            )
            filters.append(f_ghost)
            area_top += int(H * 0.08)

        usable       = area_bot - area_top
        item_h_max   = int(H * 0.155) if has_sub else int(H * 0.115)
        y_offset_prov= min(item_h_max, usable // max(n_items, 1))
        bullet_fs    = max(int(H * 0.042), min(int(H * 0.065), int(y_offset_prov * 0.55)))
        sub_fs       = max(int(H * 0.032), min(int(H * 0.048), int(y_offset_prov * 0.40)))

        x_start  = int(W * 0.06)
        avail_w  = int(W * 0.84)
        max_chars= max(15, int(avail_w / (bullet_fs * 0.52)))

        processed = []
        for item in items_to_process:
            element = item
            subtext = ""
            m2 = re.match(r"(.*)\[(.*)\]", item)
            if m2:
                element = m2.group(1).strip()
                subtext = m2.group(2).strip()
            wrapped = textwrap.wrap(f"- {element}", width=max_chars) or [f"- {element}"]
            processed.append((element, subtext, wrapped))

        line_h   = int(bullet_fs * 1.18)
        sub_gap  = int(H * 0.012)
        item_gap = int(H * 0.022)

        item_heights = []
        for (el, sub, lines) in processed:
            h = len(lines) * line_h
            if sub:
                h += int(sub_fs * 1.3) + sub_gap
            item_heights.append(h)

        total_block_h = sum(item_heights) + item_gap * max(n_items - 1, 0)
        y_base        = area_top + max(0, (usable - total_block_h) // 2)

        current_search_abs = segment["tiempo_inicio"]
        current_y          = y_base

        for (element, subtext, wrapped_lines), item_h in zip(processed, item_heights):
            trigger_abs  = _find_keyword_abs_time(
                bloques, current_search_abs, segment["tiempo_inicio"] + dur, element
            )
            trigger_time = max(0.0, trigger_abs - segment["tiempo_inicio"])
            current_search_abs = trigger_abs + 0.5

            x_indent = x_start + int(bullet_fs * 1.1)
            for li, line_text in enumerate(wrapped_lines):
                lt     = escape_ff_text(line_text)
                y_line = current_y + (li * line_h)
                x_line = x_start if li == 0 else x_indent
                f_bullet = (
                    f"drawtext=fontfile='{font_main}':text='{lt}':"
                    f"fontcolor=0x{list_bullet_color}:fontsize={bullet_fs}:x={x_line}:y={y_line}:"
                    f"{_alpha(trigger_time)}"
                )
                filters.append(f_bullet)

            if subtext:
                st_txt = escape_ff_text(subtext)
                sub_y  = current_y + len(wrapped_lines) * line_h + sub_gap
                f_sub  = (
                    f"drawtext=fontfile='{font_reg}':text='{st_txt}':"
                    f"fontcolor=0x{list_sub_color}:fontsize={sub_fs}:x={int(W * 0.08)}:y={sub_y}:"
                    f"{_alpha(round(trigger_time + 0.2, 4))}"
                )
                filters.append(f_sub)

            current_y += item_h + item_gap

    else:
        font_fallback = font_main or font_reg
        if font_fallback:
            filters.append(
                f"drawtext=fontfile='{font_fallback}':text='...':fontcolor=0x{txt_color}"
                f":fontsize=50:x=(w-text_w)/2:y=(h-text_h)/2"
            )

    if not filters:
        filters.append("null")

    # Build filter graph with explicit input/output labels for -filter_complex_script.
    # Writing to a file avoids Windows CreateProcess command-line length limits.
    # ASCII encoding + \, escaping avoids cp1252 / quoting issues on any OS.
    vf_chain = ",".join(filters)
    script_content = f"[0:v]{vf_chain}[vout]"

    script_path = os.path.join(tmp_dir, f"vf_{os.path.splitext(os.path.basename(out_path))[0]}.txt")
    with open(script_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(script_content)

    cmd = [
        "ffmpeg", "-y", "-v", "warning",
        "-f", "lavfi", "-i", color_src,
        "-filter_complex_script", normalizar_ruta_ffmpeg(script_path),
        "-map", "[vout]",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        normalizar_ruta_ffmpeg(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"dynamic_animator FFmpeg falló (exit {result.returncode}):\n{result.stderr[-2000:]}"
        )
    return out_path
