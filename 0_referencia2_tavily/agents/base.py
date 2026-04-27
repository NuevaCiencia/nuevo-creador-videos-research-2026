import os
import json
import re
from openai import OpenAI
from anthropic import Anthropic

from config import LLM_MODEL, CLAUDE_MODEL
MODEL = LLM_MODEL

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def embed_text(texts: list) -> list:
    """Embed a list of strings. Returns list of embedding vectors."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[t[:8000] for t in texts],
    )
    return [item.embedding for item in response.data]


def call_llm(prompt: str, system: str, temperature: float = 0.8, model_override: str = None) -> dict:
    """Call the LLM and return parsed JSON. Raises on failure."""
    response = client.chat.completions.create(
        model=model_override if model_override else MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


def call_claude(prompt: str, system: str, temperature: float = 0.8, model: str = CLAUDE_MODEL) -> dict:
    """Call Anthropic's Claude and return parsed JSON."""
    anthropic_client = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY", ""))

    response = anthropic_client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.content[0].text.strip()

    # Quitar bloques de markdown si Claude los pone (```json ... ```)
    if raw.startswith("```"):
        raw = re.sub(r'^```[a-z]*\n?', '', raw)
        raw = re.sub(r'```$', '', raw).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Intento de rescate: buscar el primer objeto JSON dentro del texto
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            return {"content": raw}

    # Normalizar saltos de línea en todos los strings del resultado
    return {k: v.replace('\\n', '\n') if isinstance(v, str) else v for k, v in parsed.items()}
