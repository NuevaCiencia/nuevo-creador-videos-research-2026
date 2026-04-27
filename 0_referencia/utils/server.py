import os
import re
import json
import shutil
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path

app = FastAPI()

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
PROJECTS_DIR = BASE_DIR / "proyectos"
STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/projects", StaticFiles(directory=str(PROJECTS_DIR)), name="projects")

class UnifiedScene(BaseModel):
    index: int
    type: str # Tipo actual (del MD)
    original_type: str # Tipo guardado en el MD originalmente
    params: Optional[str] = ""
    content_md: str # Contenido del bloque MD
    raw_block_md: str
    
    # Datos del guion consolidado (.txt)
    timestamp: Optional[str] = None
    duration: Optional[str] = "0.0"
    speech: Optional[str] = ""
    text_on_screen: Optional[str] = ""
    raw_block_txt: Optional[str] = ""
    extra_fields_txt: Optional[Dict[str, str]] = {}
    
    has_guion: bool = False

class UnifiedProjectData(BaseModel):
    project_id: str
    header_md: str
    header_txt: str
    scenes: List[UnifiedScene]

class SaveUnifiedRequest(BaseModel):
    header_md: str
    header_txt: str
    scenes: List[UnifiedScene]

def parse_md(project_id: str):
    file_path = PROJECTS_DIR / project_id / "original_speech.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Archivo MD no encontrado")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = re.split(r"(<!--\s*type:)", content)
    header = parts[0]
    scenes = []
    for i in range(1, len(parts), 2):
        rest = parts[i+1]
        m = re.match(r"(.*?)-->", rest, re.DOTALL)
        if not m: continue
        full_tag = m.group(1).strip()
        tags = full_tag.split("//")
        type_p = tags[0].strip()
        params_p = "//".join(tags[1:]).strip() if len(tags) > 1 else ""
        block_content = rest[m.end():]
        scenes.append({
            "type": type_p,
            "params": params_p,
            "content": block_content,
            "raw": block_content
        })
    return header, scenes

def parse_txt(project_id: str):
    file_path = PROJECTS_DIR / project_id / "output/03_guion/guion_consolidado.txt"
    if not file_path.exists():
        return "", []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = re.split(r"(#SEGMENT\s+\[[^\]]+\])", content)
    header = parts[0]
    segments = []
    for i in range(1, len(parts), 2):
        ts_header = parts[i]
        block_data = parts[i+1]
        ts = ts_header.replace("#SEGMENT", "").strip(" []")
        lines = block_data.strip().split("\n")
        data = {}
        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip().upper()] = v.strip()
        segments.append({
            "timestamp": ts,
            "raw": block_data,
            "fields": data
        })
    return header, segments

@app.get("/api/projects")
def list_projects():
    if not PROJECTS_DIR.exists(): return []
    return sorted([d.name for d in PROJECTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")])

@app.get("/api/load/{project_id}/unified")
def load_unified(project_id: str):
    header_md, scenes_md = parse_md(project_id)
    header_txt, segments_txt = parse_txt(project_id)
    
    count_md = len(scenes_md)
    count_txt = len(segments_txt)
    is_synced = (count_md == count_txt) if count_txt > 0 else True # Si no hay TXT, no hay descuadre que validar aún
    
    unified_scenes = []
    has_guion = count_txt > 0
    
    for i, smd in enumerate(scenes_md):
        stxt = segments_txt[i] if i < count_txt else None
        
        unified_scenes.append(UnifiedScene(
            index=i,
            type=smd["type"],
            original_type=smd["type"],
            params=smd["params"],
            content_md=smd["content"],
            raw_block_md=smd["raw"],
            
            timestamp=stxt["timestamp"] if stxt else None,
            duration=stxt["fields"].get("TIME", "0.0") if stxt else "0.0",
            speech=stxt["fields"].get("SPEECH", "") if stxt else "",
            text_on_screen=stxt["fields"].get("TEXT", "") if stxt else "",
            raw_block_txt=stxt["raw"] if stxt else "",
            extra_fields_txt=stxt["fields"] if stxt else {},
            has_guion=has_guion
        ))
        
    # Verificar sesión unificada
    session_path = PROJECTS_DIR / project_id / "unified_session.json"
    session_data = None
    if session_path.exists():
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except: pass

    # Obtener resolución del video_config.yaml
    video_cfg_path = PROJECTS_DIR / project_id / "video_config.yaml"
    resolution = "1920x1080" # Fallback
    bg_color = "#000000"     # Fallback
    text_color = "#FFFFFF"   # Fallback
    if video_cfg_path.exists():
        try:
            import yaml
            with open(video_cfg_path, "r", encoding="utf-8") as fb:
                cfg = yaml.safe_load(fb)
                resolution = cfg.get("RESOLUTION", resolution)
                bg_color = cfg.get("BACKGROUND_COLOR", bg_color)
                text_color = cfg.get("MAIN_TEXT_COLOR", text_color)
        except: pass

    return {
        "project_id": project_id,
        "header_md": header_md,
        "header_txt": header_txt,
        "scenes": unified_scenes,
        "has_session": session_path.exists(),
        "session_data": session_data,
        "is_synced": is_synced,
        "count_md": count_md,
        "count_txt": count_txt,
        "resolution": resolution,
        "bg_color": bg_color,
        "text_color": text_color
    }


@app.post("/api/cache/{project_id}/unified")
def cache_unified(project_id: str, data: SaveUnifiedRequest):
    session_path = PROJECTS_DIR / project_id / "unified_session.json"
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, ensure_ascii=False, indent=2)
    return {"status": "cached"}

@app.post("/api/save/{project_id}/unified")
def save_unified(project_id: str, data: SaveUnifiedRequest):
    p_dir = PROJECTS_DIR / project_id
    md_path = p_dir / "original_speech.md"
    txt_path = p_dir / "output/03_guion/guion_consolidado.txt"
    
    # 1. Backups
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if md_path.exists():
        (p_dir / "backups").mkdir(exist_ok=True)
        shutil.copy2(md_path, p_dir / "backups" / f"original_speech_{ts}.md")
    if txt_path.exists():
        (p_dir / "output/03_guion/backups").mkdir(exist_ok=True, parents=True)
        shutil.copy2(txt_path, p_dir / "output/03_guion/backups" / f"guion_{ts}.txt")
        
    # 2. Guardar MD
    new_md = data.header_md
    for s in data.scenes:
        tag = f"<!-- type:{s.type}"
        if s.params: tag += f" // {s.params}"
        tag += " -->"
        new_md += tag + s.raw_block_md
    with open(md_path, "w", encoding="utf-8") as f: f.write(new_md)
    
    # 3. Guardar TXT (si existe)
    if txt_path.exists():
        new_txt = data.header_txt
        for s in data.scenes:
            new_txt += f"#SEGMENT [{s.timestamp}]\n"
            fields = s.extra_fields_txt or {}
            fields["TEXT"] = s.text_on_screen or ""
            fields["TYPE"] = s.type # Sincronizar tipo también en el TXT por si acaso
            for k, v in fields.items():
                new_txt += f"{k}={v}\n"
            new_txt += "\n"
        with open(txt_path, "w", encoding="utf-8") as f: f.write(new_txt)
        
    # 4. Limpiar sesión
    session_path = p_dir / "unified_session.json"
    if session_path.exists(): os.remove(session_path)
    
    return {"status": "saved"}

@app.delete("/api/cache/{project_id}/unified")
def delete_cache(project_id: str):
    session_path = PROJECTS_DIR / project_id / "unified_session.json"
    if session_path.exists():
        os.remove(session_path)
    return {"status": "deleted"}

@app.get("/")
def read_index():
    from fastapi.responses import FileResponse
    return FileResponse(STATIC_DIR / "index.html")
