import os
from tavily import TavilyClient
from utils.llm import call_llm

_tavily_client = None

def get_tavily():
    global _tavily_client
    if _tavily_client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise Exception("TAVILY_API_KEY not found in environment")
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client

SYSTEM_EXTRACTOR = """Eres un investigador jefe de una revista científica de alto impacto. 
Tu misión es extraer afirmaciones que requieran evidencia empírica.

REGLAS DE BÚSQUEDA (ESTRICTO):
- Para cada afirmación, genera un query que fuerce dominios de alta confianza usando el operador 'site:'.
- Ejemplo de query: "(afirmación) site:.edu OR site:.gov OR site:ncbi.nlm.nih.gov OR site:nature.com OR site:sciencemag.org"
- NUNCA generes búsquedas genéricas que devuelvan blogs .com.

Responde en este formato JSON:
{
  "claims": [
    {
      "claim": "La afirmación exacta",
      "query": "QUERY con filtros site:.edu OR site:.gov OR dominios científicos"
    }
  ]
}"""

SYSTEM_VERIFIER = """Eres un revisor de pares (peer-reviewer) extremadamente riguroso.
Tu tarea es validar una afirmación basándote ÚNICAMENTE en fuentes primarias o académicas.

REGLAS DE VALIDACIÓN:
1. RECHAZA automáticamente cualquier blog personal, sitios tipo 'healthline', 'webmd', 'medium' o portales de noticias genéricos .com.
2. SOLO acepta:
   - Artículos de revistas científicas indexadas.
   - Datos de agencias gubernamentales (.gov).
   - Publicaciones de universidades de prestigio (.edu).
   - Informes de organismos internacionales oficiales.
3. Si los resultados de búsqueda son mediocres (blogs, prensa), marca como 'not_found' y explica: "Fuentes encontradas sin rigor científico".

Responde en este formato JSON:
{
  "status": "verified | disputed | not_found",
  "confidence": 0-100,
  "reason": "Explicación técnica del porqué la fuente es (o no es) de alto rigor",
  "source_url": "URL (solo si es .edu, .gov o repositorio científico)",
  "source_title": "Título de la fuente",
  "source_snippet": "Fragmento de evidencia directa"
}"""

def extract_claims(text: str) -> list:
    """Extract verifiable claims from text."""
    prompt = f"GUION:\n{text}"
    result = call_llm(prompt, SYSTEM_EXTRACTOR)
    return result.get("claims", [])

def verify_claim(claim_obj: dict) -> dict:
    """Verify a single claim using Tavily."""
    query = claim_obj["query"]
    try:
        results = get_tavily().search(query=query, max_results=5, search_depth="advanced")
        if not results.get("results"):
            return {"status": "not_found", "reason": "No se encontraron resultados en dominios de alto rigor (.edu, .gov, etc.)"}
        
        # Call LLM to evaluate results
        search_context = "\n---\n".join([
            f"Título: {r['title']}\nURL: {r['url']}\nContenido: {r['content']}"
            for r in results["results"]
        ])
        
        prompt = f"AFIRMACIÓN: {claim_obj['claim']}\n\nRESULTADOS DE BÚSQUEDA:\n{search_context}"
        verification = call_llm(prompt, SYSTEM_VERIFIER)
        return verification
    except Exception as e:
        return {"status": "error", "reason": str(e)}
