from .utils import (hex_a_ass_color, generar_color_por_intensidad,
                    redondear_tiempo, segundos_a_ass, segundos_a_mmss,
                    limpiar_override, wrap_text)


def css_to_ass_style(name, css, d_font, d_color):
    fs, font, bold, italic = 80, d_font, 0, 0
    color = d_color
    for prop in css.split(';'):
        if ':' not in prop:
            continue
        key, val = map(str.strip, prop.split(':', 1))
        key = key.lower()
        if key == "font-size":
            fs = int(val.rstrip("px")) if val.rstrip("px").isdigit() else fs
        elif key == "font-family":
            font = val
        elif key == "font-weight" and "bold" in val.lower():
            bold = 1
        elif key == "font-style" and "italic" in val.lower():
            italic = 1
        elif key == "color":
            color = val
    ass_color = hex_a_ass_color(color) if color.startswith("#") else color
    return (f"Style: {name},{font},{fs},{ass_color},&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,"
            f"{bold},{italic},0,0,100,100,0,0,1,0,0,5,10,10,10,1")


def generar_subtitulos_ass(meta, styles, segments, out_file, debug_mode=False):
    W, H = map(int, meta.get("RESOLUTION", "1920x1080").split('x'))
    font_name = meta.get("MAIN_FONT", "Inter")
    main_color = meta.get("MAIN_TEXT_COLOR", "#000000")

    header = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n"
        f"ScaledBorderAndShadow: yes\n\n"
        f"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        f"OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
        f"Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{font_name},54,&H00000000,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,"
        f"0,0,0,0,100,100,0,0,1,0,0,5,10,10,10,1\n"
    )

    if debug_mode:
        header += (f"Style: Debug,{font_name},36,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,"
                   f"1,0,0,0,100,100,0,0,1,2,1,9,20,20,20,1\n")

    for name, css in styles.items():
        header += css_to_ass_style(name, css, font_name, main_color) + "\n"

    header += "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

    texts = [s for s in segments if s.get("TEXT")]
    total = len(texts)
    ev_lines = []

    for i, seg in enumerate(texts):
        ini      = seg["tiempo_inicio"]
        dur      = float(seg.get("TIME", "0"))
        fin      = redondear_tiempo(ini + dur - 0.01)
        s_ini    = segundos_a_ass(ini)
        s_fin    = segundos_a_ass(fin)
        style    = seg.get("TEXT_STYLE", "Default")
        plain    = limpiar_override(seg["TEXT"])
        seg_type = seg.get("TYPE", "TEXT").upper()

        hex_c = generar_color_por_intensidad(i + 1, total).lstrip('#')
        r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        color_override = f"\\c&H00{b:02X}{g:02X}{r:02X}"

        margin_l, margin_r = 0, 0

        if seg_type in ("SPLIT_LEFT", "SPLIT_RIGHT", "VIDEO", "FULL_IMAGE"):
            if seg_type == "SPLIT_LEFT":
                pos_x, clip, max_chars = int(W * 0.75), f"\\clip({W//2},0,{W},{H})", 22
            elif seg_type == "SPLIT_RIGHT":
                pos_x, clip, max_chars = int(W * 0.25), f"\\clip(0,0,{W//2},{H})", 22
            else:
                pos_x, clip, max_chars = W // 2, f"\\clip(0,{int(H*0.75)},{W},{H})", 45
            pos_y   = int(H / 2) if "SPLIT" in seg_type else int(H * 0.9)
            wrapped = wrap_text(plain, max_chars)
            over    = f"\\pos({pos_x},{pos_y}){clip}{color_override}"
            txt     = f"{{{over}}}{wrapped}"
        else:
            size_override = "\\fscx150\\fscy150"
            override = size_override + color_override
            txt = f"{{{override}}}{plain}"
            margin_l = int(W * 0.15)
            margin_r = int(W * 0.15)

        ev_lines.append(f"Dialogue: 0,{s_ini},{s_fin},{style},,{margin_l},{margin_r},0,,{txt}")

        if debug_mode:
            tiempo_str = segundos_a_mmss(ini)
            debug_pos  = f"\\pos({W - 20},{40})"
            debug_text = f"{{{debug_pos}}}[{tiempo_str}]"
            ev_lines.append(f"Dialogue: 1,{s_ini},{s_fin},Debug,,0,0,0,,{debug_text}")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(ev_lines))

    return out_file
