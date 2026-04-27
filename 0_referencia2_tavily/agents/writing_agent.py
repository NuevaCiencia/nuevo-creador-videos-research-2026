from .base import call_llm
from .tone_agent import build_tone_prompt_block

SYSTEM = """Eres un escritor fantasma de élite con 20 años de experiencia en libros de no-ficción y autoayuda.

Tu misión: escribir UNA SECCIÓN ESPECÍFICA de un capítulo con el máximo nivel de calidad literaria.

PRINCIPIOS ABSOLUTOS:
1. Escribe SOLO sobre el territorio declarado de esta parte — ni más, ni menos
2. La voz del párrafo ancla es la referencia de ESTILO, nunca de contenido — no lo copies
3. Cada parte del capítulo debe tener una entrada ÚNICA y DISTINTA a las demás
4. Usa la investigación solo cuando encaje orgánicamente, nunca forzada
5. La longitud debe acercarse a las palabras estimadas

SEÑALES DE ESCRITURA DE IA QUE DEBES ELIMINAR:
- Empezar con "En este capítulo/sección/texto..."
- Listar puntos mecánicamente: "Primero...", "Segundo...", "Tercero..."
- Transiciones telegráficas: "Como veremos...", "Pasemos ahora a..."
- Cierre con moraleja obvia o resumen
- Frases que podrían aparecer en cualquier libro sobre cualquier tema
- Abrir con una pregunta retórica genérica ("¿Te has preguntado alguna vez...")
- Copiar o parafrasear el párrafo ancla — si tu apertura recuerda al ancla, reescríbela

COHERENCIA DE VOZ — REGLA DE ORO:
- Cada párrafo tiene UNA sola persona gramatical dominante — nunca mezcles en el mismo párrafo
- Si estás narrando una historia real (tercera persona): "ella/él/ellos" — hasta que termines ese bloque
- Si estás hablando al lector (segunda persona): "tú/te/tu" — hasta que termines ese bloque
- El cambio de voz es una decisión estructural, no algo que ocurre sin querer dentro de un párrafo
- Una frase de pivote explícita sirve de puente entre registros: "Lo que Elena no vio es lo que tú..."

COHERENCIA NARRATIVA ENTRE PARTES:
- Conoces el arco completo del capítulo (se te da la lista de todas las partes)
- Tu sección debe conectar con lo anterior y preparar lo siguiente
- Si la parte previa explicó un mecanismo, tú puedes aplicarlo; no re-explicarlo
- Si la parte siguiente es un ejercicio, cierra tu sección dejando al lector listo para actuar

Responde ÚNICAMENTE en este JSON:
{
  "content": "El texto completo de la sección"
}"""

REWRITE_SYSTEM = """Eres un editor literario de élite. Reescribes secciones de libros siguiendo instrucciones del autor sin perder la voz ni la coherencia narrativa.

REGLAS:
1. Respeta el territorio de la parte — no te salgas de su scope
2. Mantén la voz y tono del libro
3. Aplica EXACTAMENTE las instrucciones del autor
4. Preserva o mejora la calidad literaria del texto original
5. No copies el párrafo ancla

REGLA DE VOZ — CRÍTICA:
Cada párrafo tiene UNA sola persona gramatical dominante. Nunca mezcles en el mismo párrafo.
- Narración de historia real: tercera persona hasta cerrar ese bloque
- Conexión con el lector: segunda persona (o la voz del libro) hasta cerrar ese bloque
- Si el autor pide "inicia con una historia en tercera persona", toda la narración de esa
  historia debe estar en tercera persona, sin "tú/te" mezclados dentro de esos párrafos.
  El cambio a segunda persona ocurre DESPUÉS, en un párrafo nuevo con pivote explícito.

Responde ÚNICAMENTE en este JSON:
{
  "content": "El texto reescrito de la sección"
}"""

TYPE_INSTRUCTIONS = {
    'apertura': """INSTRUCCIONES ESPECIALES — APERTURA DE CAPÍTULO:
Esta es la primera sección. Abre el capítulo como lo haría un libro real de no-ficción de primer nivel.
- Arranca con una escena concreta, un dato que sacuda, una paradoja o una tensión que ponga al lector en movimiento
- No empieces con pregunta retórica genérica ni con contexto histórico
- El lector debe estar dentro del problema antes de que acabe el primer párrafo
- Establece la tesis del capítulo de forma oblicua, no declarativa ("En este capítulo vamos a ver..." está prohibido)
- El tono debe generar urgencia o curiosidad, no exposición académica""",

    'ciencia': """INSTRUCCIONES ESPECIALES — SECCIÓN DE CIENCIA:
- Integra los hallazgos científicos en el flujo narrativo — no los presentes como lista de estudios
- Primero la idea o tensión, luego el respaldo científico, no al revés
- Humaniza cada hallazgo: explica qué significa en términos de decisiones reales
- Si citas un autor, hazlo en una frase que justifique su presencia, no como referencia bibliográfica
- La ciencia ilumina, no decora""",

    'historia': """INSTRUCCIONES ESPECIALES — SECCIÓN DE HISTORIA REAL:

REGLA DE VOZ — CRÍTICA:
Esta sección tiene DOS registros con voces distintas. NUNCA los mezcles en el mismo párrafo:

  REGISTRO 1 — NARRACIÓN DE LA HISTORIA: tercera persona
    El protagonista actúa, decide, falla o descubre. Tú narras desde fuera.
    "Elena cerró el portátil a las 11pm y pensó que mañana lo arreglaba."
    NO uses "tú" ni "te" cuando estás narrando al protagonista.

  REGISTRO 2 — CONEXIÓN CON EL LECTOR: segunda persona (o la voz configurada del libro)
    Cuando salgas de la historia para conectar con el lector, cambia de voz explícitamente.
    "Lo que Elena no veía es lo que tú sí puedes ver en tu propia semana."
    Nunca mezcles esto dentro del párrafo de narración.

ESTRUCTURA RECOMENDADA:
  1. Abre con el protagonista EN ACCIÓN (tercera persona, imagen concreta, momento específico)
  2. Desarrolla la historia en tercera persona — que el lector la viva
  3. Haz el pivote explícito: una frase corta que cierre la historia y abra la conexión
  4. Conecta con el lector en la voz del libro (segunda persona si ese es el tono)

PROHIBIDO:
- Mezclar "ella/él" y "tú/te" en el mismo párrafo narrativo
- Abrir con "La historia de X nos enseña que..."
- Convertir la historia en un ejemplo ilustrativo — debe sentirse real y específica
- Resumir la historia en lugar de narrarla""",

    'ejercicio': """INSTRUCCIONES ESPECIALES — SECCIÓN DE EJERCICIO:
- Sé directivo desde la primera línea: el lector sabe que va a hacer algo
- Cada instrucción debe ser específica y ejecutable (con verbos concretos, plazos reales)
- Anticipa la resistencia: dile al lector por qué vale la pena hacerlo ahora
- El ejercicio debe ser pequeño y medible — no un proyecto, sino un gesto con feedback rápido
- Cierra con lo que el lector va a notar o aprender al completarlo""",

    'reflexion': """INSTRUCCIONES ESPECIALES — SECCIÓN DE REFLEXIÓN:
- No es un resumen disfrazado ni un sermón
- Plantea preguntas de alto impacto que desplacen la perspectiva del lector
- Las preguntas deben ser incómodas, específicas, no retóricas ni genéricas
- Alterna entre pregunta y consecuencia concreta de esa pregunta
- El lector debe terminar esta sección con una imagen mental de sí mismo más nítida""",

    'sintesis': """INSTRUCCIONES ESPECIALES — SÍNTESIS FINAL DEL CAPÍTULO:
- No hagas un resumen de lo que el lector acaba de leer — él ya lo leyó
- Consolida el argumento en una frase que lo lleve más lejos de donde empezó
- Cierra con movimiento hacia adelante: el lector debe sentir que hay un siguiente paso lógico
- Establece el puente al siguiente capítulo sin nombrarlo directamente
- No cierres con moraleja de autoayuda — cierra con un criterio de acción concreto""",

    'teoria': """INSTRUCCIONES ESPECIALES — SECCIÓN TEÓRICA:
- Primero el concepto en términos de vida real, luego la teoría formal
- Cada idea abstracta necesita una imagen concreta que la ancle
- Evita la acumulación de conceptos: desarrolla uno bien en lugar de listar cinco
- El lector debe poder usar la teoría para tomar una decisión — si no puede, la sección está incompleta""",
}


def write_part(
    part: dict,
    chapter: dict,
    book_idea: str,
    tone: dict,
    word_bans: list,
    research_items: list = None,
    written_context: str = "",
    all_parts: list = None,
) -> str:
    tone_block = build_tone_prompt_block(tone or {}, word_bans or [])
    puntos = part.get('puntos_clave') or []
    puntos_text = "\n".join(f"  • {p}" for p in puntos)
    research_block = _build_research_block(research_items or [], part.get('num', 0))
    type_instruction = TYPE_INSTRUCTIONS.get(part.get('tipo', ''), '')

    # Chapter arc block
    arc_block = _build_arc_block(part, all_parts or [])

    # Written context block
    context_block = ""
    if written_context:
        context_block = f"""━━━ YA ESCRITO EN ESTE CAPÍTULO (construye sobre esto, NO lo repitas) ━━━
{written_context}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    prompt = f"""LIBRO: {book_idea}

CAPÍTULO {chapter.get('num', '')}: {chapter.get('titulo', '')}
Tesis del capítulo: {chapter.get('tesis', '')}
Territorio exclusivo: {chapter.get('territorio_exclusivo', '')}
Posición en el arco narrativo: {chapter.get('posicion_arco', '')}
Promesa al lector: {chapter.get('promesa_al_lector', '')}

{arc_block}
━━━ PARTE A ESCRIBIR AHORA ━━━
Título: {part.get('titulo', '')}
Tipo: {part.get('tipo', '')}
Propósito: {part.get('proposito', '')}
Puntos clave que DEBEN quedar cubiertos:
{puntos_text}
Longitud objetivo: ~{part.get('palabras_estimadas', 500)} palabras

{type_instruction}

{context_block}

{research_block}
{tone_block}

Escribe la sección completa. No incluyas el título en el texto. Entrada única — distinta a todas las demás partes del capítulo."""

    result = call_llm(prompt, SYSTEM, temperature=0.8)
    return result.get('content', '')


def rewrite_part(
    original_content: str,
    instructions: str,
    part: dict,
    chapter: dict,
    book_idea: str,
    tone: dict,
    word_bans: list,
) -> str:
    tone_block = build_tone_prompt_block(tone or {}, word_bans or [])

    prompt = f"""LIBRO: {book_idea}

CAPÍTULO {chapter.get('num', '')}: {chapter.get('titulo', '')}
Tesis: {chapter.get('tesis', '')}

PARTE: {part.get('titulo', '')} (tipo: {part.get('tipo', '')})
Propósito: {part.get('proposito', '')}
Longitud objetivo: ~{part.get('palabras_estimadas', 500)} palabras

TEXTO ORIGINAL:
{original_content}

━━━ INSTRUCCIONES DEL AUTOR ━━━
{instructions}

{tone_block}

Reescribe la sección aplicando las instrucciones. No incluyas el título. No copies el párrafo ancla."""

    result = call_llm(prompt, REWRITE_SYSTEM, temperature=0.78)
    return result.get('content', '')


def _build_arc_block(current_part: dict, all_parts: list) -> str:
    if not all_parts:
        return ""

    current_num = current_part.get('num', 0)
    total = len(all_parts)

    lines = [f"ARCO COMPLETO DEL CAPÍTULO ({total} partes):"]
    for p in all_parts:
        pnum = p.get('num', 0)
        marker = "→ ESTA" if pnum == current_num else "  "
        lines.append(f"{marker} Parte {pnum}: [{p.get('tipo', '').upper()}] {p.get('titulo', '')}")

    # Adjacent context
    prev_part = next((p for p in all_parts if p.get('num') == current_num - 1), None)
    next_part = next((p for p in all_parts if p.get('num') == current_num + 1), None)

    if prev_part or next_part:
        lines.append("")
        lines.append(f"Posición: parte {current_num} de {total}")
        if prev_part:
            lines.append(f"Parte anterior ({prev_part.get('tipo', '')}): {prev_part.get('titulo', '')} — {prev_part.get('proposito', '')[:100]}")
        if next_part:
            lines.append(f"Parte siguiente ({next_part.get('tipo', '')}): {next_part.get('titulo', '')} — {next_part.get('proposito', '')[:100]}")

    return '\n'.join(lines)


def _build_research_block(research_items: list, part_num: int) -> str:
    if not research_items:
        return ""

    science = [r for r in research_items if r.get('tipo') == 'ciencia']
    stories = [
        r for r in research_items
        if r.get('tipo') == 'historia' and r.get('parte_sugerida') == part_num
    ]

    lines = []
    if science:
        lines.append("RESPALDO CIENTÍFICO DISPONIBLE (integra orgánicamente si es relevante):")
        for s in science[:3]:
            autor_año = f"{s.get('autor', 'Autor desconocido')} ({s.get('año', '')})"
            lines.append(f"  • {autor_año}: {s.get('hallazgo_clave', '')}")

    if stories:
        lines.append("\nHISTORIA REAL SUGERIDA PARA ESTA PARTE:")
        for h in stories[:1]:
            lines.append(f"  • Protagonista: {h.get('protagonista', '')}")
            lines.append(f"    Qué pasó: {h.get('que_paso', '')}")
            lines.append(f"    Qué ilustra: {h.get('que_ilustra', '')}")

    return '\n'.join(lines) + "\n" if lines else ""
