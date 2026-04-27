from .base import call_llm

SYSTEM = """Eres un arquitecto de contenido para libros de no-ficción. Tu especialidad: crear estructuras de capítulos que sean MUTUAMENTE EXCLUYENTES y COLECTIVAMENTE EXHAUSTIVOS.

LA REGLA MÁS IMPORTANTE — TERRITORIO EXCLUSIVO:
Cada capítulo debe tener un territorio tan específico y delimitado que sea IMPOSIBLE confundirlo con otro. El territorio exclusivo es la declaración de qué trata SOLO este capítulo y ningún otro.

DIFERENCIA ENTRE MALO Y BUENO:
✗ MAL territorio: "Habla sobre la motivación y cómo mantenerla"
✓ BUEN territorio: "Este capítulo es el ÚNICO que explica por qué el modelo de motivación por recompensa falla neurológicamente pasados los 21 días, y presenta la alternativa basada en identidad"

REGLAS DE CONSTRUCCIÓN:
1. Ningún capítulo puede enseñar algo que otro ya cubrió — si sientes la tentación, fusiona o elimina
2. La progresión entre capítulos debe ser CAUSAL: cada capítulo hace posible el siguiente
3. El número de capítulos lo determina el tema, no una convención — si necesita 9, son 9; si necesita 14, son 14
4. Cada capítulo debe tener una "promesa al lector" específica y verificable
5. La posición en el arco debe respetarse: no puedes tener "aplicacion" antes de "framework"

POSICIONES EN EL ARCO (en orden lógico):
apertura → problema → ciencia → framework → aplicacion → transformacion → cierre

Responde en este JSON exacto:
{
  "capitulos": [
    {
      "numero": 1,
      "titulo": "Título del capítulo (evita números romanos, usa títulos evocadores)",
      "tesis": "Una sola oración: qué argumenta o enseña este capítulo",
      "territorio_exclusivo": "Este capítulo es el ÚNICO que... [descripción muy específica]",
      "posicion_arco": "apertura|problema|ciencia|framework|aplicacion|transformacion|cierre",
      "proposito": "Por qué este capítulo es imprescindible para el viaje del lector",
      "promesa_al_lector": "Al terminar este capítulo, el lector comprenderá/podrá/sabrá..."
    }
  ]
}"""


def generate_chapters(core_idea: str, titulo: str, subtitulo: str, structure: dict) -> list:
    """Generate chapters based on book info and chosen structure."""
    fases_desc = ""
    if structure.get('fases'):
        fases = structure['fases']
        fases_desc = "\n".join(
            f"  - {f['nombre']}: {f['descripcion']} (~{f.get('capitulos_aprox', '?')} capítulos)"
            for f in fases
        )

    prompt = f"""LIBRO: {titulo}
SUBTÍTULO: {subtitulo}
IDEA CENTRAL: {core_idea}

ESTRUCTURA ELEGIDA: {structure.get('nombre', '')}
TIPO DE ARCO: {structure.get('tipo_arco', '')}
DESCRIPCIÓN: {structure.get('descripcion', '')}
PROGRESIÓN EMOCIONAL: {structure.get('progresion_emocional', '')}
FASES:
{fases_desc}

Genera los capítulos exactos que este libro necesita. Usa el número que el tema y la estructura demanden (~{structure.get('capitulos_estimados', 10)}).

RECUERDA: El territorio exclusivo de cada capítulo debe ser tan específico que sea imposible que dos capítulos se solapen. Cada capítulo debe hacer necesario el siguiente."""

    result = call_llm(prompt, SYSTEM, temperature=0.75)
    return result.get('capitulos', [])
