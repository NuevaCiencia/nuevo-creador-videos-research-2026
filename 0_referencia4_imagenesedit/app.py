import streamlit as st
from pathlib import Path
import shutil
import importlib
import zipfile
import subprocess
import sys
from datetime import datetime
from PIL import Image

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Imágenes Educativas",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  /* fondo general */
  .stApp { background: #ffffff; }
  .block-container { padding: 2rem 2.5rem 4rem; max-width: 1100px; }

  /* quitar borde del file uploader */
  [data-testid="stFileUploadDropzone"] {
    background: #f8fafc !important;
    border: 2px dashed #cbd5e1 !important;
    border-radius: 12px !important;
  }

  /* botones primarios */
  .stButton > button[kind="primary"] {
    background: #6366f1 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.65rem 1.5rem !important;
    color: white !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #4f46e5 !important;
  }

  /* botones secundarios */
  .stButton > button[kind="secondary"] {
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #475569 !important;
    font-weight: 600 !important;
  }

  /* botón danger */
  .stButton > button[kind="secondary"].danger-btn {
    background: #fef2f2 !important;
    border: 1px solid #fca5a5 !important;
    color: #dc2626 !important;
  }

  /* inputs */
  input[type="text"] {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #1e293b !important;
  }

  /* separadores */
  hr { border-color: #e2e8f0 !important; }

  /* caption */
  .stCaption { color: #64748b !important; }

  /* métricas */
  [data-testid="stMetricValue"] { color: #1e293b !important; font-weight: 700; }
  [data-testid="stMetricLabel"] { color: #64748b !important; }
</style>
""", unsafe_allow_html=True)

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
INPUT_SPLIT = BASE_DIR / "imagenes_iniciales" / "split"
INPUT_FULL  = BASE_DIR / "imagenes_iniciales" / "full"
OUT_SPLIT   = BASE_DIR / "imagenes_procesadas" / "split"
OUT_FULL    = BASE_DIR / "imagenes_procesadas" / "full"
DEPRECATED  = BASE_DIR / "deprecated"

EXTS          = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
CANVAS_SPLIT  = (960, 1080)
CANVAS_FULL   = (1920, 1080)
PROYECTOS_DIR = Path("/Users/javier/Documents/DEVELOPER/creador-videos-mac-investigacion/proyectos")


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_config():
    try:
        import config as cfg
        importlib.reload(cfg)
        proyectos_dir = Path(getattr(cfg, "PROYECTOS_DIR", str(PROYECTOS_DIR)))
        proyecto      = getattr(cfg, "PROYECTO", "")
        return proyectos_dir, proyecto
    except Exception:
        return PROYECTOS_DIR, ""


def save_config(proyectos_dir: Path, proyecto: str):
    with open(BASE_DIR / "config.py", "w", encoding="utf-8") as f:
        f.write(f'PROYECTOS_DIR = "{proyectos_dir}"\n')
        f.write(f'PROYECTO = "{proyecto}"\n')


def get_proyectos(proyectos_dir: Path):
    if not proyectos_dir.exists():
        return []
    return sorted(p.name for p in proyectos_dir.iterdir() if p.is_dir())


def dest_images(proyectos_dir: Path, proyecto: str) -> Path:
    return proyectos_dir / proyecto / "assets" / "images"


def get_files(folder: Path):
    if not folder.exists():
        return []
    return sorted(f for f in folder.iterdir() if f.suffix.lower() in EXTS)


def centrar_imagen(img, canvas_size):
    cw, ch = canvas_size
    iw, ih = img.size
    scale = min(cw / iw, ch / ih)
    img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
    canvas = Image.new("RGB", canvas_size, (255, 255, 255))
    iw, ih = img.size
    mask = img.split()[-1] if img.mode in ("RGBA", "LA") else None
    canvas.paste(img, ((cw - iw) // 2, (ch - ih) // 2), mask=mask)
    return canvas


def badge(text, color):
    return (
        f'<span style="background:{color}22; color:{color}; border:1px solid {color}55; '
        f'border-radius:6px; padding:2px 10px; font-size:0.8rem; font-weight:700">'
        f'{text}</span>'
    )


def section_header(icon, title, subtitle=""):
    st.markdown(
        f'<div style="margin:2rem 0 1rem">'
        f'<span style="font-size:1.5rem">{icon}</span>'
        f'<span style="font-size:1.2rem; font-weight:800; color:#1e293b; margin-left:10px">{title}</span>'
        f'{"<span style=color:#64748b;font-size:0.9rem;margin-left:10px> " + subtitle + "</span>" if subtitle else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def thumbnail_grid(files, cols=4, max_show=12):
    if not files:
        st.markdown(
            '<div style="text-align:center; color:#94a3b8; padding:32px 0; '
            'border:2px dashed #e2e8f0; border-radius:12px; margin:8px 0">'
            '📭 &nbsp; Sin imágenes cargadas</div>',
            unsafe_allow_html=True,
        )
        return

    display = files[:max_show]
    grid = st.columns(cols)
    for i, f in enumerate(display):
        with grid[i % cols]:
            try:
                img = Image.open(f)
                img.thumbnail((240, 240))
                st.image(img, use_container_width=True)
                st.caption(f.name)
            except Exception:
                st.warning(f.name)

    if len(files) > max_show:
        st.caption(f"... y {len(files) - max_show} archivo(s) más")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#f8fafc,#f1f5f9);
     border:1px solid #e2e8f0; border-radius:16px; padding:28px 32px; margin-bottom:16px">
  <div style="font-size:2rem; font-weight:900; color:#1e293b; letter-spacing:-0.5px">
    🖼️ &nbsp;Imágenes Educativas
  </div>
  <div style="color:#64748b; margin-top:4px; font-size:0.95rem">
    Pipeline de procesado para video educativo
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROYECTO ACTIVO (top bar)
# ══════════════════════════════════════════════════════════════════════════════
cfg_proyectos_dir, cfg_proyecto = load_config()
proyectos = get_proyectos(cfg_proyectos_dir)

proyecto_activo = cfg_proyecto

st.markdown(
    '<div style="font-weight:700; color:#6366f1; font-size:0.8rem; '
    'text-transform:uppercase; letter-spacing:0.6px; margin-bottom:6px">'
    '📁 &nbsp;Proyecto activo</div>',
    unsafe_allow_html=True,
)

if not proyectos:
    st.warning(f"No se encontraron proyectos en `{cfg_proyectos_dir}`")
else:
    default_idx = proyectos.index(cfg_proyecto) if cfg_proyecto in proyectos else 0
    col_proj, col_dest_top = st.columns([2, 4])
    with col_proj:
        proyecto_activo = st.selectbox(
            "Proyecto", proyectos, index=default_idx,
            key="proyecto_selector", label_visibility="collapsed",
        )
    with col_dest_top:
        dest_activa = dest_images(cfg_proyectos_dir, proyecto_activo)
        dest_activa.mkdir(parents=True, exist_ok=True)
        st.markdown(
            f'<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; '
            f'padding:9px 14px; font-family:monospace; font-size:0.85rem; color:#475569; '
            f'margin-top:2px">{dest_activa}</div>',
            unsafe_allow_html=True,
        )

    if proyecto_activo != cfg_proyecto:
        save_config(cfg_proyectos_dir, proyecto_activo)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Estado global (procesadas y métricas se actualizan al final) ───────────────
split_files_out = get_files(OUT_SPLIT)
full_files_out  = get_files(OUT_FULL)

metrics_placeholder = st.empty()
st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1 · CARGAR
# ══════════════════════════════════════════════════════════════════════════════

# Inicializar contador para resetear uploaders
if "upload_reset_key" not in st.session_state:
    st.session_state["upload_reset_key"] = 0

col_header, col_clear_btn = st.columns([5, 1])
with col_header:
    section_header("📥", "Cargar imágenes", "arrastra o selecciona")

# Leer archivos antes para saber si hay algo cargado
split_files_in_check = get_files(INPUT_SPLIT)
full_files_in_check  = get_files(INPUT_FULL)
hay_cargado = bool(split_files_in_check or full_files_in_check)

with col_clear_btn:
    st.markdown("<div style='padding-top:1.6rem'>", unsafe_allow_html=True)
    if st.button(
        "💾  Backup y limpiar",
        key="btn_clear_loaded",
        type="secondary",
        disabled=not hay_cargado,
        use_container_width=True,
    ):
        st.session_state["confirm_clear"] = True
    st.markdown("</div>", unsafe_allow_html=True)

# Confirmación de backup + limpieza
if st.session_state.get("confirm_clear"):
    total_a_limpiar = len(split_files_in_check) + len(full_files_in_check)
    st.warning(
        f"⚠️  Se creará un ZIP de respaldo con **{total_a_limpiar} archivo(s)** "
        f"y se vaciarán todas las carpetas de trabajo. ¿Confirmar?"
    )
    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button("✅  Sí, backup y limpiar", key="clear_yes"):
        DEPRECATED.mkdir(exist_ok=True)
        fecha    = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = DEPRECATED / f"backup_imagenes_videos_{fecha}.zip"
        CARPETAS_BACKUP = ["imagenes_iniciales", "imagenes_procesadas"]
        with st.spinner("Creando backup…"):
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for carpeta in CARPETAS_BACKUP:
                    ruta = BASE_DIR / carpeta
                    if not ruta.exists():
                        continue
                    for archivo in ruta.rglob("*"):
                        if archivo.is_file():
                            zf.write(archivo, archivo.relative_to(BASE_DIR))
            for carpeta in CARPETAS_BACKUP:
                ruta = BASE_DIR / carpeta
                if ruta.exists():
                    for archivo in ruta.rglob("*"):
                        if archivo.is_file():
                            archivo.unlink()
        st.session_state["confirm_clear"] = False
        st.session_state["upload_reset_key"] += 1
        st.rerun()
    if c2.button("❌  Cancelar", key="clear_no"):
        st.session_state["confirm_clear"] = False
        st.rerun()

reset_k = st.session_state["upload_reset_key"]
col_s, col_f = st.columns(2, gap="large")

# ── SPLIT ──────────────────────────────────────────────────────────────────────
with col_s:
    uploaded_split = st.file_uploader(
        "split_uploader",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
        accept_multiple_files=True,
        key=f"upload_split_{reset_k}",
        label_visibility="collapsed",
    )
    if uploaded_split:
        INPUT_SPLIT.mkdir(parents=True, exist_ok=True)
        for f in uploaded_split:
            (INPUT_SPLIT / f.name).write_bytes(f.getvalue())

    split_files_in = get_files(INPUT_SPLIT)

    st.markdown(
        f'<div style="background:#f0fdf4; border:1.5px solid #16a34a; border-radius:12px; '
        f'padding:14px 18px; margin-bottom:12px; display:flex; align-items:center; gap:12px">'
        f'<span style="font-size:1.4rem">📐</span>'
        f'<div><div style="font-weight:800; color:#15803d; font-size:1.1rem">SPLIT</div>'
        f'<div style="color:#64748b; font-size:0.8rem">960 × 1080 px · media pantalla</div></div>'
        f'{badge(str(len(split_files_in)) + " archivo(s)", "#16a34a")}</div>',
        unsafe_allow_html=True,
    )
    thumbnail_grid(split_files_in)

# ── FULL ───────────────────────────────────────────────────────────────────────
with col_f:
    uploaded_full = st.file_uploader(
        "full_uploader",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
        accept_multiple_files=True,
        key=f"upload_full_{reset_k}",
        label_visibility="collapsed",
    )
    if uploaded_full:
        INPUT_FULL.mkdir(parents=True, exist_ok=True)
        for f in uploaded_full:
            (INPUT_FULL / f.name).write_bytes(f.getvalue())

    full_files_in = get_files(INPUT_FULL)

    st.markdown(
        f'<div style="background:#eff6ff; border:1.5px solid #2563eb; border-radius:12px; '
        f'padding:14px 18px; margin-bottom:12px; display:flex; align-items:center; gap:12px">'
        f'<span style="font-size:1.4rem">🖥️</span>'
        f'<div><div style="font-weight:800; color:#1d4ed8; font-size:1.1rem">FULL</div>'
        f'<div style="color:#64748b; font-size:0.8rem">1920 × 1080 px · pantalla completa</div></div>'
        f'{badge(str(len(full_files_in)) + " archivo(s)", "#2563eb")}</div>',
        unsafe_allow_html=True,
    )
    thumbnail_grid(full_files_in)

# Métricas actualizadas con los valores reales del disco
with metrics_placeholder.container():
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SPLIT cargadas",   len(split_files_in))
    m2.metric("FULL cargadas",    len(full_files_in))
    m3.metric("SPLIT procesadas", len(split_files_out))
    m4.metric("FULL procesadas",  len(full_files_out))

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2 · PROCESAR
# ══════════════════════════════════════════════════════════════════════════════
section_header("⚙️", "Procesar imágenes", "escala y centra sobre el canvas")

hay_algo = split_files_in or full_files_in

if st.button(
    "⚙️  PROCESAR TODO",
    use_container_width=True,
    type="primary",
    disabled=not hay_algo,
):
    todos = []
    for in_dir, out_dir, canvas in [
        (INPUT_SPLIT, OUT_SPLIT, CANVAS_SPLIT),
        (INPUT_FULL,  OUT_FULL,  CANVAS_FULL),
    ]:
        for f in get_files(in_dir):
            todos.append((f, out_dir, canvas))

    if not todos:
        st.warning("No había imágenes para procesar.")
    else:
        barra    = st.progress(0, text="Iniciando…")
        estado   = st.empty()
        errores  = []
        total    = len(todos)

        for i, (f, out_dir, canvas) in enumerate(todos):
            out_dir.mkdir(parents=True, exist_ok=True)
            barra.progress((i) / total, text=f"Procesando {i+1}/{total}: {f.name}")
            estado.caption(f"⚙️ {f.name}")
            try:
                img      = Image.open(f)
                out_name = f.stem[:4] + ".png"
                centrar_imagen(img, canvas).save(out_dir / out_name, "PNG", optimize=True)
            except Exception as e:
                errores.append(f"{f.name}: {e}")

        barra.progress(1.0, text="¡Listo!")
        estado.empty()

        if errores:
            st.error("Errores:\n" + "\n".join(errores))
        else:
            st.success(f"✅ {total} imagen(es) procesada(s) correctamente")
        st.rerun()

if not hay_algo:
    st.caption("Carga imágenes en el paso 1 para habilitar el procesado.")

# Vista previa de procesadas
if split_files_out or full_files_out:
    with st.expander(f"👁  Ver imágenes procesadas ({len(split_files_out)} SPLIT · {len(full_files_out)} FULL)"):
        tab_s, tab_f = st.tabs(["SPLIT", "FULL"])
        with tab_s:
            thumbnail_grid(split_files_out)
        with tab_f:
            thumbnail_grid(full_files_out)

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 3 · EXPORTAR
# ══════════════════════════════════════════════════════════════════════════════
section_header("📤", "Exportar al proyecto", "copia las procesadas al proyecto activo")

if not proyectos:
    st.warning(f"No se encontraron proyectos en `{cfg_proyectos_dir}`")
else:
    dest = dest_activa  # ya calculado arriba con el proyecto_activo del top bar

    ex_s, ex_f = st.columns(2, gap="large")

    def do_export(files, dest_dir, modo):
        conflictos = [f for f in files if (dest_dir / f.name).exists()]
        if conflictos:
            st.session_state["_export_pending"] = modo
            st.session_state["_export_conflictos"] = [f.name for f in conflictos]
        else:
            for f in files:
                shutil.copy2(f, dest_dir / f.name)
            st.success(f"✅ {len(files)} archivo(s) exportado(s) → {dest_dir}")

    with ex_s:
        st.markdown(
            '<div style="font-weight:700; color:#15803d; margin-bottom:6px">📐 SPLIT</div>',
            unsafe_allow_html=True,
        )
        if st.button("📤  Exportar SPLIT", use_container_width=True,
                     disabled=not split_files_out, key="btn_exp_split"):
            do_export(split_files_out, dest, "split")
        if not split_files_out:
            st.caption("Procesa primero las imágenes SPLIT.")

    with ex_f:
        st.markdown(
            '<div style="font-weight:700; color:#1d4ed8; margin-bottom:6px">🖥️ FULL</div>',
            unsafe_allow_html=True,
        )
        if st.button("📤  Exportar FULL", use_container_width=True,
                     disabled=not full_files_out, key="btn_exp_full"):
            do_export(full_files_out, dest, "full")
        if not full_files_out:
            st.caption("Procesa primero las imágenes FULL.")

    # ── Confirmación de sobreescritura ─────────────────────────────────────────
    if st.session_state.get("_export_pending"):
        modo       = st.session_state["_export_pending"]
        conflictos = st.session_state["_export_conflictos"]
        files      = split_files_out if modo == "split" else full_files_out

        st.warning(
            f"⚠️  **{len(conflictos)} archivo(s)** ya existen en el destino:\n\n"
            + "  ".join(f"`{n}`" for n in conflictos[:6])
            + ("  …" if len(conflictos) > 6 else "")
            + "\n\n¿Reescribir encima?"
        )
        c1, c2, _ = st.columns([1, 1, 3])
        if c1.button("✅  Sí, reescribir", key="overwrite_yes"):
            for f in files:
                shutil.copy2(f, dest / f.name)
            st.success(f"✅ {len(files)} archivo(s) exportado(s) → {dest}")
            st.session_state.pop("_export_pending")
            st.session_state.pop("_export_conflictos")
            st.rerun()
        if c2.button("❌  Cancelar", key="overwrite_no"):
            st.session_state.pop("_export_pending")
            st.session_state.pop("_export_conflictos")
            st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4 · BACKUP
# ══════════════════════════════════════════════════════════════════════════════
section_header("💾", "Backup", "comprime todo y vacía las carpetas")

total_archivos = len(split_files_in) + len(full_files_in) + len(split_files_out) + len(full_files_out)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.markdown(
        f'<div style="color:#475569; padding:10px 0">'
        f'Empaqueta <b style="color:#e2e8f0">{total_archivos} archivo(s)</b> en un ZIP con timestamp '
        f'y vacía las carpetas de trabajo.</div>',
        unsafe_allow_html=True,
    )
with col_btn:
    if st.button("💾  HACER BACKUP", use_container_width=True,
                 disabled=total_archivos == 0):
        st.session_state["confirm_backup"] = True

if st.session_state.get("confirm_backup"):
    st.warning("⚠️  Se creará el ZIP y **se vaciarán** las carpetas. ¿Confirmar?")
    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button("✅  Sí, hacer backup", key="backup_yes"):
        DEPRECATED.mkdir(exist_ok=True)
        fecha    = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = DEPRECATED / f"backup_imagenes_videos_{fecha}.zip"
        CARPETAS = ["imagenes_iniciales", "imagenes_procesadas"]

        with st.spinner("Creando backup…"):
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for carpeta in CARPETAS:
                    ruta = BASE_DIR / carpeta
                    if not ruta.exists():
                        continue
                    for archivo in ruta.rglob("*"):
                        if archivo.is_file():
                            zf.write(archivo, archivo.relative_to(BASE_DIR))
            for carpeta in CARPETAS:
                ruta = BASE_DIR / carpeta
                if ruta.exists():
                    for archivo in ruta.rglob("*"):
                        if archivo.is_file():
                            archivo.unlink()

        st.success(f"✅ Backup creado: **{zip_path.name}**")
        st.session_state["confirm_backup"] = False
        st.rerun()

    if c2.button("❌  Cancelar", key="backup_no"):
        st.session_state["confirm_backup"] = False
        st.rerun()
