from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
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

    # Video production config — equivalent to video_config.yaml in 0_referencia
    fps                  = Column(Integer,      default=30)
    resolution           = Column(String(20),   default="1920x1080")
    main_font            = Column(String(50),   default="Inter")
    background_color     = Column(String(20),   default="#fefefe")
    main_text_color      = Column(String(20),   default="#bd0505")
    highlight_text_color = Column(String(20),   default="#e3943b")
    cover_asset          = Column(String(255),  default="videos/portada.mp4")

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
    research_items  = relationship("ResearchItem",  back_populates="class_obj", cascade="all, delete-orphan")
    screen_segments = relationship(
        "ScreenSegment",
        back_populates="class_obj",
        cascade="all, delete-orphan",
        order_by="ScreenSegment.order",
    )
    audio               = relationship("ClassAudio",              back_populates="class_obj", uselist=False, cascade="all, delete-orphan")
    spell_correction    = relationship("ClassSpellCorrection",    back_populates="class_obj", uselist=False, cascade="all, delete-orphan")
    guion_base          = relationship("ClassGuionBase",          back_populates="class_obj", uselist=False, cascade="all, delete-orphan")
    guion_consolidado   = relationship("ClassGuionConsolidado",   back_populates="class_obj", uselist=False, cascade="all, delete-orphan")
    render              = relationship("ClassRender",             back_populates="class_obj", uselist=False, cascade="all, delete-orphan")


class ResearchItem(Base):
    __tablename__ = "research_items"
    id                  = Column(Integer, primary_key=True, index=True)
    class_id            = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    
    claim               = Column(Text, nullable=False)
    query               = Column(Text, nullable=True)
    status              = Column(String(50), default="pending") # pending, verified, disputed, not_found, error
    confidence          = Column(Integer, nullable=True) # 0-100
    source_url          = Column(String(500), nullable=True)
    source_title        = Column(String(500), nullable=True)
    source_snippet      = Column(Text, nullable=True)
    
    created_at          = Column(DateTime, default=datetime.utcnow)
    
    class_obj           = relationship("Class", back_populates="research_items")


# ── Per-class: Audio + Transcription ──────────────────────────────────────────
# One row per class. Stores audio metadata and the full transcription state
# so the frontend can poll for live progress without a separate job queue.

class ClassAudio(Base):
    __tablename__ = "class_audio"

    id         = Column(Integer, primary_key=True, index=True)
    class_id   = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Audio file metadata
    filename   = Column(String(255), nullable=False)
    file_path  = Column(String(500), nullable=False)   # relative to app/
    duration   = Column(Float,  nullable=True)          # seconds
    size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Transcription state (updated in-place by background thread)
    whisper_model = Column(String(50),  nullable=True)
    tx_status     = Column(String(30),  default="idle")  # idle | loading_model | transcribing | aligning | saving | done | error
    tx_progress   = Column(Integer,     default=0)        # 0-100
    tx_phase      = Column(String(255), default="")       # human-readable current step
    tx_error      = Column(Text,        nullable=True)    # full error/traceback
    tx_raw_text   = Column(Text,        nullable=True)    # [start.xxx - end.xxx]: text per block (spell-checker input)
    tx_srt        = Column(Text,        nullable=True)    # SRT format for video production
    tx_segments   = Column(Text,        nullable=True)    # JSON [{start, end, text}] blocks — aligner input
    tx_updated_at = Column(DateTime,    nullable=True)

    class_obj = relationship("Class", back_populates="audio")


# ── Per-class: Spell Correction ───────────────────────────────────────────────
# Stores the spell-corrected transcription blocks (FASE 2 of pipeline).
# Input:  ClassAudio.tx_segments  +  Class.raw_narration (as reference)
# Output: same [{start, end, text}] format, text corrected via GPT

class ClassSpellCorrection(Base):
    __tablename__ = "class_spell_corrections"

    id         = Column(Integer, primary_key=True, index=True)
    class_id   = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, unique=True)
    status     = Column(String(30),  default="idle")   # idle | running | done | error
    progress   = Column(Integer,     default=0)
    phase      = Column(String(255), default="")
    error      = Column(Text,        nullable=True)
    segments_json = Column(Text,     nullable=True)    # JSON [{start, end, text}] corrected
    raw_text      = Column(Text,     nullable=True)    # [start.xxx - end.xxx]: text per line
    created_at = Column(DateTime,    default=datetime.utcnow)
    updated_at = Column(DateTime,    nullable=True)

    class_obj = relationship("Class", back_populates="spell_correction")


# ── Per-class: Guion Base (aligned output) ────────────────────────────────────
# Stores the result of SegmentAligner + GuionFormatter (FASE 3a of pipeline).
# Input:  ClassSpellCorrection.segments_json  +  ScreenSegment rows (tagged script)
# Output: timed segments with tipo/params + guion_base.txt content

class ClassGuionBase(Base):
    __tablename__ = "class_guion_base"

    id         = Column(Integer, primary_key=True, index=True)
    class_id   = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, unique=True)
    status     = Column(String(30),  default="idle")
    phase      = Column(String(255), default="")
    error      = Column(Text,        nullable=True)
    segments_json = Column(Text,     nullable=True)    # JSON [{inicio,fin,duracion,texto,tipo,params}]
    content       = Column(Text,     nullable=True)    # guion_base.txt format
    created_at = Column(DateTime,    default=datetime.utcnow)

    class_obj = relationship("Class", back_populates="guion_base")


# ── Per-class: Guion Consolidado (FASE 3b output) ─────────────────────────────
# Stores VisualOrchestrator output: guion_consolidado.txt + recursos_visuales.json
# TEXT=, TEXT_STYLE=, ASSET=, ASSET_TIPO=, ASSET_DESCRIPCION= filled by AI.

class ClassGuionConsolidado(Base):
    __tablename__ = "class_guion_consolidado"

    id         = Column(Integer, primary_key=True, index=True)
    class_id   = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, unique=True)
    status     = Column(String(30),  default="idle")   # idle | running | done | error
    progress   = Column(Integer,     default=0)
    phase      = Column(String(255), default="")
    error      = Column(Text,        nullable=True)
    content    = Column(Text,        nullable=True)    # guion_consolidado.txt
    recursos_json = Column(Text,     nullable=True)    # recursos_visuales.json
    created_at = Column(DateTime,    default=datetime.utcnow)

    class_obj = relationship("Class", back_populates="guion_consolidado")


# ── Per-class: Render ──────────────────────────────────────────────────────────
# Tracks the final video render job for a class.
# Status flow: idle → building_dummies → dummies_done → rendering → done | error

class ClassRender(Base):
    __tablename__ = "class_renders"

    id          = Column(Integer, primary_key=True, index=True)
    class_id    = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, unique=True)
    status      = Column(String(30),  default="idle")   # idle | building_dummies | dummies_done | rendering | done | error
    progress    = Column(Integer,     default=0)         # 0-100
    phase       = Column(String(255), default="")        # human-readable step
    error       = Column(Text,        nullable=True)
    output_path = Column(String(500), nullable=True)     # relative to app/
    created_at  = Column(DateTime,    default=datetime.utcnow)
    updated_at  = Column(DateTime,    nullable=True)

    class_obj = relationship("Class", back_populates="render")


# ── Per-class: Screen Segments ────────────────────────────────────────────────
# Result of GPT segmentation: each row is one screen block for a class.

class ScreenSegment(Base):
    __tablename__ = "screen_segments"

    id               = Column(Integer, primary_key=True, index=True)
    class_id         = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    order            = Column(Integer, default=0)
    screen_type      = Column(String(50), nullable=False)       # matches ScreenType.name
    narration        = Column(Text, default="")                 # exact narration fragment
    params           = Column(Text, default="")                 # inline params string
    remotion_template= Column(String(100), nullable=True)       # only for REMOTION type
    notes            = Column(Text, default="")                 # AI reasoning
    created_at       = Column(DateTime, default=datetime.utcnow)

    class_obj = relationship("Class", back_populates="screen_segments")


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
