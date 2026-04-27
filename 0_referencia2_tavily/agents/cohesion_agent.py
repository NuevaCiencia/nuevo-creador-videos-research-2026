from .base import call_llm, call_claude
from .tone_agent import build_tone_prompt_block
from config import (
    POLISH_SYSTEM_GPT, POLISH_SYSTEM_CLAUDE,
    REGEN_SYSTEM_GPT, REGEN_SYSTEM_CLAUDE,
    EVALUATION_SYSTEM, EVALUATION_LLM_MODEL,
)


def polish_full_chapter(
    chapter: dict,
    parts_content_list: list,
    tone: dict,
    word_bans: list,
    book_context: list,
    book_idea: str,
    use_claude: bool = False,
) -> str:
    tone_block = build_tone_prompt_block(tone or {}, word_bans or [])

    # Construir el contexto de las partes
    parts_text = []
    for i, part in enumerate(parts_content_list):
        parts_text.append(f"━━━ PARTE {i+1}: {part.get('titulo', '')} ({part.get('tipo', '')}) ━━━\n{part.get('content', '')}\n")
    full_draft = "\n".join(parts_text)

    # Construir el contexto del libro
    book_context_block = ""
    if book_context:
        book_context_block = "CONTEXTO DEL LIBRO (Para evitar repetir o adelantar temas de otros capítulos):\n"
        for ch in book_context:
            marker = " (→ ESTE ES TU CAPÍTULO)" if ch['id'] == chapter['id'] else ""
            book_context_block += f"- Cap {ch.get('num', '')}: {ch.get('titulo', '')} - Tesis: {ch.get('tesis', '')}{marker}\n"

    if use_claude:
        system = POLISH_SYSTEM_CLAUDE
        prompt = f"""LIBRO: {book_idea}

CAPÍTULO A EDITAR:
Capítulo {chapter.get('num', '')}: {chapter.get('titulo', '')}
Tesis: {chapter.get('tesis', '')}
Territorio exclusivo: {chapter.get('territorio_exclusivo', '')}

{book_context_block}
{tone_block}

━━━ BORRADOR EN PARTES (DEBES DISOLVER ESTA ESTRUCTURA EN UN ÚNICO TEXTO CONTINUO) ━━━
El siguiente borrador está dividido en partes marcadas. Tu output debe eliminar completamente esa estructura y producir un único capítulo en prosa corrida, sin separadores ni encabezados de sección.

{full_draft}

Produce el capítulo como UN SOLO BLOQUE de prosa continua. No incluyas el título ni marcadores de parte."""
        result = call_claude(prompt, system, temperature=0.7)
    else:
        system = POLISH_SYSTEM_GPT
        prompt = f"""LIBRO: {book_idea}

CAPÍTULO A EDITAR:
Capítulo {chapter.get('num', '')}: {chapter.get('titulo', '')}
Tesis: {chapter.get('tesis', '')}
Territorio exclusivo: {chapter.get('territorio_exclusivo', '')}

{book_context_block}
{tone_block}

━━━ BORRADOR DEL CAPÍTULO ━━━
El siguiente texto es la unión en bruto de todas las partes escritas del capítulo.
Tu tarea es leerlo por completo, consolidar, eliminar solapamientos y generar una versión final perfecta.

{full_draft}

Escribe el capítulo consolidado completo. No incluyas el título en el texto, empieza directamente con la narrativa."""
        result = call_llm(prompt, system, temperature=0.7)

    return result.get('content', '')


def evaluate_consolidated_chapter(content: str) -> str:
    prompt = f"TEXTO A EVALUAR:\n\n{content}"
    try:
        result = call_llm(prompt, EVALUATION_SYSTEM, temperature=0.5, model_override=EVALUATION_LLM_MODEL)
        return result.get('evaluacion', 'Error en la evaluación.')
    except Exception as e:
        return f"Error al generar la evaluación: {str(e)}"


def regenerate_consolidated_chapter(
    content: str,
    evaluation: str,
    tone: dict,
    word_bans: list,
    book_idea: str,
    use_claude: bool = True,
) -> str:
    tone_block = build_tone_prompt_block(tone or {}, word_bans or [])

    if use_claude:
        system = REGEN_SYSTEM_CLAUDE
        prompt = f"""LIBRO: {book_idea}

{tone_block}

━━━ EVALUACIÓN EDITORIAL — CORRÍGELA AL PIE DE LA LETRA ━━━
{evaluation}

━━━ TEXTO ACTUAL DEL CAPÍTULO ━━━
{content}

Reescribe el capítulo completo como UN ÚNICO BLOQUE DE PROSA CONTINUA aplicando cada corrección de la evaluación. Sin separadores, sin subtítulos, sin numeraciones. Solo narrativa corrida."""
        result = call_claude(prompt, system, temperature=0.7)
    else:
        system = REGEN_SYSTEM_GPT
        prompt = f"""LIBRO: {book_idea}

{tone_block}

━━━ EVALUACIÓN EDITORIAL (CORRIGE ESTO) ━━━
{evaluation}

━━━ TEXTO ACTUAL DEL CAPÍTULO ━━━
{content}

Reescribe el capítulo completo aplicando las correcciones de la evaluación. No incluyas el título en el texto, empieza directamente con la narrativa."""
        result = call_llm(prompt, system, temperature=0.7)

    return result.get('content', '')
