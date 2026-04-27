import os
import re
import time
import yaml
from openai import OpenAI
from pathlib import Path
from typing import List


def _load_ai_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'ai_config.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class CorrectorOrtografia:
    def __init__(self, modelo: str = None, context_threshold: int = None):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada")
        self.client = OpenAI(api_key=api_key)
        cfg = _load_ai_config().get('spell_checker', {})
        self.modelo = modelo or cfg.get('model', 'gpt-4.1-mini-2025-04-14')
        self.temperature = cfg.get('temperature', 0.1)
        self.max_tokens = cfg.get('max_tokens', 4000)
        self.context_threshold = context_threshold or cfg.get('context_threshold', 50)
        self._system_prompt = cfg.get('system_prompt', '')
        self._user_prompt_template = cfg.get('user_prompt_template', '')

    def limpiar_texto_original(self, contenido: str) -> str:
        # Eliminar comentarios humanos <# ... #>
        contenido = re.sub(r'<#.*?#>', '', contenido, flags=re.DOTALL)
        # Eliminar etiquetas de tipo
        contenido = re.sub(r'<!--\s*type:.*?-->', '', contenido, flags=re.DOTALL)
        # Eliminar separadores de bloque
        contenido = re.sub(r'^\s*-{3,}\s*$', '', contenido, flags=re.MULTILINE)
        return '\n'.join([ln.strip() for ln in contenido.split('\n') if ln.strip()])

    def fragmentar_bloques(self, bloques: List[dict]) -> List[List[dict]]:
        """Divide la lista de bloques crudos en sublistas para enviar a la IA."""
        secciones, current = [], []
        for b in bloques:
            current.append(b)
            if len(current) >= self.context_threshold:
                secciones.append(current)
                current = []
        if current: secciones.append(current)
        return secciones

    def bloques_a_texto(self, sub_bloques: List[dict]) -> str:
        return "\n".join(f"[{b['start']:.3f} - {b['end']:.3f}]: {b['text']}" for b in sub_bloques)

    def encontrar_texto_referencia(self, texto_original_limpio: str, texto_buscar: str) -> str:
        for size, limit in [(10,1500),(5,1000)]:
            palabras = texto_buscar.split()[:size]
            if not palabras: continue
            idx = texto_original_limpio.lower().find(' '.join(palabras).lower())
            if idx != -1: return texto_original_limpio[idx:idx+limit]
        return texto_original_limpio[:1000]

    def crear_prompt(self, seccion_txt: str, texto_ref: str):
        sys_msg = {"role": "system", "content": self._system_prompt.strip()}
        user_content = self._user_prompt_template.format(
            texto_ref=texto_ref,
            seccion_txt=seccion_txt
        )
        user_msg = {"role": "user", "content": user_content}
        return sys_msg, user_msg

    def corregir_seccion(self, sub_bloques: List[dict], texto_original_limpio: str) -> List[dict]:
        texto_busqueda = " ".join(b["text"] for b in sub_bloques)
        ref = self.encontrar_texto_referencia(texto_original_limpio, texto_busqueda)
        texto_crudo = self.bloques_a_texto(sub_bloques)
        ts_orig = re.findall(r"\[\d+\.\d+\s*-\s*\d+\.\d+\]", texto_crudo)

        for intento in range(1, 4):
            try:
                sys_msg, user_msg = self.crear_prompt(texto_crudo, ref)
                resp = self.client.chat.completions.create(
                    model=self.modelo,
                    messages=[sys_msg, user_msg],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                corr = resp.choices[0].message.content.strip()
                ts_corr = re.findall(r"\[\d+\.\d+\s*-\s*\d+\.\d+\]", corr)

                if ts_corr == ts_orig:
                    nuevos_bloques = []
                    lines = corr.split('\n')
                    for ln in lines:
                        m = re.search(r"\[(\d+\.\d+)\s*-\s*(\d+\.\d+)\]:\s*(.+)$", ln.strip())
                        if m:
                            nuevos_bloques.append({
                                "start": float(m.group(1)),
                                "end": float(m.group(2)),
                                "text": m.group(3).strip()
                            })
                    if len(nuevos_bloques) == len(sub_bloques):
                        return nuevos_bloques
                print(f"⚠️ OpenAI alteró los timestamps o formato. Intento {intento}/3 declinado.")
            except Exception as e:
                print(f"❌ Error API: {e}")
                time.sleep(2)
        print("❌ Fallo crítico en corrección. Retornando bloque vulnerable.")
        return sub_bloques

    def corregir_memoria(self, bloques_crudos: List[dict], original_speech_path: str,
                         output_dir: str = 'output/02_correccion') -> List[dict]:
        print("\n✨ Iniciando Inteligencia del Módulo Corrector Ortográfico...")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        with open(original_speech_path, "r", encoding="utf-8") as f:
            original = self.limpiar_texto_original(f.read())

        sublistas = self.fragmentar_bloques(bloques_crudos)
        print(f"📦 Procesando {len(sublistas)} bloques mediante la API ({len(bloques_crudos)} segmentos)...")

        bloques_finales = []
        for i, sub in enumerate(sublistas, 1):
            print(f"   -> LLM batch {i}/{len(sublistas)} en curso...")
            corregidos = self.corregir_seccion(sub, original)
            bloques_finales.extend(corregidos)
            time.sleep(1)

        outfile = os.path.join(output_dir, "subtitulos_corregido.txt")
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(self.bloques_a_texto(bloques_finales))
        print(f"✅ Corrección exitosa. Guardado en: {outfile}")
        return bloques_finales
