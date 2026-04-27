import os
import re
import yaml
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

# Cargar .env si existe
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Prompt Imágenes API")

PROJECTS_DIR = BASE_DIR / "proyectos"
STATIC_DIR = Path(__file__).parent / "static_imagenes"
META_PROMPT_PATH = BASE_DIR / "META_PROMPT_ARREGLA_IMAGENES.txt"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Modelos ───────────────────────────────────────────────────────────────────

class ImageEntry(BaseModel):
    id: str                     # Ej: F001, S003
    filename: str               # Ej: F001.png
    kind: str                   # "full" | "split"
    timestamp: Optional[str]    # [MM:SS.mmm]
    duration: Optional[str]
    tipo_contenido: Optional[str]
    prompt: str
    prompt_reparado: Optional[str] = "" # Nuevo campo persistido
    speech: str                 # Extraído del guion_consolidado.txt
    asset_ref: str              # Valor del campo ASSET en el TXT

class FixPromptRequest(BaseModel):
    project_id: str
    image_id: str
    filename: str
    prompt: str
    speech: str


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_imagenes_md(path: Path, kind: str) -> List[dict]:
    """
    Parsea imagenes_full.md o imagenes_split.md.
    Cada entrada tiene encabezado ### XXXX.png con bullets debajo.
    """
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    # Separar por ### XXX.png
    blocks = re.split(r"(###\s+\S+\.png)", content)
    entries = []

    for i in range(1, len(blocks), 2):
        header = blocks[i].strip()          # "### F001.png"
        body   = blocks[i + 1].strip() if (i + 1) < len(blocks) else ""

        filename = header.lstrip("#").strip()   # "F001.png"
        img_id   = filename.replace(".png", "") # "F001"

        fields = {}
        for line in body.splitlines():
            m = re.match(r"-\s+\*\*(.+?)\*\*[:\s]*(.*)", line)
            if m:
                key = m.group(1).strip().rstrip(":").lower().replace(" ", "_")
                val = m.group(2).strip()
                fields[key] = val

        # Campo descripción (puede ser largo, puede ser "Descripción" o "Descripcion")
        prompt = fields.get("descripción", fields.get("descripcion", ""))
        timestamp = fields.get("segmento", "")
        timestamp = timestamp.strip("[]")   # Quitar corchetes si los tiene

        entries.append({
            "id": img_id,
            "filename": filename,
            "kind": kind,
            "timestamp": timestamp,
            "duration": fields.get("duración", fields.get("duracion", "")),
            "tipo_contenido": fields.get("tipo_contenido", ""),
            "prompt": prompt,
        })

    return entries


def parse_guion_txt(project_id: str) -> dict:
    """
    Parsea guion_consolidado.txt y devuelve un dict
    {asset_filename: {speech, timestamp, ...}}
    keyed por el valor de ASSET (ej: images/F001.png → F001.png)
    también por timestamp para fallback.
    """
    txt_path = PROJECTS_DIR / project_id / "output/03_guion/guion_consolidado.txt"
    if not txt_path.exists():
        return {}

    content = txt_path.read_text(encoding="utf-8")
    parts = re.split(r"(#SEGMENT\s+\[[^\]]+\])", content)

    by_asset = {}     # key: "F001.png" or "S001.png"
    by_timestamp = {} # key: "13:00.188"

    for i in range(1, len(parts), 2):
        ts_header  = parts[i]
        block_data = parts[i + 1] if (i + 1) < len(parts) else ""

        ts = ts_header.replace("#SEGMENT", "").strip(" []")
        lines = block_data.strip().splitlines()
        fields = {}
        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                fields[k.strip().upper()] = v.strip()

        speech = fields.get("SPEECH", "")
        asset  = fields.get("ASSET", "")

        # Normalizar asset → solo nombre de archivo
        asset_filename = Path(asset).name if asset else ""

        record = {
            "speech": speech,
            "timestamp": ts,
            "asset_ref": asset,
            "fields": fields,
        }

        if asset_filename:
            by_asset[asset_filename] = record
        by_timestamp[ts] = record

    return {"by_asset": by_asset, "by_timestamp": by_timestamp}


def parse_reparados_md(path: Path) -> dict:
    """
    Parsea prompt_imagenes_reparado.md y devuelve dict {filename: prompt_reparado}
    """
    if not path.exists():
        return {}
    
    content = path.read_text(encoding="utf-8")
    blocks = re.split(r"(###\s+\S+\.png)", content)
    reparados = {}

    for i in range(1, len(blocks), 2):
        header = blocks[i].strip()
        body   = blocks[i + 1].strip() if (i + 1) < len(blocks) else ""
        filename = header.lstrip("#").strip()
        
        # El cuerpo es el prompt reparado directamente
        reparados[filename] = body.strip()
    
    return reparados


def save_reparado_md(path: Path, filename: str, prompt_reparado: str):
    """
    Guarda o actualiza un prompt reparado en el archivo.
    """
    reparados = parse_reparados_md(path)
    reparados[filename] = prompt_reparado

    new_content = "# Prompts Reparados con IA\n\n"
    # Ordenar para consistencia
    for fname in sorted(reparados.keys()):
        new_content += f"### {fname}\n{reparados[fname]}\n\n"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_content, encoding="utf-8")


def build_entries(project_id: str) -> List[ImageEntry]:
    base = PROJECTS_DIR / project_id / "output/03_guion"
    full_entries  = parse_imagenes_md(base / "imagenes_full.md",  "full")
    split_entries = parse_imagenes_md(base / "imagenes_split.md", "split")
    
    reparados = parse_reparados_md(base / "prompt_imagenes_reparado.md")

    guion = parse_guion_txt(project_id)
    by_asset     = guion.get("by_asset", {})
    by_timestamp = guion.get("by_timestamp", {})

    all_entries = full_entries + split_entries
    result = []

    for e in all_entries:
        # Buscar speech: primero por filename, luego por timestamp
        guion_rec = by_asset.get(e["filename"]) or by_timestamp.get(e["timestamp"]) or {}

        result.append(ImageEntry(
            id=e["id"],
            filename=e["filename"],
            kind=e["kind"],
            timestamp=e["timestamp"],
            duration=e["duration"],
            tipo_contenido=e["tipo_contenido"],
            prompt=e["prompt"],
            prompt_reparado=reparados.get(e["filename"], ""),
            speech=guion_rec.get("speech", ""),
            asset_ref=guion_rec.get("asset_ref", f"images/{e['filename']}"),
        ))

    # Ordenar por timestamp (MM:SS.mmm)
    def ts_sort_key(entry: ImageEntry):
        ts = entry.timestamp or "99:99.999"
        try:
            parts = ts.replace("[", "").replace("]", "").split(":")
            mins = int(parts[0])
            secs = float(parts[1])
            return mins * 60 + secs
        except Exception:
            return 9999

    result.sort(key=ts_sort_key)
    return result


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/projects")
def list_projects():
    if not PROJECTS_DIR.exists():
        return []
    projects = []
    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        guion_dir = d / "output/03_guion"
        # Solo incluir proyectos que tengan al menos uno de los archivos
        if (guion_dir / "imagenes_full.md").exists() or (guion_dir / "imagenes_split.md").exists():
            projects.append(d.name)
    return projects


@app.get("/api/imagenes/{project_id}", response_model=List[ImageEntry])
def get_imagenes(project_id: str):
    base = PROJECTS_DIR / project_id / "output/03_guion"
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Proyecto '{project_id}' no encontrado")
    return build_entries(project_id)


@app.get("/api/stats/{project_id}")
def get_stats(project_id: str):
    entries = build_entries(project_id)
    total_full  = sum(1 for e in entries if e.kind == "full")
    total_split = sum(1 for e in entries if e.kind == "split")
    total_with_speech = sum(1 for e in entries if e.speech)
    return {
        "total": len(entries),
        "full": total_full,
        "split": total_split,
        "with_speech": total_with_speech,
    }


@app.post("/api/fix-prompt")
def fix_prompt(req: FixPromptRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY no configurada")
    
    if not META_PROMPT_PATH.exists():
        raise HTTPException(status_code=500, detail="Archivo META_PROMPT_ARREGLA_IMAGENES.txt no encontrado")
    
    meta_prompt = META_PROMPT_PATH.read_text(encoding="utf-8")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Cargar modelo de ai_config.yaml (usamos el del visual_assistant como referencia)
    ai_cfg_path = BASE_DIR / "ai_config.yaml"
    model = "gpt-4o" # Fallback
    if ai_cfg_path.exists():
        try:
            cfg = yaml.safe_load(ai_cfg_path.read_text(encoding="utf-8"))
            model = cfg.get("visual_assistant", {}).get("model", model)
        except: pass

    user_content = f"INPUT PROMPT (Spanish): {req.prompt}\nINPUT NARRATION: {req.speech}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": meta_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3
        )
        
        reparado = response.choices[0].message.content.strip()
        
        # Guardar persistencia
        base = PROJECTS_DIR / req.project_id / "output/03_guion"
        save_reparado_md(base / "prompt_imagenes_reparado.md", req.filename, reparado)
        
        return {"reparado": reparado}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
