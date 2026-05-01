import re as _re


def _escape_ass_path(path: str) -> str:
    """
    Escape a path for use inside an FFmpeg filtergraph ass= option.
    On Windows, the drive letter colon (C:) must be escaped as C\\:
    so FFmpeg's filter parser doesn't treat it as an option separator.
    """
    # Escape Windows drive letter colon: C:/ → C\:/
    escaped = _re.sub(r'^([A-Za-z]):', r'\1\\:', path)
    # Wrap in single quotes if not already quoted
    return f"'{escaped}'"


def _escape_fontsdir(path: str) -> str:
    """Escape fontsdir path for FFmpeg filter option inside a filter_complex_script.
    Must use single quotes (same as ass= path) — without them, the escaped colon
    C\\:/ causes FFmpeg to split the value and treat the rest as an unknown option."""
    path = path.replace('\\', '/')
    escaped = _re.sub(r'^([A-Za-z]):', r'\1\\:', path)
    return f"'{escaped}'"


def construir_filtro_ffmpeg(recursos, W, H, fps, ass_path_ffmpeg, filtro_path,
                            use_trans=False, dur_t=0.5, fonts_dir: str = ""):
    half = W // 2
    with open(filtro_path, "w", encoding="utf-8") as f:
        f.write("[0:v]null[bg];\n")
        idx_in, overlay_idx = 1, 0

        for r in recursos:
            ini, dur, fin = r["ini"], r["dur"], r["fin"]
            margen = 0.01

            fade_filter = ""
            if use_trans and dur_t > 0 and dur > dur_t * 2:
                fade_filter = (f",format=rgba,"
                               f"fade=t=in:st={ini}:d={dur_t}:alpha=1,"
                               f"fade=t=out:st={fin-dur_t}:d={dur_t}:alpha=1")

            if r["tipo"] == "img":
                if r["pos"] == "COMPLETA":
                    scale_str = f"scale={W}:{H},setsar=1"
                else:
                    scale_str = (f"scale={half}:-1,setsar=1,"
                                 f"pad={half}:{H}:(ow-iw)/2:(oh-ih)/2:color=white")
                f.write(f"[{idx_in}:v]{scale_str},setpts=PTS-STARTPTS+{ini}/TB{fade_filter}[img{overlay_idx}];\n")
                x_pos = "0" if r["pos"] in ("COMPLETA", "IZQUIERDA") else str(half)
                tag = f"img{overlay_idx}"
                ovl = f"overlay=x={x_pos}:y=0:enable='between(t,{ini-margen},{fin+margen})':format=auto"
            else:
                x_pos = "0" if r["pos"] in ("COMPLETA", "IZQUIERDA") else str(half)
                f.write(f"[{idx_in}:v]trim=duration={dur},setpts=PTS-STARTPTS+{ini}/TB,"
                        f"scale={W}:{H},setsar=1,fps={fps}:round=near{fade_filter}[vid{overlay_idx}];\n")
                tag = f"vid{overlay_idx}"
                ovl = f"overlay=x={x_pos}:y=0:enable='between(t,{ini-margen},{fin+margen})':format=auto"

            base = "bg" if overlay_idx == 0 else f"v{overlay_idx-1}"
            f.write(f"[{base}][{tag}]{ovl}[v{overlay_idx}];\n")

            idx_in     += 1
            overlay_idx += 1

        fontsdir_opt = f":fontsdir={_escape_fontsdir(fonts_dir)}" if fonts_dir else ""
        f.write(f"[v{overlay_idx-1}]ass={_escape_ass_path(ass_path_ffmpeg)}{fontsdir_opt}[vout]")

    return overlay_idx
