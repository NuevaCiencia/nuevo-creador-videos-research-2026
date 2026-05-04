"""
dummy_builder.py — Constructor de assets dummy inteligente.

Solo crea dummies para los assets que NO existen en disco.
Si el archivo ya existe (real o dummy previo), lo deja intacto.
"""
import os
import json
import subprocess
import traceback
from pathlib import Path


def _crear_imagen_dummy(w, h, texto, output_path: Path):
    """Crea PNG gris con texto centrado usando FFmpeg drawtext (sin Pillow)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_text = texto.replace("'", "").replace(":", " ").replace("/", " ")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=0xb4b4b4:s={w}x{h}:r=1:d=1",
        "-vf", f"drawtext=text='{safe_text}':fontsize={max(24, h//18)}:fontcolor=333333:x=(w-tw)/2:y=(h-th)/2",
        "-frames:v", "1",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=True, timeout=30)


def _crear_video_dummy(w, h, texto, dur, output_path: Path):
    """Crea MP4 placeholder usando FFmpeg drawtext."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_text = texto.replace("'", "").replace(":", " ").replace("/", " ")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=0x333333:s={w}x{h}:r=1:d={max(1, int(dur))}",
        "-vf", f"drawtext=text='{safe_text}':fontsize={max(24, h//12)}:fontcolor=ffffff:x=(w-tw)/2:y=(h-th)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=True, timeout=60)


def _build_one(recurso: dict, assets_base: Path) -> dict:
    nombre    = recurso.get("nombre", "")
    tipo      = recurso.get("tipo", "")
    ubicacion = recurso.get("ubicacion", "")  # e.g. "images/S001.png"
    duracion  = float(recurso.get("duracion", 5.0))

    dest = assets_base / ubicacion
    if dest.exists():
        return {"nombre": nombre, "status": "exists"}

    dest.parent.mkdir(parents=True, exist_ok=True)

    stem = Path(ubicacion).stem.upper()
    is_video = stem.startswith(("V", "REM")) or Path(ubicacion).suffix.lower() == ".mp4"

    # Robust detection of split images: either type label or filename starting with S
    is_split = (tipo in ("split", "imagen_split")) or stem.startswith("S")

    try:
        if is_video:
            label = f"REMOTION  {nombre}" if nombre.upper().startswith("REM") else f"VIDEO  {nombre}"
            _crear_video_dummy(1920, 1080, label, duracion, dest)
        elif is_split:
            _crear_imagen_dummy(960, 1080, nombre, dest)
        else:
            _crear_imagen_dummy(1920, 1080, nombre, dest)

        return {"nombre": nombre, "status": "created"}
    except Exception as e:
        return {"nombre": nombre, "status": "error", "error": str(e)}


def build_missing_dummies(class_id: int, recursos_json: str, assets_base_dir: str,
                           cover_asset: str = "videos/portada.mp4"):
    """
    Entry point — called from background thread.
    Builds dummies only for missing assets.
    Updates ClassRender in DB with progress.
    """
    from database import SessionLocal
    import models

    def _update(status, pct, msg, error=None):
        db = SessionLocal()
        try:
            row = db.query(models.ClassRender).filter(
                models.ClassRender.class_id == class_id
            ).first()
            if row:
                row.status   = status
                row.progress = pct
                row.phase    = msg
                if error is not None:
                    row.error = error
                db.commit()
        finally:
            db.close()

    try:
        assets_base = Path(assets_base_dir)
        data        = json.loads(recursos_json)
        recursos    = data.get("recursos", [])

        # Always ensure portada dummy exists
        portada_dest = assets_base / cover_asset
        if not portada_dest.exists():
            recursos_con_portada = [{"nombre": "portada.mp4", "tipo": "portada",
                                     "ubicacion": cover_asset, "duracion": 5}] + recursos
        else:
            recursos_con_portada = recursos

        # Filter only missing
        faltantes = [r for r in recursos_con_portada
                     if not (assets_base / r.get("ubicacion", "")).exists()]

        if not faltantes:
            _update("dummies_done", 100, "✅ Todos los assets ya existen")
            return

        _update("building_dummies", 5,
                f"🏗 Construyendo {len(faltantes)} dummies…")

        errores  = 0
        creados  = 0
        total    = len(faltantes)

        for i, recurso in enumerate(faltantes):
            pct = 5 + int((i / total) * 90)
            _update("building_dummies", pct,
                    f"🏗 [{i+1}/{total}] {recurso.get('nombre', '')}")

            result = _build_one(recurso, assets_base)
            if result["status"] == "created":
                creados += 1
            elif result["status"] == "error":
                errores += 1
                print(f"⚠️ dummy error: {result}")

        msg = f"✅ {creados} dummies creados"
        if errores:
            msg += f" · {errores} errores"
        _update("dummies_done", 100, msg)

    except Exception as e:
        _update("error", 0, "❌ Error construyendo dummies",
                error=f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}")


def check_assets_status(recursos_json: str, assets_base_dir: str,
                         cover_asset: str = "videos/portada.mp4") -> dict:
    """
    Returns status of every asset: exists or missing.
    Used by the GET endpoint — no DB writes.
    """
    assets_base = Path(assets_base_dir)
    data        = json.loads(recursos_json) if recursos_json else {}
    recursos    = data.get("recursos", [])

    items    = []
    n_ok     = 0
    n_miss   = 0

    # Check portada
    portada_path = assets_base / cover_asset
    portada_ok   = portada_path.exists()
    items.append({
        "nombre":    "portada.mp4",
        "tipo":      "portada",
        "ubicacion": cover_asset,
        "exists":    portada_ok,
    })
    if portada_ok: n_ok += 1
    else:          n_miss += 1

    for r in recursos:
        ubicacion = r.get("ubicacion", "")
        exists    = (assets_base / ubicacion).exists() if ubicacion else False
        items.append({
            "nombre":    r.get("nombre", ""),
            "tipo":      r.get("tipo", ""),
            "ubicacion": ubicacion,
            "full_path": str((assets_base / ubicacion).absolute()) if ubicacion else "",
            "segmento":  r.get("segmento", ""),
            "exists":    exists,
        })
        if exists: n_ok += 1
        else:      n_miss += 1

    return {
        "total":   len(items),
        "ok":      n_ok,
        "missing": n_miss,
        "all_ok":  n_miss == 0,
        "items":   items,
    }
