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
from ai_agents import research_agent, screen_agent, whisper_agent, spell_agent, aligner_agent, visual_agent, dummy_builder, render_agent, remotion_agent

_whisper_pool = ThreadPoolExecutor(max_workers=1)  # one transcription at a time

# ── Bootstrap ──────────────────────────────────────────────────────────────────
init_db()

app = FastAPI(title="Video Creator")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR  = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR,  exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/fonts",  StaticFiles(directory=FONTS_DIR),  name="fonts")


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


_WPM           = 130    # palabras/min — ritmo estándar de locución en español
_VIDEO_OVERHEAD = 1.15  # 15% extra para transiciones, pausas y énfasis visuales


@app.get("/api/courses/{course_id}/stats")
def get_course_stats(course_id: int, db: Session = Depends(get_db)):
    from collections import Counter, defaultdict

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Curso no encontrado")

    sections = (db.query(models.Section)
                .filter(models.Section.course_id == course_id)
                .order_by(models.Section.order).all())
    section_ids = [s.id for s in sections]

    all_classes = (db.query(models.Class)
                   .filter(models.Class.section_id.in_(section_ids)).all()
                   if section_ids else [])
    class_ids = [c.id for c in all_classes]

    def _map(rows, key):
        return {getattr(r, key): r for r in rows}

    audio_map  = _map(db.query(models.ClassAudio).filter(models.ClassAudio.class_id.in_(class_ids)).all(), "class_id") if class_ids else {}
    spell_map  = _map(db.query(models.ClassSpellCorrection).filter(models.ClassSpellCorrection.class_id.in_(class_ids)).all(), "class_id") if class_ids else {}
    guion_map  = _map(db.query(models.ClassGuionBase).filter(models.ClassGuionBase.class_id.in_(class_ids)).all(), "class_id") if class_ids else {}

    seg_rows      = db.query(models.ScreenSegment).filter(models.ScreenSegment.class_id.in_(class_ids)).all() if class_ids else []
    research_rows = db.query(models.ResearchItem).filter(models.ResearchItem.class_id.in_(class_ids)).all()   if class_ids else []

    segs_by_class   = defaultdict(int)
    for s in seg_rows: segs_by_class[s.class_id] += 1
    screen_type_cnt = Counter(s.screen_type for s in seg_rows)
    research_status = Counter(r.status for r in research_rows)

    st_rows  = db.query(models.ScreenType).filter(models.ScreenType.name.in_(list(screen_type_cnt.keys()))).all() if screen_type_cnt else []
    st_info  = {s.name: {"color": s.color, "icon": s.icon, "label": s.label} for s in st_rows}

    cls_by_section = defaultdict(list)
    for c in all_classes: cls_by_section[c.section_id].append(c)

    total_words = total_chars = 0
    p_guion = p_seg = p_audio = p_tx = p_spell = p_align = 0
    word_counts = []
    section_stats = []

    for sec in sections:
        sw = sc = 0
        cls_list = sorted(cls_by_section.get(sec.id, []), key=lambda x: x.order)
        cls_stats = []

        for cls in cls_list:
            txt   = cls.raw_narration or ""
            words = len(txt.split()) if txt.strip() else 0
            chars = len(txt)
            sw += words; sc += chars
            total_words += words; total_chars += chars
            word_counts.append(words)

            audio = audio_map.get(cls.id)
            spell = spell_map.get(cls.id)
            guion = guion_map.get(cls.id)
            hg = words > 0
            hs = segs_by_class.get(cls.id, 0) > 0
            ha = audio is not None
            ht = ha and audio.tx_status == "done"
            hsp= spell is not None and spell.status == "done"
            hal= guion is not None and guion.status == "done"

            if hg:  p_guion += 1
            if hs:  p_seg   += 1
            if ha:  p_audio += 1
            if ht:  p_tx    += 1
            if hsp: p_spell += 1
            if hal: p_align += 1

            stage = sum([hg, hs, ht, hsp, hal])  # 0-5
            cls_stats.append({
                "id": cls.id, "title": cls.title,
                "words": words, "chars": chars,
                "narration_min": round(words / _WPM, 1),
                "stage": stage,
                "flags": {"guion": hg, "segments": hs, "audio": ha,
                          "transcription": ht, "spell": hsp, "alignment": hal},
            })

        nm = sw / _WPM
        section_stats.append({
            "id": sec.id, "title": sec.title,
            "class_count": len(cls_list),
            "words": sw, "chars": sc,
            "narration_min": round(nm, 1),
            "video_min": round(nm * _VIDEO_OVERHEAD, 1),
            "classes": cls_stats,
        })

    n  = len(all_classes)
    nm = total_words / _WPM

    return {
        "course": {"id": course.id, "title": course.title},
        "overview": {
            "total_sections":         len(sections),
            "total_classes":          n,
            "avg_classes_per_section":round(n / len(sections), 1) if sections else 0,
            "total_words":            total_words,
            "total_chars":            total_chars,
            "avg_words_per_class":    round(total_words / n) if n else 0,
            "avg_words_per_section":  round(total_words / len(sections)) if sections else 0,
            "max_words_class":        max(word_counts) if word_counts else 0,
            "min_words_class":        min(w for w in word_counts if w > 0) if any(word_counts) else 0,
            "narration_min":          round(nm, 1),
            "narration_fmt":          f"{int(nm//60)}h {int(nm%60)}m" if nm >= 60 else f"{round(nm,1)}min",
            "video_min":              round(nm * _VIDEO_OVERHEAD, 1),
            "video_fmt":              f"{int(nm*_VIDEO_OVERHEAD//60)}h {int(nm*_VIDEO_OVERHEAD%60)}m" if nm*_VIDEO_OVERHEAD >= 60 else f"{round(nm*_VIDEO_OVERHEAD,1)}min",
            "total_screens":          len(seg_rows),
            "completion_pct":         round(p_align / n * 100, 1) if n else 0,
            "wpm_rate":               _WPM,
        },
        "pipeline": {
            "guion": p_guion, "segments": p_seg, "audio": p_audio,
            "transcription": p_tx, "spell": p_spell, "alignment": p_align,
            "total": n,
        },
        "research": {
            "total":     len(research_rows),
            "verified":  research_status.get("verified",  0),
            "disputed":  research_status.get("disputed",  0),
            "not_found": research_status.get("not_found", 0),
            "error":     research_status.get("error",     0),
        },
        "screen_types": sorted([
            {"name": k, "count": v,
             "color": st_info.get(k, {}).get("color", "#666"),
             "icon":  st_info.get(k, {}).get("icon",  "▪"),
             "label": st_info.get(k, {}).get("label",  k)}
            for k, v in screen_type_cnt.items()
        ], key=lambda x: -x["count"]),
        "sections": section_stats,
    }


@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ── Schemas ────────────────────────────────────────────────────────────────────

class VideoConfig(BaseModel):
    fps:                  Optional[int]   = 30
    resolution:           Optional[str]   = "1920x1080"
    main_font:            Optional[str]   = "Inter"
    background_color:     Optional[str]   = "#fefefe"
    main_text_color:      Optional[str]   = "#bd0505"
    highlight_text_color: Optional[str]   = "#e3943b"
    cover_asset:          Optional[str]   = "videos/portada.mp4"

class CourseIn(BaseModel):
    title:       str
    description: Optional[str] = ""
    fps:                  Optional[int] = 30
    resolution:           Optional[str] = "1920x1080"
    main_font:            Optional[str] = "Inter"
    background_color:     Optional[str] = "#fefefe"
    main_text_color:      Optional[str] = "#bd0505"
    highlight_text_color: Optional[str] = "#e3943b"
    cover_asset:          Optional[str] = "videos/portada.mp4"

class CourseUpdate(BaseModel):
    title:                Optional[str] = None
    description:          Optional[str] = None
    fps:                  Optional[int] = None
    resolution:           Optional[str] = None
    main_font:            Optional[str] = None
    background_color:     Optional[str] = None
    main_text_color:      Optional[str] = None
    highlight_text_color: Optional[str] = None
    cover_asset:          Optional[str] = None

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

class ImgPromptUpdate(BaseModel):
    prompt: str


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
        "id":          c.id,
        "title":       c.title,
        "description": c.description or "",
        "section_count": section_count,
        "class_count":   class_count,
        "created_at":  c.created_at.isoformat() if c.created_at else None,
        "updated_at":  c.updated_at.isoformat() if c.updated_at else None,
        # video config
        "fps":                  c.fps                  or 30,
        "resolution":           c.resolution           or "1920x1080",
        "main_font":            c.main_font            or "Inter",
        "background_color":     c.background_color     or "#fefefe",
        "main_text_color":      c.main_text_color      or "#bd0505",
        "highlight_text_color": c.highlight_text_color or "#e3943b",
        "cover_asset":          c.cover_asset          or "videos/portada.mp4",
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
    course = models.Course(
        title=data.title.strip(), description=data.description or "",
        fps=data.fps, resolution=data.resolution, main_font=data.main_font,
        background_color=data.background_color, main_text_color=data.main_text_color,
        highlight_text_color=data.highlight_text_color, cover_asset=data.cover_asset,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return ser_course(course)


@app.put("/api/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Curso no encontrado")
    # Fields that are embedded in guion_consolidado #META — require re-running visual phase
    VISUAL_FIELDS = {"main_font","background_color","main_text_color","highlight_text_color",
                     "fps","resolution","cover_asset"}

    update_data = data.dict(exclude_unset=True)
    visual_changed = any(k in VISUAL_FIELDS for k in update_data)

    for key, value in update_data.items():
        if key == "title":
            setattr(course, key, value.strip())
        else:
            setattr(course, key, value)
    course.updated_at = datetime.utcnow()

    # Cascade: visual config change invalidates guion_consolidado for all classes in this course
    if visual_changed:
        section_ids = [s.id for s in db.query(models.Section.id)
                       .filter(models.Section.course_id == course_id).all()]
        if section_ids:
            class_ids = [c.id for c in db.query(models.Class.id)
                         .filter(models.Class.section_id.in_(section_ids)).all()]
            if class_ids:
                db.query(models.ClassGuionConsolidado).filter(
                    models.ClassGuionConsolidado.class_id.in_(class_ids)
                ).update({"status": "stale"}, synchronize_session=False)

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
        narration_changed = cls.raw_narration != data.raw_narration
        cls.raw_narration = data.raw_narration
        # Cascade: narration change invalidates alignment and visual orchestration
        if narration_changed:
            for model_cls in (models.ClassGuionBase, models.ClassGuionConsolidado):
                row = db.query(model_cls).filter(model_cls.class_id == class_id).first()
                if row:
                    row.status = "stale"
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

    # Store relative path from app/ so DB is portable across machines
    app_dir       = os.path.dirname(__file__)
    file_path_rel = os.path.relpath(file_path, app_dir)

    # Upsert
    row = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if row:
        row.filename   = safe_name
        row.file_path  = file_path_rel
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
            file_path=file_path_rel,
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


# ── Visual Orchestration (FASE 3b) ────────────────────────────────────────────

def ser_visual(row: models.ClassGuionConsolidado):
    return {
        "class_id":     row.class_id,
        "status":       row.status,
        "progress":     row.progress,
        "phase":        row.phase or "",
        "error":        row.error,
        "content":      row.content,
        "recursos_json": row.recursos_json,
        "created_at":   row.created_at.isoformat() if row.created_at else None,
    }


@app.get("/api/classes/{class_id}/visual")
def get_visual(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if not row:
        raise HTTPException(404, "Sin orquestación visual")
    return ser_visual(row)


@app.get("/api/classes/{class_id}/visual/status")
def get_visual_status(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if not row:
        return {"status": "idle"}
    return {"status": row.status, "progress": row.progress, "phase": row.phase or "", "error": row.error}


@app.post("/api/classes/{class_id}/visual")
async def start_visual(class_id: int, db: Session = Depends(get_db)):
    # Verify prerequisites
    guion = db.query(models.ClassGuionBase).filter(
        models.ClassGuionBase.class_id == class_id
    ).first()
    if not guion or guion.status != "done" or not guion.content:
        raise HTTPException(400, "Primero completa la alineación (Guion Base)")

    # Get course config
    cls     = db.query(models.Class).filter(models.Class.id == class_id).first()
    section = db.query(models.Section).filter(models.Section.id == cls.section_id).first()
    course  = db.query(models.Course).filter(models.Course.id == section.course_id).first()

    audio = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    audio_filename = os.path.basename(audio.file_path) if audio else "audio.mp3"

    course_cfg = {
        "title":               course.title,
        "files_folder":        "assets",
        "fps":                 course.fps or 30,
        "resolution":          course.resolution or "1920x1080",
        "main_font":           course.main_font or "Inter",
        "background_color":    course.background_color or "#fefefe",
        "main_text_color":     course.main_text_color or "#bd0505",
        "highlight_text_color":course.highlight_text_color or "#e3943b",
        "cover_asset":         course.cover_asset or "videos/portada.mp4",
    }

    # Upsert visual row
    row = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if row:
        row.status = "running"; row.progress = 0; row.phase = "⏳ Iniciando…"
        row.error  = None; row.content = None; row.recursos_json = None
    else:
        row = models.ClassGuionConsolidado(class_id=class_id, status="running",
                                           progress=0, phase="⏳ Iniciando…")
        db.add(row)
    db.commit()

    _whisper_pool.submit(
        visual_agent.run_visual_orchestration,
        class_id, guion.content, course_cfg, audio_filename
    )
    return {"status": "started"}


# ── Visualizador de Pantallas ──────────────────────────────────────────────────

@app.get("/api/classes/{class_id}/visualizador")
def get_visualizador(class_id: int, db: Session = Depends(get_db)):
    """
    Returns merged data: ScreenSegments + parsed guion_consolidado + course config.
    Used by the Visualizador de Pantallas tab.
    """
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    section = db.query(models.Section).filter(models.Section.id == cls.section_id).first()
    course  = db.query(models.Course).filter(models.Course.id == section.course_id).first()

    # Screen segments from DB
    segs = (db.query(models.ScreenSegment)
            .filter(models.ScreenSegment.class_id == class_id)
            .order_by(models.ScreenSegment.order).all())

    # Parse guion_consolidado if available
    guion_row = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()

    guion_segments: list = []
    if guion_row and guion_row.content and guion_row.status == "done":
        import re as _re
        cur = None
        for raw in guion_row.content.splitlines():
            line = raw.strip()
            if not line:
                continue
            up = line.upper()
            if up.startswith("#SEGMENT"):
                m = _re.search(r"\[(\d+):(\d+)(?:\.(\d+))?\]", line)
                ts = ""
                if m:
                    mn, sc = int(m.group(1)), int(m.group(2))
                    dec = m.group(3)
                    sc_total = mn * 60 + sc + (float(f"0.{dec}") if dec else 0)
                    ts = f"{mn}:{sc:02d}"
                    cur = {"timestamp": ts, "time_sec": round(sc_total, 2)}
                guion_segments.append(cur or {"timestamp": "", "time_sec": 0})
                cur = guion_segments[-1]
                continue
            if cur is not None and "=" in line:
                k, v = map(str.strip, line.split("=", 1))
                cur[k.upper()] = v

    # Merge: pair each screen_segment with its guion segment by index
    result = []
    for i, seg in enumerate(segs):
        g = guion_segments[i] if i < len(guion_segments) else {}
        result.append({
            "id":          seg.id,
            "order":       seg.order,
            "screen_type": seg.screen_type,
            "params":      seg.params or "",
            "narration":   seg.narration or "",
            "notes":       seg.notes or "",
            # From guion_consolidado
            "timestamp":   g.get("timestamp", ""),
            "time_sec":    g.get("time_sec", 0),
            "duration":    g.get("TIME", "0"),
            "text_on_screen": g.get("TEXT", ""),
            "asset":       g.get("ASSET", ""),
            "asset_tipo":  g.get("ASSET_TIPO", ""),
            "asset_desc":  g.get("ASSET_DESCRIPCION", ""),
            "has_guion":   bool(g),
        })

    # Screen types catalog (global)
    st_rows = db.query(models.ScreenType).order_by(models.ScreenType.sort_order).all()

    return {
        "segments": result,
        "has_guion": bool(guion_segments),
        "course": {
            "resolution":       course.resolution or "1920x1080",
            "background_color": course.background_color or "#fefefe",
            "main_text_color":  course.main_text_color or "#bd0505",
            "main_font":        course.main_font or "Inter",
        },
        "screen_types": [ser_screen_type(st) for st in st_rows],
    }


@app.get("/api/classes/{class_id}/estructura")
def get_estructura(class_id: int, db: Session = Depends(get_db)):
    """
    Returns the narration split into paragraphs + current segment tag positions.
    Used by the Estructura editor tab.
    """
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    segs = (db.query(models.ScreenSegment)
            .filter(models.ScreenSegment.class_id == class_id)
            .order_by(models.ScreenSegment.order).all())

    st_rows = db.query(models.ScreenType).order_by(models.ScreenType.sort_order).all()

    # Split narration into non-empty paragraphs, tracking original line indices
    raw = cls.raw_narration or ""
    lines = raw.split("\n")
    paragraphs = []
    i = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break
        start = i
        chunk = []
        while i < len(lines) and lines[i].strip():
            chunk.append(lines[i])
            i += 1
        paragraphs.append({"text": "\n".join(chunk), "line_idx": start})

    # Map segment narrations to paragraph indices (best-effort prefix match)
    tags = []
    search_from = 0
    for seg in segs:
        first = (seg.narration or "").split("\n")[0].strip()[:40]
        matched = search_from
        for pi in range(search_from, len(paragraphs)):
            if first and paragraphs[pi]["text"].strip().startswith(first):
                matched = pi
                break
        tags.append({
            "para_idx":    matched,
            "screen_type": seg.screen_type,
            "params":      seg.params or "",
            "seg_id":      seg.id,
        })
        search_from = matched + 1

    return {
        "paragraphs":   paragraphs,
        "tags":         tags,
        "screen_types": [ser_screen_type(st) for st in st_rows],
        "has_segments": len(segs) > 0,
    }


@app.put("/api/classes/{class_id}/estructura")
def save_estructura(class_id: int, payload: dict, db: Session = Depends(get_db)):
    """
    Rebuild screen_segments from new tag positions.
    payload: { "tags": [{"para_idx": int, "screen_type": str, "params": str}, ...],
               "paragraphs": [{"text": str, "line_idx": int}, ...] }
    """
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    tags       = sorted(payload.get("tags", []),       key=lambda t: t["para_idx"])
    paragraphs = payload.get("paragraphs", [])

    if not tags:
        raise HTTPException(400, "Se necesita al menos un tag")

    # Delete existing segments
    db.query(models.ScreenSegment).filter(
        models.ScreenSegment.class_id == class_id
    ).delete()

    # Create new segments — each segment gets paragraphs from its para_idx to next tag
    for order, tag in enumerate(tags):
        start = tag["para_idx"]
        end   = tags[order + 1]["para_idx"] if order + 1 < len(tags) else len(paragraphs)
        narration = "\n\n".join(
            p["text"] for p in paragraphs[start:end] if p["text"].strip()
        )
        db.add(models.ScreenSegment(
            class_id    = class_id,
            order       = order,
            screen_type = tag["screen_type"],
            params      = tag.get("params", ""),
            narration   = narration,
            notes       = "",
        ))

    # Cascade invalidation
    for model_cls in (models.ClassGuionBase, models.ClassGuionConsolidado):
        row = db.query(model_cls).filter(model_cls.class_id == class_id).first()
        if row:
            row.status = "stale"

    db.commit()
    return {"saved": len(tags)}


@app.put("/api/segments/{segment_id}/type")
def update_segment_type(segment_id: int, payload: dict, db: Session = Depends(get_db)):
    """Update screen_type and params of a segment. Marks guion_base stale."""
    seg = db.query(models.ScreenSegment).filter(models.ScreenSegment.id == segment_id).first()
    if not seg:
        raise HTTPException(404, "Segmento no encontrado")

    if "screen_type" in payload:
        seg.screen_type = payload["screen_type"]
    if "params" in payload:
        seg.params = payload["params"]

    # Cascade invalidation
    class_id = seg.class_id
    for model_cls in (models.ClassGuionBase, models.ClassGuionConsolidado):
        row = db.query(model_cls).filter(model_cls.class_id == class_id).first()
        if row:
            row.status = "stale"
            row.phase  = "⚠️ Tipo de pantalla editado — re-ejecuta Alineación"
    db.commit()
    return {"id": seg.id, "screen_type": seg.screen_type, "params": seg.params}


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

    # Invalidar guion_base y guion_consolidado — los screen_segments cambiaron,
    # hay que realinear antes de poder volver a generar visuales.
    guion_base = db.query(models.ClassGuionBase).filter(
        models.ClassGuionBase.class_id == class_id
    ).first()
    if guion_base:
        guion_base.status = "stale"
        guion_base.phase  = "⚠️ Pantallas regeneradas — re-ejecuta la Alineación"

    guion_consolidado = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if guion_consolidado:
        guion_consolidado.status = "stale"
        guion_consolidado.phase  = "⚠️ Pantallas regeneradas — re-ejecuta Alineación y luego Visuales"

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


# ── Image Prompts ──────────────────────────────────────────────────────────────

_IMAGE_TYPES = {"SPLIT_LEFT", "SPLIT_RIGHT", "FULL_IMAGE"}

def ser_img_prompt(row: models.ClassImgPrompt):
    return {
        "class_id":   row.class_id,
        "asset_name": row.asset_name,
        "prompt":     row.prompt,
        "fixed_by":   row.fixed_by,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@app.get("/api/classes/{class_id}/img-prompts")
def get_img_prompts(class_id: int, db: Session = Depends(get_db)):
    """Image-bearing segments with original prompts (from recursos_json) + custom edits."""
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    segs = (db.query(models.ScreenSegment)
            .filter(models.ScreenSegment.class_id == class_id)
            .order_by(models.ScreenSegment.order).all())
    img_segs = [s for s in segs if s.screen_type in _IMAGE_TYPES]

    if not img_segs:
        return {"items": [], "has_guion": False}

    guion_row = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    has_guion = guion_row is not None and guion_row.status == "done"

    # Build prompt map from recursos_json: {asset_name → descripcion}
    prompt_map: dict = {}  # "S001.png" → "A premium educational..."
    asset_name_map: dict = {}  # segment_order → asset_name (from guion content)
    if has_guion and guion_row.recursos_json:
        try:
            recursos = json.loads(guion_row.recursos_json).get("recursos", [])
            for r in recursos:
                nombre = r.get("nombre", "")
                desc   = r.get("descripcion", "")
                if nombre and desc:
                    prompt_map[nombre] = desc
        except Exception:
            pass

    # Also parse guion content to get ASSET per segment order
    if has_guion and guion_row.content:
        cur_idx = -1
        cur: dict = {}
        for raw in guion_row.content.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.upper().startswith("#SEGMENT"):
                if cur_idx >= 0 and cur:
                    asset_name_map[cur_idx] = cur.get("ASSET", "").split("/")[-1]
                cur_idx += 1
                cur = {}
            elif "=" in line and cur_idx >= 0:
                k, v = map(str.strip, line.split("=", 1))
                cur[k.upper()] = v
        if cur_idx >= 0:
            asset_name_map[cur_idx] = cur.get("ASSET", "").split("/")[-1]

    # Custom prompts saved by user/AI
    custom_prompts = {
        r.asset_name: r
        for r in db.query(models.ClassImgPrompt).filter(
            models.ClassImgPrompt.class_id == class_id
        ).all()
    }

    items = []
    for seg in img_segs:
        asset_name      = asset_name_map.get(seg.order, "")
        original_prompt = prompt_map.get(asset_name, "")
        custom          = custom_prompts.get(asset_name)
        items.append({
            "segment_id":      seg.id,
            "order":           seg.order,
            "screen_type":     seg.screen_type,
            "asset_name":      asset_name,
            "narration":       seg.narration or "",
            "original_prompt": original_prompt,
            "custom_prompt":   custom.prompt if custom else None,
            "fixed_by":        custom.fixed_by if custom else None,
            "updated_at":      custom.updated_at.isoformat() if custom and custom.updated_at else None,
        })

    return {"items": items, "has_guion": has_guion}


@app.put("/api/classes/{class_id}/img-prompts/{asset_name}")
def save_img_prompt(class_id: int, asset_name: str, data: ImgPromptUpdate,
                    db: Session = Depends(get_db)):
    row = db.query(models.ClassImgPrompt).filter(
        models.ClassImgPrompt.class_id == class_id,
        models.ClassImgPrompt.asset_name == asset_name,
    ).first()
    if row:
        row.prompt    = data.prompt
        row.fixed_by  = "user"
        row.updated_at = datetime.utcnow()
    else:
        row = models.ClassImgPrompt(
            class_id=class_id, asset_name=asset_name,
            prompt=data.prompt, fixed_by="user",
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return ser_img_prompt(row)


@app.delete("/api/classes/{class_id}/img-prompts/{asset_name}", status_code=204)
def delete_img_prompt(class_id: int, asset_name: str, db: Session = Depends(get_db)):
    row = db.query(models.ClassImgPrompt).filter(
        models.ClassImgPrompt.class_id == class_id,
        models.ClassImgPrompt.asset_name == asset_name,
    ).first()
    if row:
        db.delete(row)
        db.commit()


_META_PROMPT_PATH        = os.path.join(os.path.dirname(__file__), "..", "0_referencia", "META_PROMPT_ARREGLA_IMAGENES.txt")
_CUSTOM_META_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "custom_meta_prompt.txt")

def _load_meta_prompt(override: str = None) -> str:
    """Return override if given, else custom file, else 0_referencia default."""
    if override:
        return override.strip()
    try:
        with open(_CUSTOM_META_PROMPT_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        pass
    try:
        with open(_META_PROMPT_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


_META_PROMPT_HISTORY_DIR = os.path.join(os.path.dirname(__file__), "meta_prompt_history")


def _get_active_text() -> str:
    """Returns the currently active prompt text (custom or original)."""
    if os.path.exists(_CUSTOM_META_PROMPT_PATH):
        with open(_CUSTOM_META_PROMPT_PATH, encoding="utf-8") as f:
            t = f.read().strip()
        if t:
            return t
    try:
        with open(_META_PROMPT_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def _list_meta_prompt_versions() -> list:
    """All saved custom versions, each annotated with active:bool."""
    active_text = _get_active_text() or ""
    entries = []
    if os.path.exists(_META_PROMPT_HISTORY_DIR):
        for fname in sorted(os.listdir(_META_PROMPT_HISTORY_DIR), reverse=True):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(_META_PROMPT_HISTORY_DIR, fname), encoding="utf-8") as fh:
                    e = json.load(fh)
                e["filename"] = fname
                e["active"]   = (e.get("text", "").strip() == active_text) and bool(active_text)
                entries.append(e)
            except Exception:
                pass
    return entries


def _full_versions_response():
    active_text  = _get_active_text()
    original_txt = None
    try:
        with open(_META_PROMPT_PATH, encoding="utf-8") as f:
            original_txt = f.read().strip()
    except FileNotFoundError:
        pass
    custom_active = os.path.exists(_CUSTOM_META_PROMPT_PATH)
    original_active = not custom_active
    return {
        "active_text":     active_text,
        "original_active": original_active,
        "versions":        _list_meta_prompt_versions(),
        "original_text":   original_txt,
    }


@app.get("/api/img-prompts/meta-prompt")
def get_meta_prompt():
    r = _full_versions_response()
    if not r["active_text"]:
        raise HTTPException(500, "META_PROMPT_ARREGLA_IMAGENES.txt no encontrado")
    return r


@app.post("/api/img-prompts/meta-prompt/version")
async def add_meta_prompt_version(payload: dict):
    """Add a new version to the list (inactive by default)."""
    text = payload.get("text", "").strip()
    note = payload.get("note", "").strip()
    if not text:
        raise HTTPException(400, "text requerido")
    os.makedirs(_META_PROMPT_HISTORY_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    entry = {"timestamp": datetime.utcnow().isoformat(), "note": note, "text": text}
    with open(os.path.join(_META_PROMPT_HISTORY_DIR, f"{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    return _full_versions_response()


@app.post("/api/img-prompts/meta-prompt/activate")
async def activate_meta_prompt_version(payload: dict):
    """Activate a saved version or the original."""
    filename = payload.get("filename")  # None or "original" = activate original
    if not filename or filename == "original":
        if os.path.exists(_CUSTOM_META_PROMPT_PATH):
            os.remove(_CUSTOM_META_PROMPT_PATH)
    else:
        path = os.path.join(_META_PROMPT_HISTORY_DIR, filename)
        if not os.path.exists(path):
            raise HTTPException(404, "Versión no encontrada")
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)
        text = entry.get("text", "").strip()
        if not text:
            raise HTTPException(400, "La versión no tiene texto")
        with open(_CUSTOM_META_PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(text)
    return _full_versions_response()


@app.delete("/api/img-prompts/meta-prompt/version/{filename}", status_code=204)
def delete_meta_prompt_version(filename: str):
    path = os.path.join(_META_PROMPT_HISTORY_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


@app.post("/api/classes/{class_id}/img-prompts/{asset_name}/fix")
async def fix_img_prompt(class_id: int, asset_name: str, payload: dict,
                          db: Session = Depends(get_db)):
    """Refine an image prompt using META_PROMPT_ARREGLA_IMAGENES + narration."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "OPENAI_API_KEY no configurada")

    original_prompt   = payload.get("original_prompt", "")
    narration         = payload.get("narration", "")
    meta_prompt_override = payload.get("meta_prompt", None)
    if not original_prompt and not narration:
        raise HTTPException(400, "Se necesita original_prompt o narration")

    meta_prompt = _load_meta_prompt(override=meta_prompt_override)
    if not meta_prompt:
        raise HTTPException(500, "META_PROMPT_ARREGLA_IMAGENES.txt no encontrado en 0_referencia/")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # If no original prompt, generate a raw one first from narration alone
    raw_prompt = original_prompt
    if not raw_prompt and narration:
        try:
            seed_resp = client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[
                    {"role": "system", "content": (
                        "You are an educational image prompt generator. "
                        "Given a narration fragment from a video course, write a short English image description "
                        "that captures the core concept visually. 2-3 sentences, descriptive and concrete. "
                        "No labels, no preamble, just the description."
                    )},
                    {"role": "user", "content": f"NARRACIÓN: {narration}"},
                ],
                temperature=0.3,
            )
            raw_prompt = seed_resp.choices[0].message.content.strip()
        except Exception as e:
            raise HTTPException(500, f"Error generando prompt base: {str(e)}")

    # Format matches META_PROMPT_ARREGLA_IMAGENES.txt input format
    user_msg = f"PROMPT: {raw_prompt}\nLOCUCIÓN: {narration}"

    try:
        resp = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": meta_prompt},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.3,
        )
        improved = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(500, f"Error OpenAI: {str(e)}")

    # Upsert
    row = db.query(models.ClassImgPrompt).filter(
        models.ClassImgPrompt.class_id == class_id,
        models.ClassImgPrompt.asset_name == asset_name,
    ).first()
    if row:
        row.prompt    = improved
        row.fixed_by  = "ai"
        row.updated_at = datetime.utcnow()
    else:
        row = models.ClassImgPrompt(
            class_id=class_id, asset_name=asset_name,
            prompt=improved, fixed_by="ai",
        )
        db.add(row)
    db.commit()
    return {"asset_name": asset_name, "prompt": improved, "fixed_by": "ai"}


# ── VIDEO: Assets status + Dummy builder + Final Render ───────────────────────

@app.get("/api/classes/{class_id}/render/assets-status")
def get_assets_status(class_id: int, db: Session = Depends(get_db)):
    """Returns exists/missing status for every asset in the guion consolidado."""
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    guion = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if not guion or not guion.recursos_json:
        raise HTTPException(400, "No hay guion visual — ejecuta la fase Visual primero")

    section = db.query(models.Section).filter(models.Section.id == cls.section_id).first()
    course  = db.query(models.Course).filter(models.Course.id == section.course_id).first()
    assets_base = os.path.join(ASSETS_DIR, str(class_id))

    result = dummy_builder.check_assets_status(
        guion.recursos_json, assets_base, course.cover_asset or "videos/portada.mp4"
    )
    return result


_CANVAS_SPLIT = (960, 1080)
_CANVAS_FULL  = (1920, 1080)
_WHITE_THRESH = 235
_BORDER_SAMPLE = 20

def _tiene_borde_blanco(img):
    import numpy as np
    arr = np.array(img.convert("RGB"))
    h, w = arr.shape[:2]
    top    = arr[:_BORDER_SAMPLE, :, :]
    bottom = arr[max(0, h - _BORDER_SAMPLE):, :, :]
    left   = arr[:, :_BORDER_SAMPLE, :]
    right  = arr[:, max(0, w - _BORDER_SAMPLE):, :]
    border = np.concatenate([top.reshape(-1,3), bottom.reshape(-1,3),
                             left.reshape(-1,3), right.reshape(-1,3)], axis=0)
    return np.all(border > _WHITE_THRESH, axis=1).mean() > 0.90

def _centrar_imagen(img, canvas_size):
    from PIL import Image as PILImage
    cw, ch = canvas_size
    iw, ih = img.size
    scale = min(cw / iw, ch / ih)
    img = img.resize((int(iw * scale), int(ih * scale)), PILImage.LANCZOS)
    canvas = PILImage.new("RGB", canvas_size, (255, 255, 255))
    iw, ih = img.size
    mask = img.split()[-1] if img.mode in ("RGBA", "LA") else None
    canvas.paste(img, ((cw - iw) // 2, (ch - ih) // 2), mask=mask)
    return canvas

def _rellenar_imagen(img, canvas_size):
    from PIL import Image as PILImage
    cw, ch = canvas_size
    iw, ih = img.size
    scale = max(cw / iw, ch / ih)
    img = img.resize((int(iw * scale), int(ih * scale)), PILImage.LANCZOS)
    ox = (img.width  - cw) // 2
    oy = (img.height - ch) // 2
    return img.crop((ox, oy, ox + cw, oy + ch)).convert("RGB")

def _procesar_imagen_asset(content: bytes, ubicacion: str) -> tuple[bytes, str]:
    """Resize/fit image to the correct canvas based on asset name. Returns (png_bytes, mode)."""
    from PIL import Image as PILImage
    import io
    stem = os.path.splitext(os.path.basename(ubicacion))[0].upper()
    if stem.startswith("S"):
        canvas = _CANVAS_SPLIT
    elif stem.startswith("F"):
        canvas = _CANVAS_FULL
    else:
        return content, "raw"

    img = PILImage.open(io.BytesIO(content))
    if _tiene_borde_blanco(img):
        result, mode = _centrar_imagen(img, canvas), "fit"
    else:
        result, mode = _rellenar_imagen(img, canvas), "fill"

    buf = io.BytesIO()
    result.save(buf, "PNG", optimize=True)
    return buf.getvalue(), mode


@app.post("/api/classes/{class_id}/assets/upload")
async def upload_asset(
    class_id: int,
    ubicacion: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an asset file. Images (S*/F*) are auto-resized to the correct canvas."""
    if not db.query(models.Class).filter(models.Class.id == class_id).first():
        raise HTTPException(404, "Clase no encontrada")

    content = await file.read()
    mode    = "raw"

    ext = os.path.splitext(ubicacion)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
        content, mode = _procesar_imagen_asset(content, ubicacion)
        dest_path = os.path.splitext(os.path.join(ASSETS_DIR, str(class_id), ubicacion))[0] + ".png"
        ubicacion = os.path.splitext(ubicacion)[0] + ".png"
    else:
        dest_path = os.path.join(ASSETS_DIR, str(class_id), ubicacion)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(content)
    return {"ok": True, "path": ubicacion, "size": len(content), "mode": mode}


@app.post("/api/classes/{class_id}/render/build-dummies")
def build_dummies(class_id: int, db: Session = Depends(get_db)):
    """Launches background task to build placeholder files for missing assets."""
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    guion = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if not guion or not guion.recursos_json:
        raise HTTPException(400, "No hay guion visual — ejecuta la fase Visual primero")

    section = db.query(models.Section).filter(models.Section.id == cls.section_id).first()
    course  = db.query(models.Course).filter(models.Course.id == section.course_id).first()
    assets_base = os.path.join(ASSETS_DIR, str(class_id))

    # Upsert render row
    row = db.query(models.ClassRender).filter(models.ClassRender.class_id == class_id).first()
    if row:
        row.status = "building_dummies"; row.progress = 0; row.phase = "⏳ Iniciando dummies…"; row.error = None
    else:
        row = models.ClassRender(class_id=class_id, status="building_dummies",
                                 progress=0, phase="⏳ Iniciando dummies…")
        db.add(row)
    db.commit()

    _whisper_pool.submit(
        dummy_builder.build_missing_dummies,
        class_id, guion.recursos_json, assets_base,
        course.cover_asset or "videos/portada.mp4"
    )
    return {"status": "started"}


@app.get("/api/classes/{class_id}/render/status")
def get_render_status(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassRender).filter(models.ClassRender.class_id == class_id).first()
    if not row:
        return {"status": "idle", "progress": 0, "phase": "", "error": None, "output_path": None}
    return {
        "status":      row.status,
        "progress":    row.progress,
        "phase":       row.phase or "",
        "error":       row.error,
        "output_path": row.output_path,
    }


@app.post("/api/classes/{class_id}/render")
def start_render(class_id: int, db: Session = Depends(get_db)):
    """Launches the final video render in background."""
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    # Prerequisites
    audio = db.query(models.ClassAudio).filter(models.ClassAudio.class_id == class_id).first()
    if not audio or not audio.file_path:
        raise HTTPException(400, "No hay audio — sube el audio primero")

    guion = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if not guion or guion.status not in ("done",) or not guion.content:
        raise HTTPException(400, "El guion visual no está listo — ejecuta la fase Visual primero")

    # Upsert render row
    row = db.query(models.ClassRender).filter(models.ClassRender.class_id == class_id).first()
    if row:
        row.status = "rendering"; row.progress = 0; row.phase = "⏳ Iniciando render…"
        row.error  = None; row.output_path = None
    else:
        row = models.ClassRender(class_id=class_id, status="rendering",
                                 progress=0, phase="⏳ Iniciando render…")
        db.add(row)
    db.commit()

    _whisper_pool.submit(render_agent.run_render, class_id)
    return {"status": "started"}


@app.post("/api/classes/{class_id}/render/remotion")
def start_remotion_render(class_id: int, db: Session = Depends(get_db)):
    """Launch background Remotion render for all REM assets of this class."""
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")

    guion = db.query(models.ClassGuionConsolidado).filter(
        models.ClassGuionConsolidado.class_id == class_id
    ).first()
    if not guion or not guion.recursos_json:
        raise HTTPException(400, "Sin recursos_json — ejecuta la fase Visual primero")

    row = db.query(models.ClassRemotionRender).filter(
        models.ClassRemotionRender.class_id == class_id
    ).first()
    if row:
        row.status = "rendering"; row.progress = 0; row.phase = "⏳ Iniciando…"; row.error = None
    else:
        row = models.ClassRemotionRender(class_id=class_id, status="rendering", progress=0, phase="⏳ Iniciando…")
        db.add(row)
    db.commit()

    _whisper_pool.submit(remotion_agent.run_remotion, class_id)
    return {"status": "started"}


@app.get("/api/classes/{class_id}/render/remotion/status")
def get_remotion_status(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassRemotionRender).filter(
        models.ClassRemotionRender.class_id == class_id
    ).first()
    if not row:
        return {"status": "idle", "progress": 0, "phase": "", "error": None}
    return {"status": row.status, "progress": row.progress, "phase": row.phase, "error": row.error}


@app.get("/api/classes/{class_id}/render/download")
def download_render(class_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ClassRender).filter(models.ClassRender.class_id == class_id).first()
    if not row or not row.output_path:
        raise HTTPException(404, "No hay video renderizado")

    abs_path = os.path.join(os.path.dirname(__file__), row.output_path)
    if not os.path.exists(abs_path):
        raise HTTPException(404, "Archivo no encontrado en disco")

    return FileResponse(
        abs_path,
        media_type="video/mp4",
        filename=os.path.basename(abs_path),
    )


# ── FONTS ──────────────────────────────────────────────────────────────────────

FONT_EXTS = {".ttf", ".otf"}
# Known family → display name + weights mapping (for bundled fonts)
_FAMILY_MAP = {
    "inter":        {"family": "Inter",         "weights": ["Regular", "Bold", "Italic"]},
    "montserrat":   {"family": "Montserrat",     "weights": ["Regular", "Bold", "Italic"]},
    "jetbrainsmono":{"family": "JetBrains Mono", "weights": ["Regular"]},
}


def _parse_font_file(filename: str) -> dict:
    """Extract family name and weight from a font filename."""
    stem = os.path.splitext(filename)[0]   # e.g. "Inter-Bold"
    ext  = os.path.splitext(filename)[1].lower()
    parts = stem.split("-", 1)
    family = parts[0]
    weight = parts[1] if len(parts) > 1 else "Regular"
    return {
        "filename": filename,
        "family":   family,
        "weight":   weight,
        "ext":      ext,
        "url":      f"/fonts/{filename}",
    }


@app.get("/api/fonts")
def list_fonts():
    """List all installed font files from app/fonts/."""
    files = []
    for fname in sorted(os.listdir(FONTS_DIR)):
        if os.path.splitext(fname)[1].lower() in FONT_EXTS:
            files.append(_parse_font_file(fname))

    # Group by family
    families: dict = {}
    for f in files:
        fam = f["family"]
        if fam not in families:
            families[fam] = {"family": fam, "weights": []}
        families[fam]["weights"].append({"weight": f["weight"], "filename": f["filename"], "url": f["url"]})

    return {"fonts": files, "families": list(families.values())}


@app.post("/api/fonts", status_code=201)
async def upload_font(file: UploadFile = File(...)):
    """Upload a TTF or OTF font file to app/fonts/."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in FONT_EXTS:
        raise HTTPException(400, f"Solo se aceptan archivos TTF u OTF. Recibido: {ext or 'sin extensión'}")

    # Sanitize filename
    safe_name = "".join(c for c in (file.filename or "font.ttf")
                        if c.isalnum() or c in "-_.")
    dest = os.path.join(FONTS_DIR, safe_name)
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    return _parse_font_file(safe_name)


@app.delete("/api/fonts/{filename}", status_code=204)
def delete_font(filename: str):
    """Delete a font file. Bundled fonts can also be deleted (user's choice)."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Nombre de archivo inválido")
    dest = os.path.join(FONTS_DIR, filename)
    if not os.path.exists(dest):
        raise HTTPException(404, "Fuente no encontrada")
    os.remove(dest)
