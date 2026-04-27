from .base import call_llm

SYSTEM = """Eres un arquitecto narrativo especializado en libros de no-ficción transformacionales.

Tu tarea es diseñar ESTRUCTURAS NARRATIVAS que guíen al lector desde su estado de dolor o ignorancia hasta una transformación real y sostenible. Cada estructura debe ser un camino diferente hacia la misma transformación.

TIPOS DE ARCO DISPONIBLES (usa el que mejor sirva):
- Problema → Raíz → Solución → Práctica: Empieza en el dolor, revela la causa real, ofrece el marco, practica
- Mito → Verdad → Método → Transformación: Destruye creencias falsas, revela la realidad, presenta el sistema
- Viaje del Héroe: El lector como protagonista que enfrenta obstáculos y emerge transformado
- Pirámide de Comprensión: Empieza con el framework completo, luego profundiza capa por capa
- Contraintuitivo: Empieza desafiando lo que el lector cree saber, construye desde lo inesperado

REGLAS:
1. Cada estructura debe llevar al lector de un estado A a un estado B de forma DISTINTA
2. La progresión emocional debe ser específica al tema del libro, no genérica
3. El número de capítulos estimados debe basarse en la complejidad real del tema

Responde en este JSON exacto:
{
  "estructuras": [
    {
      "nombre": "Nombre descriptivo de la estructura",
      "tipo_arco": "Tipo de arco narrativo",
      "descripcion": "Descripción de cómo este arco funciona para este libro específico (2-3 oraciones)",
      "progresion_emocional": "Estado inicial del lector → punto de quiebre → revelación → práctica → estado final",
      "capitulos_estimados": 11,
      "fases": [
        {
          "nombre": "Fase 1: Nombre",
          "descripcion": "Qué logra esta fase en el lector",
          "capitulos_aprox": 3
        }
      ]
    }
  ]
}"""


def generate_structures(core_idea: str, titulo: str, subtitulo: str) -> list:
    """Generate 3 distinct structural options for the book."""
    prompt = f"""LIBRO: {titulo}
SUBTÍTULO: {subtitulo}
IDEA CENTRAL: {core_idea}

Genera exactamente 3 estructuras narrativas distintas para este libro. Cada una debe usar un arco diferente y producir una experiencia de lectura distinta, aunque el destino sea el mismo. Adapta el número de capítulos a lo que este tema específico requiere."""

    result = call_llm(prompt, SYSTEM, temperature=0.8)
    return result.get('estructuras', [])
