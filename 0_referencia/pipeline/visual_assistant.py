import os
import json
import yaml
import openai
from dotenv import load_dotenv

# Cargar .env de la raiz si existe
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


def _load_ai_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'ai_config.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class VisualAssistant:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("❌ ERROR: OPENAI_API_KEY no detectada. Configurarla en el entorno.")
        self.client = openai.OpenAI(api_key=api_key)
        cfg = _load_ai_config().get('visual_assistant', {})
        self.model = cfg.get('model', 'gpt-5.4-mini')
        self.temperature = cfg.get('temperature', 0.3)
        self.system_prompt = cfg.get('system_prompt', '')

    def enriquecer_visuales(self, segmentos):
        print("🧠 VisualAssistant: Analizando narrativa y diseñando arquitectura visual...")

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json.dumps(segmentos, ensure_ascii=False)}
            ],
            temperature=self.temperature
        )

        try:
            resultado = json.loads(response.choices[0].message.content)
            return resultado.get("actualizaciones", [])
        except Exception as e:
            raise RuntimeError(f"Fallo grave leyendo JSON de OpenAI: {str(e)}")
