"""
Port exacto de 0_referencia/pipeline/spell_checker.py → CorrectorOrtografia
Mismos prompts, mismo modelo, misma lógica de validación de timestamps.
Adaptado para leer/escribir en DB en lugar de archivos.
"""
import re
import time
import json
import os
import traceback
from datetime import datetime
from openai import OpenAI

# ── Configuración exacta de 0_referencia/ai_config.yaml ───────────────────────
MODEL              = "gpt-4.1-mini-2025-04-14"
TEMPERATURE        = 0.1
MAX_TOKENS         = 4000
CONTEXT_THRESHOLD  = 50   # bloques por batch

SYSTEM_PROMPT = (
    "Eres un corrector ortográfico experto. Tu ÚNICA tarea es corregir errores ortográficos "
    "y de tipeo de la transcripción.\n"
    "MANTÉN EXACTAMENTE:\n"
    "- El formato de timestamps [X.XXX - X.XXX]: texto\n"
    "- Una línea de entrada = una línea de salida\n"
    "- NO agregues ni quites caracteres especiales. Si una palabra está bien escrita, NO la cambies."
)

USER_PROMPT_TEMPLATE = (
    "TEXTO DE REFERENCIA:\n{texto_ref}\n\n"
    "INSTRUCCIÓN: Corrige ÚNICAMENTE errores ortográficos. "
    "NO cambies la estructura ni los números de tiempo:\n\n{seccion_txt}"
)


# ── Helpers (exactos de CorrectorOrtografia) ──────────────────────────────────

def _limpiar_texto_original(contenido: str) -> str:
    contenido = re.sub(r'<#.*?#>', '', contenido, flags=re.DOTALL)
    contenido = re.sub(r'<!--\s*type:.*?-->', '', contenido, flags=re.DOTALL)
    contenido = re.sub(r'^\s*-{3,}\s*$', '', contenido, flags=re.MULTILINE)
    return '\n'.join(ln.strip() for ln in contenido.split('\n') if ln.strip())


def _bloques_a_texto(bloques: list) -> str:
    return "\n".join(f"[{b['start']:.3f} - {b['end']:.3f}]: {b['text']}" for b in bloques)


def _encontrar_texto_referencia(original_limpio: str, texto_buscar: str) -> str:
    for size, limit in [(10, 1500), (5, 1000)]:
        palabras = texto_buscar.split()[:size]
        if not palabras:
            continue
        idx = original_limpio.lower().find(' '.join(palabras).lower())
        if idx != -1:
            return original_limpio[idx:idx + limit]
    return original_limpio[:1000]


def _corregir_seccion(client: OpenAI, sub_bloques: list, original_limpio: str) -> list:
    """Exact port of CorrectorOrtografia.corregir_seccion() — 3 retries, timestamp validation."""
    texto_busqueda = " ".join(b["text"] for b in sub_bloques)
    ref       = _encontrar_texto_referencia(original_limpio, texto_busqueda)
    texto_crudo = _bloques_a_texto(sub_bloques)
    ts_orig   = re.findall(r"\[\d+\.\d+\s*-\s*\d+\.\d+\]", texto_crudo)

    for intento in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": USER_PROMPT_TEMPLATE.format(
                        texto_ref=ref, seccion_txt=texto_crudo
                    )},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            corr    = resp.choices[0].message.content.strip()
            ts_corr = re.findall(r"\[\d+\.\d+\s*-\s*\d+\.\d+\]", corr)

            if ts_corr == ts_orig:
                nuevos = []
                for ln in corr.split('\n'):
                    m = re.search(r"\[(\d+\.\d+)\s*-\s*(\d+\.\d+)\]:\s*(.+)$", ln.strip())
                    if m:
                        nuevos.append({
                            "start": float(m.group(1)),
                            "end":   float(m.group(2)),
                            "text":  m.group(3).strip(),
                        })
                if len(nuevos) == len(sub_bloques):
                    return nuevos

            print(f"⚠️ Timestamps alterados o recuento incorrecto — intento {intento}/3")
        except Exception as e:
            print(f"❌ Error API spell_agent: {e}")
            time.sleep(2)

    print("❌ Fallo crítico en corrección — retornando bloques originales")
    return sub_bloques


# ── DB helper ─────────────────────────────────────────────────────────────────

def _update_db(class_id: int, updates: dict):
    from database import SessionLocal
    import models
    db = SessionLocal()
    try:
        row = db.query(models.ClassSpellCorrection).filter(
            models.ClassSpellCorrection.class_id == class_id
        ).first()
        if row:
            for k, v in updates.items():
                setattr(row, k, v)
            row.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[spell_agent] DB error: {e}")
    finally:
        db.close()


# ── Entry point (background thread) ──────────────────────────────────────────

def run_spell_correction(class_id: int, raw_narration: str, bloques_crudos: list):
    """
    Port exacto de CorrectorOrtografia.corregir_memoria().
    raw_narration → referencia de texto limpio.
    bloques_crudos → [{start, end, text}] de ClassAudio.tx_segments.
    """

    def phase(status, pct, msg, error=None):
        upd = {"status": status, "progress": pct, "phase": msg}
        if error is not None:
            upd["error"] = error
        _update_db(class_id, upd)

    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            phase("error", 0, "❌ OPENAI_API_KEY no encontrada", error="OPENAI_API_KEY no configurada")
            return

        client = OpenAI(api_key=api_key)
        original_limpio = _limpiar_texto_original(raw_narration)

        # Fragmentar en batches de CONTEXT_THRESHOLD (igual que 0_referencia)
        batches, current = [], []
        for b in bloques_crudos:
            current.append(b)
            if len(current) >= CONTEXT_THRESHOLD:
                batches.append(current)
                current = []
        if current:
            batches.append(current)

        phase("running", 5,
              f"✨ Corrección ortográfica — {len(batches)} batches · {len(bloques_crudos)} bloques")

        finales = []
        for i, batch in enumerate(batches):
            pct = 5 + int((i / len(batches)) * 90)
            phase("running", pct, f"✏️ Corrigiendo batch {i + 1}/{len(batches)}…")
            corrected = _corregir_seccion(client, batch, original_limpio)
            finales.extend(corrected)
            time.sleep(1)   # Rate limiting — igual que 0_referencia

        raw_text = _bloques_a_texto(finales)

        _update_db(class_id, {
            "status":        "done",
            "progress":      100,
            "phase":         f"✅ Corrección completada — {len(finales)} bloques",
            "error":         None,
            "segments_json": json.dumps(finales, ensure_ascii=False),
            "raw_text":      raw_text,
        })

    except Exception as e:
        err = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        phase("error", 0, "❌ Error en corrección ortográfica", error=err)
