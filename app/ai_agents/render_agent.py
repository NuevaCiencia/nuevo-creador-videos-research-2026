"""
render_agent.py — Ejecuta el render final del video de una clase.

Flujo:
1. Lee guion_consolidado + audio + config de curso de la DB
2. Parsea guion → meta, styles, cover, segments
3. Genera ASS subtitles
4. Construye filtro FFmpeg
5. Mezcla audio + assets + subtítulos → body.mp4
6. Prepende portada → final.mp4
7. Guarda output_path en ClassRender
"""

import os
import json
import shutil
import traceback
import tempfile
from pathlib import Path


def _update_render(class_id: int, status: str, pct: int, msg: str, error=None, output_path=None):
    from database import SessionLocal
    import models
    from datetime import datetime

    db = SessionLocal()
    try:
        row = db.query(models.ClassRender).filter(
            models.ClassRender.class_id == class_id
        ).first()
        if not row:
            row = models.ClassRender(class_id=class_id)
            db.add(row)
        row.status   = status
        row.progress = pct
        row.phase    = msg
        row.updated_at = datetime.utcnow()
        if error is not None:
            row.error = error
        if output_path is not None:
            row.output_path = output_path
        db.commit()
    finally:
        db.close()


def run_render(class_id: int):
    """Entry point — called from background thread."""
    from database import SessionLocal
    import models

    try:
        _update_render(class_id, "rendering", 2, "⚙️ Cargando datos…")

        # ── Load data from DB ────────────────────────────────────────────────
        db = SessionLocal()
        try:
            cls = db.query(models.Class).filter(models.Class.id == class_id).first()
            if not cls:
                raise ValueError(f"Class {class_id} not found")

            course = cls.section.course

            # Audio
            audio_row = cls.audio
            if not audio_row or not audio_row.file_path:
                raise ValueError("No hay audio subido para esta clase")

            # Guion consolidado
            guion_row = cls.guion_consolidado
            if not guion_row or not guion_row.content:
                raise ValueError("No hay guion consolidado — ejecuta la fase Visual primero")

            # Config
            cfg = {
                "FPS":              course.fps or 30,
                "RESOLUTION":       course.resolution or "1920x1080",
                "MAIN_FONT":        course.main_font or "Inter",
                "BACKGROUND_COLOR": course.background_color or "#fefefe",
                "MAIN_TEXT_COLOR":  course.main_text_color or "#bd0505",
                "COVER_ASSET":      course.cover_asset or "videos/portada.mp4",
                "USE_TRANSITIONS":  False,
                "TRANSITION_DURATION": 0.5,
            }

            guion_content = guion_row.content
            audio_path    = audio_row.file_path  # relative to app/
            recursos_json = guion_row.recursos_json or "{}"

        finally:
            db.close()

        # Resolve absolute paths
        app_dir    = Path(__file__).parent.parent   # app/
        audio_abs  = str(app_dir / audio_path) if not os.path.isabs(audio_path) else audio_path
        assets_dir = str(app_dir)                   # assets live relative to app/

        cfg["FILES_FOLDER"] = assets_dir

        if not os.path.exists(audio_abs):
            raise FileNotFoundError(f"Audio no encontrado: {audio_abs}")

        _update_render(class_id, "rendering", 8, "📄 Parseando guion…")

        # ── Parse guion ──────────────────────────────────────────────────────
        from core.utils import parsear_guion_nuevo, get_audio_sample_rate, get_audio_channels
        meta, styles, cover_seg, segments = parsear_guion_nuevo(guion_content)

        # Merge course config into meta (meta may override with values from guion)
        meta.setdefault("FPS",              str(cfg["FPS"]))
        meta.setdefault("RESOLUTION",       cfg["RESOLUTION"])
        meta.setdefault("MAIN_FONT",        cfg["MAIN_FONT"])
        meta.setdefault("MAIN_TEXT_COLOR",  cfg["MAIN_TEXT_COLOR"])
        meta.setdefault("BACKGROUND_COLOR", cfg["BACKGROUND_COLOR"])
        meta["FILES_FOLDER"] = assets_dir

        sample_rate = get_audio_sample_rate(audio_abs)
        channels    = get_audio_channels(audio_abs)

        _update_render(class_id, "rendering", 15, "📝 Generando subtítulos ASS…")

        # ── Prepare output dirs ──────────────────────────────────────────────
        renders_dir = app_dir / "renders"
        renders_dir.mkdir(exist_ok=True)

        tmp_dir = tempfile.mkdtemp(prefix=f"render_{class_id}_")
        try:
            ass_path  = os.path.join(tmp_dir, "subtitulos.ass")
            body_path = os.path.join(tmp_dir, "body.mp4")
            out_name  = f"clase_{class_id}_final.mp4"
            out_path  = str(renders_dir / out_name)

            # ── ASS subtitles ────────────────────────────────────────────────
            from core.ass_builder import generar_subtitulos_ass
            generar_subtitulos_ass(meta, styles, segments, ass_path)

            _update_render(class_id, "rendering", 25, "🎬 Mezclando video…")

            # ── Video body ───────────────────────────────────────────────────
            from core.video_engine import crear_video_mixto, procesar_portada
            crear_video_mixto(
                audio_abs, ass_path, segments, meta,
                body_path, sample_rate, channels, tmp_dir
            )

            _update_render(class_id, "rendering", 80, "🎞️ Añadiendo portada…")

            # ── Cover ────────────────────────────────────────────────────────
            final_path = procesar_portada(cover_seg, body_path, meta, sample_rate, channels, tmp_dir)

            _update_render(class_id, "rendering", 92, "💾 Guardando video final…")

            # Copy to renders/
            shutil.copy2(final_path, out_path)

            rel_out = f"renders/{out_name}"
            _update_render(class_id, "done", 100, "✅ Video renderizado", output_path=rel_out)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception as e:
        _update_render(
            class_id, "error", 0, "❌ Error en render",
            error=f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        )
