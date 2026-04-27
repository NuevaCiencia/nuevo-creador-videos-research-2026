import json
import os
import utils.keys  # carga OPENAI_API_KEY y TAVILY_API_KEY desde el registro de Windows
import streamlit as st

from database.db import (
    init_db, create_book, get_book, get_all_books, update_book_phase,
    save_title_options, get_title_options, select_title, get_selected_title,
    save_structure_options, get_structure_options, select_structure, get_selected_structure,
    save_chapters, get_chapters, update_chapter, delete_chapter,
    save_parts, get_parts,
    save_overlap_flags, get_overlap_flags, get_coherence_summary, resolve_overlap,
    get_global_word_bans, get_project_word_bans, add_word_ban, toggle_word_ban,
    delete_word_ban, get_active_word_bans,
    save_tone_pattern, get_tone_pattern, approve_parrafo_ancla,
    save_research_dossier, get_research_items, get_placement_map, get_chapter_note,
    verify_research_item, toggle_research_item, delete_research_item,
    update_research_item_notes, has_research,
    save_written_part, get_written_versions, get_latest_written_part,
    approve_written_part, get_approved_written_part,
    get_chapter_written_context, get_book_writing_progress,
    seed_style_references, get_style_references,
    update_style_reference_embedding, save_style_review, get_style_review,
)
from agents.title_agent import generate_titles
from agents.structure_agent import generate_structures
from agents.chapter_agent import generate_chapters
from agents.parts_agent import generate_parts
from agents.overlap_agent import check_overlaps, fix_overlap
from agents.tone_agent import generate_tone_examples
from agents.research_agent import research_chapter, verify_item
from agents.writing_agent import write_part, rewrite_part
from agents.style_agent import review_chapter, STYLE_CORPUS
from agents.cohesion_agent import polish_full_chapter, regenerate_consolidated_chapter

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Creador de Libros",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

PHASES = [
    ("💡", "Idea"),
    ("📝", "Títulos"),
    ("🏗️", "Estructura"),
    ("📚", "Capítulos"),
    ("📋", "Partes"),
    ("🔍", "Coherencia"),
    ("✅", "Esqueleto Final"),
    ("🚫", "Bolsa de Palabras"),
    ("🔬", "Investigación"),
    ("🎨", "Tono Patrón"),
    ("✍️", "Escritura"),
    ("🔗", "Cohesión"),
    ("🔎", "Revisión de Estilo"),
]

ARC_OPTIONS = ['apertura', 'problema', 'ciencia', 'framework', 'aplicacion', 'transformacion', 'cierre']

# ─── Session state ────────────────────────────────────────────────────────────

def init_state():
    defaults = {'phase': 0, 'book_id': None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def go_to_phase(phase: int):
    if st.session_state.book_id:
        update_book_phase(st.session_state.book_id, phase)
    st.session_state.phase = phase
    st.rerun()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## 📚 Creador de Libros")
        st.divider()

        book_id = st.session_state.book_id
        if book_id:
            book = get_book(book_id)
            selected_title = get_selected_title(book_id)

            st.caption("LIBRO ACTUAL")
            if selected_title:
                st.markdown(f"**{selected_title['titulo']}**")
                st.caption(selected_title['subtitulo'])
            else:
                idea_preview = (book['core_idea'][:60] + "...") if len(book['core_idea']) > 60 else book['core_idea']
                st.markdown(f"*{idea_preview}*")

            st.divider()
            st.caption("PROGRESO")
            current = st.session_state.phase
            max_reached = book.get('current_phase', current)
            for i, (icon, name) in enumerate(PHASES):
                if i == current:
                    st.markdown(f"<span style='color:#2196F3'>**→ {icon} {name}**</span>", unsafe_allow_html=True)
                elif i <= max_reached or (max_reached >= 10 and i <= 12):
                    if st.button(f"✓ {icon} {name}", key=f"nav_{i}", use_container_width=True):
                        st.session_state.phase = i
                        st.rerun()
                else:
                    st.markdown(f"<span style='color:#9E9E9E'>○ {icon} {name}</span>", unsafe_allow_html=True)

            st.divider()

        all_books = get_all_books()
        if all_books:
            st.caption("OTROS LIBROS")
            for b in all_books[:6]:
                if b['id'] == st.session_state.book_id:
                    continue
                t = get_selected_title(b['id'])
                label = t['titulo'] if t else f"Libro #{b['id']}"
                short = label[:28] + "…" if len(label) > 28 else label
                if st.button(f"📖 {short}", key=f"load_{b['id']}", use_container_width=True):
                    st.session_state.book_id = b['id']
                    st.session_state.phase = b['current_phase']
                    st.rerun()

        if st.button("➕ Nuevo Libro", use_container_width=True, type="secondary"):
            st.session_state.book_id = None
            st.session_state.phase = 0
            st.rerun()


# ─── Phase 0: Idea ────────────────────────────────────────────────────────────

def phase_idea():
    st.title("💡 ¿De qué trata tu libro?")
    st.markdown("Describe tu idea con la mayor claridad posible. Cuanto más específico seas, mejores serán los títulos y la estructura generados.")
    st.divider()

    with st.form("idea_form"):
        idea = st.text_area(
            "Idea central del libro",
            height=160,
            placeholder=(
                "Ejemplo: Un libro sobre cómo las personas que sufrieron traumas en la infancia "
                "desarrollan patrones de auto-sabotaje en sus relaciones adultas, y cómo identificar "
                "y romper esos patrones usando neuroplasticidad y terapia cognitivo-conductual."
            ),
        )

        col1, col2 = st.columns(2)
        with col1:
            target_reader = st.text_input(
                "Lector objetivo (opcional)",
                placeholder="Adultos de 30-50 años que sienten que se sabotean a sí mismos…",
            )
        with col2:
            key_problem = st.text_input(
                "Problema principal que resuelve (opcional)",
                placeholder="No entienden por qué repiten los mismos errores relacionales…",
            )

        submitted = st.form_submit_button("🚀 Generar opciones de título", type="primary", use_container_width=True)

    if submitted:
        if not idea.strip():
            st.warning("Describe la idea del libro antes de continuar.")
            return
        with st.spinner("Generando títulos…"):
            book_id = create_book(idea.strip(), target_reader.strip(), key_problem.strip())
            st.session_state.book_id = book_id
            titles = generate_titles(idea, target_reader, key_problem)
            save_title_options(book_id, titles)
        go_to_phase(1)


# ─── Phase 1: Titles ──────────────────────────────────────────────────────────

def phase_titles():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    title_options = get_title_options(book_id)

    st.title("📝 Elige el título de tu libro")
    st.markdown("Selecciona el que mejor captura la esencia, o úsalo como inspiración para tu propio título.")
    st.divider()

    if not title_options:
        st.error("No hay opciones de título.")
        return

    cols = st.columns(2)
    for i, opt in enumerate(title_options):
        with cols[i % 2]:
            is_selected = bool(opt.get('selected'))
            border = "2px solid #2196F3" if is_selected else "1px solid #e0e0e0"
            bg = "#E3F2FD" if is_selected else "#FAFAFA"
            st.markdown(
                f"""<div style="border:{border};border-radius:10px;padding:16px;margin-bottom:12px;background:{bg}">
                <h4 style="margin:0 0 4px 0">{opt['titulo']}</h4>
                <p style="color:#555;margin:0 0 8px 0;font-style:italic">{opt['subtitulo']}</p>
                <small style="color:#888">{opt['razon']}</small>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(
                "✓ Seleccionado" if is_selected else "Seleccionar",
                key=f"sel_t_{opt['id']}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                select_title(book_id, opt['id'])
                st.rerun()

    st.divider()

    with st.expander("✏️ Escribir un título personalizado"):
        with st.form("custom_title"):
            ct = st.text_input("Título")
            cs = st.text_input("Subtítulo")
            if st.form_submit_button("Añadir y seleccionar"):
                if ct:
                    ids = save_title_options(book_id, [{"titulo": ct, "subtitulo": cs, "razon": "Título personalizado"}], replace=False)
                    select_title(book_id, ids[0])
                    st.rerun()

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Regenerar"):
            with st.spinner("Generando nuevas opciones…"):
                titles = generate_titles(book['core_idea'], book['target_reader'], book['key_problem'])
                save_title_options(book_id, titles, replace=True)
            st.rerun()

    selected = get_selected_title(book_id)
    with col3:
        if selected:
            st.success(f"Seleccionado: **{selected['titulo']}**")
            if st.button("Continuar → Estructura", type="primary", use_container_width=True):
                with st.spinner("Generando estructuras narrativas…"):
                    structures = generate_structures(book['core_idea'], selected['titulo'], selected['subtitulo'])
                    save_structure_options(book_id, structures)
                go_to_phase(2)
        else:
            st.info("Selecciona un título para continuar.")


# ─── Phase 2: Structure ───────────────────────────────────────────────────────

def phase_structure():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    structures = get_structure_options(book_id)

    st.title("🏗️ Elige la estructura narrativa")
    st.markdown(f"**{selected_title['titulo']}** — Elige el arco que mejor guiará la transformación del lector.")
    st.divider()

    if not structures:
        st.error("No hay estructuras generadas.")
        return

    for struct in structures:
        is_selected = bool(struct.get('selected'))
        border = "2px solid #2196F3" if is_selected else "1px solid #e0e0e0"
        bg = "#E3F2FD" if is_selected else "#FAFAFA"

        with st.container():
            st.markdown(
                f"""<div style="border:{border};border-radius:10px;padding:16px;margin-bottom:8px;background:{bg}">
                <h3 style="margin:0 0 4px 0">{struct['nombre']}</h3>
                <small style="color:#888">Tipo: {struct['tipo_arco']} · ~{struct['capitulos_estimados']} capítulos</small>
                </div>""",
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(struct['descripcion'])
                st.markdown(f"**Viaje del lector:** *{struct['progresion_emocional']}*")

                fases = struct.get('fases', [])
                if fases:
                    fase_cols = st.columns(len(fases))
                    for j, fase in enumerate(fases):
                        with fase_cols[j]:
                            st.markdown(f"**{fase['nombre']}**")
                            st.caption(fase['descripcion'])
                            st.caption(f"~{fase.get('capitulos_aprox', '?')} caps.")

            with col2:
                if st.button(
                    "✓ Elegida" if is_selected else "Elegir esta",
                    key=f"sel_s_{struct['id']}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    select_structure(book_id, struct['id'])
                    st.rerun()

            st.divider()

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Regenerar"):
            with st.spinner("Generando nuevas estructuras…"):
                structs = generate_structures(book['core_idea'], selected_title['titulo'], selected_title['subtitulo'])
                save_structure_options(book_id, structs, replace=True)
            st.rerun()

    selected_struct = get_selected_structure(book_id)
    with col3:
        if selected_struct:
            st.success(f"Elegida: **{selected_struct['nombre']}**")
            if st.button("Continuar → Capítulos", type="primary", use_container_width=True):
                with st.spinner("Generando capítulos…"):
                    chapters = generate_chapters(
                        book['core_idea'], selected_title['titulo'],
                        selected_title['subtitulo'], selected_struct,
                    )
                    save_chapters(book_id, chapters)
                go_to_phase(3)
        else:
            st.info("Elige una estructura para continuar.")


# ─── Phase 3: Chapters ────────────────────────────────────────────────────────

def phase_chapters():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    chapters = get_chapters(book_id)

    st.title("📚 Capítulos del libro")
    st.markdown(
        f"**{selected_title['titulo']}** — {len(chapters)} capítulos  \n"
        "Revisa y edita. El **Territorio Exclusivo** es el campo más crítico: "
        "debe ser único e imposible de confundir con otro capítulo."
    )
    st.divider()

    if not chapters:
        st.error("No hay capítulos generados.")
        return

    arc_color = {
        'apertura': '#9C27B0', 'problema': '#F44336', 'ciencia': '#2196F3',
        'framework': '#FF9800', 'aplicacion': '#4CAF50',
        'transformacion': '#009688', 'cierre': '#607D8B',
    }

    for ch in chapters:
        color = arc_color.get(ch.get('posicion_arco', ''), '#888')
        with st.expander(
            f"**Cap. {ch['num']}: {ch['titulo']}** — `{ch.get('posicion_arco', '')}`",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                new_title = st.text_input("Título", value=ch['titulo'], key=f"ct_{ch['id']}")
                new_tesis = st.text_area("Tesis", value=ch['tesis'], key=f"cte_{ch['id']}", height=70)
                new_terr = st.text_area(
                    "🔑 Territorio Exclusivo (lo más importante)",
                    value=ch['territorio_exclusivo'], key=f"ctr_{ch['id']}", height=80,
                )
                new_prom = st.text_area(
                    "Promesa al lector",
                    value=ch.get('promesa_al_lector', ''), key=f"cpr_{ch['id']}", height=60,
                )

            with col2:
                new_arc = st.selectbox(
                    "Posición en el arco",
                    options=ARC_OPTIONS,
                    index=ARC_OPTIONS.index(ch.get('posicion_arco', 'ciencia')),
                    key=f"ca_{ch['id']}",
                )
                new_prop = st.text_area("Propósito", value=ch['proposito'], key=f"cpp_{ch['id']}", height=90)

                if st.button("💾 Guardar cambios", key=f"sv_{ch['id']}", use_container_width=True, type="primary"):
                    update_chapter(ch['id'], {
                        'titulo': new_title, 'tesis': new_tesis,
                        'territorio_exclusivo': new_terr, 'posicion_arco': new_arc,
                        'proposito': new_prop, 'promesa_al_lector': new_prom,
                    })
                    st.success("Guardado ✓")

                if st.button("🗑️ Eliminar capítulo", key=f"dl_{ch['id']}", use_container_width=True):
                    delete_chapter(ch['id'])
                    st.rerun()

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Regenerar todos"):
            struct = get_selected_structure(book_id)
            with st.spinner("Regenerando…"):
                new_chapters = generate_chapters(
                    book['core_idea'], selected_title['titulo'],
                    selected_title['subtitulo'], struct,
                )
                save_chapters(book_id, new_chapters, replace=True)
            st.rerun()

    with col2:
        if st.button("➕ Añadir capítulo en blanco"):
            save_chapters(book_id, [{
                'numero': len(chapters) + 1,
                'titulo': 'Nuevo Capítulo',
                'tesis': '',
                'territorio_exclusivo': 'Este capítulo es el ÚNICO que…',
                'posicion_arco': 'ciencia',
                'proposito': '',
                'promesa_al_lector': '',
            }], replace=False)
            st.rerun()

    with col3:
        if st.button("Continuar → Partes", type="primary", use_container_width=True):
            go_to_phase(4)


# ─── Phase 4: Parts ────────────────────────────────────────────────────────────

def phase_parts():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    chapters = get_chapters(book_id)

    st.title("📋 Partes de cada capítulo")
    st.markdown(
        f"**{selected_title['titulo']}**  \n"
        "Define las secciones internas. Cada parte debe tener un propósito único e irremplazable."
    )

    tipo_emoji = {
        'apertura': '🎯', 'ciencia': '🔬', 'historia': '📖',
        'teoria': '💡', 'ejercicio': '✍️', 'reflexion': '🤔', 'sintesis': '🔗',
    }

    chapters_with_parts = 0
    for ch in chapters:
        parts = get_parts(ch['id'])
        has_parts = len(parts) > 0
        if has_parts:
            chapters_with_parts += 1
        total_words = sum(p.get('palabras_estimadas', 0) for p in parts)

        with st.expander(
            f"{'✅' if has_parts else '○'} Cap. {ch['num']}: {ch['titulo']}"
            + (f" — {total_words:,} palabras est." if has_parts else ""),
            expanded=False,
        ):
            st.caption(f"Territorio: *{ch['territorio_exclusivo']}*")

            if has_parts:
                for part in parts:
                    emoji = tipo_emoji.get(part['tipo'], '•')
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(f"{emoji} **{part['num']}. {part['titulo']}** `{part['tipo']}`")
                            for pt in part.get('puntos_clave', []):
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• {pt}", unsafe_allow_html=True)
                        with col2:
                            st.caption(f"~{part['palabras_estimadas']} pal.")
                        st.caption(f"*{part['proposito']}*")
                        st.markdown("---")

            col_a, col_b = st.columns(2)
            with col_a:
                label = "🔄 Regenerar partes" if has_parts else "✨ Generar partes"
                if st.button(label, key=f"gp_{ch['id']}", use_container_width=True):
                    with st.spinner(f"Generando partes para '{ch['titulo']}'…"):
                        new_parts = generate_parts(ch, book['core_idea'])
                        save_parts(ch['id'], new_parts)
                    st.rerun()

    st.divider()
    st.caption(f"{chapters_with_parts}/{len(chapters)} capítulos con partes definidas")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("✨ Generar partes para TODOS los capítulos", use_container_width=True):
            prog = st.progress(0, text="Generando partes…")
            for i, ch in enumerate(chapters):
                prog.progress((i + 1) / len(chapters), text=f"Cap. {ch['num']}: {ch['titulo']}…")
                new_parts = generate_parts(ch, book['core_idea'])
                save_parts(ch['id'], new_parts)
            prog.empty()
            st.rerun()

    with col2:
        if st.button("Continuar → Verificar Coherencia", type="primary", use_container_width=True):
            with st.spinner("Analizando solapamientos…"):
                fresh_chapters = get_chapters(book_id)
                analysis = check_overlaps(fresh_chapters)
                save_overlap_flags(book_id, analysis)
            go_to_phase(5)


# ─── Phase 5: Overlap ─────────────────────────────────────────────────────────

def phase_overlap():
    book_id = st.session_state.book_id
    summary = get_coherence_summary(book_id)
    chapters = get_chapters(book_id)
    chapter_by_num = {ch['num']: ch for ch in chapters}

    # Auto-run on first visit if no analysis exists yet
    if not summary:
        with st.spinner("Analizando coherencia entre capítulos…"):
            analysis = check_overlaps(chapters)
            save_overlap_flags(book_id, analysis, replace=True)
        st.rerun()

    flags = get_overlap_flags(book_id)

    st.title("🔍 Verificación de Coherencia")
    st.markdown("El sistema ha analizado todos los capítulos en busca de solapamientos conceptuales.")
    st.divider()

    if summary:
        score = summary.get('score_coherencia', 0)
        col1, col2 = st.columns([1, 3])
        with col1:
            color = "normal" if score >= 80 else "inverse"
            st.metric("Score de coherencia", f"{score}/100")
        with col2:
            st.progress(score / 100)
            if summary.get('evaluacion_general'):
                st.info(f"💬 {summary['evaluacion_general']}")

    st.divider()

    if not flags:
        st.success("✅ Sin solapamientos detectados. La estructura es sólida.")
    else:
        pending = [f for f in flags if not f['resuelto']]
        resolved = [f for f in flags if f['resuelto']]

        high = [f for f in pending if f['severidad'] == 'alto']
        mid = [f for f in pending if f['severidad'] == 'medio']
        low = [f for f in pending if f['severidad'] == 'bajo']

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Altos", len(high))
        c2.metric("🟡 Medios", len(mid))
        c3.metric("🟢 Bajos", len(low))
        c4.metric("✅ Resueltos", len(resolved))

        st.divider()

        sev_config = {
            'alto':  ("🔴 ALTO — requiere resolución", "#FFEBEE"),
            'medio': ("🟡 MEDIO — revisar delimitación", "#FFFDE7"),
            'bajo':  ("🟢 BAJO — resonancia aceptable", "#F1F8E9"),
        }

        for flag in pending:
            sev = flag['severidad']
            label, bg = sev_config.get(sev, ("○", "#FFF"))
            ch_a = chapter_by_num.get(flag['capitulo_a'])
            ch_b = chapter_by_num.get(flag['capitulo_b'])

            st.markdown(
                f"""<div style="background:{bg};border-radius:8px;padding:12px 16px;margin-bottom:8px">
                <strong>{label}</strong><br>
                Cap. {flag['capitulo_a']}: <em>{ch_a['titulo'] if ch_a else '?'}</em>
                &nbsp;↔&nbsp;
                Cap. {flag['capitulo_b']}: <em>{ch_b['titulo'] if ch_b else '?'}</em>
                </div>""",
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns([5, 2])
            with col1:
                st.markdown(f"**Solapamiento:** {flag['descripcion']}")
                st.markdown(f"**Sugerencia:** {flag['resolucion_sugerida']}")
            with col2:
                if st.button("🔧 Auto-corregir", key=f"fix_{flag['id']}", use_container_width=True, type="primary"):
                    ch_a = chapter_by_num.get(flag['capitulo_a'])
                    ch_b = chapter_by_num.get(flag['capitulo_b'])
                    if ch_a and ch_b:
                        with st.spinner("Corrigiendo territorios…"):
                            result = fix_overlap(ch_a, ch_b, flag['descripcion'], flag['resolucion_sugerida'])
                        if result.get('capitulo_a') and result.get('capitulo_b'):
                            update_chapter(ch_a['id'], {'territorio_exclusivo': result['capitulo_a']['territorio_exclusivo']})
                            update_chapter(ch_b['id'], {'territorio_exclusivo': result['capitulo_b']['territorio_exclusivo']})
                            resolve_overlap(flag['id'])
                            if result.get('explicacion'):
                                st.session_state[f'fix_msg_{flag["id"]}'] = result['explicacion']
                            st.rerun()
                if st.button("✅ Marcar resuelto", key=f"res_{flag['id']}", use_container_width=True):
                    resolve_overlap(flag['id'])
                    st.rerun()
            fix_msg_key = f"fix_msg_{flag['id']}"
            if st.session_state.get(fix_msg_key):
                st.success(f"✓ {st.session_state.pop(fix_msg_key)}")
            st.divider()

        if resolved:
            with st.expander(f"Ver {len(resolved)} solapamientos resueltos"):
                for f in resolved:
                    ch_a = chapter_by_num.get(f['capitulo_a'])
                    ch_b = chapter_by_num.get(f['capitulo_b'])
                    st.markdown(
                        f"~~Cap. {f['capitulo_a']}: {ch_a['titulo'] if ch_a else '?'}"
                        f" ↔ Cap. {f['capitulo_b']}: {ch_b['titulo'] if ch_b else '?'}~~ ✓"
                    )

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Re-analizar"):
            with st.spinner("Analizando…"):
                fresh = get_chapters(book_id)
                analysis = check_overlaps(fresh)
                save_overlap_flags(book_id, analysis, replace=True)
            st.rerun()

    pending_high = [f for f in flags if f['severidad'] == 'alto' and not f['resuelto']]
    with col3:
        if pending_high:
            st.warning(f"{len(pending_high)} solapamiento(s) alto(s) sin resolver.")
        else:
            if st.button("Continuar → Esqueleto Final", type="primary", use_container_width=True):
                go_to_phase(6)


# ─── Phase 6: Final Skeleton ──────────────────────────────────────────────────

def phase_final():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    selected_struct = get_selected_structure(book_id)
    chapters = get_chapters(book_id)

    st.title("✅ Esqueleto Final del Libro")
    st.markdown(
        f"# {selected_title['titulo']}\n"
        f"### *{selected_title['subtitulo']}*"
    )
    if selected_struct:
        st.caption(f"Estructura: {selected_struct['nombre']} · {selected_struct['tipo_arco']}")
    st.divider()

    total_words = 0
    total_parts = 0
    export_lines = [
        f"# {selected_title['titulo']}",
        f"## {selected_title['subtitulo']}",
        "",
        f"Idea central: {book['core_idea']}",
        "",
        "---",
        "",
    ]

    arc_color = {
        'apertura': '#9C27B0', 'problema': '#F44336', 'ciencia': '#2196F3',
        'framework': '#FF9800', 'aplicacion': '#4CAF50',
        'transformacion': '#009688', 'cierre': '#607D8B',
    }
    tipo_emoji = {
        'apertura': '🎯', 'ciencia': '🔬', 'historia': '📖',
        'teoria': '💡', 'ejercicio': '✍️', 'reflexion': '🤔', 'sintesis': '🔗',
    }

    for ch in chapters:
        parts = get_parts(ch['id'])
        ch_words = sum(p.get('palabras_estimadas', 0) for p in parts)
        total_words += ch_words
        total_parts += len(parts)
        color = arc_color.get(ch.get('posicion_arco', ''), '#888')

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"<h3 style='margin-bottom:4px'>Capítulo {ch['num']}: {ch['titulo']}"
                f" <span style='font-size:0.6em;color:{color};border:1px solid {color};"
                f"border-radius:4px;padding:2px 6px'>{ch.get('posicion_arco','')}</span></h3>",
                unsafe_allow_html=True,
            )
            st.caption(f"*{ch['tesis']}*")
        with col2:
            if ch_words:
                st.metric("Palabras est.", f"{ch_words:,}")

        for part in parts:
            emoji = tipo_emoji.get(part['tipo'], '•')
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(f"&nbsp;&nbsp;&nbsp;{emoji} **{part['num']}. {part['titulo']}** `{part['tipo']}`", unsafe_allow_html=True)
                for pt in part.get('puntos_clave', []):
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;• {pt}", unsafe_allow_html=True)
            with col_b:
                st.caption(f"~{part['palabras_estimadas']} pal.")

        st.divider()

        # Build export
        export_lines += [
            f"## Capítulo {ch['num']}: {ch['titulo']}",
            f"Tesis: {ch['tesis']}",
            f"Territorio exclusivo: {ch['territorio_exclusivo']}",
            "",
        ]
        for part in parts:
            export_lines.append(f"### {part['num']}. {part['titulo']} ({part['tipo']})")
            for pt in part.get('puntos_clave', []):
                export_lines.append(f"- {pt}")
            export_lines.append("")
        export_lines.append("---\n")

    # Summary metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Capítulos", len(chapters))
    c2.metric("Secciones totales", total_parts)
    c3.metric("Palabras estimadas", f"{total_words:,}")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Exportar esqueleto (.txt)",
            data="\n".join(export_lines),
            file_name=f"{selected_title['titulo']}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        if st.button("✏️ Volver a editar capítulos", use_container_width=True):
            go_to_phase(3)
    with col3:
        if st.button("Continuar → Bolsa de Palabras", type="primary", use_container_width=True):
            go_to_phase(7)

    st.success("🎉 Esqueleto completado. Siguiente paso: define las palabras prohibidas y el tono del libro.")


# ─── Phase 7: Word Ban ────────────────────────────────────────────────────────

CATEGORIA_LABELS = {
    'cliche_ia':       '🤖 Cliché de IA',
    'cierre_mecanico': '🔒 Cierre mecánico',
    'adjetivo_vacio':  '💨 Adjetivo vacío',
    'intensificador':  '📢 Intensificador vacío',
    'jerga':           '💼 Jerga / sobreusado',
    'enfasis_vacio':   '❗ Énfasis vacío',
    'apertura_cliche': '🎭 Apertura cliché',
    'especifico_tema': '📌 Específico del tema',
    'redundante':      '🔁 Redundante',
}


def phase_word_ban():
    book_id = st.session_state.book_id
    selected_title = get_selected_title(book_id)

    st.title("🚫 Bolsa de Palabras Prohibidas")
    st.markdown(
        f"**{selected_title['titulo']}**  \n"
        "Define qué palabras y frases la IA no puede usar al escribir este libro. "
        "La lista global aplica a todos los libros. Las específicas del proyecto son tuyas."
    )
    st.divider()

    tab1, tab2 = st.tabs(["🌐 Lista Global (clichés de IA)", "📌 Específicas de este libro"])

    with tab1:
        global_bans = get_global_word_bans()
        st.markdown(f"**{len(global_bans)} palabras y frases** pre-cargadas. Desactiva las que no apliquen.")
        st.divider()

        by_cat = {}
        for ban in global_bans:
            cat = ban.get('categoria', 'general')
            by_cat.setdefault(cat, []).append(ban)

        for cat, bans in by_cat.items():
            cat_label = CATEGORIA_LABELS.get(cat, cat)
            with st.expander(f"{cat_label} ({len(bans)})", expanded=True):
                for ban in bans:
                    col1, col2, col3 = st.columns([3, 3, 1])
                    with col1:
                        style = "" if ban['activa'] else "text-decoration:line-through;color:#aaa"
                        st.markdown(f"<span style='{style}'>**{ban['word']}**</span>", unsafe_allow_html=True)
                    with col2:
                        st.caption(ban.get('reason', ''))
                    with col3:
                        label = "ON" if ban['activa'] else "OFF"
                        if st.button(label, key=f"tog_{ban['id']}", use_container_width=True):
                            toggle_word_ban(ban['id'])
                            st.rerun()

    with tab2:
        project_bans = get_project_word_bans(book_id)
        st.markdown(
            "Añade palabras que **en este libro específico** tiendan a repetirse demasiado. "
            "Por ejemplo: si el libro es sobre hábitos, quizás quieras limitar *'rutina'*, *'disciplina'*, *'constancia'*."
        )
        st.divider()

        with st.form("add_word_ban"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_word = st.text_input("Palabra o frase a prohibir")
            with col2:
                new_reason = st.text_input("Motivo (opcional)")
            with col3:
                new_cat = st.selectbox("Categoría", options=['especifico_tema', 'redundante', 'jerga'])
            if st.form_submit_button("➕ Añadir", use_container_width=True):
                if new_word.strip():
                    add_word_ban(book_id, new_word, new_reason, new_cat)
                    st.rerun()

        if project_bans:
            st.divider()
            for ban in project_bans:
                col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
                with col1:
                    style = "" if ban['activa'] else "text-decoration:line-through;color:#aaa"
                    st.markdown(f"<span style='{style}'>**{ban['word']}**</span>", unsafe_allow_html=True)
                with col2:
                    st.caption(ban.get('reason', ''))
                with col3:
                    label = "ON" if ban['activa'] else "OFF"
                    if st.button(label, key=f"ptog_{ban['id']}", use_container_width=True):
                        toggle_word_ban(ban['id'])
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"pdel_{ban['id']}", use_container_width=True):
                        delete_word_ban(ban['id'])
                        st.rerun()
        else:
            st.info("Aún no has añadido palabras específicas para este libro.")

    st.divider()
    active_total = len(get_active_word_bans(book_id))
    st.caption(f"Total activas: {active_total} palabras y frases prohibidas")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("← Volver al Esqueleto"):
            go_to_phase(6)
    with col2:
        if st.button("Continuar → Tono Patrón", type="primary", use_container_width=True):
            go_to_phase(8)


# ─── Phase 8: Tone Pattern ────────────────────────────────────────────────────

VOZ_OPTIONS = ['segunda', 'primera', 'mixta']
VOZ_LABELS  = ['Segunda persona (tú)', 'Primera persona (yo/autor)', 'Mixta']

REGISTRO_OPTIONS = ['conversacional', 'periodistico', 'academico_accesible', 'intimo']
REGISTRO_LABELS  = ['Conversacional', 'Periodístico', 'Académico accesible', 'Íntimo y confesional']

LONGITUD_OPTIONS = ['mixta', 'corta', 'media']
LONGITUD_LABELS  = ['Mixta (ritmo deliberado)', 'Corta e impactante', 'Media y fluida']

METAFORA_OPTIONS = ['moderado', 'frecuente', 'minimo']
METAFORA_LABELS  = ['Moderado (solo cuando ilumina)', 'Frecuente (siempre con imagen)', 'Mínimo (lenguaje directo)']

CIENCIA_OPTIONS  = ['analogias', 'integrada', 'informal']
CIENCIA_LABELS   = ['Con analogías cotidianas', 'Integrada en la narrativa', 'Informal (sin jerga técnica)']

TEMP_OPTIONS = ['equilibrada', 'alta', 'racional_calidez']
TEMP_LABELS  = ['Equilibrada (cabeza y corazón)', 'Alta (intensa, urgente)', 'Racional con calidez']


from agents.style_extractor_agent import extract_and_replicate_style

def phase_tone_pattern():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    existing_tone = get_tone_pattern(book_id) or {}

    st.title("🎨 Tono Patrón del Libro")
    st.markdown(
        f"**{selected_title['titulo']}**  \n"
        "El sistema calculará matemáticamente la huella estilística del autor usando textos de referencia, "
        "y probará distintas variantes de IA para encontrar el prompt que mejor replique ese estilo."
    )
    st.divider()

    # --- NUEVO FLUJO AUTOMATIZADO ---
    st.markdown("### 🤖 Automatización de Estilo (StyleDistance)")
    raw_dir = "data/raw_author_texts"
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.info(f"Directorio de textos crudos: `{raw_dir}`")
    with col_b:
        if st.button("🚀 Extraer y Replicar Estilo", use_container_width=True, type="primary"):
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def update_progress(val, msg):
                progress_bar.progress(val)
                status_text.text(msg)
                
            try:
                result = extract_and_replicate_style(raw_dir, progress_callback=update_progress)
                from database.db import save_auto_tone_pattern
                save_auto_tone_pattern(
                    book_id, 
                    result['winning_prompt'], 
                    result['winning_text'], 
                    result['similarity_score']
                )
                st.session_state['style_result'] = result
                update_progress(1.0, "¡Estilo extraído con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error en la extracción: {e}")

    existing_tone = get_tone_pattern(book_id) or {}
    
    if existing_tone.get('is_auto_generated') == 1 or 'style_result' in st.session_state:
        st.success("✅ Estilo automatizado configurado")
        
        prompt_rector = existing_tone.get('prompt_rector') or st.session_state['style_result']['winning_prompt']
        texto_campeon = existing_tone.get('texto_campeon') or st.session_state['style_result']['winning_text']
        score = existing_tone.get('score_similitud') or st.session_state['style_result']['similarity_score']
        
        st.metric("Score de Similitud (StyleDistance)", f"{score:.4f}")
        
        st.markdown("#### Texto Campeón (Párrafo Ancla)")
        st.markdown(f"> *{texto_campeon}*")
        
        with st.expander("Ver Prompt Rector (Instrucción Base)"):
            st.code(prompt_rector, language="text")

    st.divider()

    # --- FLUJO LEGACY MANUAL ---
    with st.expander("⚙️ Modo Manual de Tono (Legacy)"):
        col_form, col_preview = st.columns([1, 1])

    with col_form:
        st.markdown("### Configuración de tono")

        def idx(options, val):
            return options.index(val) if val in options else 0

        voz = st.radio("Voz narrativa", options=VOZ_LABELS,
                       index=idx(VOZ_OPTIONS, existing_tone.get('voz', 'segunda')))
        voz_val = VOZ_OPTIONS[VOZ_LABELS.index(voz)]

        registro = st.radio("Registro", options=REGISTRO_LABELS,
                             index=idx(REGISTRO_OPTIONS, existing_tone.get('registro', 'conversacional')))
        registro_val = REGISTRO_OPTIONS[REGISTRO_LABELS.index(registro)]

        longitud = st.radio("Longitud de frase", options=LONGITUD_LABELS,
                            index=idx(LONGITUD_OPTIONS, existing_tone.get('longitud_frase', 'mixta')))
        longitud_val = LONGITUD_OPTIONS[LONGITUD_LABELS.index(longitud)]

        metaforas = st.radio("Uso de metáforas", options=METAFORA_LABELS,
                             index=idx(METAFORA_OPTIONS, existing_tone.get('uso_metaforas', 'moderado')))
        metaforas_val = METAFORA_OPTIONS[METAFORA_LABELS.index(metaforas)]

        ciencia = st.radio("Tratamiento de la ciencia", options=CIENCIA_LABELS,
                           index=idx(CIENCIA_OPTIONS, existing_tone.get('tratamiento_ciencia', 'analogias')))
        ciencia_val = CIENCIA_OPTIONS[CIENCIA_LABELS.index(ciencia)]

        temperatura = st.radio("Temperatura emocional", options=TEMP_LABELS,
                               index=idx(TEMP_OPTIONS, existing_tone.get('temperatura_emocional', 'equilibrada')))
        temperatura_val = TEMP_OPTIONS[TEMP_LABELS.index(temperatura)]

        instrucciones = st.text_area(
            "Instrucciones adicionales de estilo (opcional)",
            value=existing_tone.get('instrucciones_adicionales', ''),
            placeholder="Ej: Evitar preguntas retóricas al inicio de párrafo. Usar punto y seguido frecuente. El autor tiene humor seco.",
            height=80,
        )

        tone_config = {
            'voz': voz_val, 'registro': registro_val, 'longitud_frase': longitud_val,
            'uso_metaforas': metaforas_val, 'tratamiento_ciencia': ciencia_val,
            'temperatura_emocional': temperatura_val, 'instrucciones_adicionales': instrucciones,
        }

        if st.button("💾 Guardar configuración", use_container_width=True):
            save_tone_pattern(book_id, tone_config)
            st.success("Configuración guardada ✓")

        st.divider()
        if st.button("✨ Generar ejemplos de tono", type="primary", use_container_width=True):
            save_tone_pattern(book_id, tone_config)
            with st.spinner("Generando ejemplos…"):
                examples = generate_tone_examples(book['core_idea'], selected_title['titulo'], tone_config)
            st.session_state['tone_examples'] = examples
            st.rerun()

    with col_preview:
        st.markdown("### Ejemplos generados")

        examples = st.session_state.get('tone_examples', [])
        approved = existing_tone.get('parrafo_ancla', '')
        is_approved = bool(existing_tone.get('parrafo_ancla_aprobado'))

        if is_approved and approved:
            st.success("✅ Párrafo ancla aprobado")
            st.markdown(
                f"""<div style="background:#E8F5E9;border-left:4px solid #4CAF50;
                padding:16px;border-radius:6px;font-style:italic">{approved}</div>""",
                unsafe_allow_html=True,
            )
            if st.button("🔄 Cambiar párrafo ancla"):
                approve_parrafo_ancla(book_id, '')
                st.session_state.pop('tone_examples', None)
                st.rerun()
        elif examples:
            st.markdown("Selecciona el que más se acerque al tono que buscas, edítalo si quieres y apruébalo:")
            for i, ex in enumerate(examples):
                with st.expander(f"Opción {i+1}: {ex.get('etiqueta', '')}", expanded=(i == 0)):
                    edited = st.text_area(
                        "Texto (puedes editarlo antes de aprobar)",
                        value=ex.get('parrafo', ''),
                        key=f"ex_{i}",
                        height=180,
                    )
                    if st.button(f"✅ Aprobar esta como párrafo ancla", key=f"appr_{i}", use_container_width=True, type="primary"):
                        save_tone_pattern(book_id, tone_config)
                        approve_parrafo_ancla(book_id, edited)
                        st.session_state.pop('tone_examples', None)
                        st.rerun()
        else:
            st.info("Configura el tono y pulsa **Generar ejemplos** para ver opciones reales.")
            st.markdown(
                """**¿Qué es el párrafo ancla?**
                Es un párrafo de ~150 palabras sobre el tema real de tu libro, escrito en el tono elegido.
                La IA lo consultará antes de escribir cada sección para mantener coherencia de estilo."""
            )

    st.divider()
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← Volver a Investigación"):
            go_to_phase(8)
    with col3:
        tone_ready = existing_tone.get('parrafo_ancla_aprobado', False)
        if tone_ready:
            st.success("✅ Tono patrón listo.")
            if st.button("Continuar → Escritura", type="primary", use_container_width=True):
                go_to_phase(10)
        else:
            st.warning("Aprueba un párrafo ancla para continuar.")


# ─── Phase 9: Research ────────────────────────────────────────────────────────

PLACEMENT_LABELS = {
    'apertura':     '🎯 Apertura del capítulo',
    'post_ciencia': '🔬 Después de la ciencia',
    'pre_ejercicio':'✍️ Antes del ejercicio',
    'cierre':       '🔗 Cierre del capítulo',
}

VERIFICADO_BADGE = {
    0: ("⚠️", "#FFF9C4", "Sin verificar"),
    1: ("✅", "#E8F5E9", "Verificado"),
}


def _run_tavily_verification(chapter_id: int) -> dict:
    """Verify all unverified items for a chapter. Returns stats dict."""
    stats = {'total': 0, 'verified': 0, 'not_found': 0, 'error': None}
    items = get_research_items(chapter_id)
    for item in items:
        if item['verificado'] or not item.get('busqueda_sugerida', '').strip():
            continue
        stats['total'] += 1
        result = verify_item(item['busqueda_sugerida'])
        if result.get('error'):
            stats['error'] = result['error']
            break
        if result['found']:
            stats['verified'] += 1
            verify_research_item(item['id'], result['url'], result['title'], result['snippet'])
        else:
            stats['not_found'] += 1
    return stats


def phase_research():
    book_id = st.session_state.book_id
    book    = get_book(book_id)
    selected_title = get_selected_title(book_id)
    chapters = get_chapters(book_id)

    st.title("🔬 Investigación por Capítulo")
    st.markdown(f"**{selected_title['titulo']}**")

    # ── Tavily status banner ──────────────────────────────────────────────────
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if tavily_key:
        st.success(f"🔑 Tavily conectado — key detectada (`...{tavily_key[-6:]}`)")
    else:
        st.error("🔑 TAVILY_API_KEY no encontrada en el entorno. La verificación automática no funcionará.")

    # Mostrar resultado de la última operación (persiste entre reruns)
    if 'research_last_result' in st.session_state:
        r = st.session_state.pop('research_last_result')
        if r.get('error'):
            st.error(f"❌ Tavily error: {r['error']}")
        else:
            v, nf, t = r.get('verified', 0), r.get('not_found', 0), r.get('total', 0)
            if t == 0:
                st.info("ℹ️ Ningún ítem tenía query de búsqueda (ya estaban verificados o sin query).")
            else:
                st.success(
                    f"✅ Tavily completó: **{v} verificados con URL** · "
                    f"**{nf} no encontrados** (quedan en ⚠️ para verificación manual) · "
                    f"**{t} total procesados**"
                )

    st.divider()

    # ── Progreso general ─────────────────────────────────────────────────────
    researched = sum(1 for ch in chapters if has_research(ch['id']))
    st.progress(
        researched / len(chapters) if chapters else 0,
        text=f"{researched}/{len(chapters)} capítulos con dossier generado"
    )

    # ── Botón generar todos ──────────────────────────────────────────────────
    if st.button("⚡ Generar dossier para TODOS los capítulos", use_container_width=True, type="primary"):
        total_v, total_nf, total_t, first_error = 0, 0, 0, None
        prog = st.progress(0)
        status_text = st.empty()
        for i, ch in enumerate(chapters):
            status_text.markdown(
                f"**Paso 1/2 — IA investigando:** Cap. {ch['num']}: {ch['titulo']}…"
            )
            prog.progress((i + 0.5) / len(chapters))
            parts   = get_parts(ch['id'])
            dossier = research_chapter(ch, book['core_idea'], parts)
            save_research_dossier(ch['id'], dossier)

            status_text.markdown(
                f"**Paso 2/2 — Tavily verificando:** Cap. {ch['num']}: {ch['titulo']}…"
            )
            stats = _run_tavily_verification(ch['id'])
            if stats['error'] and not first_error:
                first_error = stats['error']
            total_v  += stats['verified']
            total_nf += stats['not_found']
            total_t  += stats['total']
            prog.progress((i + 1) / len(chapters))

        prog.empty()
        status_text.empty()
        st.session_state['research_last_result'] = {
            'verified': total_v, 'not_found': total_nf,
            'total': total_t, 'error': first_error,
        }
        st.rerun()

    st.divider()

    # ── Capítulo por capítulo ─────────────────────────────────────────────────
    for ch in chapters:
        science_items = get_research_items(ch['id'], 'ciencia')
        story_items   = get_research_items(ch['id'], 'historia')
        placement_map = get_placement_map(ch['id'])
        chapter_note  = get_chapter_note(ch['id'])
        ready         = has_research(ch['id'])

        n_verified = sum(1 for i in science_items + story_items if i['verificado'])
        n_total    = len(science_items) + len(story_items)
        badge_str  = f"✅ {n_verified}/{n_total} verificados" if ready else "○ sin dossier"

        with st.expander(f"Cap. {ch['num']}: {ch['titulo']}  —  {badge_str}", expanded=False):
            st.caption(f"*{ch['territorio_exclusivo']}*")
            if chapter_note:
                st.info(f"💬 {chapter_note}")

            col_g1, col_g2 = st.columns([3, 1])
            with col_g1:
                btn_label = "🔄 Regenerar dossier" if ready else "✨ Generar dossier"
                if st.button(btn_label, key=f"gen_{ch['id']}", use_container_width=True):
                    with st.spinner("Paso 1/2: IA investigando…"):
                        parts   = get_parts(ch['id'])
                        dossier = research_chapter(ch, book['core_idea'], parts)
                        save_research_dossier(ch['id'], dossier)
                    with st.spinner("Paso 2/2: Tavily verificando fuentes…"):
                        stats = _run_tavily_verification(ch['id'])
                    st.session_state['research_last_result'] = stats
                    st.rerun()

            with col_g2:
                if ready and st.button("🔍 Re-verificar", key=f"rever_{ch['id']}", use_container_width=True):
                    with st.spinner("Tavily buscando…"):
                        stats = _run_tavily_verification(ch['id'])
                    st.session_state['research_last_result'] = stats
                    st.rerun()

            if not ready:
                continue

            # ── Ciencia ──────────────────────────────────────────────────────
            st.markdown("#### 📊 Sustento Científico")
            for item in science_items:
                badge = "✅" if item['verificado'] else "⚠️"
                bg    = "#E8F5E9" if item['verificado'] else "#FFFDE7"
                st.markdown(
                    f"""<div style="background:{bg};border-radius:8px;padding:10px 14px;margin-bottom:6px">
                    <strong>{badge} {item['titulo']}</strong><br>
                    <small style="color:#555">{item['autor']} · {item['año']} · {item['campo']}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**Hallazgo:** {item['hallazgo_clave']}")
                    if item.get('fuente_url'):
                        st.markdown(f"[🔗 {item.get('fuente_titulo') or 'Ver fuente'}]({item['fuente_url']})")
                    elif item.get('busqueda_sugerida'):
                        st.caption(f"Query: *{item['busqueda_sugerida']}*")
                with col2:
                    if not item['verificado']:
                        if st.button("🔍", key=f"v_sci_{item['id']}", use_container_width=True, help="Verificar con Tavily"):
                            with st.spinner("Buscando…"):
                                r = verify_item(item['busqueda_sugerida'])
                            st.session_state['research_last_result'] = r if r.get('error') else {
                                'verified': 1 if r['found'] else 0,
                                'not_found': 0 if r['found'] else 1,
                                'total': 1, 'error': None,
                            }
                            if r['found']:
                                verify_research_item(item['id'], r['url'], r['title'], r['snippet'])
                            st.rerun()
                    if st.button("🗑️", key=f"d_sci_{item['id']}", use_container_width=True):
                        delete_research_item(item['id'])
                        st.rerun()
                st.markdown("---")

            # ── Historias ────────────────────────────────────────────────────
            if story_items:
                st.markdown("#### 📖 Historias Reales")
                for item in story_items:
                    badge = "✅" if item['verificado'] else "⚠️"
                    bg    = "#E8F5E9" if item['verificado'] else "#FFFDE7"
                    pl    = PLACEMENT_LABELS.get(item.get('placement', ''), item.get('placement', ''))
                    st.markdown(
                        f"""<div style="background:{bg};border-radius:8px;padding:10px 14px;margin-bottom:6px">
                        <strong>{badge} {item['protagonista']}</strong>
                        &nbsp;<span style="background:#E3F2FD;padding:1px 7px;border-radius:4px;font-size:0.8em">{pl}</span>
                        &nbsp;<span style="color:#888;font-size:0.8em">→ Parte {item.get('parte_sugerida','?')}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**Qué pasó:** {item['que_paso']}")
                        st.caption(f"**Ilustra:** {item['que_ilustra']}")
                        if item.get('fuente_url'):
                            st.markdown(f"[🔗 {item.get('fuente_titulo') or 'Ver fuente'}]({item['fuente_url']})")
                        elif item.get('busqueda_sugerida'):
                            st.caption(f"Query: *{item['busqueda_sugerida']}*")
                    with col2:
                        if not item['verificado']:
                            if st.button("🔍", key=f"v_sto_{item['id']}", use_container_width=True, help="Verificar con Tavily"):
                                with st.spinner("Buscando…"):
                                    r = verify_item(item['busqueda_sugerida'])
                                st.session_state['research_last_result'] = {
                                    'verified': 1 if r['found'] else 0,
                                    'not_found': 0 if r['found'] else 1,
                                    'total': 1, 'error': r.get('error'),
                                }
                                if r['found']:
                                    verify_research_item(item['id'], r['url'], r['title'], r['snippet'])
                                st.rerun()
                        if st.button("🗑️", key=f"d_sto_{item['id']}", use_container_width=True):
                            delete_research_item(item['id'])
                            st.rerun()
                    st.markdown("---")

            # ── Mapa de colocación ───────────────────────────────────────────
            if placement_map:
                st.markdown("#### 🗺️ Mapa de Colocación Narrativa")
                parts_map = {p['num']: p['titulo'] for p in get_parts(ch['id'])}
                for entry in placement_map:
                    pnum = entry['parte_num']
                    if entry['necesita_historia']:
                        st.markdown(f"📖 **Parte {pnum}: {parts_map.get(pnum, '')}** — {entry['razon']}")
                    else:
                        st.caption(f"— Parte {pnum}: {parts_map.get(pnum, '')} — sin historia")

    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Volver a Bolsa de Palabras"):
            go_to_phase(7)
    with col2:
        if researched == len(chapters):
            st.success("✅ Investigación completa.")
        else:
            st.info(f"Faltan {len(chapters) - researched} capítulos por investigar.")
    with col3:
        if st.button("Tono Patrón →", type="primary", use_container_width=True):
            go_to_phase(9)


# ─── Writing helpers ──────────────────────────────────────────────────────────

def _run_batch_write(all_parts, target_parts, chapter, book, tone, word_bans, research):
    """Generate content for target_parts sequentially, passing accumulated context."""
    bar = st.progress(0)
    status = st.empty()
    written_so_far = []
    for i, part in enumerate(target_parts):
        status.markdown(f"**Escribiendo** parte {part['num']}/{len(all_parts)}: *{part['titulo']}*…")
        bar.progress(i / len(target_parts))
        context_str = "\n\n".join(written_so_far[-2:])
        content = write_part(
            part, chapter, book['core_idea'],
            tone, word_bans, research, context_str, all_parts,
        )
        save_written_part(part['id'], content)
        preview = content[:200] + "…" if len(content) > 200 else content
        written_so_far.append(f"[Parte {part['num']} · {part.get('tipo','').upper()} · '{part['titulo']}']\n{preview}")
        st.session_state[f"_pending_ta_{part['id']}"] = content
        bar.progress((i + 1) / len(target_parts))
    bar.empty()
    status.empty()
    st.rerun()


# ─── Phase 10: Escritura ──────────────────────────────────────────────────────

def phase_writing():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    chapters = get_chapters(book_id)
    tone = get_tone_pattern(book_id)
    word_bans = get_active_word_bans(book_id)

    st.title("✍️ Escritura del Libro")
    if selected_title:
        st.markdown(f"**{selected_title['titulo']}**")

    # ── Progreso general ──────────────────────────────────────────────────────
    prog = get_book_writing_progress(book_id)
    total = prog['total']
    approved = prog['approved']
    written = prog['written']

    col_p1, col_p2, col_p3 = st.columns([3, 1, 1])
    with col_p1:
        pct = approved / total if total > 0 else 0
        st.progress(pct, text=f"{approved}/{total} partes aprobadas")
    with col_p2:
        st.metric("Escritas", f"{written}/{total}")
    with col_p3:
        st.metric("Aprobadas", f"{approved}/{total}")

    if not tone or not tone.get('parrafo_ancla_aprobado'):
        st.warning("⚠️ No hay párrafo ancla aprobado (Fase 8). La escritura funcionará pero sin referencia de tono.")

    st.divider()

    # ── Selector de capítulo ──────────────────────────────────────────────────
    ch_options = {ch['id']: f"Cap. {ch['num']}: {ch['titulo']}" for ch in chapters}

    selected_ch_id = st.selectbox(
        "Capítulo a trabajar",
        options=list(ch_options.keys()),
        format_func=lambda x: ch_options[x],
        key="writing_ch_selector",
    )

    chapter = next(ch for ch in chapters if ch['id'] == selected_ch_id)
    parts = get_parts(selected_ch_id)
    research = get_research_items(selected_ch_id)

    # Chapter progress badge
    ch_approved = sum(1 for p in parts if get_approved_written_part(p['id']))
    ch_written = sum(1 for p in parts if get_latest_written_part(p['id']))
    st.caption(f"Este capítulo: {ch_written}/{len(parts)} escritas · {ch_approved}/{len(parts)} aprobadas")

    # ── Botones de generación masiva ──────────────────────────────────────────
    pending_parts = [p for p in parts if not get_latest_written_part(p['id'])]
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        if pending_parts:
            if st.button(
                f"⚡ Generar pendientes ({len(pending_parts)})",
                use_container_width=True,
                type="primary",
            ):
                _run_batch_write(parts, pending_parts, chapter, book, tone, word_bans, research)

    with col_b2:
        if st.button(
            f"🔄 Regenerar todo el capítulo ({len(parts)} partes)",
            use_container_width=True,
        ):
            _run_batch_write(parts, parts, chapter, book, tone, word_bans, research)

    st.divider()

    # ── Partes del capítulo ───────────────────────────────────────────────────
    for part in parts:
        latest = get_latest_written_part(part['id'])
        approved_v = get_approved_written_part(part['id'])

        status_icon = "✅" if approved_v else ("📝" if latest else "○")
        word_est = part.get('palabras_estimadas', 500)

        with st.expander(
            f"{status_icon} Parte {part['num']}: {part['titulo']}  ·  {part['tipo']}  ·  ~{word_est} palabras",
            expanded=(not approved_v and latest is not None),
        ):
            # Metadata
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.caption(f"**Propósito:** {part.get('proposito', '')}")
            with col_m2:
                puntos = part.get('puntos_clave') or []
                if puntos:
                    st.caption("**Puntos clave:** " + " · ".join(puntos))

            # Research assigned to this part
            part_stories = [
                r for r in research
                if r.get('tipo') == 'historia' and r.get('parte_sugerida') == part['num']
            ]
            if part_stories:
                st.caption(f"📖 Historia sugerida: *{part_stories[0].get('protagonista', '')}*")

            st.divider()

            if latest:
                ta_key = f"ta_{part['id']}"
                pending_key = f"_pending_{ta_key}"

                # Apply pending update BEFORE the widget is instantiated
                if pending_key in st.session_state:
                    st.session_state[ta_key] = st.session_state.pop(pending_key)
                elif ta_key not in st.session_state:
                    st.session_state[ta_key] = latest['content']

                content = st.text_area(
                    "Contenido",
                    key=ta_key,
                    height=380,
                    label_visibility="collapsed",
                )

                word_count = len(content.split()) if content else 0
                st.caption(f"~{word_count} palabras  ·  objetivo: ~{word_est}")

                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    if st.button("💾 Guardar edición", key=f"save_{part['id']}", use_container_width=True):
                        save_written_part(part['id'], content)
                        st.rerun()
                with col_a2:
                    if approved_v and approved_v['content'] == content:
                        st.success("✅ Aprobado")
                    else:
                        if st.button(
                            "✅ Aprobar esta versión",
                            key=f"approve_{part['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            wp_id = save_written_part(part['id'], content)
                            approve_written_part(wp_id)
                            st.rerun()
                with col_a3:
                    versions = get_written_versions(part['id'])
                    if len(versions) > 1:
                        with st.popover(f"🕒 {len(versions)} versiones"):
                            for v in versions:
                                approved_badge = " ✅" if v['approved'] else ""
                                label = f"v{v['version']}{approved_badge} — {v['created_at'][:16]}"
                                if v.get('instructions'):
                                    label += f"\n*\"{v['instructions'][:40]}\"*"
                                if st.button(label, key=f"restore_{v['id']}"):
                                    st.session_state[pending_key] = v['content']
                                    st.rerun()

                # Reescribir con instrucciones
                st.markdown("---")
                st.markdown("##### 🔄 Reescribir con instrucciones")
                col_r1, col_r2 = st.columns([3, 1])
                with col_r1:
                    instructions = st.text_input(
                        "Instrucciones para la reescritura",
                        placeholder='ej: "más corto", "menos metáforas", "añade la historia de X aquí"',
                        key=f"instr_{part['id']}",
                        label_visibility="collapsed",
                    )
                with col_r2:
                    if st.button("Reescribir", key=f"rewrite_{part['id']}", use_container_width=True):
                        if instructions.strip():
                            with st.spinner("Reescribiendo…"):
                                new_content = rewrite_part(
                                    content, instructions, part, chapter,
                                    book['core_idea'], tone, word_bans,
                                )
                            save_written_part(part['id'], new_content, instructions)
                            st.session_state[pending_key] = new_content
                            st.rerun()
                        else:
                            st.warning("Escribe instrucciones primero.")

            else:
                # Sin contenido todavía
                st.info("Esta parte aún no tiene texto generado.")
                if st.button(
                    f"✨ Generar '{part['titulo']}'",
                    key=f"gen_{part['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner(f"Escribiendo '{part['titulo']}'…"):
                        written_context = get_chapter_written_context(
                            selected_ch_id, up_to_part_num=part['num']
                        )
                        new_content = write_part(
                            part, chapter, book['core_idea'],
                            tone, word_bans, research, written_context, parts,
                        )
                    save_written_part(part['id'], new_content)
                    st.session_state[f"_pending_ta_{part['id']}"] = new_content
                    st.rerun()

    # ── Navegación ────────────────────────────────────────────────────────────
    st.divider()
    col_n1, col_n2, col_n3 = st.columns([1, 2, 1])
    with col_n1:
        if st.button("← Volver a Investigación"):
            go_to_phase(9)
    with col_n2:
        if approved == total and total > 0:
            st.success("✅ Todas las partes aprobadas. ¡Libro completo!")
        else:
            remaining = total - approved
            st.info(f"Faltan {remaining} partes por aprobar.")
    with col_n3:
        if st.button("Continuar a Cohesión →", type="primary", use_container_width=True):
            go_to_phase(11)


# ─── Phase 11: Style Review ───────────────────────────────────────────────────

def _ensure_ref_embeddings() -> list:
    """Seed corpus and embed references that don't have embeddings yet."""
    from agents.base import embed_text as _embed
    seed_style_references(STYLE_CORPUS)
    refs = get_style_references()
    needs_embed = [r for r in refs if not r['embedding']]
    if needs_embed:
        texts = [r['text'] for r in needs_embed]
        embeddings = _embed(texts)
        for ref, emb in zip(needs_embed, embeddings):
            update_style_reference_embedding(ref['id'], emb)
        refs = get_style_references()
    return refs


def _score_color(score, thresholds=(40, 70)):
    if score is None:
        return "#9E9E9E"
    if score < thresholds[0]:
        return "#F44336"
    if score < thresholds[1]:
        return "#FF9800"
    return "#4CAF50"


def _apply_style_fix(part_obj, chapter, book, tone, word_bans, current_content, fb):
    """Apply priority fix + warnings as a rewrite. Returns (before, after, wp_id_before, wp_id_after)."""
    instructions = fb['priority_fix']
    if fb.get('warnings'):
        instructions += " Además: " + " | ".join(fb['warnings'])
    versions_before = get_written_versions(part_obj['id'])
    wp_id_before = versions_before[0]['id'] if versions_before else None
    new_content = rewrite_part(
        current_content, instructions, part_obj, chapter,
        book['core_idea'], tone, word_bans,
    )
    wp_id_after = save_written_part(part_obj['id'], new_content, instructions)
    st.session_state[f"_pending_ta_{part_obj['id']}"] = new_content
    return current_content, new_content, wp_id_before, wp_id_after


# ─── Phase 11: Cohesión ───────────────────────────────────────────────────────

def phase_cohesion():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    chapters = get_chapters(book_id)
    tone = get_tone_pattern(book_id)
    word_bans = get_active_word_bans(book_id)

    st.title("🔗 Editor de Cohesión de Capítulo")
    if selected_title:
        st.markdown(f"**{selected_title['titulo']}**")
    st.markdown("El Editor de Cohesión toma todas las partes individuales de un capítulo y las consolida en un solo texto fluido, eliminando redundancias y suavizando transiciones.")
    st.divider()

    # Progreso
    ready_chapters = 0
    for ch in chapters:
        parts = get_parts(ch['id'])
        if not parts:
            continue
        approved_parts = [p for p in parts if get_approved_written_part(p['id'])]
        if len(approved_parts) == len(parts):
            ready_chapters += 1

    st.caption(f"{ready_chapters}/{len(chapters)} capítulos listos para cohesión.")
    
    if st.button("⚡ Procesar Capítulos Listos Automáticamente", type="primary", use_container_width=True):
        processed = 0
        bar = st.progress(0)
        status = st.empty()
        
        for i, ch in enumerate(chapters):
            parts = get_parts(ch['id'])
            if not parts:
                continue
            approved_parts = [get_approved_written_part(p['id']) for p in parts]
            if all(approved_parts) and not ch.get('final_content'):
                status.markdown(f"Consolidando Cap. {ch['num']}: {ch['titulo']}...")
                parts_content_list = []
                for p, ap in zip(parts, approved_parts):
                    parts_content_list.append({"titulo": p['titulo'], "tipo": p['tipo'], "content": ap['content']})
                
                final_content = polish_full_chapter(ch, parts_content_list, tone, word_bans, chapters, book['core_idea'])
                update_chapter(ch['id'], {'final_content': final_content})
                processed += 1
            bar.progress((i + 1) / len(chapters))
        
        bar.empty()
        status.empty()
        if processed > 0:
            st.success(f"✅ Se consolidaron {processed} capítulos.")
        else:
            st.info("No se encontraron capítulos nuevos listos para consolidar.")
        st.rerun()
        
    st.divider()

    for ch in chapters:
        parts = get_parts(ch['id'])
        if not parts:
            continue
            
        approved_parts = [get_approved_written_part(p['id']) for p in parts]
        is_ready = len(parts) > 0 and all(approved_parts)
        
        status_icon = "✅" if ch.get('final_content') else ("⏳" if is_ready else "○")
        
        with st.expander(f"{status_icon} Cap. {ch['num']}: {ch['titulo']}", expanded=is_ready and not ch.get('final_content')):
            if not is_ready:
                st.info("Aún faltan partes por aprobar en la fase de Escritura.")
                continue
                
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                st.markdown("### Borrador de Partes")
                raw_draft = ""
                for p, ap in zip(parts, approved_parts):
                    raw_draft += f"**{p['titulo']}**\n\n{ap['content']}\n\n---\n\n"
                st.markdown(f"<div style='height:400px;overflow-y:scroll;padding:10px;border:1px solid #ccc;border-radius:5px;'>{raw_draft}</div>", unsafe_allow_html=True)
                
            with col_b2:
                st.markdown("### Versión Final Pulida")
                final_content = ch.get('final_content', '')

                # ── Selectores de modelo ──────────────────────────────────────
                from config import LLM_MODEL, CLAUDE_MODEL
                sel_col1, sel_col2 = st.columns(2)
                with sel_col1:
                    polish_model = st.selectbox(
                        "🤖 Modelo para generar versión pulida",
                        options=[f"GPT ({LLM_MODEL})", f"Claude ({CLAUDE_MODEL})"],
                        key=f"polish_model_{ch['id']}",
                    )
                with sel_col2:
                    regen_model = st.selectbox(
                        "🤖 Modelo para regenerar según sugerencias",
                        options=[f"Claude ({CLAUDE_MODEL})", f"GPT ({LLM_MODEL})"],
                        key=f"regen_model_{ch['id']}",
                    )
                polish_use_claude = "Claude" in polish_model
                regen_use_claude = "Claude" in regen_model

                ta_key = f"final_ta_{ch['id']}"
                pending_key = f"_pending_{ta_key}"
                if pending_key in st.session_state:
                    st.session_state[ta_key] = st.session_state.pop(pending_key)
                elif ta_key not in st.session_state:
                    st.session_state[ta_key] = final_content

                edited_content = st.text_area("Contenido", key=ta_key, height=400, label_visibility="collapsed")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✨ Generar / Regenerar Cohesión", key=f"coh_{ch['id']}", use_container_width=True):
                        model_label = CLAUDE_MODEL if polish_use_claude else LLM_MODEL
                        with st.spinner(f"Consolidando con {model_label}..."):
                            parts_content_list = [{"titulo": p['titulo'], "tipo": p['tipo'], "content": ap['content']} for p, ap in zip(parts, approved_parts)]
                            new_final = polish_full_chapter(ch, parts_content_list, tone, word_bans, chapters, book['core_idea'], use_claude=polish_use_claude)
                            update_chapter(ch['id'], {'final_content': new_final, 'cohesion_evaluation': ''})
                            st.session_state[pending_key] = new_final
                            st.rerun()
                with col_btn2:
                    if edited_content != final_content:
                        if st.button("💾 Guardar edición", key=f"save_coh_{ch['id']}", type="primary", use_container_width=True):
                            update_chapter(ch['id'], {'final_content': edited_content, 'cohesion_evaluation': ''})
                            st.rerun()

                st.markdown("---")
                st.markdown("#### ⚖️ Evaluación Editorial")
                eval_content = ch.get('cohesion_evaluation', '')
                if eval_content:
                    import re
                    # Limpiar si el LLM devolvió un string que parece JSON literal
                    clean_eval = eval_content
                    if clean_eval.strip().startswith('{') and '"evaluacion"' in clean_eval:
                        try:
                            import json
                            parsed = json.loads(clean_eval)
                            if 'evaluacion' in parsed:
                                clean_eval = parsed['evaluacion']
                        except:
                            # Si falla el parseo, usar regex para extraer el contenido de evaluacion
                            match = re.search(r'"evaluacion"\s*:\s*"(.*?)"\s*}', clean_eval, re.DOTALL)
                            if match:
                                clean_eval = match.group(1).replace('\\n', '\n')
                    
                    # Limpiar literales \n si el LLM los envió como texto crudo
                    clean_eval = clean_eval.replace('\\n', '\n')
                    st.info(clean_eval)
                    
                    if st.button("🔄 REGENERAR SEGÚN SUGERENCIAS", key=f"regen_{ch['id']}", type="secondary", use_container_width=True):
                        from config import CLAUDE_MODEL, LLM_MODEL
                        regen_label = CLAUDE_MODEL if regen_use_claude else LLM_MODEL
                        with st.spinner(f"Regenerando capítulo según la evaluación usando {regen_label}..."):
                            try:
                                new_final = regenerate_consolidated_chapter(
                                    content=final_content,
                                    evaluation=clean_eval,
                                    tone=tone,
                                    word_bans=word_bans,
                                    book_idea=book['core_idea'],
                                    use_claude=regen_use_claude,
                                )
                                update_chapter(ch['id'], {'final_content': new_final, 'cohesion_evaluation': ''})
                                st.session_state[pending_key] = new_final
                                st.rerun()
                            except Exception as e:
                                st.error(f"ERROR: Falló la regeneración con {regen_label}. Detalles: {str(e)}")
                else:
                    st.caption("Aún no has evaluado esta versión del capítulo.")
                
                if final_content and st.button("🔍 Evaluar Capítulo", key=f"eval_{ch['id']}", use_container_width=True):
                    from config import EVALUATION_LLM_MODEL
                    with st.spinner(f"Evaluando rigor y calidad editorial usando {EVALUATION_LLM_MODEL}..."):
                        from agents.cohesion_agent import evaluate_consolidated_chapter
                        new_eval = evaluate_consolidated_chapter(final_content)
                        update_chapter(ch['id'], {'cohesion_evaluation': new_eval})
                        st.rerun()

    st.divider()
    col_n1, col_n2, col_n3 = st.columns([1, 2, 1])
    with col_n1:
        if st.button("← Volver a Escritura"):
            go_to_phase(10)
    with col_n3:
        if st.button("Revisión de Estilo →", type="primary", use_container_width=True):
            go_to_phase(12)


# ─── Phase 12: Style Review ───────────────────────────────────────────────────

def phase_style_review():
    book_id = st.session_state.book_id
    book = get_book(book_id)
    selected_title = get_selected_title(book_id)
    chapters = get_chapters(book_id)
    tone = get_tone_pattern(book_id)
    word_bans = get_active_word_bans(book_id)

    st.title("🔎 Revisión de Estilo")
    if selected_title:
        st.markdown(f"**{selected_title['titulo']}**")
    if not tone or not tone.get('parrafo_ancla_aprobado'):
        st.warning("⚠️ Sin párrafo ancla aprobado (Fase 8). Análisis de deriva de tono no disponible.")
    st.divider()

    # ── Selector de capítulo ──────────────────────────────────────────────────
    ch_options = {ch['id']: f"Cap. {ch['num']}: {ch['titulo']}" for ch in chapters}
    selected_ch_id = st.selectbox(
        "Capítulo",
        options=list(ch_options.keys()),
        format_func=lambda x: ch_options[x],
        key="style_ch_selector",
    )
    chapter = next(ch for ch in chapters if ch['id'] == selected_ch_id)
    parts = get_parts(selected_ch_id)

    written_map = {}
    for p in parts:
        latest = get_latest_written_part(p['id'])
        if latest:
            written_map[p['id']] = latest['content']
    written_count = len(written_map)

    review = get_style_review(selected_ch_id)
    corrections_key = f"style_corrections_{selected_ch_id}"

    # ── Barra de acciones ─────────────────────────────────────────────────────
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        if st.button("🔬 Analizar capítulo", type="primary", use_container_width=True, disabled=written_count == 0):
            with st.spinner("Preparando referencias de estilo…"):
                ref_embeddings = _ensure_ref_embeddings()
            with st.spinner(f"Analizando {written_count} partes…"):
                results = review_chapter(chapter, parts, written_map, tone, ref_embeddings)
            save_style_review(book_id, selected_ch_id, results)
            st.session_state.pop(corrections_key, None)
            st.rerun()
    with col_a2:
        has_review = review is not None
        if st.button("🔧 Corregir todo", use_container_width=True, disabled=not has_review):
            parts_data = review['results'].get('parts', [])
            fixable = [pr for pr in parts_data if pr.get('feedback', {}).get('priority_fix')]
            if not fixable:
                st.info("No hay correcciones pendientes.")
            else:
                corrections = []
                bar = st.progress(0)
                status = st.empty()
                for i, pr in enumerate(fixable):
                    status.markdown(f"Corrigiendo {pr['part_num']}/{len(parts)}: *{pr['part_titulo']}*…")
                    bar.progress(i / len(fixable))
                    part_obj = next((p for p in parts if p['num'] == pr['part_num']), None)
                    if not part_obj:
                        continue
                    before, after, wp_before, wp_after = _apply_style_fix(
                        part_obj, chapter, book, tone, word_bans,
                        written_map.get(part_obj['id'], ''), pr['feedback']
                    )
                    corrections.append({
                        'part_id': part_obj['id'], 'part_num': pr['part_num'],
                        'titulo': pr['part_titulo'], 'tipo': pr['part_tipo'],
                        'before': before, 'after': after,
                        'wp_id_before': wp_before, 'wp_id_after': wp_after,
                    })
                    bar.progress((i + 1) / len(fixable))
                bar.empty()
                status.empty()
                st.session_state[corrections_key] = corrections
                st.rerun()
    with col_a3:
        if review:
            st.caption(f"Analizado: {review['created_at'][:16]}")
        else:
            st.caption(f"{written_count}/{len(parts)} partes escritas")

    # ── Panel de comparación antes/después ────────────────────────────────────
    corrections = st.session_state.get(corrections_key, [])
    if corrections:
        st.markdown(f"### ✏️ {len(corrections)} partes corregidas — revisa los cambios")
        st.caption("Acepta cada corrección para mantenerla, o reviértela para volver al texto anterior.")

        for c in corrections:
            before_preview = c['before'][:500] + "…" if len(c['before']) > 500 else c['before']
            after_preview = c['after'][:500] + "…" if len(c['after']) > 500 else c['after']

            with st.expander(f"Parte {c['part_num']}: {c['titulo']} [{c['tipo'].upper()}]", expanded=True):
                col_b, col_a = st.columns(2)
                with col_b:
                    st.markdown("**Antes**")
                    st.markdown(
                        f"<div style='background:#fff3e0;border-left:3px solid #FF9800;padding:10px;border-radius:4px;font-size:0.9em;white-space:pre-wrap'>{before_preview}</div>",
                        unsafe_allow_html=True,
                    )
                with col_a:
                    st.markdown("**Después**")
                    st.markdown(
                        f"<div style='background:#e8f5e9;border-left:3px solid #4CAF50;padding:10px;border-radius:4px;font-size:0.9em;white-space:pre-wrap'>{after_preview}</div>",
                        unsafe_allow_html=True,
                    )
                col_acc, col_rev = st.columns(2)
                with col_acc:
                    if st.button("✅ Aceptar corrección", key=f"acc_{c['part_id']}", use_container_width=True, type="primary"):
                        corrections[:] = [x for x in corrections if x['part_id'] != c['part_id']]
                        st.session_state[corrections_key] = corrections
                        st.rerun()
                with col_rev:
                    if st.button("↩️ Revertir al original", key=f"rev_{c['part_id']}", use_container_width=True):
                        save_written_part(c['part_id'], c['before'], 'revertido')
                        st.session_state[f"_pending_ta_{c['part_id']}"] = c['before']
                        corrections[:] = [x for x in corrections if x['part_id'] != c['part_id']]
                        st.session_state[corrections_key] = corrections
                        st.rerun()

        if not corrections:
            st.session_state.pop(corrections_key, None)
        st.divider()

    # ── Resultados del análisis ───────────────────────────────────────────────
    if not review:
        st.info("Pulsa **Analizar capítulo** para ver el informe de estilo.")
    else:
        data = review['results']
        avg_rhythm = data.get('avg_rhythm_score')
        avg_drift = data.get('avg_drift_score')
        clone_pairs = data.get('clone_openings', [])

        # Summary
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            c = _score_color(avg_rhythm)
            st.markdown(f"<div style='background:{c}22;border-left:4px solid {c};padding:10px;border-radius:4px'><strong>Ritmo promedio</strong><br><span style='font-size:1.8em;color:{c}'>{avg_rhythm or '—'}</span>/100</div>", unsafe_allow_html=True)
        with col_s2:
            dc = _score_color(100 - avg_drift if avg_drift else None, (20, 40))
            st.markdown(f"<div style='background:{dc}22;border-left:4px solid {dc};padding:10px;border-radius:4px'><strong>Deriva de tono</strong><br><span style='font-size:1.8em;color:{dc}'>{f'{avg_drift}%' if avg_drift is not None else '—'}</span></div>", unsafe_allow_html=True)
        with col_s3:
            cc = "#F44336" if clone_pairs else "#4CAF50"
            st.markdown(f"<div style='background:{cc}22;border-left:4px solid {cc};padding:10px;border-radius:4px'><strong>Aperturas clónicas</strong><br><span style='font-size:1.4em;color:{cc}'>{f'{len(clone_pairs)} par(es)' if clone_pairs else 'Sin clones'}</span></div>", unsafe_allow_html=True)

        if clone_pairs:
            st.warning("**Aperturas similares:** " + " · ".join(f"Parte {c['part_a']} ↔ {c['part_b']} ({int(c['similarity']*100)}%)" for c in clone_pairs))

        st.divider()

        # Per-part
        for pr in data.get('parts', []):
            struct = pr['structural']
            sem = pr['semantic']
            fb = pr.get('feedback', {})
            rhythm = struct.get('rhythm_score')
            warnings_list = fb.get('warnings', [])
            rcolor = _score_color(rhythm)
            has_fix = bool(fb.get('priority_fix'))

            header = f"Parte {pr['part_num']}: {pr['part_titulo']}  ·  [{pr['part_tipo'].upper()}]"
            if rhythm is not None:
                header += f"  —  Ritmo {rhythm}/100"

            with st.expander(header, expanded=has_fix and rhythm is not None and rhythm < 60):
                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Ritmo", f"{rhythm}/100" if rhythm is not None else "—")
                col2.metric("Frases", struct.get('sentence_count', '—'))
                col3.metric("Prom. pal/frase", struct.get('avg_words', '—'))
                col4.metric("Desv. est.", struct.get('std_dev', '—'))

                if rhythm is not None:
                    st.markdown(f"<div style='background:#eee;border-radius:4px;height:6px;margin:4px 0'><div style='background:{rcolor};width:{rhythm}%;height:6px;border-radius:4px'></div></div>", unsafe_allow_html=True)

                if sem.get('anchor_similarity') is not None:
                    sim_pct = int(sem['anchor_similarity'] * 100)
                    dc2 = _score_color(sim_pct, (60, 75))
                    st.caption(f"Similitud con ancla: {sim_pct}%")
                    st.markdown(f"<div style='background:#eee;border-radius:4px;height:4px;margin:2px 0'><div style='background:{dc2};width:{sim_pct}%;height:4px;border-radius:4px'></div></div>", unsafe_allow_html=True)

                if sem.get('nearest_ref_label'):
                    st.caption(f"Estilo más cercano: *{sem['nearest_ref_label']}*")

                if warnings_list:
                    for w in warnings_list:
                        st.warning(f"⚠️ {w}")

                if fb.get('feedback'):
                    st.info(f"📝 {fb['feedback']}")

                if has_fix:
                    st.error(f"🎯 **Corrección prioritaria:** {fb['priority_fix']}")
                    part_obj = next((p for p in parts if p['num'] == pr['part_num']), None)
                    if part_obj and st.button(
                        f"🔧 Corregir esta parte",
                        key=f"stylefix_{pr['part_id']}",
                        use_container_width=True,
                    ):
                        with st.spinner("Corrigiendo…"):
                            before, after, wp_b, wp_a = _apply_style_fix(
                                part_obj, chapter, book, tone, word_bans,
                                written_map.get(part_obj['id'], ''), fb
                            )
                        entry = {
                            'part_id': part_obj['id'], 'part_num': pr['part_num'],
                            'titulo': pr['part_titulo'], 'tipo': pr['part_tipo'],
                            'before': before, 'after': after,
                            'wp_id_before': wp_b, 'wp_id_after': wp_a,
                        }
                        existing_corr = st.session_state.get(corrections_key, [])
                        existing_corr = [x for x in existing_corr if x['part_id'] != part_obj['id']]
                        existing_corr.append(entry)
                        st.session_state[corrections_key] = existing_corr
                        st.rerun()

    st.divider()
    if st.button("← Volver a Cohesión"):
        go_to_phase(11)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    init_db()
    init_state()

    # Validar API Keys
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY no configurada. Configúrala en el archivo `.env` o como variable de entorno.")
    if not os.environ.get("TAVILY_API_KEY"):
        st.warning("⚠️ TAVILY_API_KEY no configurada. La fase de investigación no funcionará.")

    render_sidebar()

    if st.session_state.book_id is None and st.session_state.phase > 0:
        st.session_state.phase = 0

    renderers = [
        phase_idea, phase_titles, phase_structure, phase_chapters,
        phase_parts, phase_overlap, phase_final,
        phase_word_ban, phase_research, phase_tone_pattern,
        phase_writing, phase_cohesion, phase_style_review,
    ]
    renderers[st.session_state.phase]()


if __name__ == "__main__":
    main()
