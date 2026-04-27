from .base import call_llm

SYSTEM = """Eres un auditor de coherencia estructural para libros de no-ficción. Tu única función: detectar solapamientos conceptuales entre capítulos con precisión clínica.

QUÉ ES UN SOLAPAMIENTO:
Un solapamiento ocurre cuando dos capítulos tocan el mismo concepto, mecanismo, o enseñanza desde ángulos tan similares que el lector recibiría información redundante. No es solapamiento que dos capítulos mencionen el mismo tema — es solapamiento cuando ambos ENSEÑAN lo mismo sobre ese tema.

NIVELES DE SEVERIDAD:
- ALTO: El solapamiento invalida uno de los dos capítulos. Sin resolución, el lector notará la repetición y perderá confianza. Debe fusionarse o eliminarse uno.
- MEDIO: Hay superposición parcial que puede confundir. Requiere delimitar mejor los territorios y asegurarse de que cada capítulo entre al tema desde un ángulo claramente distinto.
- BAJO: Hay resonancia temática natural y aceptable. Puede mantenerse si los tratamientos son genuinamente distintos.

TU EVALUACIÓN DEBE SER:
- Basada en los TERRITORIOS EXCLUSIVOS declarados, no solo en los títulos
- Específica: di exactamente qué parte se solapa, no "estos dos capítulos son similares"
- Accionable: la resolución sugerida debe ser concreta y aplicable

SCORING DE COHERENCIA:
- 90-100: Sin solapamientos significativos, estructura sólida
- 75-89: Solapamientos menores o medios que se pueden resolver fácilmente
- 60-74: Solapamientos medios que requieren revisión seria
- <60: Solapamientos altos que invalidan la estructura actual

Responde en este JSON exacto:
{
  "solapamientos": [
    {
      "capitulo_a": 2,
      "capitulo_b": 5,
      "descripcion": "Descripción específica de qué exactamente se solapa entre estos dos capítulos",
      "severidad": "alto|medio|bajo",
      "resolucion_sugerida": "Instrucción concreta de cómo resolver este solapamiento específico"
    }
  ],
  "evaluacion_general": "Evaluación honesta de la coherencia global de la estructura",
  "score_coherencia": 85
}

Si no hay solapamientos, devuelve "solapamientos": [] con score alto y evaluación positiva."""


FIX_SYSTEM = """Eres un editor estructural de libros de no-ficción. Tu tarea es reescribir los territorios exclusivos de dos capítulos para eliminar el solapamiento detectado.

REGLAS:
1. Cada territorio debe declarar qué cubre ESE capítulo y SOLO ese capítulo
2. Los nuevos territorios no deben contradecir la tesis del capítulo — solo acotar mejor su scope
3. Sé específico y quirúrgico — el menor cambio que resuelva el solapamiento
4. El territorio debe seguir siendo una declaración positiva de lo que el capítulo SÍ cubre

Responde en este JSON exacto:
{
  "capitulo_a": {
    "num": 2,
    "territorio_exclusivo": "Nuevo territorio acotado para el capítulo A"
  },
  "capitulo_b": {
    "num": 5,
    "territorio_exclusivo": "Nuevo territorio acotado para el capítulo B"
  },
  "explicacion": "Qué cambió y por qué esto resuelve el solapamiento"
}"""


def fix_overlap(chapter_a: dict, chapter_b: dict, descripcion: str, resolucion_sugerida: str) -> dict:
    """Rewrite the exclusive territories of two chapters to eliminate an overlap."""
    prompt = f"""SOLAPAMIENTO DETECTADO:
{descripcion}

RESOLUCIÓN SUGERIDA:
{resolucion_sugerida}

CAPÍTULO {chapter_a['num']}: {chapter_a['titulo']}
Tesis: {chapter_a['tesis']}
Territorio actual: {chapter_a['territorio_exclusivo']}

CAPÍTULO {chapter_b['num']}: {chapter_b['titulo']}
Tesis: {chapter_b['tesis']}
Territorio actual: {chapter_b['territorio_exclusivo']}

Reescribe los territorios exclusivos de ambos capítulos para eliminar el solapamiento aplicando la resolución sugerida."""

    result = call_llm(prompt, FIX_SYSTEM, temperature=0.3)
    return result


def check_overlaps(chapters: list) -> dict:
    """Analyze all chapters for conceptual overlaps. Returns analysis dict."""
    chapters_desc = []
    for ch in chapters:
        chapters_desc.append(
            f"Capítulo {ch['num']}: {ch['titulo']}\n"
            f"  Tesis: {ch['tesis']}\n"
            f"  Territorio exclusivo: {ch['territorio_exclusivo']}\n"
            f"  Posición: {ch['posicion_arco']}"
        )

    prompt = f"""Analiza la coherencia de esta estructura de {len(chapters)} capítulos y detecta todos los solapamientos conceptuales:

{chr(10).join(chapters_desc)}

Sé riguroso: examina CADA par posible de capítulos. Un lector que lea el libro completo no debe sentir que le están repitiendo información. Si dos capítulos pueden confundirse, hay solapamiento."""

    result = call_llm(prompt, SYSTEM, temperature=0.3)
    return result
