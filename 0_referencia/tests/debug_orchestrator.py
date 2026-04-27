import os
import sys

# Añadir el directorio raíz al path para poder importar pipeline
sys.path.append(os.getcwd())

from pipeline.visual_orchestrator import VisualOrchestrator

PROJECT = "demo"
root = os.path.join(os.getcwd(), "proyectos", PROJECT)
guion_base = os.path.join(root, "output", "03_guion", "guion_base.txt")
output_dir = os.path.join(root, "output", "03_guion")

print("--- DEBUG RUN START ---")
orchestrator = VisualOrchestrator(input_file=guion_base, output_dir=output_dir, project_root=root)

# Simular procesar_guion pero con prints
with open(guion_base, 'r', encoding='utf-8') as f:
    contenido = f.read()

bloques_crudos = contenido.split('#SEGMENT [')
print(f"Bloques crudos found: {len(bloques_crudos)}")

segmentos_procesados = []
payload_openai = []
payload_remotion = []

for index, block in enumerate(bloques_crudos[1:], start=1):
    lineas = block.strip().split('\n')
    diccionario_segmento = {"index_debug": index}
    for linea in lineas[1:]:
        if '=' in linea:
            k, v = linea.split('=', 1)
            diccionario_segmento[k.strip()] = v.strip()
    
    tipo_seg = diccionario_segmento.get('TYPE', '')
    if tipo_seg == 'REMOTION':
        payload_remotion.append({"id": index})
    else:
        payload_openai.append({"id": index})
    
    segmentos_procesados.append(diccionario_segmento)

print(f"payload_openai length: {len(payload_openai)}")
print(f"payload_remotion length: {len(payload_remotion)}")
print(f"segmentos_procesados length: {len(segmentos_procesados)}")

print("--- DEBUG RUN END ---")
