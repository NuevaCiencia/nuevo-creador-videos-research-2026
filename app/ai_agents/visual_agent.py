"""
Port de VisualOrchestrator + VisualAssistant + RemotionAssistant.
Completamente autónomo — no depende de 0_referencia ni de archivos externos.
Prompts hardcodeados. Templates Remotion leídos desde la DB (remotion_templates).
"""
import json
import os
import re
import traceback
from datetime import datetime

# ── Configuración de modelos ───────────────────────────────────────────────────
VISUAL_MODEL        = "gpt-5.4-mini"
VISUAL_TEMPERATURE  = 0.3
REMOTION_MODEL      = "gpt-5.4-mini"
REMOTION_TEMPERATURE = 0.1

# ── System prompt: VisualAssistant ────────────────────────────────────────────
VISUAL_SYSTEM_PROMPT = """\
Eres un experto en diseño instruccional y dirección de arte visual para videos educativos.
Recibirás una lista de segmentos con su respectivo 'speech' (texto hablado) y 'tipo' de pantalla.

Tu tarea es tomar decisiones exclusivas de ARTE y devolver un JSON con la actualización de los segmentos.

REGLAS ESTRICTAS DE ASIGNACIÓN:
1. TEXT (El texto que aparecerá en pantalla):
   - Para tipos SPLIT_LEFT, SPLIT_RIGHT, TEXT: Analiza el 'speech' para identificar si el segmento desarrolla una categoría, nivel, propiedad, arquitectura o concepto específico con nombre propio.
     * Si SÍ lo tiene (ej: "Nivel 1", "Autonomía", "Arquitectura BDI"): El TEXT DEBE comenzar con ese nombre, seguido de dos puntos y una frase de apoyo corta. Ejemplo: "Nivel 1: Reacción inmediata", "Autonomía: Sin intervención humana".
     * Si NO hay categoría específica (es un segmento de introducción o cierre general): Extrae la frase más gancho de 1 sola línea (5-8 palabras máx) según el speech.
   - Para tipos VIDEO, FULL_IMAGE: DEBE SER EXACTAMENTE "".

2. TEXT_STYLE (Los estilos tipográficos):
   - Elige entre "TITLE", "HIGHLIGHT", "CODE".
   - Para tipos VIDEO, FULL_IMAGE: DEBE SER EXACTAMENTE "".

3. ASSET_FILENAME (El nombre del archivo multimedia):
   - Para SPLIT_LEFT / SPLIT_RIGHT: OBLIGATORIO ej. S001.png, S002.png...
   - Para FULL_IMAGE: OBLIGATORIO ej. F001.png, F002.png...
   - Para VIDEO: OBLIGATORIO ej. V001.mp4, V002.mp4...
   - Para TEXT: DEBE SER EXACTAMENTE "".
   - PROHIBICIÓN: NUNCA uses el prefijo 'L' ni otros prefijos inventados. Solo S, F, V o "".

4. ASSET_TIPO:
   - "imagen_split" para (S), "imagen_completa" para (F), "video" para (V).
   - "" para tipo TEXT.

5. ASSET_TIPO_CONTENIDO:
   - "conceptual", "stock", "manim", "captura" o "especifica".
   - "" para tipo TEXT.

6. ASSET_DESCRIPCION:
   - REGLA CERO: Si es tipo TEXT, DEBE SER EXACTAMENTE "".
   - SI ES IMAGEN (SPLIT_LEFT, SPLIT_RIGHT, FULL_IMAGE) -> APLICA LA ESTRUCTURA "SCIENTIFIC AMERICAN" (EN INGLÉS):
     * El prompt resultante DEBE ESTAR COMPLETAMENTE EN INGLÉS.
     * Capa 1 (Base/Estilo): Inicia SIEMPRE con: "A premium educational infographic, Scientific American style, horizontal 16:9, white background."
     * Capa 2 (Estructura de la Composición): Describe la división espacial usando relaciones de ubicación claras ("left side", "top center", "evenly spaced"), SIN USAR números ni porcentajes.
     * Capa 3 (Objetos y Texturas Fotorealistas): Detalla físicamente cada bloque. Usa metáforas claras con texturas palpables (lámparas, placas de cristal, cableado, sensores).
     * Capa 4 (Color Funcional y Tipografía): Define paleta con HEX (ej. "electric blue #1E88E5"). Textos precisos, elegantes y no agolpados.
     * Capa 5 (Conexiones Orgánicas): Describe cómo fluye la información con flechas y conectores orgánicos.
     * OBLIGATORIO: Finaliza SIEMPRE con: "Ultra-detailed, studio lighting, 8K resolution, didactic and visually authoritative."
   - SI ES VIDEO -> APLICA DIRECCIÓN DE CINE EN UN PÁRRAFO:
     * NO uses las 5 Capas. NO incluyas textos estáticos. NO uses Fondo Blanco.
     * Si "manim": Describe la animación fluida de conceptos matemáticos transformándose.
     * Si "stock": Describe exactamente qué video de archivo real de 30s se debe descargar.

IMPORTANTE: El JSON debe contener un arreglo llamado "actualizaciones" respondiendo uno a uno a los IDs enviados.
LAS LLAVES DEL JSON DEBEN SER EN MINÚSCULAS: "text", "text_style", "asset_filename", "asset_tipo", "asset_tipo_contenido", "asset_descripcion"."""

# ── System prompt base: RemotionAssistant ─────────────────────────────────────
REMOTION_SYSTEM_BASE = """\
Eres un experto en motion graphics y diseño instruccional que genera configuraciones JSON para videos dinámicos (Remotion).
Recibirás un JSON con una lista de segmentos REMOTION. Cada segmento incluirá:
- id: Identificador único.
- template: El estilo visual solicitado (ej. TypeWriter, MindMap, LinearSteps).
- speech: Lo que el locutor estará diciendo. Úsalo para deducir qué textos poner en pantalla.
- duration: La duración REAL formateada como "MM:SS" que DEBES usar obligatoriamente.
- output_filename: El nombre del archivo que DEBES usar en la propiedad "output".

Tu tarea es generar el contenido gráfico (nodo "data") para CADA pantalla devolviendo un JSON con "resultados".
NO generes las llaves "template", "output" o "duration" — esas las auto-asigna el sistema. Céntrate en "data".

CATÁLOGO DE TEMPLATES DISPONIBLES:
{templates_catalog}

FORMATO ESPERADO:
{{
  "resultados": [
    {{
      "id": 1,
      "data": {{
        ... parámetros del template correspondiente ...
      }}
    }}
  ]
}}

IMPORTANTE:
- Devuelve exactamente el mismo número de elementos que hay en el input.
- ADAPTA INTELIGENTEMENTE EL TEXTO basándote en el "speech" para llenar los campos del template."""


# ── DB helpers ────────────────────────────────────────────────────────────────

def _update_db(class_id: int, updates: dict):
    from database import SessionLocal
    import models
    db = SessionLocal()
    try:
        row = db.query(models.ClassGuionConsolidado).filter(
            models.ClassGuionConsolidado.class_id == class_id
        ).first()
        if row:
            for k, v in updates.items():
                setattr(row, k, v)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[visual_agent] DB error: {e}")
    finally:
        db.close()


def _load_remotion_templates() -> str:
    """Build template catalog string from DB (remotion_templates table)."""
    from database import SessionLocal
    import models
    db = SessionLocal()
    try:
        templates = (
            db.query(models.RemotionTemplate)
            .filter(models.RemotionTemplate.enabled == True)
            .order_by(models.RemotionTemplate.sort_order)
            .all()
        )
        lines = []
        for t in templates:
            lines.append(
                f"- {t.name} ({t.category}): {t.description}\n"
                f"  Límites: {t.limits}\n"
                f"  Schema: {t.data_schema}"
            )
        return "\n\n".join(lines)
    finally:
        db.close()


# ── Parsing ───────────────────────────────────────────────────────────────────

def _parse_guion_base(content: str) -> list:
    bloques = content.split('#SEGMENT [')
    segments = []
    for block in bloques[1:]:
        lines = block.strip().split('\n')
        seg = {'TIMESTAMP': lines[0].strip().rstrip(']')}
        for line in lines[1:]:
            if '=' in line and not line.startswith('///'):
                key, val = line.split('=', 1)
                seg[key.strip()] = val.strip()
        segments.append(seg)
    return segments


# ── VisualAssistant ───────────────────────────────────────────────────────────

def _enriquecer_visuales(client, payload: list) -> list:
    if not payload:
        return []
    resp = client.chat.completions.create(
        model=VISUAL_MODEL,
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': VISUAL_SYSTEM_PROMPT},
            {'role': 'user',   'content': json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=VISUAL_TEMPERATURE,
    )
    result = json.loads(resp.choices[0].message.content)
    return result.get('actualizaciones', [])


# ── RemotionAssistant ─────────────────────────────────────────────────────────

def _generar_configs_remotion(client, payload: list) -> list:
    if not payload:
        return []
    catalog = _load_remotion_templates()
    prompt  = REMOTION_SYSTEM_BASE.format(templates_catalog=catalog)
    resp = client.chat.completions.create(
        model=REMOTION_MODEL,
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user',   'content': json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=REMOTION_TEMPERATURE,
    )
    resultado = json.loads(resp.choices[0].message.content)
    configs   = []
    for req in payload:
        matched = {}
        for res in resultado.get('resultados', []):
            if res.get('id') == req.get('id'):
                matched = res.get('data', {})
                break
        configs.append({
            'template': req['template'],
            'output':   req['output_filename'],
            'duration': req['duration'],
            'data':     matched,
        })
    return configs


# ── Header ────────────────────────────────────────────────────────────────────

def _generar_header(course_cfg: dict, audio_filename: str) -> str:
    return (
        f"/// HEADER AUTOGENERADO POR VISUAL-ORCHESTRATOR\n"
        f"### Metadatos\n#META\n"
        f"FILES_FOLDER={course_cfg.get('files_folder', 'assets')}\n"
        f"TITLE={course_cfg.get('title', 'Proyecto')}\n"
        f"MAIN_AUDIO={audio_filename}\n"
        f"FPS={course_cfg.get('fps', 30)}\n"
        f"RESOLUTION={course_cfg.get('resolution', '1920x1080')}\n"
        f"MAIN_FONT={course_cfg.get('main_font', 'Inter')}\n"
        f"BACKGROUND_COLOR={course_cfg.get('background_color', '#fefefe')}\n"
        f"MAIN_TEXT_COLOR={course_cfg.get('main_text_color', '#bd0505')}\n"
        f"HIGHLIGHT_TEXT_COLOR={course_cfg.get('highlight_text_color', '#e3943b')}\n\n"
        f"### Estilos\n#STYLES\n"
        f"TITLE={{font-size:48px;font-weight:bold}}\n"
        f"SUBTITLE={{font-size:36px;font-weight:bold;color:#3498DB}}\n"
        f"CODE={{font-family:Consolas;background:#282C34;color:#61AFEF;padding:10px}}\n"
        f"QUOTE={{font-style:italic;font-size:32px}}\n"
        f"LIST_ITEM={{font-size:32px;text-align:left;margin-left:30px}}\n"
        f"HIGHLIGHT={{color:#3498DB;font-weight:bold}}\n\n"
        f"### Portada\n#COVER\n"
        f"ASSET={course_cfg.get('cover_asset', 'videos/portada.mp4')}\n"
        f"NOTES=Video de portada\n\n\n"
        f"### Segmentos\n"
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def run_visual_orchestration(class_id: int, guion_base_content: str,
                              course_cfg: dict, audio_filename: str):
    from openai import OpenAI

    def phase(status, pct, msg, error=None):
        upd = {'status': status, 'progress': pct, 'phase': msg}
        if error is not None:
            upd['error'] = error
        _update_db(class_id, upd)

    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            phase('error', 0, '❌ OPENAI_API_KEY no encontrada', error='OPENAI_API_KEY no configurada')
            return

        client = OpenAI(api_key=api_key)

        phase('running', 5, '📖 Parseando guion base…')
        segments = _parse_guion_base(guion_base_content)
        if not segments:
            phase('error', 0, '❌ guion_base vacío', error='No se encontraron segmentos #SEGMENT')
            return

        payload_visual   = []
        payload_remotion = []
        rem_counter      = 0

        for idx, seg in enumerate(segments, start=1):
            tipo = seg.get('TYPE', '')
            if tipo == 'REMOTION':
                params_str  = seg.get('PARAMS', '')
                template    = params_str.split('//')[0].replace('$', '').strip() or 'TypeWriter'
                dur_s       = float(seg.get('TIME', 0.0))
                m, s        = int(dur_s // 60), int(dur_s % 60)
                rem_counter += 1
                out_file    = f"REM{rem_counter:02d}.mp4"
                payload_remotion.append({
                    'id': idx, 'template': template,
                    'speech': seg.get('SPEECH', ''),
                    'duration': f"{m}:{s:02d}",
                    'output_filename': out_file,
                })
            else:
                payload_visual.append({'id': idx, 'tipo': tipo, 'speech': seg.get('SPEECH', '')})

        phase('running', 10,
              f"🔍 {len(payload_visual)} segmentos visuales · {len(payload_remotion)} REMOTION")

        # VisualAssistant
        mapa_visual = {}
        if payload_visual:
            phase('running', 15, '🧠 Diseñando arquitectura visual con IA…')
            actualizaciones = _enriquecer_visuales(client, payload_visual)
            if len(actualizaciones) != len(payload_visual):
                print(f"⚠️ IA devolvió {len(actualizaciones)} pero se enviaron {len(payload_visual)}")
            for p, sub in zip(payload_visual, actualizaciones):
                mapa_visual[sub.get('id', p['id'])] = sub

        # RemotionAssistant
        mapa_remotion    = {}
        remotion_configs = []
        if payload_remotion:
            phase('running', 60, f'🎬 Generando datos Remotion ({len(payload_remotion)} escenas)…')
            remotion_configs = _generar_configs_remotion(client, payload_remotion)
            mapa_remotion    = {p['id']: p for p in payload_remotion}

        phase('running', 80, '📝 Construyendo guion consolidado…')

        texto_final   = _generar_header(course_cfg, audio_filename)
        recursos      = []
        field_order   = ['TYPE', 'PARAMS', 'TIME', 'TEXT', 'TEXT_STYLE', 'ASSET', 'SPEECH', 'NOTES']
        rem_cfg_idx   = 0

        for idx, sg in enumerate(segments, start=1):
            tipo = sg.get('TYPE', '')

            if tipo == 'REMOTION':
                cfg_rem  = remotion_configs[rem_cfg_idx] if rem_cfg_idx < len(remotion_configs) else {}
                rem_cfg_idx += 1
                out_file = cfg_rem.get('output', mapa_remotion.get(idx, {}).get('output_filename', f"REM{rem_cfg_idx:02d}.mp4"))
                sg['ASSET'] = f"videos/{out_file}"
                sg['TEXT']  = ''
                recursos.append({
                    'nombre': out_file, 'ubicacion': f"videos/{out_file}",
                    'tipo': 'video', 'tipo_contenido': 'remotion',
                    'segmento': sg['TIMESTAMP'],
                    'duracion': float(sg.get('TIME', 0.0)),
                    'descripcion': f"Remotion template: {cfg_rem.get('template', '')}",
                    'remotion_data': cfg_rem.get('data', {}),
                })
            else:
                sub = mapa_visual.get(idx, {})

                def _v(d, k):
                    return d.get(k) or d.get(k.upper(), '')

                sg['TEXT']       = _v(sub, 'text')
                sg['TEXT_STYLE'] = _v(sub, 'text_style')

                if not sg['TEXT'] and tipo in ('TEXT', 'SPLIT_LEFT', 'SPLIT_RIGHT'):
                    palabras = sg.get('SPEECH', '').split()
                    sg['TEXT'] = ' '.join(palabras[:10]) + ('…' if len(palabras) > 10 else '')

                asset_file = _v(sub, 'asset_filename')

                if asset_file:
                    new_prefix = None
                    if 'SPLIT' in tipo:        new_prefix = 'S'
                    elif tipo == 'FULL_IMAGE':  new_prefix = 'F'
                    elif tipo == 'VIDEO':        new_prefix = 'V'
                    if new_prefix and not asset_file.startswith(new_prefix):
                        digits     = ''.join(c for c in asset_file if c.isdigit()) or str(idx).zfill(2)
                        ext        = 'mp4' if new_prefix == 'V' else 'png'
                        asset_file = f"{new_prefix}{digits}.{ext}"

                if not asset_file and tipo in ('SPLIT_LEFT', 'SPLIT_RIGHT', 'FULL_IMAGE', 'VIDEO'):
                    ts         = sg['TIMESTAMP'].replace(':', '_').replace('.', '_')
                    prefix     = 'S' if 'SPLIT' in tipo else ('F' if tipo == 'FULL_IMAGE' else 'V')
                    ext        = 'mp4' if tipo == 'VIDEO' else 'png'
                    asset_file = f"{prefix}_AUTO_{ts}.{ext}"

                if asset_file and tipo not in ('CONCEPT', 'LIST'):
                    folder      = 'videos' if asset_file.endswith('.mp4') else 'images'
                    sg['ASSET'] = f"{folder}/{asset_file}"
                    recursos.append({
                        'nombre': asset_file, 'ubicacion': f"{folder}/{asset_file}",
                        'tipo': _v(sub, 'asset_tipo'),
                        'tipo_contenido': _v(sub, 'asset_tipo_contenido'),
                        'segmento': sg['TIMESTAMP'],
                        'duracion': float(sg.get('TIME', 0.0)),
                        'descripcion': _v(sub, 'asset_descripcion'),
                    })
                elif tipo in ('CONCEPT', 'LIST'):
                    sg['ASSET'] = 'DYNAMIC_GENERATED'
                    sg['TEXT']  = ''
                else:
                    sg['ASSET'] = ''

            texto_final += f"#SEGMENT [{sg['TIMESTAMP']}]\n"
            for field in field_order:
                if field in sg:
                    texto_final += f"{field}={sg.get(field, '')}\n"
            texto_final += '\n'

        phase('running', 95, '💾 Generando recursos_visuales.json…')

        json_maestro = {
            'proyecto':       course_cfg.get('title', 'Proyecto'),
            'total_recursos': len(recursos),
            'recursos':       [{k: v for k, v in r.items() if k != 'descripcion'} for r in recursos],
        }
        if remotion_configs:
            json_maestro['remotion'] = remotion_configs

        _update_db(class_id, {
            'status':        'done',
            'progress':      100,
            'phase':         f"✅ {len(segments)} segmentos · {len(recursos)} assets · {len(payload_remotion)} Remotion",
            'error':         None,
            'content':       texto_final,
            'recursos_json': json.dumps(json_maestro, ensure_ascii=False, indent=2),
        })

    except Exception as e:
        err = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        phase('error', 0, '❌ Error en orquestación visual', error=err)
