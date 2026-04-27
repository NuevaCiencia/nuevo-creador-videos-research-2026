from .base import call_llm

SYSTEM = """Eres un editor literario de élite, especializado en libros de no-ficción, autoayuda y desarrollo personal con respaldo científico.

Tu tarea es generar opciones de título que sean MAGNÉTICAS: claros en su promesa, memorables, que evoquen curiosidad o urgencia, y que hablen directamente al lector objetivo.

CRITERIOS PARA UN TÍTULO EXCEPCIONAL:
- El título principal: corto, poderoso, fácil de recordar (máx. 6 palabras idealmente)
- El subtítulo: explica el MÉTODO o la PROMESA específica, menciona al lector si aplica
- Evita clichés del género: "el arte de", "la ciencia de", "descubre tu..."
- El subtítulo debe ser lo suficientemente específico para diferenciar el libro de cualquier otro sobre el mismo tema

Responde SIEMPRE en este JSON exacto:
{
  "opciones": [
    {
      "titulo": "...",
      "subtitulo": "...",
      "razon": "Por qué este título captura la esencia del libro y atrae al lector objetivo"
    }
  ]
}"""


def generate_titles(core_idea: str, target_reader: str = '', key_problem: str = '') -> list:
    """Generate 6 title options for the book."""
    context_parts = [f"IDEA DEL LIBRO:\n{core_idea}"]
    if target_reader:
        context_parts.append(f"LECTOR OBJETIVO:\n{target_reader}")
    if key_problem:
        context_parts.append(f"PROBLEMA PRINCIPAL QUE RESUELVE:\n{key_problem}")

    prompt = "\n\n".join(context_parts)
    prompt += "\n\nGenera exactamente 6 opciones de título distintas entre sí. Cada una debe explorar un ángulo diferente: emocional, racional, provocador, aspiracional, directo, metafórico."

    result = call_llm(prompt, SYSTEM, temperature=0.9)
    return result.get('opciones', [])
