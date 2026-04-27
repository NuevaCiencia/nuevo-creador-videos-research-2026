import os
from .base import call_llm
from tavily import TavilyClient

_tavily_client = None

def _tavily():
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    return _tavily_client

SYSTEM = """Eres el director de investigación de un proyecto editorial de alto nivel. Tu especialidad: identificar evidencia científica real e historias reales poderosas para libros de autoayuda con respaldo científico.

REGLAS PARA SUSTENTO CIENTÍFICO:
- Solo propones estudios y datos que sabes que existen con alta confianza
- Das suficiente detalle para encontrar la fuente: autor, año aproximado, institución si la conoces
- Priorizas: estudios landmark, meta-análisis, experimentos clásicos bien documentados
- El hallazgo debe ser directamente relevante a la tesis del capítulo, no genéricamente relacionado

REGLAS PARA HISTORIAS REALES:
- Solo personas reales y nombradas — nunca compuestas ni ficticias
- El evento debe ser específico y verificable (no "en algún momento de su vida...")
- EVITA historias sobreusadas en autoayuda: Edison y las bombillas, el bamboú, el elefante encadenado, etc.
- Busca historias menos conocidas pero igualmente poderosas: científicos, atletas, figuras históricas, empresarios, casos clínicos documentados
- Cada historia debe iluminar el TERRITORIO EXCLUSIVO del capítulo, no un tema general

CRITERIO DE COLOCACIÓN (no mecánico, narrativo):
- apertura: el concepto del capítulo es abstracto o contraintuitivo — necesita anclaje emocional inmediato
- post_ciencia: después de una sección densa de datos, el lector necesita humanizar lo que acaba de leer
- pre_ejercicio: el lector necesita motivación emocional antes de actuar
- cierre: la historia redondea la transformación del capítulo
- NO colocar historia si: el capítulo es metodológico, ya tiene historia en el anterior, o la información fluye mejor sin ella

Responde en este JSON exacto:
{
  "ciencia": [
    {
      "titulo": "Nombre descriptivo del estudio o hallazgo",
      "autor": "Nombre(s) del investigador principal",
      "año": "año o rango aproximado",
      "campo": "Campo de investigación",
      "hallazgo_clave": "El hallazgo específico relevante a este capítulo en 1-2 oraciones",
      "busqueda_sugerida": "Query de búsqueda para verificar esta fuente"
    }
  ],
  "historias": [
    {
      "protagonista": "Nombre completo de la persona real",
      "que_paso": "Descripción específica del evento en 2-3 oraciones",
      "que_ilustra": "Qué concepto exacto del territorio del capítulo demuestra esta historia",
      "placement": "apertura|post_ciencia|pre_ejercicio|cierre",
      "parte_sugerida": 2,
      "busqueda_sugerida": "Query de búsqueda para verificar esta historia"
    }
  ],
  "mapa_colocacion": [
    {
      "parte_num": 1,
      "necesita_historia": true,
      "razon": "Por qué esta parte se beneficia de una historia"
    }
  ],
  "nota_investigador": "Observación general sobre qué tipo de evidencia es más poderosa para este capítulo específico"
}"""


def research_chapter(chapter: dict, book_idea: str, parts: list) -> dict:
    """Generate research dossier for a single chapter."""
    parts_desc = "\n".join(
        f"  Parte {p['num']}: {p['titulo']} ({p['tipo']})" for p in parts
    )

    prompt = f"""LIBRO: {book_idea}

CAPÍTULO {chapter['num']}: {chapter['titulo']}
TESIS: {chapter['tesis']}
TERRITORIO EXCLUSIVO: {chapter['territorio_exclusivo']}
POSICIÓN EN EL ARCO: {chapter['posicion_arco']}
PROMESA AL LECTOR: {chapter.get('promesa_al_lector', '')}

PARTES DE ESTE CAPÍTULO:
{parts_desc}

Genera el dossier de investigación para este capítulo:
- 3 a 5 fuentes científicas reales y verificables
- 2 a 4 historias reales con protagonistas nombrados
- Mapa de colocación narrativo (no mecánico) indicando en cuáles partes tiene sentido una historia

Recuerda: cada elemento debe ser relevante al TERRITORIO EXCLUSIVO del capítulo, no al tema general del libro."""

    return call_llm(prompt, SYSTEM, temperature=0.5)


def verify_item(query: str) -> dict:
    """Search Tavily for a given query. Returns {url, title, found, error}."""
    if not query or not query.strip():
        return {'found': False, 'url': '', 'title': '', 'snippet': '', 'error': None}
    try:
        results = _tavily().search(query=query, max_results=2, search_depth="basic")
        if results and results.get('results'):
            top = results['results'][0]
            return {
                'found': True,
                'url': top.get('url', ''),
                'title': top.get('title', ''),
                'snippet': top.get('content', '')[:200],
                'error': None,
            }
        return {'found': False, 'url': '', 'title': '', 'snippet': '', 'error': None}
    except Exception as e:
        return {'found': False, 'url': '', 'title': '', 'snippet': '', 'error': str(e)}
