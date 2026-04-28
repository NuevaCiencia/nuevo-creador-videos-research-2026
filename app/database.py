import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'video_creator.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate()
    _seed_screen_types()
    _seed_remotion_templates()


def _migrate():
    """Non-destructive ALTER TABLE migrations for existing tables."""
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    try:
        existing = {r[1] for r in conn.execute("PRAGMA table_info(courses)")}
        new_cols = [
            ("fps",                  "INTEGER DEFAULT 30"),
            ("resolution",           "VARCHAR(20) DEFAULT '1920x1080'"),
            ("main_font",            "VARCHAR(50) DEFAULT 'Inter'"),
            ("background_color",     "VARCHAR(20) DEFAULT '#fefefe'"),
            ("main_text_color",      "VARCHAR(20) DEFAULT '#bd0505'"),
            ("highlight_text_color", "VARCHAR(20) DEFAULT '#e3943b'"),
            ("cover_asset",          "VARCHAR(255) DEFAULT 'videos/portada.mp4'"),
        ]
        for col, defn in new_cols:
            if col not in existing:
                conn.execute(f"ALTER TABLE courses ADD COLUMN {col} {defn}")
                print(f"  migration: courses.{col} added")
        conn.commit()

        # Sanitize absolute audio paths stored from a different machine
        _migrate_audio_paths(conn)

    except Exception as e:
        print(f"⚠️ migration error: {e}")
    finally:
        conn.close()


def _migrate_audio_paths(conn):
    """Convert stale absolute file_path values in class_audio to relative (assets/...)."""
    import os
    app_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        rows = conn.execute("SELECT id, file_path FROM class_audio").fetchall()
        for row_id, fp in rows:
            if not fp or not os.path.isabs(fp):
                continue  # already relative or empty
            if os.path.exists(fp):
                # Absolute but valid on this machine — make relative
                rel = os.path.relpath(fp, app_dir)
                conn.execute("UPDATE class_audio SET file_path=? WHERE id=?", (rel, row_id))
                print(f"  migration: class_audio.{row_id} path made relative")
            else:
                # Absolute from another machine — try to find assets/ segment
                from pathlib import Path
                parts = Path(fp).parts
                for marker in ("assets",):
                    try:
                        idx = parts.index(marker)
                        rel = str(Path(*parts[idx:]))
                        candidate = os.path.join(app_dir, rel)
                        if os.path.exists(candidate):
                            conn.execute("UPDATE class_audio SET file_path=? WHERE id=?", (rel, row_id))
                            print(f"  migration: class_audio.{row_id} path resolved from {fp} → {rel}")
                            break
                    except ValueError:
                        continue
        conn.commit()
    except Exception as e:
        print(f"⚠️ audio path migration error: {e}")


# ── SEED DATA ─────────────────────────────────────────────────────────────────

SCREEN_TYPES_SEED = [
    {
        "name": "TEXT",
        "label": "Texto en Pantalla",
        "description": "Solo texto visible en pantalla. Ideal para títulos de sección, conceptos clave o transiciones.",
        "category": "layout",
        "icon": "📝",
        "color": "#6366f1",
        "asset_prefix": "",
        "asset_ext": "",
        "has_params": False,
        "params_syntax": "",
        "tag_format": "<!-- type:TEXT -->",
        "sort_order": 1,
    },
    {
        "name": "SPLIT_LEFT",
        "label": "Split — Imagen Izquierda",
        "description": "Imagen en la mitad izquierda, texto/narración en la derecha. Asset tipo S###.png.",
        "category": "layout",
        "icon": "◧",
        "color": "#8b5cf6",
        "asset_prefix": "S",
        "asset_ext": "png",
        "has_params": False,
        "params_syntax": "",
        "tag_format": "<!-- type:SPLIT_LEFT -->",
        "sort_order": 2,
    },
    {
        "name": "SPLIT_RIGHT",
        "label": "Split — Imagen Derecha",
        "description": "Texto/narración en la izquierda, imagen en la derecha. Asset tipo S###.png.",
        "category": "layout",
        "icon": "◨",
        "color": "#a78bfa",
        "asset_prefix": "S",
        "asset_ext": "png",
        "has_params": False,
        "params_syntax": "",
        "tag_format": "<!-- type:SPLIT_RIGHT -->",
        "sort_order": 3,
    },
    {
        "name": "FULL_IMAGE",
        "label": "Imagen Completa",
        "description": "Imagen ocupa toda la pantalla. Ideal para ilustraciones de impacto o síntesis visual.",
        "category": "layout",
        "icon": "🖼",
        "color": "#06b6d4",
        "asset_prefix": "F",
        "asset_ext": "png",
        "has_params": False,
        "params_syntax": "",
        "tag_format": "<!-- type:FULL_IMAGE -->",
        "sort_order": 4,
    },
    {
        "name": "VIDEO",
        "label": "Video de Fondo",
        "description": "Video de stock o generado como fondo, con el audio de locución encima.",
        "category": "layout",
        "icon": "▶",
        "color": "#0ea5e9",
        "asset_prefix": "V",
        "asset_ext": "mp4",
        "has_params": False,
        "params_syntax": "",
        "tag_format": "<!-- type:VIDEO -->",
        "sort_order": 5,
    },
    {
        "name": "LIST",
        "label": "Lista Animada",
        "description": "Lista de ítems que aparecen animados. Generado dinámicamente, sin asset externo.",
        "category": "dynamic",
        "icon": "📋",
        "color": "#10b981",
        "asset_prefix": "",
        "asset_ext": "",
        "has_params": True,
        "params_syntax": "// @ Título // Ítem 1 // Ítem 2 // ...",
        "tag_format": "<!-- type:LIST // @ Título // Ítem 1 // Ítem 2 -->",
        "sort_order": 6,
    },
    {
        "name": "CONCEPT",
        "label": "Caja de Concepto",
        "description": "Caja destacada con el nombre del concepto y su descripción. Generado dinámicamente.",
        "category": "dynamic",
        "icon": "💡",
        "color": "#f59e0b",
        "asset_prefix": "",
        "asset_ext": "",
        "has_params": True,
        "params_syntax": "// NombreConcepto // Descripción corta",
        "tag_format": "<!-- type:CONCEPT // Nombre // Descripción -->",
        "sort_order": 7,
    },
    {
        "name": "REMOTION",
        "label": "Animación Remotion",
        "description": "Animación generada con Remotion (React). Selecciona un template y la IA llena los datos.",
        "category": "rendering",
        "icon": "🎬",
        "color": "#f43f5e",
        "asset_prefix": "REM",
        "asset_ext": "mp4",
        "has_params": True,
        "params_syntax": "// $NombreTemplate",
        "tag_format": "<!-- type:REMOTION // $TypeWriter -->",
        "sort_order": 8,
    },
]

# Only the 4 templates that have real implementations in 0_referencia/ai_remotion_templates.yaml
REMOTION_TEMPLATES_SEED = [
    {
        "name": "TypeWriter",
        "label": "Terminal / TypeWriter",
        "category": "narrativo",
        "description": "Pantalla negra estilo terminal. Las líneas aparecen escritas letra a letra. Ideal para conceptos técnicos o apertura con impacto.",
        "limits": "min 1 línea — max 6 recomendado (hasta 10 técnico)",
        "data_schema": '{"accent": "hex", "lines": [{"prefix": "$ | → | > | ✓ | ! | //", "text": "string", "delay": "frames"}]}',
        "sort_order": 1,
    },
    {
        "name": "MindMap",
        "label": "Mapa Mental",
        "category": "flujo",
        "description": "Concepto central rodeado de ramas distribuidas radialmente. Nodos y colores automáticos.",
        "limits": "min 3 nodos — max 8 nodos — recomendado 4-6",
        "data_schema": '{"center": "string", "nodes": [{"text": "string", "sub": "string (opcional)"}]}',
        "sort_order": 2,
    },
    {
        "name": "LinearSteps",
        "label": "Pasos Lineales",
        "category": "flujo",
        "description": "Tarjetas horizontales conectadas por flechas, de izquierda a derecha.",
        "limits": "min 2 pasos — max 6 — recomendado 3-4",
        "data_schema": '{"title": "string (opcional)", "steps": [{"title": "string", "description": "string"}]}',
        "sort_order": 3,
    },
    {
        "name": "FlipCards",
        "label": "Flip Cards",
        "category": "clasificacion",
        "description": "Tarjetas que aparecen y giran para revelar título y descripción en el reverso.",
        "limits": "min 2 tarjetas — max 6 — recomendado 3-4",
        "data_schema": '{"title": "string (opcional)", "items": [{"icon": "emoji", "label": "string", "title": "string", "description": "string"}]}',
        "sort_order": 4,
    },
]


def _seed_screen_types():
    from models import ScreenType
    db = SessionLocal()
    try:
        existing = db.query(ScreenType).count()
        if existing > 0:
            return  # Already seeded
        for item in SCREEN_TYPES_SEED:
            db.add(ScreenType(**item))
        db.commit()
        print(f"✅ Seeded {len(SCREEN_TYPES_SEED)} screen types.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Screen types seed error: {e}")
    finally:
        db.close()


def _seed_remotion_templates():
    """Sync remotion_templates table with REMOTION_TEMPLATES_SEED.
    Removes templates not in the seed list and adds missing ones."""
    from models import RemotionTemplate
    db = SessionLocal()
    try:
        valid_names = {item["name"] for item in REMOTION_TEMPLATES_SEED}
        # Remove any template not in the current seed list
        db.query(RemotionTemplate).filter(
            RemotionTemplate.name.notin_(list(valid_names))
        ).delete(synchronize_session=False)
        # Add missing templates
        existing_names = {r.name for r in db.query(RemotionTemplate.name).all()}
        added = 0
        for item in REMOTION_TEMPLATES_SEED:
            if item["name"] not in existing_names:
                db.add(RemotionTemplate(**item))
                added += 1
        db.commit()
        if added:
            print(f"✅ Seeded {added} Remotion template(s).")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Remotion templates seed error: {e}")
    finally:
        db.close()
