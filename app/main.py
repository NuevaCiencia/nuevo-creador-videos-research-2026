import os
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, get_db, init_db
import models

# ── Bootstrap ──────────────────────────────────────────────────────────────────
init_db()

app = FastAPI(title="Video Creator")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
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


@app.delete("/api/classes/{class_id}", status_code=204)
def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "Clase no encontrada")
    db.delete(cls)
    db.commit()
