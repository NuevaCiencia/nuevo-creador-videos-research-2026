import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "books.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row) -> dict:
    return dict(row) if row else None


def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


# ─── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                core_idea       TEXT NOT NULL,
                target_reader   TEXT DEFAULT '',
                key_problem     TEXT DEFAULT '',
                current_phase   INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS title_options (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id     INTEGER NOT NULL,
                titulo      TEXT NOT NULL,
                subtitulo   TEXT DEFAULT '',
                razon       TEXT DEFAULT '',
                selected    INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS structure_options (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id                 INTEGER NOT NULL,
                nombre                  TEXT NOT NULL,
                tipo_arco               TEXT DEFAULT '',
                descripcion             TEXT DEFAULT '',
                progresion_emocional    TEXT DEFAULT '',
                capitulos_estimados     INTEGER DEFAULT 10,
                fases                   TEXT DEFAULT '[]',
                selected                INTEGER DEFAULT 0,
                created_at              TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS chapters (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id                 INTEGER NOT NULL,
                num                     INTEGER NOT NULL,
                titulo                  TEXT NOT NULL,
                tesis                   TEXT DEFAULT '',
                territorio_exclusivo    TEXT DEFAULT '',
                posicion_arco           TEXT DEFAULT 'ciencia',
                proposito               TEXT DEFAULT '',
                promesa_al_lector       TEXT DEFAULT '',
                created_at              TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS chapter_parts (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id          INTEGER NOT NULL,
                num                 INTEGER NOT NULL,
                titulo              TEXT NOT NULL,
                tipo                TEXT DEFAULT 'teoria',
                puntos_clave        TEXT DEFAULT '[]',
                proposito           TEXT DEFAULT '',
                palabras_estimadas  INTEGER DEFAULT 500,
                created_at          TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            );

            CREATE TABLE IF NOT EXISTS overlap_analyses (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id             INTEGER NOT NULL,
                score_coherencia    INTEGER DEFAULT 0,
                evaluacion_general  TEXT DEFAULT '',
                created_at          TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS overlap_flags (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id         INTEGER NOT NULL,
                book_id             INTEGER NOT NULL,
                capitulo_a          INTEGER NOT NULL,
                capitulo_b          INTEGER NOT NULL,
                descripcion         TEXT DEFAULT '',
                severidad           TEXT DEFAULT 'bajo',
                resolucion_sugerida TEXT DEFAULT '',
                resuelto            INTEGER DEFAULT 0,
                created_at          TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (analysis_id) REFERENCES overlap_analyses(id),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS research_items (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id          INTEGER NOT NULL,
                tipo                TEXT NOT NULL,
                titulo              TEXT DEFAULT '',
                autor               TEXT DEFAULT '',
                año                 TEXT DEFAULT '',
                campo               TEXT DEFAULT '',
                hallazgo_clave      TEXT DEFAULT '',
                protagonista        TEXT DEFAULT '',
                que_paso            TEXT DEFAULT '',
                que_ilustra         TEXT DEFAULT '',
                placement           TEXT DEFAULT '',
                parte_sugerida      INTEGER DEFAULT 0,
                busqueda_sugerida   TEXT DEFAULT '',
                fuente_url          TEXT DEFAULT '',
                fuente_titulo       TEXT DEFAULT '',
                fuente_snippet      TEXT DEFAULT '',
                verificado          INTEGER DEFAULT 0,
                activo              INTEGER DEFAULT 1,
                notas               TEXT DEFAULT '',
                created_at          TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            );

            CREATE TABLE IF NOT EXISTS placement_maps (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id      INTEGER NOT NULL,
                parte_num       INTEGER NOT NULL,
                necesita_historia INTEGER DEFAULT 0,
                razon           TEXT DEFAULT '',
                research_item_id INTEGER,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            );

            CREATE TABLE IF NOT EXISTS chapter_notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id  INTEGER NOT NULL UNIQUE,
                nota_investigador TEXT DEFAULT '',
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            );

            CREATE TABLE IF NOT EXISTS word_bans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id     INTEGER,
                word        TEXT NOT NULL,
                reason      TEXT DEFAULT '',
                categoria   TEXT DEFAULT 'cliche_ia',
                activa      INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tone_patterns (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id                     INTEGER NOT NULL UNIQUE,
                voz                         TEXT DEFAULT 'segunda',
                registro                    TEXT DEFAULT 'conversacional',
                longitud_frase              TEXT DEFAULT 'mixta',
                uso_metaforas               TEXT DEFAULT 'moderado',
                tratamiento_ciencia         TEXT DEFAULT 'analogias',
                temperatura_emocional       TEXT DEFAULT 'equilibrada',
                instrucciones_adicionales   TEXT DEFAULT '',
                parrafo_ancla               TEXT DEFAULT '',
                parrafo_ancla_aprobado      INTEGER DEFAULT 0,
                created_at                  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS style_references (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                label       TEXT NOT NULL,
                category    TEXT NOT NULL,
                text        TEXT NOT NULL,
                embedding   TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS style_reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id     INTEGER NOT NULL,
                chapter_id  INTEGER NOT NULL,
                results     TEXT NOT NULL DEFAULT '{}',
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (book_id) REFERENCES books(id),
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            );

            CREATE TABLE IF NOT EXISTS written_parts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id     INTEGER NOT NULL,
                version     INTEGER NOT NULL DEFAULT 1,
                content     TEXT NOT NULL DEFAULT '',
                instructions TEXT DEFAULT '',
                approved    INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (part_id) REFERENCES chapter_parts(id)
            );
        """)
        
        try:
            conn.execute("ALTER TABLE tone_patterns ADD COLUMN prompt_rector TEXT DEFAULT ''")
            conn.execute("ALTER TABLE tone_patterns ADD COLUMN texto_campeon TEXT DEFAULT ''")
            conn.execute("ALTER TABLE tone_patterns ADD COLUMN score_similitud REAL DEFAULT 0.0")
            conn.execute("ALTER TABLE tone_patterns ADD COLUMN is_auto_generated INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE chapters ADD COLUMN final_content TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE chapters ADD COLUMN cohesion_evaluation TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
            
        conn.commit()
        _seed_global_word_bans()


# ─── Books ─────────────────────────────────────────────────────────────────────

def create_book(core_idea: str, target_reader: str = '', key_problem: str = '') -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO books (core_idea, target_reader, key_problem) VALUES (?, ?, ?)",
            (core_idea, target_reader, key_problem)
        )
        conn.commit()
        return cur.lastrowid


def get_book(book_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return row_to_dict(row)


def get_all_books() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM books ORDER BY created_at DESC").fetchall()
        return rows_to_list(rows)


def update_book_phase(book_id: int, phase: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE books SET current_phase = MAX(current_phase, ?) WHERE id = ?",
            (phase, book_id),
        )
        conn.commit()


# ─── Titles ────────────────────────────────────────────────────────────────────

def save_title_options(book_id: int, options: list, replace: bool = True) -> list:
    with get_conn() as conn:
        if replace:
            conn.execute("DELETE FROM title_options WHERE book_id = ?", (book_id,))
        ids = []
        for opt in options:
            cur = conn.execute(
                "INSERT INTO title_options (book_id, titulo, subtitulo, razon) VALUES (?, ?, ?, ?)",
                (book_id, opt.get('titulo', ''), opt.get('subtitulo', ''), opt.get('razon', ''))
            )
            ids.append(cur.lastrowid)
        conn.commit()
        return ids


def get_title_options(book_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM title_options WHERE book_id = ? ORDER BY id",
            (book_id,)
        ).fetchall()
        return rows_to_list(rows)


def select_title(book_id: int, title_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE title_options SET selected = 0 WHERE book_id = ?", (book_id,))
        conn.execute("UPDATE title_options SET selected = 1 WHERE id = ?", (title_id,))
        conn.commit()


def get_selected_title(book_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM title_options WHERE book_id = ? AND selected = 1",
            (book_id,)
        ).fetchone()
        return row_to_dict(row)


# ─── Structures ────────────────────────────────────────────────────────────────

def save_structure_options(book_id: int, options: list, replace: bool = True) -> list:
    with get_conn() as conn:
        if replace:
            conn.execute("DELETE FROM structure_options WHERE book_id = ?", (book_id,))
        ids = []
        for opt in options:
            fases_json = json.dumps(opt.get('fases', []), ensure_ascii=False)
            cur = conn.execute(
                """INSERT INTO structure_options
                   (book_id, nombre, tipo_arco, descripcion, progresion_emocional, capitulos_estimados, fases)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    book_id,
                    opt.get('nombre', ''),
                    opt.get('tipo_arco', ''),
                    opt.get('descripcion', ''),
                    opt.get('progresion_emocional', ''),
                    opt.get('capitulos_estimados', 10),
                    fases_json,
                )
            )
            ids.append(cur.lastrowid)
        conn.commit()
        return ids


def get_structure_options(book_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM structure_options WHERE book_id = ? ORDER BY id",
            (book_id,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d['fases'] = json.loads(d['fases']) if d['fases'] else []
            result.append(d)
        return result


def select_structure(book_id: int, structure_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE structure_options SET selected = 0 WHERE book_id = ?", (book_id,))
        conn.execute("UPDATE structure_options SET selected = 1 WHERE id = ?", (structure_id,))
        conn.commit()


def get_selected_structure(book_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM structure_options WHERE book_id = ? AND selected = 1",
            (book_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d['fases'] = json.loads(d['fases']) if d['fases'] else []
        return d


# ─── Chapters ──────────────────────────────────────────────────────────────────

def _delete_chapters(conn, book_id: int):
    chapter_ids = [
        r[0] for r in conn.execute(
            "SELECT id FROM chapters WHERE book_id = ?", (book_id,)
        ).fetchall()
    ]
    for cid in chapter_ids:
        conn.execute("DELETE FROM chapter_parts WHERE chapter_id = ?", (cid,))
    conn.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))


def save_chapters(book_id: int, chapters: list, replace: bool = True):
    with get_conn() as conn:
        if replace:
            _delete_chapters(conn, book_id)
        for ch in chapters:
            conn.execute(
                """INSERT INTO chapters
                   (book_id, num, titulo, tesis, territorio_exclusivo, posicion_arco, proposito, promesa_al_lector)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    book_id,
                    ch.get('numero', ch.get('num', 0)),
                    ch.get('titulo', ''),
                    ch.get('tesis', ''),
                    ch.get('territorio_exclusivo', ''),
                    ch.get('posicion_arco', 'ciencia'),
                    ch.get('proposito', ''),
                    ch.get('promesa_al_lector', ''),
                )
            )
        conn.commit()


def get_chapters(book_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chapters WHERE book_id = ? ORDER BY num",
            (book_id,)
        ).fetchall()
        return rows_to_list(rows)


def update_chapter(chapter_id: int, data: dict):
    fields = ['titulo', 'tesis', 'territorio_exclusivo', 'posicion_arco', 'proposito', 'promesa_al_lector', 'final_content', 'cohesion_evaluation']
    updates = {k: v for k, v in data.items() if k in fields}
    if not updates:
        return
    set_clause = ', '.join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [chapter_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE chapters SET {set_clause} WHERE id = ?", values)
        conn.commit()


def delete_chapter(chapter_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM chapter_parts WHERE chapter_id = ?", (chapter_id,))
        conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
        conn.commit()


# ─── Parts ─────────────────────────────────────────────────────────────────────

def save_parts(chapter_id: int, parts: list):
    with get_conn() as conn:
        conn.execute("DELETE FROM chapter_parts WHERE chapter_id = ?", (chapter_id,))
        for part in parts:
            puntos_json = json.dumps(part.get('puntos_clave', []), ensure_ascii=False)
            conn.execute(
                """INSERT INTO chapter_parts
                   (chapter_id, num, titulo, tipo, puntos_clave, proposito, palabras_estimadas)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    chapter_id,
                    part.get('numero', part.get('num', 0)),
                    part.get('titulo', ''),
                    part.get('tipo', 'teoria'),
                    puntos_json,
                    part.get('proposito', ''),
                    part.get('palabras_estimadas', 500),
                )
            )
        conn.commit()


def get_parts(chapter_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chapter_parts WHERE chapter_id = ? ORDER BY num",
            (chapter_id,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d['puntos_clave'] = json.loads(d['puntos_clave']) if d['puntos_clave'] else []
            result.append(d)
        return result


# ─── Overlap ───────────────────────────────────────────────────────────────────

def save_overlap_flags(book_id: int, analysis_data: dict, replace: bool = True):
    with get_conn() as conn:
        if replace:
            old_analyses = conn.execute(
                "SELECT id FROM overlap_analyses WHERE book_id = ?", (book_id,)
            ).fetchall()
            for a in old_analyses:
                conn.execute("DELETE FROM overlap_flags WHERE analysis_id = ?", (a[0],))
            conn.execute("DELETE FROM overlap_analyses WHERE book_id = ?", (book_id,))

        cur = conn.execute(
            "INSERT INTO overlap_analyses (book_id, score_coherencia, evaluacion_general) VALUES (?, ?, ?)",
            (
                book_id,
                analysis_data.get('score_coherencia', 0),
                analysis_data.get('evaluacion_general', ''),
            )
        )
        analysis_id = cur.lastrowid

        for flag in analysis_data.get('solapamientos', []):
            conn.execute(
                """INSERT INTO overlap_flags
                   (analysis_id, book_id, capitulo_a, capitulo_b, descripcion, severidad, resolucion_sugerida)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    analysis_id,
                    book_id,
                    flag.get('capitulo_a', 0),
                    flag.get('capitulo_b', 0),
                    flag.get('descripcion', ''),
                    flag.get('severidad', 'bajo'),
                    flag.get('resolucion_sugerida', ''),
                )
            )
        conn.commit()


def get_coherence_summary(book_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM overlap_analyses WHERE book_id = ? ORDER BY created_at DESC LIMIT 1",
            (book_id,)
        ).fetchone()
        return row_to_dict(row)


def get_overlap_flags(book_id: int) -> list:
    with get_conn() as conn:
        analysis = conn.execute(
            "SELECT id FROM overlap_analyses WHERE book_id = ? ORDER BY created_at DESC LIMIT 1",
            (book_id,)
        ).fetchone()
        if not analysis:
            return []
        rows = conn.execute(
            "SELECT * FROM overlap_flags WHERE analysis_id = ? ORDER BY severidad DESC, id",
            (analysis[0],)
        ).fetchall()
        return rows_to_list(rows)


def resolve_overlap(flag_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE overlap_flags SET resuelto = 1 WHERE id = ?", (flag_id,))
        conn.commit()


# ─── Word Bans ─────────────────────────────────────────────────────────────────

GLOBAL_WORD_BANS = [
    # Clichés de IA
    ("sin lugar a dudas",           "cliche_ia",    "Expresión vacía"),
    ("es importante destacar",      "cliche_ia",    "Relleno típico de IA"),
    ("cabe mencionar",              "cliche_ia",    "Relleno típico de IA"),
    ("vale la pena destacar",       "cliche_ia",    "Relleno"),
    ("como mencionamos anteriormente", "cliche_ia", "Relleno retrospectivo"),
    ("tal como hemos visto",        "cliche_ia",    "Relleno retrospectivo"),
    ("debemos tener en cuenta",     "cliche_ia",    "Relleno"),
    ("a continuación",              "cliche_ia",    "Transición mecánica"),
    ("no cabe duda",                "cliche_ia",    "Expresión vacía"),
    ("es necesario",                "cliche_ia",    "Énfasis vacío"),
    # Cierres mecánicos
    ("en conclusión",               "cierre_mecanico", "Cierre de ensayo escolar"),
    ("en resumen",                  "cierre_mecanico", "Cierre mecánico"),
    ("en definitiva",               "cierre_mecanico", "Cierre mecánico"),
    ("en última instancia",         "cierre_mecanico", "Cierre mecánico"),
    ("para concluir",               "cierre_mecanico", "Cierre mecánico"),
    # Adjetivos sobreusados
    ("fascinante",                  "adjetivo_vacio", "Adjetivo genérico de IA"),
    ("transformador",               "adjetivo_vacio", "Adjetivo genérico de IA"),
    ("revolucionario",              "adjetivo_vacio", "Hipérbole vacía"),
    ("pionero",                     "adjetivo_vacio", "Hipérbole vacía"),
    ("robusto",                     "adjetivo_vacio", "Adjetivo sobreusado"),
    ("disruptivo",                  "adjetivo_vacio", "Jerga corporativa"),
    ("innovador",                   "adjetivo_vacio", "Hipérbole vacía"),
    # Intensificadores vacíos
    ("innegablemente",              "intensificador", "Intensificador vacío"),
    ("indudablemente",              "intensificador", "Intensificador vacío"),
    ("profundamente",               "intensificador", "Adverbio genérico"),
    ("significativamente",          "intensificador", "Adverbio vago"),
    ("verdaderamente",              "intensificador", "Intensificador vacío"),
    # Jerga corporativa/autoayuda
    ("paradigma",                   "jerga",          "Jerga corporativa sobreusada"),
    ("holístico",                   "jerga",          "Palabra comodín"),
    ("sinérgico",                   "jerga",          "Jerga corporativa"),
    ("potenciar",                   "jerga",          "Verbo corporativo"),
    ("empoderar",                   "jerga",          "Verbo sobreusado"),
    ("apalancar",                   "jerga",          "Jerga corporativa"),
    ("optimizar",                   "jerga",          "Verbo genérico"),
    ("resiliencia",                 "jerga",          "Sobreusado en autoayuda"),
    ("mindset",                     "jerga",          "Anglicismo sobreusado"),
    ("crucial",                     "enfasis_vacio",  "Énfasis vacío"),
    ("fundamental",                 "enfasis_vacio",  "Énfasis vacío"),
    ("primordial",                  "enfasis_vacio",  "Énfasis vacío"),
    # Aperturas cliché
    ("en el mundo actual",          "apertura_cliche", "Apertura genérica"),
    ("en la sociedad moderna",      "apertura_cliche", "Apertura genérica"),
    ("a lo largo de la historia",   "apertura_cliche", "Apertura genérica"),
    ("hoy en día",                  "apertura_cliche", "Apertura genérica"),
    ("en los tiempos que corren",   "apertura_cliche", "Apertura genérica"),
]


def _seed_global_word_bans():
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM word_bans WHERE book_id IS NULL").fetchone()[0]
        if count == 0:
            for word, categoria, reason in GLOBAL_WORD_BANS:
                conn.execute(
                    "INSERT INTO word_bans (book_id, word, reason, categoria) VALUES (NULL, ?, ?, ?)",
                    (word, reason, categoria)
                )
            conn.commit()


def get_global_word_bans() -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM word_bans WHERE book_id IS NULL ORDER BY categoria, word"
        ).fetchall()
        return rows_to_list(rows)


def get_project_word_bans(book_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM word_bans WHERE book_id = ? ORDER BY categoria, word",
            (book_id,)
        ).fetchall()
        return rows_to_list(rows)


def add_word_ban(book_id: int, word: str, reason: str = '', categoria: str = 'especifico_tema'):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO word_bans (book_id, word, reason, categoria) VALUES (?, ?, ?, ?)",
            (book_id, word.strip().lower(), reason, categoria)
        )
        conn.commit()


def toggle_word_ban(ban_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE word_bans SET activa = 1 - activa WHERE id = ?", (ban_id,))
        conn.commit()


def delete_word_ban(ban_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM word_bans WHERE id = ?", (ban_id,))
        conn.commit()


def get_active_word_bans(book_id: int) -> list:
    """Returns all active bans (global + project) for injection into prompts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT word FROM word_bans WHERE activa = 1 AND (book_id IS NULL OR book_id = ?) ORDER BY word",
            (book_id,)
        ).fetchall()
        return [r[0] for r in rows]


# ─── Tone Pattern ──────────────────────────────────────────────────────────────

def save_tone_pattern(book_id: int, data: dict):
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM tone_patterns WHERE book_id = ?", (book_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE tone_patterns SET
                   voz=?, registro=?, longitud_frase=?, uso_metaforas=?,
                   tratamiento_ciencia=?, temperatura_emocional=?,
                   instrucciones_adicionales=?
                   WHERE book_id=?""",
                (
                    data.get('voz', 'segunda'),
                    data.get('registro', 'conversacional'),
                    data.get('longitud_frase', 'mixta'),
                    data.get('uso_metaforas', 'moderado'),
                    data.get('tratamiento_ciencia', 'analogias'),
                    data.get('temperatura_emocional', 'equilibrada'),
                    data.get('instrucciones_adicionales', ''),
                    book_id,
                )
            )
        else:
            conn.execute(
                """INSERT INTO tone_patterns
                   (book_id, voz, registro, longitud_frase, uso_metaforas,
                    tratamiento_ciencia, temperatura_emocional, instrucciones_adicionales)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    book_id,
                    data.get('voz', 'segunda'),
                    data.get('registro', 'conversacional'),
                    data.get('longitud_frase', 'mixta'),
                    data.get('uso_metaforas', 'moderado'),
                    data.get('tratamiento_ciencia', 'analogias'),
                    data.get('temperatura_emocional', 'equilibrada'),
                    data.get('instrucciones_adicionales', ''),
                )
            )
        conn.commit()


def get_tone_pattern(book_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM tone_patterns WHERE book_id = ?", (book_id,)
        ).fetchone()
        return row_to_dict(row)


def approve_parrafo_ancla(book_id: int, parrafo: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE tone_patterns SET parrafo_ancla=?, parrafo_ancla_aprobado=1 WHERE book_id=?",
            (parrafo, book_id)
        )
        conn.commit()


def save_auto_tone_pattern(book_id: int, prompt_rector: str, texto_campeon: str, score_similitud: float):
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM tone_patterns WHERE book_id = ?", (book_id,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE tone_patterns SET
                   prompt_rector=?, texto_campeon=?, score_similitud=?, is_auto_generated=1,
                   parrafo_ancla=?, parrafo_ancla_aprobado=1
                   WHERE book_id=?""",
                (prompt_rector, texto_campeon, score_similitud, texto_campeon, book_id)
            )
        else:
            conn.execute(
                """INSERT INTO tone_patterns
                   (book_id, prompt_rector, texto_campeon, score_similitud, is_auto_generated, parrafo_ancla, parrafo_ancla_aprobado)
                   VALUES (?, ?, ?, ?, 1, ?, 1)""",
                (book_id, prompt_rector, texto_campeon, score_similitud, texto_campeon)
            )
        conn.commit()



# ─── Research ──────────────────────────────────────────────────────────────────

def save_research_dossier(chapter_id: int, dossier: dict):
    """Replace all research items for a chapter and save the placement map."""
    with get_conn() as conn:
        conn.execute("DELETE FROM research_items WHERE chapter_id = ?", (chapter_id,))
        conn.execute("DELETE FROM placement_maps WHERE chapter_id = ?", (chapter_id,))
        conn.execute("DELETE FROM chapter_notes WHERE chapter_id = ?", (chapter_id,))

        for item in dossier.get('ciencia', []):
            conn.execute(
                """INSERT INTO research_items
                   (chapter_id, tipo, titulo, autor, año, campo, hallazgo_clave, busqueda_sugerida)
                   VALUES (?, 'ciencia', ?, ?, ?, ?, ?, ?)""",
                (
                    chapter_id,
                    item.get('titulo', ''),
                    item.get('autor', ''),
                    item.get('año', ''),
                    item.get('campo', ''),
                    item.get('hallazgo_clave', ''),
                    item.get('busqueda_sugerida', ''),
                )
            )

        for item in dossier.get('historias', []):
            conn.execute(
                """INSERT INTO research_items
                   (chapter_id, tipo, protagonista, que_paso, que_ilustra,
                    placement, parte_sugerida, busqueda_sugerida)
                   VALUES (?, 'historia', ?, ?, ?, ?, ?, ?)""",
                (
                    chapter_id,
                    item.get('protagonista', ''),
                    item.get('que_paso', ''),
                    item.get('que_ilustra', ''),
                    item.get('placement', ''),
                    item.get('parte_sugerida', 0),
                    item.get('busqueda_sugerida', ''),
                )
            )

        for entry in dossier.get('mapa_colocacion', []):
            conn.execute(
                """INSERT INTO placement_maps (chapter_id, parte_num, necesita_historia, razon)
                   VALUES (?, ?, ?, ?)""",
                (
                    chapter_id,
                    entry.get('parte_num', 0),
                    1 if entry.get('necesita_historia') else 0,
                    entry.get('razon', ''),
                )
            )

        if dossier.get('nota_investigador'):
            conn.execute(
                "INSERT INTO chapter_notes (chapter_id, nota_investigador) VALUES (?, ?)",
                (chapter_id, dossier['nota_investigador'])
            )

        conn.commit()


def get_research_items(chapter_id: int, tipo: str = None) -> list:
    with get_conn() as conn:
        if tipo:
            rows = conn.execute(
                "SELECT * FROM research_items WHERE chapter_id = ? AND tipo = ? AND activo = 1 ORDER BY id",
                (chapter_id, tipo)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM research_items WHERE chapter_id = ? AND activo = 1 ORDER BY tipo, id",
                (chapter_id,)
            ).fetchall()
        return rows_to_list(rows)


def get_placement_map(chapter_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM placement_maps WHERE chapter_id = ? ORDER BY parte_num",
            (chapter_id,)
        ).fetchall()
        return rows_to_list(rows)


def get_chapter_note(chapter_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT nota_investigador FROM chapter_notes WHERE chapter_id = ?",
            (chapter_id,)
        ).fetchone()
        return row[0] if row else ''


def verify_research_item(item_id: int, url: str, title: str, snippet: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE research_items SET verificado=1, fuente_url=?, fuente_titulo=?, fuente_snippet=? WHERE id=?",
            (url, title, snippet, item_id)
        )
        conn.commit()


def toggle_research_item(item_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE research_items SET activo = 1 - activo WHERE id = ?", (item_id,))
        conn.commit()


def delete_research_item(item_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM research_items WHERE id = ?", (item_id,))
        conn.commit()


def update_research_item_notes(item_id: int, notas: str):
    with get_conn() as conn:
        conn.execute("UPDATE research_items SET notas = ? WHERE id = ?", (notas, item_id))
        conn.commit()


def has_research(chapter_id: int) -> bool:
    with get_conn() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM research_items WHERE chapter_id = ? AND activo = 1",
            (chapter_id,)
        ).fetchone()[0]
        return count > 0


# ─── Written Parts ─────────────────────────────────────────────────────────────

def save_written_part(part_id: int, content: str, instructions: str = '') -> int:
    with get_conn() as conn:
        next_version = conn.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM written_parts WHERE part_id = ?",
            (part_id,)
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO written_parts (part_id, version, content, instructions) VALUES (?, ?, ?, ?)",
            (part_id, next_version, content, instructions)
        )
        conn.commit()
        return cur.lastrowid


def get_written_versions(part_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM written_parts WHERE part_id = ? ORDER BY version DESC",
            (part_id,)
        ).fetchall()
        return rows_to_list(rows)


def get_latest_written_part(part_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM written_parts WHERE part_id = ? ORDER BY version DESC LIMIT 1",
            (part_id,)
        ).fetchone()
        return row_to_dict(row)


def approve_written_part(written_part_id: int):
    with get_conn() as conn:
        part_id = conn.execute(
            "SELECT part_id FROM written_parts WHERE id = ?", (written_part_id,)
        ).fetchone()[0]
        conn.execute("UPDATE written_parts SET approved = 0 WHERE part_id = ?", (part_id,))
        conn.execute("UPDATE written_parts SET approved = 1 WHERE id = ?", (written_part_id,))
        conn.commit()


def get_approved_written_part(part_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM written_parts WHERE part_id = ? AND approved = 1 LIMIT 1",
            (part_id,)
        ).fetchone()
        return row_to_dict(row)


def get_chapter_written_context(chapter_id: int, up_to_part_num: int = 0) -> str:
    """Returns written content of previous parts to avoid repetition."""
    parts = get_parts(chapter_id)
    context_parts = []
    for part in parts:
        if part['num'] >= up_to_part_num:
            break
        approved = get_approved_written_part(part['id'])
        entry = approved or get_latest_written_part(part['id'])
        if entry:
            preview = entry['content'][:600] + "…" if len(entry['content']) > 600 else entry['content']
            context_parts.append(
                f"[Parte {part['num']} · {part['tipo'].upper()} · '{part['titulo']}']\n{preview}"
            )
    return "\n\n".join(context_parts)


# ─── Style References ──────────────────────────────────────────────────────────

def seed_style_references(corpus: list):
    """Seed style reference corpus if empty. corpus items: {label, category, text, embedding}"""
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM style_references").fetchone()[0]
        if count > 0:
            return
        for item in corpus:
            conn.execute(
                "INSERT INTO style_references (label, category, text, embedding) VALUES (?, ?, ?, ?)",
                (
                    item['label'],
                    item['category'],
                    item['text'],
                    json.dumps(item.get('embedding', [])),
                )
            )
        conn.commit()


def update_style_reference_embedding(ref_id: int, embedding: list):
    with get_conn() as conn:
        conn.execute(
            "UPDATE style_references SET embedding = ? WHERE id = ?",
            (json.dumps(embedding), ref_id)
        )
        conn.commit()


def get_style_references() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM style_references ORDER BY category, id").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d['embedding'] = json.loads(d['embedding']) if d['embedding'] else []
            result.append(d)
        return result


def save_style_review(book_id: int, chapter_id: int, results: dict):
    with get_conn() as conn:
        conn.execute("DELETE FROM style_reviews WHERE chapter_id = ?", (chapter_id,))
        conn.execute(
            "INSERT INTO style_reviews (book_id, chapter_id, results) VALUES (?, ?, ?)",
            (book_id, chapter_id, json.dumps(results, ensure_ascii=False))
        )
        conn.commit()


def get_style_review(chapter_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM style_reviews WHERE chapter_id = ? ORDER BY created_at DESC LIMIT 1",
            (chapter_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d['results'] = json.loads(d['results'])
        return d


# ─── Book progress ─────────────────────────────────────────────────────────────

def get_book_writing_progress(book_id: int) -> dict:
    chapters = get_chapters(book_id)
    total = written = approved = 0
    for ch in chapters:
        parts = get_parts(ch['id'])
        total += len(parts)
        for part in parts:
            if get_latest_written_part(part['id']):
                written += 1
            if get_approved_written_part(part['id']):
                approved += 1
    return {'total': total, 'written': written, 'approved': approved}
