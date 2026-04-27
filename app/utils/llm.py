import os
import json
from openai import OpenAI

client = None

def get_client():
    global client
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not found in environment")
        client = OpenAI(api_key=api_key)
    return client

def call_llm(prompt: str, system: str, temperature: float = 0.5, model: str = "gpt-5.4-mini") -> dict:
    """Call OpenAI and return parsed JSON."""
    try:
        response = get_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"LLM Error: {e}")
        raise e
