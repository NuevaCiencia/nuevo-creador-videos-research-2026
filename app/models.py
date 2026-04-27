from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Course(Base):
    __tablename__ = "courses"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow)

    sections = relationship(
        "Section",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Section.order",
    )


class Section(Base):
    __tablename__ = "sections"

    id         = Column(Integer, primary_key=True, index=True)
    course_id  = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title      = Column(String(255), nullable=False)
    order      = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    course  = relationship("Course", back_populates="sections")
    classes = relationship(
        "Class",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Class.order",
    )


class Class(Base):
    __tablename__ = "classes"

    id            = Column(Integer, primary_key=True, index=True)
    section_id    = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title         = Column(String(255), nullable=False)
    order         = Column(Integer, default=0)
    raw_narration = Column(Text, default="")
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="classes")


# ── GLOBAL: Screen Types ───────────────────────────────────────────────────────
# Global catalog — not per course. Defines all valid <!-- type:NAME --> tags
# that the pipeline understands. 3 categories: layout, dynamic, rendering.

class ScreenType(Base):
    __tablename__ = "screen_types"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(50), unique=True, nullable=False)   # "TEXT", "SPLIT_LEFT"...
    label        = Column(String(100), nullable=False)                # Display name
    description  = Column(Text, default="")
    category     = Column(String(30), nullable=False)                 # "layout" | "dynamic" | "rendering"
    icon         = Column(String(10), default="")                     # Emoji
    color        = Column(String(20), default="#666666")              # Badge color hex
    asset_prefix = Column(String(10), default="")                     # "S", "F", "V", "REM", ""
    asset_ext    = Column(String(10), default="")                     # "png", "mp4", ""
    has_params   = Column(Boolean, default=False)                     # Accepts // params?
    params_syntax= Column(String(255), default="")                    # Human-readable params format
    tag_format   = Column(String(255), default="")                    # Full tag example for reference
    enabled      = Column(Boolean, default=True)
    sort_order   = Column(Integer, default=0)
    
    # Validation limits
    max_items     = Column(Integer, nullable=True) # For LIST, CONCEPT, etc.
    max_words     = Column(Integer, nullable=True) # Max words per item or total
    max_chars     = Column(Integer, nullable=True) # Max chars per line/block


# ── GLOBAL: Remotion Templates ─────────────────────────────────────────────────
# Sub-catalog for REMOTION type. Each template maps to a Remotion component
# and has its own data schema (fields the AI must fill).

class RemotionTemplate(Base):
    __tablename__ = "remotion_templates"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)  # "TypeWriter", "MindMap"...
    label       = Column(String(100), nullable=False)
    category    = Column(String(50), default="")   # "narrativo" | "flujo" | "datos" | "clasificacion"
    description = Column(Text, default="")
    limits      = Column(String(255), default="")  # "min 3 nodos — max 8"
    data_schema = Column(Text, default="")         # JSON schema of data fields
    enabled     = Column(Boolean, default=True)
    sort_order  = Column(Integer, default=0)
