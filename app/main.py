import os
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, get_db, init_db
import models
from ai_agents import research_agent, screen_agent, whisper_agent, spell_agent, aligner_agent

_whisper_pool = ThreadPoolExecutor(max_workers=1)  # one transcription at a time

# ── Bootstrap ──────────────────────────────────────────────────────────────────
init_db()

app = FastAPI(title="Video Creator")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


def get_audio_duration(file_path: str) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True, timeout=15,
        )
        return round(float(r.stdout.strip()), 2)
    except Exception:
        return 0.0


@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ── Schemas ────────────────────────────────────────────────────────────────────

class CourseIn(BaseModel):
    title: str
    description: Optional[str] = ""

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class SectionIn(BaseModel):
    title: str

class SectionUpdate(BaseModel):
    title: str

class ClassIn(BaseModel):
    title: str

class ClassUpdate(BaseModel):
    title: Optional[str] = None
    raw_narration: Optional[str] = None

class ScreenTypeIn(BaseModel):
    name: str
    label: str
    category: str
    description: Optional[str] = ""
    icon: Optional[str] = ""
    color: Optional[str] = "#666666"
    asset_prefix: Optional[str] = ""
    asset_ext: Optional[str] = ""
    has_params: Optional[bool] = False
    params_syntax: Optional[str] = ""
    tag_format: Optional[str] = ""
    sort_order: Optional[int] = 0
    max_items: Optional[int] = None
    max_words: Optional[int] = None
    max_chars: Optional[int] = None

class ScreenTypeUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    asset_prefix: Optional[str] = None
    asset_ext: Optional[str] = None
    has_params: Optional[bool] = None
    params_syntax: Optional[str] = None
    tag_format: Optional[str] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = None
    max_items: Optional[int] = None
    max_words: Optional[int] = None
    max_chars: Optional[int] = None

class RemotionTemplateIn(BaseModel):
    name: str
    label: str
    category: Optional[str] = ""
    description: Optional[str] = ""
    limits: Optional[str] = ""
    data_schema: Optional[str] = ""
    sort_order: Optional[int] = 0

class RemotionTemplateUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    limits: Optional[str] = None
    data_schema: Optional[str] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = None


# ── Serializers ────────────────────────────────────────────────────────────────

def ser_course(c: models.Course, db: Session = None):
    section_count = 0
    class_count   = 0
    if db:
        section_count = db.query(models.Section).filter(models.Section.course_id == c.id).count()
        class_count   = (
            db.query(models.Class)
            .join(models.Section)
            .filter(models.Section.course_id == c.id)
            .count()
        )
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description or "",
        "section_count": section_count,
        "class_count":   class_count,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }

def ser_research_item(item: models.ResearchItem):
    return {
        "id": item.id,
        "class_id": item.class_id,
        "claim": item.claim,
        "query": item.query,
        "status": item.status,
        "confidence": item.confidence,
        "source_url": item.source_url,
        "source_title": item.source_title,
        "source_snippet": item.source_snippet,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def ser_class(c: models.Class):
    text = c.raw_narration or ""
    return {
        "id": c.id,
        "section_id": c.section_id,
        "title": c.title,
        "order": c.order,
        "raw_narration": text,
        "char_count": len(text),
        "word_count": len(text.split()) if text.strip() else 0,
        "research_items": [ser_research_item(ri) for ri in c.research_items],
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }

def ser_segment(seg: models.ScreenSegment):
    return {
        "id":               seg.id,
        "class_id":         seg.class_id,
        "order":            seg.order,
        "screen_type":      seg.screen_type,
        "narration":        seg.narration or "",
        "params":           seg.params or "",
        "remotion_template":seg.remotion_template,
        "notes":            seg.notes or "",
        "created_at":       seg.created_at.isoformat() if seg.created_at else None,
    }

def ser_section(s: models.Section):
    return {
        "id": s.id,
        "course_id": s.course_id,
        "title": s.title,
        "order": s.order,
        "classes": [ser_class(c) for c in s.classes],
    }


# ── Courses ────────────────────────────────────────────────────────────────────

@app.get("/api/courses")
def list_courses(db: Session = Depends(get_db)):
    rows = db.query(models.Course).order_by(models.Course.created_at).all()
    return [ser_course(c, db) for c in rows]


@app.post("/api/courses", status_code=201)
def create_course(data: CourseIn, db: Session = Depends(get_db)):
    course = models.Course(title=data.title.strip(), description=data.description or "")
    db.add(course)
    db.commit()
    db.refresh(course)
    return ser_course(course)


@app.put("/api/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Curso no encontrado")
    if data.title is not None:
        course.title = data.title.strip()
    if data.description is not None:
        course.description = data.description
    course.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(course)
    return ser_course(course)


@app.delete("/api/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Curso no encontrado")
    db.delete(course)
    db.commit()


# ── Sections ───────────────────────────────────────────────────────────────────

@app.get("/api/courses/{course_id}/sections")
def list_sections(course_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Section)
        .filter(models.Section.course_id == course_id)
        .order_by(models.Section.order)
        .all()
    )
    return [ser_section(s) for s in rows]


@app.post("/api/courses/{course_id}/sections", status_code=201)
def create_section(course_id: int, data: SectionIn, db: Session = Depends(get_db)):
    count = db.query(models.Section).filter(models.Section.course_id == course_id).count()
    section = models.Section(course_id=course_id, title=data.title.strip(), order=count)
    db.add(section)
    db.commit()
    db.refresh(section)
    return ser_section(section)


@app.put("/api/sections/{section_id}")
def update_section(section_id: int, data: SectionUpdate, db: Session = Depends(get_db)):
    section = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not section:
        raise HTTPException(404, "Sección no encontrada")
    section.title = data.title.strip()
    db.commit()
    db.refresh(section)
    return ser_section(section)


@app.delete("/api/sections/{section_id}", status_code=204)
def delete_section(section_id: int, db: Session = Depends(get_db)):
    section = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not section:
        raise HTTPException(404, "Sección no encontrada")
    db.delete(section)
    db.commit()


# ── Classes ────────────────────────────────────────────────────────────────────

@app.get("/api/classes/{class_id}")
def get_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")
    return ser_class(cls)


@app.post("/api/sections/{section_id}/classes", status_code=201)
def create_class(section_id: int, data: ClassIn, db: Session = Depends(get_db)):
    count = db.query(models.Class).filter(models.Class.section_id == section_id).count()
    cls = models.Class(section_id=section_id, title=data.title.strip(), order=count)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return ser_class(cls)


@app.put("/api/classes/{class_id}")
def update_class(class_id: int, data: ClassUpdate, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")
    if data.title is not None:
        cls.title = data.title.strip()
    if data.raw_narration is not None:
        cls.raw_narration = data.raw_narration
    cls.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cls)
    return ser_class(cls)


# ── Research (Tavily Verification) ─────────────────────────────────────────────

@app.get("/api/classes/{class_id}/research")
def get_class_research(class_id: int, db: Session = Depends(get_db)):
    items = db.query(models.ResearchItem).filter(models.ResearchItem.class_id == class_id).all()
    return [ser_research_item(i) for i in items]


@app.post("/api/classes/{class_id}/research")
async def run_class_research(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls or not cls.raw_narration:
        raise HTTPException(400, "La clase no tiene guion para investigar")
    
    # 1. Extract claims
    try:
        claims = research_agent.extract_claims(cls.raw_narration)
    except Exception as e:
        raise HTTPException(500, f"Error al extraer afirmaciones: {str(e)}")
    
    # 2. Clear old research
    db.query(models.ResearchItem).filter(models.ResearchItem.class_id == class_id).delete()
    
    results = []
    # 3. Verify each claim
    for c_obj in claims:
        item = models.ResearchItem(
            class_id=class_id,
            claim=c_obj["claim"],
            query=c_obj["query"],
            status="pending"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        # Verify with Tavily
        try:
            v_res = research_agent.verify_claim(c_obj)
            item.status = v_res.get("status", "error")
            item.confidence = v_res.get("confidence")
            item.source_url = v_res.get("source_url")
            item.source_title = v_res.get("source_title")
            item.source_snippet = v_res.get("source_snippet")
        except Exception as e:
            item.status = "error"
            item.source_snippet = str(e)
        
        db.commit()
        results.append(ser_research_item(item))
        
    return results


@app.post("/api/research-items/{item_id}/reexamine")
async def reexamine_research_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ResearchItem).filter(models.ResearchItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Ítem no encontrado")
    if item.status not in ("disputed", "not_found", "error"):
        raise HTTPException(400, "Solo se pueden re-examinar ítems disputed, not_found o error")

    claim_obj = {"claim": item.claim, "query": item.query or item.claim}
    try:
        result = research_agent.reexamine_claim(claim_obj, item.status)
    except Exception as e:
        raise HTTPException(500, f"Error al re-examinar: {str(e)}")

    item.status        = result.get("status", "error")
    item.confidence    = result.get("confidence")
    item.source_url    = result.get("source_url")
    item.source_title  = result.get("source_title")
    item.source_snippet= result.get("source_snippet")
    if result.get("_new_query"):
        item.query = result["_new_query"]

    db.commit()
    db.refresh(item)
    return ser_research_item(item)


@app.delete("/api/research-items/{item_id}", status_code=204)
def delete_research_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ResearchItem).filter(models.ResearchItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Ítem no encontrado")
    db.delete(item)
    db.commit()



# ── Audio & Transcription ──────────────────────────────────────────────────────

ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".mp4", ".aac", ".ogg", ".flac"}

def ser_audio(a: models.ClassAudio):
    return {
        "id":            a.id,
        "class_id":      a.class_id,
        "filename":      a.filename,
        "file_url":      f"/assets/{a.class_id}/audio/{a.filename}",
        "duration":      a.duration,
        "size_bytes":    a.size_bytes,
        "whisper_model": a.whisper_model,
        "tx_status":     a.tx_status,
        "tx_progress":   a.tx_progress,
        "tx_phase":      a.tx_phase or "",
        "tx_error":      a.tx_error,
        "tx_raw_text":   a.tx_raw_text,
        "tx_srt":        a.tx_srt,
        "tx_segments":   json.loads(a.tx_segments) if a.tx_segments else [],
        "tx_updated_at": a.tx_updated_at.isoformat() if a.tx_updated_at else None,
        "created_at":    a.created_at.isoformat() if a.created_at else None,
    }


@app.get("/api/classes/{class_id}/audio")
def get_audio(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if not row:
        raise HTTPException(404, "Sin audio")
    return ser_audio(row)


@app.get("/api/classes/{class_id}/audio/status")
def get_audio_status(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if not row:
        return {"tx_status": "no_audio"}
    return {
        "tx_status":     row.tx_status,
        "tx_progress":   row.tx_progress,
        "tx_phase":      row.tx_phase or "",
        "tx_error":      row.tx_error,
        "tx_updated_at": row.tx_updated_at.isoformat() if row.tx_updated_at else None,
    }


@app.post("/api/classes/{class_id}/audio", status_code=201)
async def upload_audio(class_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_AUDIO_EXTS:
        raise HTTPException(400, f"Formato no soportado. Usa: {', '.join(ALLOWED_AUDIO_EXTS)}")

    audio_dir = os.path.join(ASSETS_DIR, str(class_id), "audio")
    os.makedirs(audio_dir, exist_ok=True)

    safe_name = f"original{ext}"
    file_path = os.path.join(audio_dir, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    duration = get_audio_duration(file_path)

    # Upsert
    row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if row:
        row.filename   = safe_name
        row.file_path  = file_path
        row.duration   = duration
        row.size_bytes = len(content)
        row.tx_status  = "idle"
        row.tx_progress= 0
        row.tx_phase   = ""
        row.tx_error   = None
        row.tx_raw_text= None
        row.tx_segments= None
        row.whisper_model = None
    else:
        row = models.ClassAudio(
            class_id=class_id,
            filename=safe_name,
            file_path=file_path,
            duration=duration,
            size_bytes=len(content),
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return ser_audio(row)


@app.delete("/api/classes/{class_id}/audio", status_code=204)
def delete_audio(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if not row:
        raise HTTPException(404, "Sin audio")
    if row.tx_status in ("loading_model", "transcribing", "aligning", "saving"):
        raise HTTPException(400, "No se puede eliminar mientras la transcripción está en curso")
    try:
        if os.path.exists(row.file_path):
            os.remove(row.file_path)
    except OSError:
        pass
    db.delete(row)
    db.commit()


@app.post("/api/classes/{class_id}/transcription")
async def start_transcription(
    class_id: int,
    model: str = Form(default="large-v3"),
    db: Session = Depends(get_db),
):
    row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if not row:
        raise HTTPException(400, "Primero sube un archivo de audio")
    if row.tx_status in ("loading_model", "transcribing", "aligning", "saving"):
        raise HTTPException(400, "Ya hay una transcripción en curso")
    if model not in whisper_agent.AVAILABLE_MODELS:
        raise HTTPException(400, f"Modelo no válido. Opciones: {whisper_agent.AVAILABLE_MODELS}")

    row.tx_status   = "loading_model"
    row.tx_progress = 0
    row.tx_phase    = "⏳ Iniciando…"
    row.tx_error    = None
    row.tx_raw_text = None
    row.tx_segments = None
    row.whisper_model = model
    db.commit()

    _whisper_pool.submit(whisper_agent.run_transcription, class_id, row.file_path, model)

    return {"status": "started", "model": model}


# ── Spell Correction ───────────────────────────────────────────────────────────

def ser_spell(row: models.ClassSpellCorrection):
    return {
        "class_id":      row.class_id,
        "status":        row.status,
        "progress":      row.progress,
        "phase":         row.phase or "",
        "error":         row.error,
        "segments":      json.loads(row.segments_json) if row.segments_json else [],
        "raw_text":      row.raw_text,
        "updated_at":    row.updated_at.isoformat() if row.updated_at else None,
    }


@app.get("/api/classes/{class_id}/spell-correction")
def get_spell_correction(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassSpellCorrection).filter(
        models.ClassSpellCorrection.class_id == class_id
    ).first()
    if not row:
        raise HTTPException(404, "Sin corrección ortográfica")
    return ser_spell(row)


@app.get("/api/classes/{class_id}/spell-correction/status")
def get_spell_status(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassSpellCorrection).filter(
        models.ClassSpellCorrection.class_id == class_id
    ).first()
    if not row:
        return {"status": "idle"}
    return {"status": row.status, "progress": row.progress, "phase": row.phase or "", "error": row.error}


@app.post("/api/classes/{class_id}/spell-correction")
async def start_spell_correction(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    audio = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if not audio or audio.tx_status != "done" or not audio.tx_segments:
        raise HTTPException(400, "Primero completa la transcripción con Whisper")

    bloques = json.loads(audio.tx_segments)

    # Upsert spell correction row
    row = db.query(models.ClassSpellCorrection).filter(
        models.ClassSpellCorrection.class_id == class_id
    ).first()
    if row:
        row.status = "running"; row.progress = 0; row.phase = "⏳ Iniciando…"
        row.error = None; row.segments_json = None; row.raw_text = None
    else:
        row = models.ClassSpellCorrection(class_id=class_id, status="running", progress=0, phase="⏳ Iniciando…")
        db.add(row)
    db.commit()

    _whisper_pool.submit(spell_agent.run_spell_correction, class_id, cls.raw_narration or "", bloques)
    return {"status": "started"}


# ── Alignment ──────────────────────────────────────────────────────────────────

def ser_guion_base(row: models.ClassGuionBase):
    return {
        "class_id": row.class_id,
        "status":   row.status,
        "phase":    row.phase or "",
        "error":    row.error,
        "segments": json.loads(row.segments_json) if row.segments_json else [],
        "content":  row.content or "",
    }


@app.get("/api/classes/{class_id}/guion-base")
def get_guion_base(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassGuionBase).filter(models.ClassGuionBase.class_id == class_id).first()
    if not row:
        raise HTTPException(404, "Sin guion base")
    return ser_guion_base(row)


@app.post("/api/classes/{class_id}/alignment")
def run_alignment(class_id: int, db: Session = Depends(get_db)):
    spell = db.query(models.ClassSpellCorrection).filter(
        models.ClassSpellCorrection.class_id == class_id
    ).first()
    if not spell or spell.status != "done" or not spell.segments_json:
        raise HTTPException(400, "Primero completa la corrección ortográfica")

    screen_segs = (
        db.query(models.ScreenSegment)
        .filter(models.ScreenSegment.class_id == class_id)
        .order_by(models.ScreenSegment.order)
        .all()
    )
    if not screen_segs:
        raise HTTPException(400, "Primero segmenta el guion en pantallas (fase Guion)")

    bloques_corregidos = json.loads(spell.segments_json)

    try:
        result = aligner_agent.run_alignment(bloques_corregidos, screen_segs)
    except Exception as e:
        raise HTTPException(500, f"Error en alineación: {str(e)}")

    row = db.query(models.ClassGuionBase).filter(models.ClassGuionBase.class_id == class_id).first()
    if row:
        row.status = "done"; row.phase = f"✅ {len(result['segments'])} segmentos alineados"
        row.error = None; row.segments_json = json.dumps(result["segments"], ensure_ascii=False)
        row.content = result["content"]
    else:
        row = models.ClassGuionBase(
            class_id=class_id, status="done",
            phase=f"✅ {len(result['segments'])} segmentos alineados",
            segments_json=json.dumps(result["segments"], ensure_ascii=False),
            content=result["content"],
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return ser_guion_base(row)


# ── Screen Segmentation ────────────────────────────────────────────────────────

@app.get("/api/classes/{class_id}/segments")
def get_class_segments(class_id: int, db: Session = Depends(get_db)):
    segs = (
        db.query(models.ScreenSegment)
        .filter(models.ScreenSegment.class_id == class_id)
        .order_by(models.ScreenSegment.order)
        .all()
    )
    return [ser_segment(s) for s in segs]


@app.post("/api/classes/{class_id}/segment")
async def run_class_segment(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls or not cls.raw_narration:
        raise HTTPException(400, "La clase no tiene guion para segmentar")

    screen_types = (
        db.query(models.ScreenType)
        .filter(models.ScreenType.enabled == True)
        .order_by(models.ScreenType.sort_order)
        .all()
    )
    remotion_templates = (
        db.query(models.RemotionTemplate)
        .filter(models.RemotionTemplate.enabled == True)
        .order_by(models.RemotionTemplate.sort_order)
        .all()
    )

    try:
        screens = screen_agent.segment_narration(cls.raw_narration, screen_types, remotion_templates)
    except Exception as e:
        raise HTTPException(500, f"Error al segmentar: {str(e)}")

    db.query(models.ScreenSegment).filter(models.ScreenSegment.class_id == class_id).delete()

    for i, s in enumerate(screens):
        seg = models.ScreenSegment(
            class_id=class_id,
            order=i,
            screen_type=s.get("screen_type", "TEXT"),
            narration=s.get("narration", ""),
            params=s.get("params", ""),
            remotion_template=s.get("remotion_template"),
            notes=s.get("notes", ""),
        )
        db.add(seg)

    db.commit()

    segs = (
        db.query(models.ScreenSegment)
        .filter(models.ScreenSegment.class_id == class_id)
        .order_by(models.ScreenSegment.order)
        .all()
    )
    return [ser_segment(s) for s in segs]


@app.delete("/api/classes/{class_id}/segments", status_code=204)
def delete_class_segments(class_id: int, db: Session = Depends(get_db)):
    db.query(models.ScreenSegment).filter(
        models.ScreenSegment.class_id == class_id
    ).delete()
    db.commit()


@app.delete("/api/classes/{class_id}", status_code=204)
def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")
    db.delete(cls)
    db.commit()


# ── Global: Screen Types ────────────────────────────────────────────────────────────────────────────────

def ser_screen_type(st: models.ScreenType):
    return {
        "id":           st.id,
        "name":         st.name,
        "label":        st.label,
        "description":  st.description or "",
        "category":     st.category,
        "icon":         st.icon or "",
        "color":        st.color or "#666",
        "asset_prefix": st.asset_prefix or "",
        "asset_ext":    st.asset_ext or "",
        "has_params":   st.has_params,
        "params_syntax":st.params_syntax or "",
        "tag_format":    st.tag_format or "",
        "enabled":       st.enabled,
        "sort_order":    st.sort_order,
        "max_items":     st.max_items,
        "max_words":     st.max_words,
        "max_chars":     st.max_chars,
    }


@app.get("/api/screen-types")
def list_screen_types(db: Session = Depends(get_db)):
    rows = db.query(models.ScreenType).order_by(models.ScreenType.sort_order).all()
    return [ser_screen_type(r) for r in rows]


@app.post("/api/screen-types", status_code=201)
def create_screen_type(data: ScreenTypeIn, db: Session = Depends(get_db)):
    st = models.ScreenType(**data.dict())
    db.add(st)
    db.commit()
    db.refresh(st)
    return ser_screen_type(st)


@app.put("/api/screen-types/{st_id}")
def update_screen_type(st_id: int, data: ScreenTypeUpdate, db: Session = Depends(get_db)):
    st = db.query(models.ScreenType).filter(models.ScreenType.id == st_id).first()
    if not st:
        raise HTTPException(404, "Tipo no encontrado")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(st, key, value)
        
    db.commit()
    db.refresh(st)
    return ser_screen_type(st)


@app.delete("/api/screen-types/{st_id}", status_code=204)
def delete_screen_type(st_id: int, db: Session = Depends(get_db)):
    st = db.query(models.ScreenType).filter(models.ScreenType.id == st_id).first()
    if not st:
        raise HTTPException(404, "Tipo no encontrado")
    db.delete(st)
    db.commit()


# ── Global: Remotion Templates ─────────────────────────────────────────────────────────────────────

def ser_remotion_template(rt: models.RemotionTemplate):
    return {
        "id":          rt.id,
        "name":        rt.name,
        "label":       rt.label,
        "category":    rt.category or "",
        "description": rt.description or "",
        "limits":      rt.limits or "",
        "data_schema": rt.data_schema or "",
        "enabled":     rt.enabled,
        "sort_order":  rt.sort_order,
    }


@app.get("/api/remotion-templates")
def list_remotion_templates(db: Session = Depends(get_db)):
    rows = db.query(models.RemotionTemplate).order_by(models.RemotionTemplate.sort_order).all()
    return [ser_remotion_template(r) for r in rows]


@app.post("/api/remotion-templates", status_code=201)
def create_remotion_template(data: RemotionTemplateIn, db: Session = Depends(get_db)):
    rt = models.RemotionTemplate(**data.dict())
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return ser_remotion_template(rt)


@app.put("/api/remotion-templates/{rt_id}")
def update_remotion_template(rt_id: int, data: RemotionTemplateUpdate, db: Session = Depends(get_db)):
    rt = db.query(models.RemotionTemplate).filter(models.RemotionTemplate.id == rt_id).first()
    if not rt:
        raise HTTPException(404, "Template no encontrado")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rt, key, value)
        
    db.commit()
    db.refresh(rt)
    return ser_remotion_template(rt)


@app.delete("/api/remotion-templates/{rt_id}", status_code=204)
def delete_remotion_template(rt_id: int, db: Session = Depends(get_db)):
    rt = db.query(models.RemotionTemplate).filter(models.RemotionTemplate.id == rt_id).first()
    if not rt:
        raise HTTPException(404, "Template no encontrado")
    db.delete(rt)
    db.commit()
