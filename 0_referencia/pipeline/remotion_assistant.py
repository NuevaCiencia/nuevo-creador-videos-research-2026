import os
import json
import yaml
import openai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


def _load_ai_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'ai_config.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class RemotionAssistant:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("❌ ERROR: OPENAI_API_KEY no detectada.")
        self.client = openai.OpenAI(api_key=api_key)
        cfg = _load_ai_config().get('remotion_assistant', {})
        self.model = cfg.get('model', 'gpt-5.4-mini')
        self.temperature = cfg.get('temperature', 0.1)
        
        base_prompt = cfg.get('system_prompt', '')
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        templates_path = os.path.join(root, 'ai_remotion_templates.yaml')
        
        external_templates = ""
        if os.path.exists(templates_path):
            with open(templates_path, 'r', encoding='utf-8') as f:
                external_templates = f.read()
                
        self.system_prompt = base_prompt.replace(
            "[NOTA: EL CATÁLOGO DE TEMPLATES SE INYECTA DINÁMICAMENTE AQUÍ DESDE ai_remotion_templates.yaml]", 
            external_templates
        )

    def generar_configs(self, segmentos_remotion):
        """
        segmentos_remotion = [
           {"id": 1, "template": "TypeWriter", "speech": "...", "duration": "0:34", "output_filename": "REM01.mp4"},
           ...
        ]
        """
        if not segmentos_remotion:
            return []

        print(f"🎬 RemotionAssistant: Procesando {len(segmentos_remotion)} escenas REMOTION...")

        # Formatear el payload
        payload = json.dumps(segmentos_remotion, ensure_ascii=False)

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": payload}
            ],
            temperature=self.temperature
        )

        try:
            resultado = json.loads(response.choices[0].message.content)
            configs = []
            
            # Cruzar la data generada por LLM con la metadata dura del input
            for req in segmentos_remotion:
                req_id = req.get("id")
                # Buscar el par provisto por la IA
                matched_data = {}
                for res in resultado.get("resultados", []):
                    if res.get("id") == req_id:
                        matched_data = res.get("data", {})
                        break
                        
                configs.append({
                    "template": req.get("template"),
                    "output": req.get("output_filename"),
                    "duration": req.get("duration"),
                    "data": matched_data
                })
                
            return configs
        except Exception as e:
            raise RuntimeError(f"Fallo generando YAMLs de Remotion: {str(e)}")
