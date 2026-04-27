import json
import traceback
from datetime import datetime

AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large-v3"]

# Matches 0_referencia/pipeline/whisper_engine.py reconstruir_bloques()
BLOCK_MAX_WINDOW_S = 1.0


def _reconstruir_bloques(words: list, max_window: float = BLOCK_MAX_WINDOW_S) -> list:
    """
    Group word-level dicts {start, end, text} into time-window blocks.
    A new block starts when (word.end - block_start) > max_window.
    Identical logic to 0_referencia WhisperAnalyzer.reconstruir_bloques().
    """
    bloques, bloque_actual, inicio_bloque = [], [], None
    for w in words:
        if inicio_bloque is None:
            inicio_bloque = w["start"]
        if w["end"] - inicio_bloque <= max_window:
            bloque_actual.append(w)
        else:
            if bloque_actual:
                bloques.append({
                    "start": round(inicio_bloque, 3),
                    "end":   round(bloque_actual[-1]["end"], 3),
                    "text":  " ".join(x["text"] for x in bloque_actual),
                })
            bloque_actual = [w]
            inicio_bloque = w["start"]
    if bloque_actual:
        bloques.append({
            "start": round(inicio_bloque, 3),
            "end":   round(bloque_actual[-1]["end"], 3),
            "text":  " ".join(x["text"] for x in bloque_actual),
        })
    return bloques


def _to_raw_text(bloques: list) -> str:
    """[start.xxx - end.xxx]: text   — format consumed by spell checker and aligner."""
    return "\n".join(f"[{b['start']:.3f} - {b['end']:.3f}]: {b['text']}" for b in bloques)


def _to_srt(bloques: list) -> str:
    def t(s):
        h, rem = divmod(int(s), 3600)
        m, sec = divmod(rem, 60)
        ms = int(round((s % 1) * 1000))
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
    lines = []
    for i, b in enumerate(bloques, 1):
        lines.append(f"{i}\n{t(b['start'])} --> {t(b['end'])}\n{b['text']}\n")
    return "\n".join(lines)


def _update_db(class_id: int, updates: dict):
    from database import SessionLocal
    import models
    db = SessionLocal()
    try:
        row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
        if row:
            for k, v in updates.items():
                setattr(row, k, v)
            row.tx_updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[whisper_agent] DB error: {e}")
    finally:
        db.close()


def _get_device() -> str:
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


def run_transcription(class_id: int, file_path: str, model_name: str):
    """
    Background thread entry point.

    Output stored in ClassAudio:
      tx_segments  → JSON list of {start, end, text} BLOCKS (1.0 s window)
                     Ready for spell correction and alignment — same format as
                     0_referencia subtitulos_formato_personalizado.txt
      tx_raw_text  → [start.xxx - end.xxx]: text  per block (one per line)
      tx_srt       → SRT string for video production
    """

    def phase(status, pct, msg, error=None):
        upd = {"tx_status": status, "tx_progress": pct, "tx_phase": msg}
        if error is not None:
            upd["tx_error"] = error
        _update_db(class_id, upd)

    try:
        phase("loading_model", 5, f"🎙️ Cargando modelo {model_name}…")

        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            phase("error", 0, "❌ faster-whisper no instalado", error=str(e))
            return

        device = _get_device()
        compute_type = "float16" if device == "cuda" else "int8"

        phase("loading_model", 10, f"🎙️ Cargando {model_name} en {device.upper()} ({compute_type})…")
        model = WhisperModel(model_name, device=device, compute_type=compute_type)

        phase("transcribing", 20, "🤖 Iniciando transcripción…")
        segments_gen, info = model.transcribe(
            file_path,
            language="es",
            beam_size=5,
            word_timestamps=True,   # needed for reconstruir_bloques
        )

        total_duration = info.duration or 1.0
        all_words = []

        for seg in segments_gen:
            # Real-time progress: 20% → 85%
            pct = 20 + int((seg.end / total_duration) * 65)
            phase(
                "transcribing", min(pct, 85),
                f"🤖 Transcribiendo… {seg.start:.1f}s — {seg.end:.1f}s / {total_duration:.1f}s",
            )
            if seg.words:
                for w in seg.words:
                    txt = w.word.strip()
                    if txt and w.start is not None and w.end is not None:
                        all_words.append({"start": w.start, "end": w.end, "text": txt})
            else:
                txt = seg.text.strip()
                if txt:
                    all_words.append({"start": seg.start, "end": seg.end, "text": txt})

        phase("saving", 88, f"📦 Reconstruyendo bloques ({len(all_words)} palabras)…")

        bloques = _reconstruir_bloques(all_words, BLOCK_MAX_WINDOW_S)
        raw_text = _to_raw_text(bloques)
        srt_text = _to_srt(bloques)

        _update_db(class_id, {
            "tx_status":   "done",
            "tx_progress": 100,
            "tx_phase":    f"✅ Completado — {len(bloques)} bloques · {total_duration:.1f}s",
            "tx_error":    None,
            "tx_raw_text": raw_text,
            "tx_srt":      srt_text,
            "tx_segments": json.dumps(bloques, ensure_ascii=False),
        })

    except Exception as e:
        err = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        phase("error", 0, "❌ Error durante la transcripción", error=err)
