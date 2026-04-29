"""
remotion_agent.py — Renderiza assets REM*.mp4 usando Remotion (Node.js).

Lee los configs remotion ya generados por visual_agent en recursos_json,
ejecuta `npx remotion render` por cada asset, guarda en app/assets/videos/.
"""
import json
import os
import shutil
import subprocess
import tempfile
import traceback
from pathlib import Path

FPS = 30

# Short name → Remotion composition ID
TEMPLATE_MAP = {
    "TypeWriter":  "NAR-TypeWriter-Hacker",
    "MindMap":     "FLOW-MindMap",
    "LinearSteps": "FLOW-LinearSteps",
    "FlipCards":   "CLASS-FlipCards",
}

# Path to the remotion project (repo root / remotion /)
REMOTION_DIR = Path(__file__).parent.parent.parent / "remotion"


def _find_npx() -> str:
    """Locate npx — checks PATH first, then common nvm locations."""
    npx = shutil.which("npx")
    if npx:
        return npx
    nvm_base = Path.home() / ".nvm" / "versions" / "node"
    if nvm_base.exists():
        candidates = sorted(nvm_base.glob("*/bin/npx"), reverse=True)
        if candidates:
            return str(candidates[0])
    raise FileNotFoundError("npx not found — install Node.js")


_PREFIX_CANONICAL = {
    "//": "// ", "$ ": "$ ", "$": "$ ",
    "→": "→ ",  ">": "> ",  "✓": "✓ ",
    "!": "! ",  "# ": "// ",
}

def _normalize_props(template: str, data: dict) -> dict:
    """Fix AI-generated props to match each template's exact schema."""
    import copy
    data = copy.deepcopy(data)

    if template == "TypeWriter":
        lines = data.get("lines", [])
        speed = 1.8          # chars per frame (template default)
        gap   = 18           # frames between lines finishing and next starting
        cursor = 10          # initial delay before first line
        cumulative = cursor
        for ln in lines:
            # Fix prefix: ensure trailing space and canonical form
            p = str(ln.get("prefix", "$ ")).strip()
            ln["prefix"] = _PREFIX_CANONICAL.get(p, p + " " if not p.endswith(" ") else p)
            # Recalculate cumulative delay (ignore AI-generated delay)
            ln["delay"] = cumulative
            ln["speed"] = speed
            text_len = len(str(ln.get("text", "")))
            cumulative += int(text_len / speed) + gap

    return data


def _parse_frames(duration_str: str) -> int:
    """'mm:ss' or 'ss' → frame count at 30 fps."""
    parts = str(duration_str).split(":")
    if len(parts) == 2:
        total_s = int(parts[0]) * 60 + int(parts[1])
    else:
        total_s = int(parts[0])
    return max(30, total_s * FPS)


def _ensure_deps(npx: str) -> None:
    """Run npm install if node_modules is missing."""
    if not (REMOTION_DIR / "node_modules").exists():
        subprocess.run(
            ["npm", "install", "--prefer-offline"],
            cwd=REMOTION_DIR,
            check=True,
            timeout=300,
        )


def _render_one(npx: str, comp_id: str, frames: int, props: dict, output_path: Path) -> None:
    """Render a single Remotion composition to output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(props, f, ensure_ascii=False)
        props_file = f.name
    try:
        result = subprocess.run(
            [
                npx, "remotion", "render",
                "src/index.tsx",
                comp_id,
                "--props",    props_file,
                "--duration", str(frames),
                "--output",   str(output_path),
            ],
            cwd=REMOTION_DIR,
            check=False,
            timeout=600,
            capture_output=True,
            text=True,
            env={**os.environ, "NODE_ENV": "production"},
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Remotion exit {result.returncode}\n"
                f"STDOUT:\n{result.stdout[-3000:]}\n"
                f"STDERR:\n{result.stderr[-3000:]}"
            )
    finally:
        os.unlink(props_file)


def run_remotion(class_id: int) -> None:
    """Entry point — called from background thread."""
    from database import SessionLocal
    import models

    def _update(status: str, pct: int, msg: str, error: str | None = None) -> None:
        db = SessionLocal()
        try:
            row = db.query(models.ClassRemotionRender).filter(
                models.ClassRemotionRender.class_id == class_id
            ).first()
            if row:
                row.status   = status
                row.progress = pct
                row.phase    = msg
                if error is not None:
                    row.error = error
                db.commit()
        finally:
            db.close()

    try:
        # ── Load remotion configs from recursos_json ──────────────────────────
        db = SessionLocal()
        try:
            guion = db.query(models.ClassGuionConsolidado).filter(
                models.ClassGuionConsolidado.class_id == class_id
            ).first()
            recursos_json = guion.recursos_json if guion else None
        finally:
            db.close()

        if not recursos_json:
            _update("error", 0, "❌ Sin recursos_json", "Ejecuta la fase Visual primero")
            return

        data = json.loads(recursos_json)
        remotion_configs = data.get("remotion", [])

        if not remotion_configs:
            _update("done", 100, "✅ Sin assets Remotion que renderizar")
            return

        _update("rendering", 2, f"🔍 {len(remotion_configs)} assets Remotion encontrados…")

        npx = _find_npx()
        _update("rendering", 5, "📦 Verificando dependencias Node…")
        _ensure_deps(npx)

        assets_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "assets" / "videos"
        total = len(remotion_configs)

        for i, cfg in enumerate(remotion_configs):
            template    = cfg.get("template", "TypeWriter")
            output_name = cfg.get("output", f"REM{i+1:02d}.mp4")
            duration    = cfg.get("duration", "0:10")
            props       = cfg.get("data", {})

            comp_id = TEMPLATE_MAP.get(template, template)
            frames  = _parse_frames(duration)
            props   = _normalize_props(template, props)
            out     = assets_dir / output_name

            pct = 5 + int((i / total) * 90)
            _update("rendering", pct, f"🎬 [{i+1}/{total}] {output_name} ({template}, {duration})…")

            _render_one(npx, comp_id, frames, props, out)

        _update("done", 100, f"✅ {total} assets Remotion renderizados")

    except Exception as e:
        _update("error", 0, "❌ Error en render Remotion",
                error=f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}")
