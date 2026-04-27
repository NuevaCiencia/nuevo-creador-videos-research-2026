from .base import call_llm

SYSTEM = """Eres un especialista en estructura interna de capítulos para libros de no-ficción de alta calidad.

Tu tarea: diseñar las PARTES de un capítulo con precisión quirúrgica. Cada parte debe tener un propósito único e irremplazable. No hay partes decorativas.

TIPOS DE PARTES DISPONIBLES:
- apertura: Hook inicial que engancha al lector en las primeras líneas — una historia, pregunta o dato impactante
- ciencia: Base científica, investigación, estudios o datos que respaldan la tesis del capítulo
- historia: Caso real, narrativa o anécdota que ilustra el concepto de forma visceral
- teoria: Explicación conceptual del framework, modelo o idea central del capítulo
- ejercicio: Actividad práctica, reflexión guiada o herramienta que el lector puede usar ahora mismo
- reflexion: Preguntas que invitan al lector a aplicar lo aprendido a su situación específica
- sintesis: Resumen, puente hacia el siguiente capítulo y consolidación del aprendizaje

REGLAS DE COMPOSICIÓN:
1. Todo capítulo debe tener apertura y síntesis
2. No poner dos partes del mismo tipo consecutivas (excepto historia)
3. El orden importa: apertura → ciencia/teoria → historia → ejercicio/reflexion → sintesis
4. Los puntos clave deben ser específicos y accionables, no descripciones generales
5. La estimación de palabras debe ser realista: apertura ~300-500, ciencia ~600-900, historia ~500-800, teoria ~700-1000, ejercicio ~400-700, reflexion ~300-500, sintesis ~300-400

Responde en este JSON exacto:
{
  "partes": [
    {
      "numero": 1,
      "titulo": "Título evocador de la parte (no genérico)",
      "tipo": "apertura|ciencia|historia|teoria|ejercicio|reflexion|sintesis",
      "puntos_clave": [
        "Punto específico y accionable 1",
        "Punto específico y accionable 2",
        "Punto específico y accionable 3"
      ],
      "proposito": "Qué aporta esta parte al lector y por qué es necesaria aquí",
      "palabras_estimadas": 500
    }
  ]
}"""


def generate_parts(chapter: dict, book_idea: str) -> list:
    """Generate internal parts for a single chapter."""
    prompt = f"""CONTEXTO DEL LIBRO: {book_idea}

CAPÍTULO: {chapter.get('num', '?')}. {chapter.get('titulo', '')}
TESIS: {chapter.get('tesis', '')}
TERRITORIO EXCLUSIVO: {chapter.get('territorio_exclusivo', '')}
POSICIÓN EN EL ARCO: {chapter.get('posicion_arco', '')}
PROPÓSITO: {chapter.get('proposito', '')}
PROMESA AL LECTOR: {chapter.get('promesa_al_lector', '')}

Diseña las partes internas de este capítulo. Generalmente entre 4 y 7 partes es el rango óptimo. Adapta la cantidad a lo que este capítulo específico necesita para cumplir su promesa.

Cada parte debe tener un título evocador (no "Introducción", "Conclusión" — sé específico sobre el contenido real)."""

    result = call_llm(prompt, SYSTEM, temperature=0.75)
    return result.get('partes', [])
