"""
Port exacto de:
  0_referencia/pipeline/visual_orchestrator.py → VisualOrchestrator
  0_referencia/pipeline/visual_assistant.py    → VisualAssistant
  0_referencia/pipeline/remotion_assistant.py  → RemotionAssistant

Lee prompts y templates directamente desde 0_referencia/ para mantenerse en sync.
Mismos modelos, misma lógica de sanitización de assets, mismo formato de salida.
"""
import json
import os
import re
import traceback
from datetime import datetime

# ── Paths to 0_referencia configs ─────────────────────────────────────────────
_REF_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '0_referencia')
)
_AI_CONFIG_PATH       = os.path.join(_REF_ROOT, 'ai_config.yaml')
_REMOTION_TMPL_PATH   = os.path.join(_REF_ROOT, 'ai_remotion_templates.yaml')


def _load_yaml(path):
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[visual_agent] cannot load {path}: {e}")
        return {}


def _get_visual_cfg():
    cfg = _load_yaml(_AI_CONFIG_PATH)
    va  = cfg.get('visual_assistant', {})
    return {
        'model':         va.get('model',       'gpt-5.4-mini'),
        'temperature':   va.get('temperature', 0.3),
        'system_prompt': va.get('system_prompt', ''),
    }


def _get_remotion_cfg():
    cfg  = _load_yaml(_AI_CONFIG_PATH)
    ra   = cfg.get('remotion_assistant', {})
    base = ra.get('system_prompt', '')
    tmpl = ''
    if os.path.exists(_REMOTION_TMPL_PATH):
        with open(_REMOTION_TMPL_PATH, 'r', encoding='utf-8') as f:
            tmpl = f.read()
    prompt = base.replace(
        "[NOTA: EL CATÁLOGO DE TEMPLATES SE INYECTA DINÁMICAMENTE AQUÍ DESDE ai_remotion_templates.yaml]",
        tmpl
    )
    return {
        'model':         ra.get('model',       'gpt-5.4-mini'),
        'temperature':   ra.get('temperature', 0.1),
        'system_prompt': prompt,
    }


# ── Parsing ───────────────────────────────────────────────────────────────────

def _parse_guion_base(content: str) -> list:
    """Parse guion_base.txt → list of segment dicts. Same logic as VisualOrchestrator."""
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

def _enriquecer_visuales(client, payload: list, cfg: dict) -> list:
    """Exact port of VisualAssistant.enriquecer_visuales()."""
    if not payload:
        return []
    resp = client.chat.completions.create(
        model=cfg['model'],
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': cfg['system_prompt']},
            {'role': 'user',   'content': json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=cfg['temperature'],
    )
    result = json.loads(resp.choices[0].message.content)
    return result.get('actualizaciones', [])


# ── RemotionAssistant ─────────────────────────────────────────────────────────

def _generar_configs_remotion(client, payload: list, cfg: dict) -> list:
    """Exact port of RemotionAssistant.generar_configs()."""
    if not payload:
        return []
    resp = client.chat.completions.create(
        model=cfg['model'],
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': cfg['system_prompt']},
            {'role': 'user',   'content': json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=cfg['temperature'],
    )
    resultado = json.loads(resp.choices[0].message.content)
    configs = []
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


# ── Header generator ──────────────────────────────────────────────────────────

def _generar_header(course_cfg: dict, audio_filename: str) -> str:
    """Exact port of VisualOrchestrator._generar_header()."""
    return (
        f"/// HEADER GENERICO AUTOGENERADO POR VISUAL-ORCHESTRATOR\n"
        f"### Metadatos\n"
        f"#META\n"
        f"FILES_FOLDER={course_cfg.get('files_folder', 'assets')}\n"
        f"TITLE={course_cfg.get('title', 'Proyecto')}\n"
        f"MAIN_AUDIO={audio_filename}\n"
        f"FPS={course_cfg.get('fps', 30)}\n"
        f"RESOLUTION={course_cfg.get('resolution', '1920x1080')}\n"
        f"MAIN_FONT={course_cfg.get('main_font', 'Inter')}\n"
        f"BACKGROUND_COLOR={course_cfg.get('background_color', '#fefefe')}\n"
        f"MAIN_TEXT_COLOR={course_cfg.get('main_text_color', '#bd0505')}\n"
        f"HIGHLIGHT_TEXT_COLOR={course_cfg.get('highlight_text_color', '#e3943b')}\n\n"
        f"### Estilos\n"
        f"#STYLES\n"
        f"TITLE={{font-size:48px;font-weight:bold}}\n"
        f"SUBTITLE={{font-size:36px;font-weight:bold;color:#3498DB}}\n"
        f"CODE={{font-family:Consolas;background:#282C34;color:#61AFEF;padding:10px}}\n"
        f"QUOTE={{font-style:italic;font-size:32px}}\n"
        f"LIST_ITEM={{font-size:32px;text-align:left;margin-left:30px}}\n"
        f"HIGHLIGHT={{color:#3498DB;font-weight:bold}}\n\n"
        f"### Portada\n"
        f"#COVER\n"
        f"ASSET={course_cfg.get('cover_asset', 'videos/portada.mp4')}\n"
        f"NOTES=Video de portada\n\n\n"
        f"### Segmentos\n"
    )


# ── DB helper ─────────────────────────────────────────────────────────────────

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


# ── Entry point (background thread) ──────────────────────────────────────────

def run_visual_orchestration(class_id: int, guion_base_content: str,
                              course_cfg: dict, audio_filename: str):
    """
    Port exacto de VisualOrchestrator.procesar_guion().
    Produces guion_consolidado.txt + recursos_visuales.json.
    """
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
            phase('error', 0, '❌ guion_base vacío o sin segmentos', error='No se encontraron segmentos #SEGMENT')
            return

        # ── Separate REMOTION vs visual segments ──────────────────────────────
        payload_visual   = []
        payload_remotion = []
        rem_counter      = 0

        for idx, seg in enumerate(segments, start=1):
            tipo = seg.get('TYPE', '')
            if tipo == 'REMOTION':
                params_str = seg.get('PARAMS', '')
                template   = params_str.split('//')[0].replace('$', '').strip() or 'TypeWriter'
                dur_s      = float(seg.get('TIME', 0.0))
                m, s       = int(dur_s // 60), int(dur_s % 60)
                rem_counter += 1
                out_file   = f"REM{rem_counter:02d}.mp4"
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

        # ── VisualAssistant ───────────────────────────────────────────────────
        mapa_visual = {}
        if payload_visual:
            phase('running', 15, '🧠 Diseñando arquitectura visual con IA…')
            va_cfg = _get_visual_cfg()
            actualizaciones = _enriquecer_visuales(client, payload_visual, va_cfg)
            if len(actualizaciones) != len(payload_visual):
                print(f"⚠️ IA devolvió {len(actualizaciones)} pero se enviaron {len(payload_visual)}")
            for p, sub in zip(payload_visual, actualizaciones):
                mapa_visual[sub.get('id', p['id'])] = sub

        # ── RemotionAssistant ─────────────────────────────────────────────────
        mapa_remotion = {}
        remotion_configs = []
        if payload_remotion:
            phase('running', 60, f'🎬 Generando datos Remotion ({len(payload_remotion)} escenas)…')
            rem_cfg = _get_remotion_cfg()
            remotion_configs = _generar_configs_remotion(client, payload_remotion, rem_cfg)
            mapa_remotion = {p['id']: p for p in payload_remotion}

        # ── Build guion_consolidado ───────────────────────────────────────────
        phase('running', 80, '📝 Construyendo guion consolidado…')

        texto_final    = _generar_header(course_cfg, audio_filename)
        recursos       = []
        field_order    = ['TYPE', 'PARAMS', 'TIME', 'TEXT', 'TEXT_STYLE', 'ASSET', 'SPEECH', 'NOTES']

        rem_config_idx = 0

        for idx, sg in enumerate(segments, start=1):
            tipo = sg.get('TYPE', '')

            if tipo == 'REMOTION':
                cfg_rem = remotion_configs[rem_config_idx] if rem_config_idx < len(remotion_configs) else {}
                rem_config_idx += 1
                out_file = cfg_rem.get('output', mapa_remotion.get(idx, {}).get('output_filename', f"REM{rem_config_idx:02d}.mp4"))
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

                # Fallback: si la IA no llenó TEXT, extraer primeras palabras del SPEECH
                if not sg['TEXT'] and tipo in ('TEXT', 'SPLIT_LEFT', 'SPLIT_RIGHT'):
                    palabras = sg.get('SPEECH', '').split()
                    sg['TEXT'] = ' '.join(palabras[:10]) + ('…' if len(palabras) > 10 else '')

                asset_file = _v(sub, 'asset_filename')

                # ── Asset prefix sanitization (exact port) ────────────────────
                if asset_file:
                    new_prefix = None
                    if 'SPLIT' in tipo:      new_prefix = 'S'
                    elif tipo == 'FULL_IMAGE': new_prefix = 'F'
                    elif tipo == 'VIDEO':      new_prefix = 'V'

                    if new_prefix and not asset_file.startswith(new_prefix):
                        digits = ''.join(c for c in asset_file if c.isdigit()) or str(idx).zfill(2)
                        ext    = 'mp4' if new_prefix == 'V' else 'png'
                        asset_file = f"{new_prefix}{digits}.{ext}"

                if not asset_file and tipo in ('SPLIT_LEFT', 'SPLIT_RIGHT', 'FULL_IMAGE', 'VIDEO'):
                    ts = sg['TIMESTAMP'].replace(':', '_').replace('.', '_')
                    prefix = 'S' if 'SPLIT' in tipo else ('F' if tipo == 'FULL_IMAGE' else 'V')
                    ext    = 'mp4' if tipo == 'VIDEO' else 'png'
                    asset_file = f"{prefix}_AUTO_{ts}.{ext}"
                    print(f"⚠️ Auto-generando asset: {asset_file}")

                if asset_file and tipo not in ('CONCEPT', 'LIST'):
                    folder = 'videos' if asset_file.endswith('.mp4') else 'images'
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

            # ── Append to guion_consolidado ───────────────────────────────────
            texto_final += f"#SEGMENT [{sg['TIMESTAMP']}]\n"
            for field in field_order:
                if field in sg:
                    texto_final += f"{field}={sg.get(field, '')}\n"
            texto_final += '\n'

        # ── Build recursos_visuales.json ──────────────────────────────────────
        phase('running', 95, '💾 Generando recursos_visuales.json…')

        recursos_sin_desc = [{k: v for k, v in r.items() if k != 'descripcion'} for r in recursos]
        json_maestro = {
            'proyecto':       course_cfg.get('title', 'Proyecto'),
            'total_recursos': len(recursos_sin_desc),
            'recursos':       recursos_sin_desc,
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
