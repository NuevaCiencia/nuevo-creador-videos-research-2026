import os
import json
import yaml
from .visual_assistant import VisualAssistant


def _get_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class VisualOrchestrator:
    def __init__(self, input_file='output/03_guion/guion_base.txt',
                 output_dir='output/03_guion',
                 project_root=None):
        self.input_file = input_file
        self.output_dir = output_dir
        # project_root: carpeta del proyecto activo (para leer video_config.yaml)
        # Si no se indica, fallback a la raíz del repo (compatibilidad)
        self.project_root = project_root or _get_root()
        self.output_txt  = os.path.join(output_dir, 'guion_consolidado.txt')
        self.output_json = os.path.join(output_dir, 'recursos_visuales.json')
        # Reportes separados
        self.output_split = os.path.join(output_dir, 'imagenes_split.md')
        self.output_full  = os.path.join(output_dir, 'imagenes_full.md')
        self.output_video = os.path.join(output_dir, 'videos.md')
        os.makedirs(output_dir, exist_ok=True)

    def procesar_guion(self):
        print(f"📖 VisualOrchestrator: Leyendo {self.input_file}")

        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"¡Oops! {self.input_file} no existe. Ejecuta 01_preparacion.py primero.")

        with open(self.input_file, 'r', encoding='utf-8') as f:
            contenido = f.read()

        bloques_crudos = contenido.split('#SEGMENT [')

        segmentos_procesados = []
        payload_openai = []
        payload_remotion = []

        header_global = bloques_crudos[0]

        for index, block in enumerate(bloques_crudos[1:], start=1):
            lineas = block.strip().split('\n')
            timestamp = lineas[0].strip().replace(']', '')

            diccionario_segmento = {"TIMESTAMP": timestamp}
            for linea in lineas[1:]:
                if '=' in linea and not linea.startswith('///'):
                    key, val = linea.split('=', 1)
                    diccionario_segmento[key.strip()] = val.strip()

            tipo_seg = diccionario_segmento.get('TYPE', '')
            if tipo_seg == 'REMOTION':
                params_str = diccionario_segmento.get('PARAMS', '')
                template = params_str.split('//')[0].replace('$', '').strip() if params_str else 'TypeWriter'
                
                duracion_segundos = float(diccionario_segmento.get('TIME', 0.0))
                m = int(duracion_segundos // 60)
                s = int(duracion_segundos % 60)
                duracion_str = f"{m}:{s:02d}"
                output_filename = f"REM{len(payload_remotion) + 1:02d}.mp4"
                
                payload_remotion.append({
                    "id": index,
                    "template": template,
                    "speech": diccionario_segmento.get('SPEECH', ''),
                    "duration": duracion_str,
                    "output_filename": output_filename
                })
            else:
                payload_openai.append({
                    "id": index,
                    "tipo": tipo_seg,
                    "speech": diccionario_segmento.get('SPEECH', '')
                })

            # IMPORTANTE: No olvidar añadir el diccionario parseado a la memoria principal
            segmentos_procesados.append(diccionario_segmento)

        print(f"🔍 Segmentos identificados: {len(payload_openai)} para Visual, {len(payload_remotion)} para Remotion.")

        # --- Flujo Visual Normal ---
        actualizaciones = []
        if payload_openai:
            asistente = VisualAssistant()
            actualizaciones = asistente.enriquecer_visuales(payload_openai)
            
            if len(actualizaciones) != len(payload_openai):
                print(f"⚠️ ADVERTENCIA: La IA devolvió {len(actualizaciones)} resultados visuales pero se enviaron {len(payload_openai)}.")

        # Armar el mapa usando propiedades ID si existen, de lo contrario asumiendo orden 1:1
        mapa_actualizaciones = {}
        for p, sub in zip(payload_openai, actualizaciones):
            # Preferir ID del objeto devuelto por la IA si existe (más robusto), si no, usar el ID del payload (por zip)
            mapa_actualizaciones[sub.get('id', p['id'])] = sub

        # --- Flujo Remotion ---
        mapa_remotion = {}
        if payload_remotion:
            from .remotion_assistant import RemotionAssistant
            asistente_rem = RemotionAssistant()
            configs_remotion = asistente_rem.generar_configs(payload_remotion)
            
            rem_yaml_path = os.path.join(self.output_dir, 'recursos_remotion.yaml')
            print(f"💾 Guardando {rem_yaml_path}...")
            with open(rem_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump({"videos": configs_remotion}, f, allow_unicode=True, sort_keys=False)
                
            mapa_remotion = { p['id']: p for p in payload_remotion }

        recursos_metadata = []
        video_config = self._cargar_configuracion()
        texto_final = self._generar_header(video_config)

        for idx, sg in enumerate(segmentos_procesados):
            original_id = idx + 1
            tipo_segmento = sg.get('TYPE', '')

            if tipo_segmento == 'REMOTION':
                rem = mapa_remotion.get(original_id, {})
                asset_file = rem.get('output_filename', f"REM{original_id:02d}.mp4")
                sg['ASSET'] = f"videos/{asset_file}"
                sg['TEXT'] = ""
                
                tiempo_duracion = float(sg.get('TIME', 0.0))
                recursos_metadata.append({
                    "nombre": asset_file,
                    "ubicacion": f"videos/{asset_file}",
                    "tipo": "video",
                    "tipo_contenido": "remotion",
                    "segmento": sg['TIMESTAMP'],
                    "duracion": tiempo_duracion,
                    "descripcion": f"Generado mediante RemotionAssistant"
                })
            else:
                subdata = mapa_actualizaciones.get(original_id, {})

                def get_val(d, key_lower):
                    return d.get(key_lower) or d.get(key_lower.upper(), '')

                sg['TEXT'] = get_val(subdata, 'text')
                sg['TEXT_STYLE'] = get_val(subdata, 'text_style')
                
                if not sg['TEXT'] and sg.get('TYPE') in ('TEXT', 'SPLIT_LEFT', 'SPLIT_RIGHT'):
                    speech_clean = sg.get('SPEECH', '').split('//')[0].strip()
                    palabras = speech_clean.split()
                    sg['TEXT'] = " ".join(palabras[:10]) + ("..." if len(palabras) > 10 else "")
                
                asset_file = get_val(subdata, 'asset_filename')
                
                # --- Saneamiento de prefijos (Enforce S, F, V) ---
                if asset_file:
                    new_prefix = None
                    if 'SPLIT' in tipo_segmento: new_prefix = 'S'
                    elif tipo_segmento == 'FULL_IMAGE': new_prefix = 'F'
                    elif tipo_segmento == 'VIDEO': new_prefix = 'V'
                    
                    if new_prefix and not asset_file.startswith(new_prefix):
                        # Extraer solo los números del nombre original si existen
                        digits = "".join([c for c in asset_file if c.isdigit()])
                        if not digits: digits = str(original_id).zfill(2)
                        ext = 'mp4' if new_prefix == 'V' else 'png'
                        asset_file = f"{new_prefix}{digits}.{ext}"
                        subdata['asset_filename'] = asset_file
                        print(f"🔧 Corrigiendo prefijo inválido: {get_val(subdata, 'asset_filename')} -> {asset_file}")
                
                if not asset_file and tipo_segmento in ('SPLIT_LEFT', 'SPLIT_RIGHT', 'FULL_IMAGE', 'VIDEO'):
                    ts_limpio = sg['TIMESTAMP'].replace(':', '_').replace('.', '_').replace('-', '_').strip()
                    prefix = 'S' if 'SPLIT' in tipo_segmento else ('F' if tipo_segmento == 'FULL_IMAGE' else 'V')
                    ext = 'mp4' if tipo_segmento == 'VIDEO' else 'png'
                    asset_file = f"{prefix}_AUTO_{ts_limpio}.{ext}"
                    subdata['asset_filename'] = asset_file
                    print(f"⚠️ Alerta: Auto-generando asset: {asset_file}")
                    if not get_val(subdata, 'asset_tipo'):
                        subdata['asset_tipo'] = 'imagen_split' if 'SPLIT' in tipo_segmento else ('imagen_completa' if tipo_segmento == 'FULL_IMAGE' else 'video')
                    if not get_val(subdata, 'asset_tipo_contenido'):
                        subdata['asset_tipo_contenido'] = 'conceptual'

                if asset_file and tipo_segmento not in ('CONCEPT', 'LIST'):
                    folder = "videos" if asset_file.endswith(".mp4") else "images"
                    sg['ASSET'] = f"{folder}/{asset_file}"
                    tiempo_duracion = float(sg.get('TIME', 0.0))
                    recursos_metadata.append({
                        "nombre": asset_file,
                        "ubicacion": f"{folder}/{asset_file}",
                        "tipo": subdata.get('asset_tipo', ''),
                        "tipo_contenido": subdata.get('asset_tipo_contenido', ''),
                        "segmento": sg['TIMESTAMP'],
                        "duracion": tiempo_duracion,
                        "descripcion": subdata.get('asset_descripcion', '')
                    })
                else:
                    if tipo_segmento in ('CONCEPT', 'LIST'):
                        sg['ASSET'] = "DYNAMIC_GENERATED"
                        sg['TEXT'] = ""
                    else:
                        sg['ASSET'] = ""

            # Añadir segmento al texto consolidado
            texto_final += f"#SEGMENT [{sg['TIMESTAMP']}]\n"
            field_order = ['TYPE', 'PARAMS', 'TIME', 'TEXT', 'TEXT_STYLE', 'ASSET', 'SPEECH', 'NOTES']
            for f in field_order:
                if f in sg:
                    texto_final += f"{f}={sg.get(f, '')}\n"
            texto_final += "\n"

        print(f"💾 Guardando {self.output_txt}...")
        with open(self.output_txt, 'w', encoding='utf-8') as file:
            file.write(texto_final)

        print(f"💾 Guardando {self.output_json}...")
        json_limpio_metadata = []
        for r in recursos_metadata:
            copia = dict(r)
            if 'descripcion' in copia:
                del copia['descripcion']
            json_limpio_metadata.append(copia)

        json_maestro = {
            "proyecto": video_config.get('TITLE', 'Proyecto Auto'),
            "total_recursos": len(json_limpio_metadata),
            "recursos": json_limpio_metadata
        }
        with open(self.output_json, 'w', encoding='utf-8') as jpf:
            json.dump(json_maestro, jpf, ensure_ascii=False, indent=2)

        print("💾 Guardando reportes visuales separados...")
        proyecto_titulo = video_config.get('TITLE', 'Proyecto Auto')
        
        # Configuración de reportes por tipo
        reportes_config = {
            'imagen_split': (self.output_split, f"# Imágenes Split: {proyecto_titulo}"),
            'imagen_completa': (self.output_full, f"# Imágenes Full: {proyecto_titulo}"),
            'video': (self.output_video, f"# Videos: {proyecto_titulo}")
        }

        for tipo, (path, titulo) in reportes_config.items():
            recursos_filtrados = [r for r in recursos_metadata if r['tipo'] == tipo]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"{titulo}\n\n")
                if not recursos_filtrados:
                    f.write("*No se identificaron recursos para este tipo.*\n")
                    continue
                for r in recursos_filtrados:
                    f.write(f"### {r['nombre']}\n")
                    f.write(f"- **Segmento:** [{r['segmento']}]\n")
                    f.write(f"- **Tipo:** {r['tipo']}\n")
                    f.write(f"- **Duración:** {r['duracion']:.3f} segundos\n")
                    f.write(f"- **Tipo Contenido:** {r['tipo_contenido']}\n")
                    f.write(f"- **Descripción:** {r.get('descripcion', '')}\n\n")

        print("✅ Pipeline Gráfico Finalizado.")

    def _cargar_configuracion(self):
        """Lee video_config.yaml del proyecto activo (self.project_root)."""
        try:
            path = os.path.join(self.project_root, "video_config.yaml")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as fb:
                    return yaml.safe_load(fb)
        except Exception:
            pass
        return {}

    def _generar_header(self, config):
        main_audio = config.get('MAIN_AUDIO', 'audio.mp3')
        if '/' in main_audio or '\\' in main_audio:
            main_audio = os.path.basename(main_audio)

        return f'''/// HEADER GENERICO AUTOGENERADO POR VISUAL-ORCHESTRATOR
### Metadatos
#META
FILES_FOLDER={config.get('FILES_FOLDER', 'assets')}
TITLE={config.get('TITLE', 'Título Auto')}
MAIN_AUDIO={main_audio}
FPS={config.get('FPS', 30)}
RESOLUTION={config.get('RESOLUTION', '1920x1080')}
MAIN_FONT={config.get('MAIN_FONT', 'Inter')}
BACKGROUND_COLOR={config.get('BACKGROUND_COLOR', '#fefefe')}
MAIN_TEXT_COLOR={config.get('MAIN_TEXT_COLOR', '#bd0505')}
HIGHLIGHT_TEXT_COLOR={config.get('HIGHLIGHT_TEXT_COLOR', '#e3943b')}

### Estilos
#STYLES
TITLE={{font-size:48px;font-weight:bold}}
SUBTITLE={{font-size:36px;font-weight:bold;color:#3498DB}}
CODE={{font-family:Consolas;background:#282C34;color:#61AFEF;padding:10px}}
QUOTE={{font-style:italic;font-size:32px}}
LIST_ITEM={{font-size:32px;text-align:left;margin-left:30px}}
HIGHLIGHT={{color:#3498DB;font-weight:bold}}

### Portada
#COVER
ASSET={config.get('COVER_ASSET', 'videos/portada.mp4')}
NOTES={config.get('COVER_NOTES', 'Video de portada')}


### Segmentos
'''
