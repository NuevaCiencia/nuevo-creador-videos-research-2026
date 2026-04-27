from .base import call_llm

SYSTEM = """Eres un escritor fantasma de élite con 20 años de experiencia en libros de no-ficción y autoayuda.

Tu tarea es generar párrafos de ejemplo que demuestren con precisión el tono, registro y estilo solicitados. Estos párrafos serán usados como PATRÓN DE REFERENCIA para escribir todo el libro.

REGLAS ABSOLUTAS AL GENERAR LOS EJEMPLOS:
1. Usa el tema REAL del libro — no ejemplos genéricos
2. El párrafo debe demostrar el tono de forma inequívoca, no describirlo
3. Cada opción debe sentirse DISTINTA en su musicalidad y cadencia
4. La calidad literaria debe ser alta: cada oración debe ganarse su lugar

ERRORES QUE DEBES EVITAR (son señales de escritura de IA):
- Empezar con "En el mundo actual..." o similares
- Usar: fascinante, transformador, crucial, fundamental, sin lugar a dudas
- Cerrar con moraleja obvia o resumen innecesario
- Frases que podrían estar en cualquier libro sobre cualquier tema

Responde en este JSON exacto:
{
  "ejemplos": [
    {
      "etiqueta": "Nombre corto del estilo (ej: Directo y clínico)",
      "parrafo": "El párrafo de ejemplo de 120-180 palabras"
    }
  ]
}"""

TONE_LABELS = {
    'voz': {
        'primera': 'narración en primera persona (el autor habla de su propia experiencia)',
        'segunda': 'segunda persona (habla directamente al lector: "tú")',
        'mixta': 'mezcla: segunda persona dominante, primera persona para anclaje personal',
    },
    'registro': {
        'conversacional': 'tono conversacional, como si hablaras cara a cara con el lector',
        'periodistico': 'tono periodístico: preciso, directo, hechos concretos primero',
        'academico_accesible': 'académico pero accesible: rigor intelectual sin jerga innecesaria',
        'intimo': 'íntimo y confesional: el autor como confidente',
    },
    'longitud_frase': {
        'corta': 'frases cortas e impactantes. Punto seguido frecuente. Ritmo staccato.',
        'media': 'frases de longitud media, fluidas, con subordinadas ocasionales',
        'mixta': 'ritmo mixto deliberado: frase corta para impacto, larga para desarrollo, corta de cierre',
    },
    'uso_metaforas': {
        'frecuente': 'metáforas y analogías frecuentes, el concepto siempre anclado en imagen concreta',
        'moderado': 'metáforas selectivas: solo cuando iluminan algo que el lenguaje directo no puede',
        'minimo': 'lenguaje directo y preciso, metáforas casi inexistentes',
    },
    'tratamiento_ciencia': {
        'analogias': 'la ciencia siempre traducida a analogía cotidiana antes de explicarla técnicamente',
        'integrada': 'datos científicos integrados en el flujo narrativo sin interrumpirlo',
        'informal': 'referencias científicas informales, sin nombres de estudios ni jerga',
    },
    'temperatura_emocional': {
        'alta': 'emocionalmente intenso: urgencia, empatía profunda, momentos de vulnerabilidad',
        'equilibrada': 'equilibrio entre cabeza y corazón: emoción real pero contenida',
        'racional_calidez': 'predominantemente racional, con destellos de calidez humana',
    },
}


def _describe_tone(config: dict) -> str:
    parts = []
    for field, mapping in TONE_LABELS.items():
        val = config.get(field, '')
        if val in mapping:
            parts.append(f"- {mapping[val]}")
    if config.get('instrucciones_adicionales'):
        parts.append(f"- Instrucción adicional: {config['instrucciones_adicionales']}")
    return '\n'.join(parts)


def generate_tone_examples(book_idea: str, titulo: str, tone_config: dict) -> list:
    """Generate 3 paragraph examples demonstrating the chosen tone."""
    tone_desc = _describe_tone(tone_config)

    prompt = f"""LIBRO: {titulo}
IDEA CENTRAL: {book_idea}

TONO SOLICITADO:
{tone_desc}

Genera 3 párrafos de ejemplo que demuestren este tono aplicado al tema real de este libro.
Cada ejemplo debe ser una variación dentro del mismo tono — ligeras diferencias de cadencia o punto de entrada, pero todos fieles al estilo solicitado.
El lector del libro real podría encontrar cualquiera de estos párrafos en el capítulo 1."""

    result = call_llm(prompt, SYSTEM, temperature=0.85)
    return result.get('ejemplos', [])


def build_tone_prompt_block(tone: dict, word_bans: list) -> str:
    """Build the tone instruction block to inject into every writing prompt."""
    if not tone:
        return ""

    lines = ["─── TONO Y ESTILO ───"]
    
    if tone.get('is_auto_generated') == 1 and tone.get('prompt_rector'):
        lines.append(tone['prompt_rector'])
    else:
        tone_desc = _describe_tone(tone)
        lines.append(tone_desc)

        if tone.get('parrafo_ancla') and tone.get('parrafo_ancla_aprobado'):
            lines.append("\nPÁRRAFO ANCLA — SOLO REFERENCIA DE VOZ Y ESTILO:")
            lines.append(f'"{tone["parrafo_ancla"]}"')
            lines.append("↑ Este párrafo es una muestra del estilo del libro. NUNCA lo copies, ni parcialmente.")
            lines.append("  No lo uses como apertura. No lo parafrasees. No lo repitas.")
            lines.append("  Solo imita su cadencia, su temperatura emocional y su densidad.")
            lines.append("  Si tu sección empieza igual o parecido a este párrafo, está mal.")

    if word_bans:
        lines.append(f"\nPALABRAS Y FRASES PROHIBIDAS (no uses ninguna de estas):")
        lines.append(", ".join(f'"{w}"' for w in word_bans))

    lines.append("─────────────────────")
    return '\n'.join(lines)
