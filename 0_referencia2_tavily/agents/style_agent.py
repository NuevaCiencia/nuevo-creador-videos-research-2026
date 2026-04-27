import re
import math
import json
from .base import call_llm, embed_text

# ─── Reference corpus ─────────────────────────────────────────────────────────

STYLE_CORPUS = [
    # apertura_escena
    {
        "label": "Apertura: escena con acción concreta",
        "category": "apertura_escena",
        "text": "La llamada llegó un martes, cuando aún quedaba media taza de café en el escritorio. Era el director financiero, y su voz tenía ese tono plano de quien ya tomó la decisión antes de marcar el número. Tres semanas después, Elena empacaba su escritorio en una caja de cartón mientras sus compañeros evitaban mirarla."
    },
    {
        "label": "Apertura: escena de decisión postergada",
        "category": "apertura_escena",
        "text": "A las siete de la mañana del lunes, Mariana abrió su laptop con la certeza de que iba a proponer la idea que llevaba semanas desarrollando. A las siete y cuarenta, después de leer un hilo sobre automatización, cerró el borrador sin enviar. No volvió a abrirlo."
    },
    {
        "label": "Apertura: escena de momento de quiebre",
        "category": "apertura_escena",
        "text": "Rodrigo llevaba cuarenta minutos preparando la presentación cuando el sistema le notificó que otro asistente ya había generado el informe que él estaba construyendo. No fue una sensación dramática. Fue una punzada pequeña, casi administrativa, que pasó al fondo de su mente y siguió ahí durante semanas."
    },
    # apertura_tension
    {
        "label": "Apertura: paradoja o tensión conceptual",
        "category": "apertura_tension",
        "text": "El problema con prepararse para el futuro es que el futuro ya empezó. No como anuncio, no como ola que se acerca: ya está aquí, en la herramienta que tu empresa adoptó sin pedirte opinión, en el proyecto que ya no requiere tu firma."
    },
    {
        "label": "Apertura: contradicción que abre preguntas",
        "category": "apertura_tension",
        "text": "Hay una paradoja en el centro de este libro: cuanto más inteligentes somos para prever la amenaza, más mal nos preparamos para ella. No porque seamos descuidados. Porque la mente que anticipa el golpe también tiende a esquivarlo de la peor manera posible."
    },
    {
        "label": "Apertura: afirmación incómoda sin retórica",
        "category": "apertura_tension",
        "text": "Nadie te va a decir el día exacto en que tu ventaja competitiva cambia. Eso es lo que hace que la pregunta sea tan difícil y tan urgente al mismo tiempo. Y es también la razón por la que la mayoría de la gente la posterga hasta que ya no tiene opciones cómodas."
    },
    # ritmo_variado
    {
        "label": "Ritmo variado: frase corta de impacto + desarrollo largo",
        "category": "ritmo_variado",
        "text": "Espera. Antes de seguir, necesitas ver algo. No como ejercicio, sino como diagnóstico. Piensa en la última semana laboral y en las decisiones que tomaste — no las grandes, las pequeñas: qué pediste, qué evitaste, qué propusiste y qué dejaste para después. Esas decisiones tienen un patrón. Y ese patrón, repetido sin interrupción durante meses, es lo que va a definir dónde estás dentro de dos años, mucho más que cualquier cambio tecnológico que aún no puedes predecir."
    },
    {
        "label": "Ritmo variado: acumulación + cierre corto",
        "category": "ritmo_variado",
        "text": "Hay semanas que enseñan y semanas que solo pasan. Las primeras tienen algo en común: una decisión incómoda que no postergaste, una conversación que iniciaste sin garantías, una tarea nueva que aceptaste aunque no sabías del todo cómo hacerla. Esas semanas dejan algo. Las otras también dejan algo: el hábito de esperar."
    },
    {
        "label": "Ritmo variado: explicación técnica con respiración",
        "category": "ritmo_variado",
        "text": "Tu cerebro es muy bueno detectando amenazas. Demasiado bueno, en realidad. Lo que no hace bien es distinguir entre una amenaza que requiere acción y una que requiere espera. Ante la incertidumbre, el sistema nervioso prefiere hacer algo — lo que sea — que quedarse quieto con la incomodidad. Ese instinto, útil cuando el peligro era concreto y físico, produce decisiones pésimas cuando el peligro es abstracto y futuro."
    },
    # ritmo_staccato
    {
        "label": "Ritmo staccato: frases cortas para impacto emocional",
        "category": "ritmo_staccato",
        "text": "No fue la IA. Fue la decisión de no aprender. No fue el mercado. Fue el hábito de esperar. No fue la empresa. Fuiste tú, en esa semana donde todo parecía normal, eligiendo no mover nada."
    },
    # registro_periodistico
    {
        "label": "Registro periodístico: datos primero, contexto después",
        "category": "registro_periodistico",
        "text": "Un estudio de McKinsey encontró que el 60% de los trabajadores cuyas tareas son parcialmente automatizables no han modificado sus habilidades en los últimos doce meses. No porque no quieran. Porque la amenaza no se siente suficientemente urgente hasta que ya es tarde para prepararse."
    },
    {
        "label": "Registro periodístico: cifra + matiz ignorado",
        "category": "registro_periodistico",
        "text": "Investigadores de Oxford estimaron que el 47% de los empleos tenían alta probabilidad de automatización. El Foro Económico Mundial revisó esa cifra hacia arriba y añadió un matiz que los titulares no incluyeron: los trabajos que desaparecen no son reemplazados por la IA directamente. Son reemplazados por personas que saben usarla."
    },
    # registro_conversacional
    {
        "label": "Registro conversacional: directo al lector",
        "category": "registro_conversacional",
        "text": "Mira tu agenda de la última semana. No la versión que le mostrarías a tu jefe — la real. ¿Cuántas horas pasaste en tareas que sabes que podrían estar automatizadas? ¿Cuántas evitaste proyectos donde podrías fallar visiblemente? Esos números te dicen más sobre tu estrategia que cualquier plan que hayas redactado."
    },
    {
        "label": "Registro conversacional: anclaje personal antes de concepto",
        "category": "registro_conversacional",
        "text": "Seguramente has tenido esa sensación. Estás en una reunión y alguien menciona una herramienta nueva, y por un segundo no sabes si preguntar o fingir que ya la conoces. Ese segundo vale mucho. No porque revele ignorancia — sino porque revela dónde está tu resistencia."
    },
    # cierre_con_movimiento
    {
        "label": "Cierre que crea movimiento, no resumen",
        "category": "cierre_movimiento",
        "text": "La pregunta no es si vas a cambiar. Es cuándo vas a dejar de esperar la señal perfecta para hacerlo. El siguiente capítulo empieza donde este termina: no con más análisis, sino con el primer ajuste que convierte la incertidumbre en una dirección concreta."
    },
    {
        "label": "Cierre con criterio de acción, sin moraleja",
        "category": "cierre_movimiento",
        "text": "Si esta semana tus conductas consisten en evitar, reaccionar tarde y negociar menos, ya tienes el diagnóstico. No necesitas más información. Necesitas un cambio observable, pequeño y medible, que empiece antes de que cierres este libro."
    },
]

SYNTHESIS_SYSTEM = """Eres un editor literario especializado en no-ficción y autoayuda. Recibes métricas de análisis de estilo de una sección de un libro y produces feedback accionable y específico.

REGLAS:
- Sé directo y concreto — no describas los problemas de forma vaga
- Cada observación debe incluir una corrección específica
- No más de 3 observaciones por sección
- Prioriza los problemas más graves
- El tono es de colega editor, no de corrector escolar

Responde en este JSON:
{
  "feedback": "Feedback principal en 2-3 oraciones concretas",
  "priority_fix": "La corrección más urgente en una sola oración accionable",
  "warnings": ["lista", "de", "alertas", "específicas"]
}"""


# ─── Structural analysis ──────────────────────────────────────────────────────

def _split_sentences(text: str) -> list:
    cleaned = re.sub(r'\s+', ' ', text.strip())
    parts = re.split(r'(?<=[.!?])\s+', cleaned)
    return [s.strip() for s in parts if s.strip() and len(s.split()) > 1]


def analyze_structure(content: str) -> dict:
    sentences = _split_sentences(content)
    if not sentences:
        return {'sentence_count': 0, 'rhythm_score': 0}

    lengths = [len(s.split()) for s in sentences]
    n = len(lengths)
    avg = sum(lengths) / n
    variance = sum((l - avg) ** 2 for l in lengths) / n
    std_dev = math.sqrt(variance)

    short_ratio = sum(1 for l in lengths if l <= 7) / n
    long_ratio = sum(1 for l in lengths if l >= 28) / n
    question_ratio = sum(1 for s in sentences if s.rstrip().endswith('?')) / n

    paragraphs = [p.strip() for p in content.split('\n') if p.strip() and len(p.split()) > 3]

    # Rhythm score: reward variance (varied = good), penalize monotony
    rhythm_score = min(100, int(std_dev * 6))
    if avg < 8:
        rhythm_score = max(0, rhythm_score - 25)   # staccato sin intención
    if avg > 30:
        rhythm_score = max(0, rhythm_score - 20)   # frases sin respiro

    opening_sentence = sentences[0] if sentences else ""

    return {
        'sentence_count': n,
        'avg_words': round(avg, 1),
        'std_dev': round(std_dev, 1),
        'rhythm_score': min(100, max(0, rhythm_score)),
        'short_ratio': round(short_ratio, 2),
        'long_ratio': round(long_ratio, 2),
        'question_ratio': round(question_ratio, 2),
        'paragraph_count': len(paragraphs),
        'opening_sentence': opening_sentence,
        'warning_monotonous': std_dev < 3.5,
        'warning_no_breathing': avg > 28,
        'warning_too_staccato': avg < 8 and n > 3,
        'warning_question_overuse': question_ratio > 0.3,
    }


# ─── Cosine similarity ────────────────────────────────────────────────────────

def _cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(y ** 2 for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─── Semantic analysis ────────────────────────────────────────────────────────

def analyze_semantics(content: str, anchor_emb: list, ref_embeddings: list) -> dict:
    try:
        [part_emb] = embed_text([content])
    except Exception:
        return {'drift_score': None, 'nearest_ref': None, 'nearest_sim': None}

    drift_sim = _cosine(part_emb, anchor_emb) if anchor_emb else None
    drift_score = round((1 - drift_sim) * 100) if drift_sim is not None else None

    nearest_ref = None
    nearest_sim = 0.0
    for ref in ref_embeddings:
        sim = _cosine(part_emb, ref['embedding'])
        if sim > nearest_sim:
            nearest_sim = sim
            nearest_ref = ref['label']

    # Opening-only embedding for clone detection
    sentences = _split_sentences(content)
    opening = ' '.join(sentences[:2]) if len(sentences) >= 2 else content[:200]
    try:
        [opening_emb] = embed_text([opening])
    except Exception:
        opening_emb = None

    return {
        'part_embedding': part_emb,
        'opening_embedding': opening_emb,
        'drift_score': drift_score,
        'anchor_similarity': round(drift_sim, 3) if drift_sim is not None else None,
        'nearest_ref_label': nearest_ref,
        'nearest_ref_similarity': round(nearest_sim, 3),
    }


def detect_clone_openings(parts_semantic: list) -> list:
    """Returns list of (part_num_a, part_num_b, similarity) for suspiciously similar openings."""
    clones = []
    valid = [(p['part_num'], p['opening_embedding']) for p in parts_semantic if p.get('opening_embedding')]
    for i, (num_a, emb_a) in enumerate(valid):
        for num_b, emb_b in valid[i + 1:]:
            sim = _cosine(emb_a, emb_b)
            if sim > 0.88:
                clones.append({'part_a': num_a, 'part_b': num_b, 'similarity': round(sim, 3)})
    return clones


# ─── LLM synthesis ───────────────────────────────────────────────────────────

def synthesize_feedback(part: dict, structural: dict, semantic: dict) -> dict:
    drift = semantic.get('drift_score')
    anchor_sim = semantic.get('anchor_similarity')
    warnings = []
    if structural.get('warning_monotonous'):
        warnings.append(f"Ritmo monótono: desviación estándar de frase = {structural['std_dev']} palabras (ideal > 5)")
    if structural.get('warning_no_breathing'):
        warnings.append(f"Frases sin respiro: promedio {structural['avg_words']} palabras por frase")
    if structural.get('warning_too_staccato'):
        warnings.append(f"Ritmo excesivamente staccato: promedio {structural['avg_words']} palabras por frase")
    if structural.get('warning_question_overuse'):
        warnings.append(f"Sobreuso de preguntas: {int(structural['question_ratio']*100)}% de las frases son preguntas")
    if drift is not None and drift > 40:
        warnings.append(f"Deriva de tono: similitud con párrafo ancla = {anchor_sim} (ideal > 0.65)")

    prompt = f"""PARTE: "{part.get('titulo', '')}" (tipo: {part.get('tipo', '')})
Propósito: {part.get('proposito', '')}

MÉTRICAS ESTRUCTURALES:
- Frases: {structural.get('sentence_count', '?')} | Promedio palabras/frase: {structural.get('avg_words', '?')} | Desviación estándar: {structural.get('std_dev', '?')}
- Score de ritmo: {structural.get('rhythm_score', '?')}/100
- Ratio frases cortas (≤7 palabras): {structural.get('short_ratio', '?')}
- Ratio frases largas (≥28 palabras): {structural.get('long_ratio', '?')}
- Primera oración: "{structural.get('opening_sentence', '')[:120]}"
- Estilo más cercano en corpus de referencia: {semantic.get('nearest_ref_label', 'no determinado')}

ALERTAS DETECTADAS:
{chr(10).join(f'- {w}' for w in warnings) if warnings else '- Ninguna alerta crítica'}

Produce feedback editorial accionable para mejorar esta sección."""

    try:
        result = call_llm(prompt, SYNTHESIS_SYSTEM, temperature=0.4)
        return result
    except Exception:
        return {
            'feedback': 'No se pudo generar síntesis automática.',
            'priority_fix': '',
            'warnings': warnings,
        }


# ─── Main review function ─────────────────────────────────────────────────────

def review_chapter(chapter: dict, parts: list, written_map: dict, tone: dict, ref_embeddings: list) -> dict:
    """
    Analyze all written parts of a chapter.
    written_map: {part_id: content_string}
    Returns review dict with per-part results and chapter-level summary.
    """
    anchor_emb = None
    if tone and tone.get('parrafo_ancla') and tone.get('parrafo_ancla_aprobado'):
        try:
            [anchor_emb] = embed_text([tone['parrafo_ancla']])
        except Exception:
            pass

    parts_results = []
    parts_semantic = []

    for part in parts:
        content = written_map.get(part['id'], '')
        if not content:
            continue

        structural = analyze_structure(content)
        semantic = analyze_semantics(content, anchor_emb, ref_embeddings)
        semantic['part_num'] = part['num']

        parts_semantic.append(semantic)

        feedback = synthesize_feedback(part, structural, semantic)

        parts_results.append({
            'part_id': part['id'],
            'part_num': part['num'],
            'part_titulo': part.get('titulo', ''),
            'part_tipo': part.get('tipo', ''),
            'structural': structural,
            'semantic': {k: v for k, v in semantic.items() if k not in ('part_embedding', 'opening_embedding')},
            'feedback': feedback,
        })

    clone_pairs = detect_clone_openings(parts_semantic)

    # Overall chapter score
    scores = [r['structural']['rhythm_score'] for r in parts_results if r['structural'].get('rhythm_score') is not None]
    drift_scores = [r['semantic']['drift_score'] for r in parts_results if r['semantic'].get('drift_score') is not None]

    avg_rhythm = round(sum(scores) / len(scores)) if scores else None
    avg_drift = round(sum(drift_scores) / len(drift_scores)) if drift_scores else None

    return {
        'chapter_id': chapter['id'],
        'chapter_titulo': chapter.get('titulo', ''),
        'parts': parts_results,
        'clone_openings': clone_pairs,
        'avg_rhythm_score': avg_rhythm,
        'avg_drift_score': avg_drift,
    }
