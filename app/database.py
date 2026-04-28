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
    except Exception as e:
        print(f"⚠️ migration error: {e}")
    finally:
        conn.close()


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

REMOTION_TEMPLATES_SEED = [
    # ── Narrativos ──────────────────────────────────────────────────────────────
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
        "name": "Spotlight",
        "label": "Spotlight",
        "category": "narrativo",
        "description": "Foco de luz que ilumina puntos en la pantalla secuencialmente.",
        "limits": "min 2 puntos — max 6 puntos",
        "data_schema": '{"title": "string", "points": [{"label": "string", "description": "string"}]}',
        "sort_order": 2,
    },
    {
        "name": "Timeline",
        "label": "Línea de Tiempo",
        "category": "narrativo",
        "description": "Línea de tiempo horizontal con eventos que aparecen en secuencia.",
        "limits": "min 3 eventos — max 7 eventos",
        "data_schema": '{"title": "string", "events": [{"year": "string", "label": "string", "description": "string"}]}',
        "sort_order": 3,
    },
    # ── Flujo ───────────────────────────────────────────────────────────────────
    {
        "name": "MindMap",
        "label": "Mapa Mental",
        "category": "flujo",
        "description": "Concepto central rodeado de ramas distribuidas radialmente. Nodos y colores automáticos.",
        "limits": "min 3 nodos — max 8 nodos — recomendado 4-6",
        "data_schema": '{"center": "string", "nodes": [{"text": "string", "sub": "string (opcional)"}]}',
        "sort_order": 4,
    },
    {
        "name": "LinearSteps",
        "label": "Pasos Lineales",
        "category": "flujo",
        "description": "Tarjetas horizontales conectadas por flechas, de izquierda a derecha.",
        "limits": "min 2 pasos — max 6 — recomendado 3-4",
        "data_schema": '{"title": "string (opcional)", "steps": [{"title": "string", "description": "string"}]}',
        "sort_order": 5,
    },
    {
        "name": "CycleLoop",
        "label": "Ciclo / Loop",
        "category": "flujo",
        "description": "Pasos dispuestos en círculo que muestran un proceso cíclico.",
        "limits": "min 3 pasos — max 6 pasos",
        "data_schema": '{"title": "string (opcional)", "steps": [{"label": "string", "description": "string"}]}',
        "sort_order": 6,
    },
    {
        "name": "OrgChart",
        "label": "Árbol Jerárquico",
        "category": "flujo",
        "description": "Árbol organizacional con nodo raíz y ramas subordinadas.",
        "limits": "1 raíz — max 4 hijos directos — max 3 nietos por hijo",
        "data_schema": '{"root": "string", "children": [{"label": "string", "children": ["string"]}]}',
        "sort_order": 7,
    },
    {
        "name": "FunnelDiagram",
        "label": "Embudo de Etapas",
        "category": "flujo",
        "description": "Embudo visual donde cada etapa es más pequeña que la anterior.",
        "limits": "min 3 etapas — max 6 etapas",
        "data_schema": '{"title": "string (opcional)", "stages": [{"label": "string", "value": "string"}]}',
        "sort_order": 8,
    },
    # ── Datos ───────────────────────────────────────────────────────────────────
    {
        "name": "StatCounter",
        "label": "Contador de Estadísticas",
        "category": "datos",
        "description": "Números grandes que cuentan desde 0. Ideal para datos impactantes.",
        "limits": "min 1 stat — max 4 stats",
        "data_schema": '{"stats": [{"value": "number", "label": "string", "suffix": "string (ej: %, M, K)"}]}',
        "sort_order": 9,
    },
    {
        "name": "HorizontalBars",
        "label": "Barras Horizontales",
        "category": "datos",
        "description": "Barras comparativas horizontales con etiqueta y valor.",
        "limits": "min 2 barras — max 8 barras",
        "data_schema": '{"title": "string (opcional)", "bars": [{"label": "string", "value": "number (0-100)"}]}',
        "sort_order": 10,
    },
    {
        "name": "PieDonut",
        "label": "Gráfico Donut / Pie",
        "category": "datos",
        "description": "Gráfico circular o donut con segmentos proporcionales.",
        "limits": "min 2 segmentos — max 6 segmentos",
        "data_schema": '{"title": "string (opcional)", "segments": [{"label": "string", "value": "number"}]}',
        "sort_order": 11,
    },
    {
        "name": "RadarChart",
        "label": "Gráfico Radar / Araña",
        "category": "datos",
        "description": "Gráfico de araña para comparar múltiples dimensiones.",
        "limits": "min 3 dimensiones — max 8 dimensiones",
        "data_schema": '{"title": "string (opcional)", "axes": [{"label": "string", "value": "number (0-100)"}]}',
        "sort_order": 12,
    },
    {
        "name": "WaveTrend",
        "label": "Tendencia / Wave",
        "category": "datos",
        "description": "Línea de tendencia animada que muestra evolución de datos en el tiempo.",
        "limits": "min 4 puntos — max 12 puntos",
        "data_schema": '{"title": "string (opcional)", "points": [{"x": "string", "y": "number"}]}',
        "sort_order": 13,
    },
    # ── Clasificación / Concepto ────────────────────────────────────────────────
    {
        "name": "VennDiagram",
        "label": "Diagrama de Venn",
        "category": "clasificacion",
        "description": "Dos círculos con zona de intersección. Para mostrar relaciones y similitudes.",
        "limits": "Exactamente 2 conjuntos con 1 intersección",
        "data_schema": '{"left": {"label": "string", "items": ["string"]}, "right": {"label": "string", "items": ["string"]}, "intersection": ["string"]}',
        "sort_order": 14,
    },
    {
        "name": "TwoColumns",
        "label": "Dos Columnas (Comparación)",
        "category": "clasificacion",
        "description": "Comparación lado a lado. Columna A (✓) vs Columna B (✗).",
        "limits": "min 2 ítems por columna — max 6 ítems",
        "data_schema": '{"left": {"label": "string", "items": ["string"]}, "right": {"label": "string", "items": ["string"]}}',
        "sort_order": 15,
    },
    {
        "name": "FourBoxes",
        "label": "Cuatro Cajas",
        "category": "clasificacion",
        "description": "Cuatro tarjetas con ícono y descripción. Para categorías o pilares.",
        "limits": "Exactamente 4 cajas",
        "data_schema": '{"title": "string (opcional)", "boxes": [{"icon": "emoji", "label": "string", "description": "string"}]}',
        "sort_order": 16,
    },
    {
        "name": "MatrixGrid",
        "label": "Matriz 2x2",
        "category": "clasificacion",
        "description": "Cuadrante 2x2 tipo matriz (ej: Eisenhower, BCG). Ejes X e Y configurables.",
        "limits": "Exactamente 4 cuadrantes",
        "data_schema": '{"x_label": "string", "y_label": "string", "quadrants": [{"label": "string", "description": "string"}]}',
        "sort_order": 17,
    },
    {
        "name": "PyramidLevels",
        "label": "Pirámide de Niveles",
        "category": "clasificacion",
        "description": "Pirámide de niveles (base ancha → cima). Para jerarquías o prioridades.",
        "limits": "min 3 niveles — max 6 niveles",
        "data_schema": '{"title": "string (opcional)", "levels": [{"label": "string", "description": "string"}]}',
        "sort_order": 18,
    },
    {
        "name": "FlipCards",
        "label": "Flip Cards",
        "category": "clasificacion",
        "description": "Tarjetas que aparecen y giran para revelar título y descripción en el reverso.",
        "limits": "min 2 tarjetas — max 6 — recomendado 3-4",
        "data_schema": '{"title": "string (opcional)", "items": [{"icon": "emoji", "label": "string", "title": "string", "description": "string"}]}',
        "sort_order": 19,
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
    from models import RemotionTemplate
    db = SessionLocal()
    try:
        existing = db.query(RemotionTemplate).count()
        if existing > 0:
            return  # Already seeded
        for item in REMOTION_TEMPLATES_SEED:
            db.add(RemotionTemplate(**item))
        db.commit()
        print(f"✅ Seeded {len(REMOTION_TEMPLATES_SEED)} Remotion templates.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Remotion templates seed error: {e}")
    finally:
        db.close()
