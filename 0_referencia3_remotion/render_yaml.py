#!/usr/bin/env python3
"""
render_yaml.py — Sistema de construcción YAML → MP4s independientes

Lee pipeline/inputs/guiones_para_construir.yaml y renderiza cada video
de forma independiente en pipeline/output/.

Uso:
    python render_yaml.py
    python render_yaml.py --only typewriter_01.mp4

SEPARADO DE render.py: este script NO toca el sistema de Remotion Studio.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import track

app     = typer.Typer(add_completion=False)
console = Console()

REMOTION_DIR  = Path(__file__).parent / "pipeline" / "remotion"
DEFAULT_YAML  = Path(__file__).parent / "pipeline" / "inputs" / "guiones_para_construir.yaml"
DEFAULT_OUTPUT = Path(__file__).parent / "pipeline" / "output"
FPS           = 30

# ─── Mapa: nombre corto del YAML → ID de composición en index.tsx ─────────────
TEMPLATE_MAP: dict[str, str] = {
    # Narrativos
    "TypeWriter":        "NAR-TypeWriter-Hacker",
    "Spotlight":         "NAR-Spotlight",
    "Timeline":          "NAR-Timeline",
    "ParticleNetwork":   "NAR-ParticleNetwork",
    # Flujo
    "MindMap":           "FLOW-MindMap",
    "LinearSteps":       "FLOW-LinearSteps",
    "CycleLoop":         "FLOW-CycleLoop",
    "OrgChart":          "FLOW-OrgChart",
    "FunnelDiagram":     "FLOW-Funnel",
    "SketchDiagram":     "FLOW-SketchDiagram",
    # Datos
    "StatCounter":       "DATA-StatCounter",
    "HorizontalBars":    "DATA-HorizontalBars",
    "PieDonut":          "DATA-PieDonut",
    "RadarChart":        "DATA-RadarChart",
    "WaveTrend":         "DATA-WaveTrend",
    "CircleStats":       "DATA-CircleStats",
    # Clase / clasificación
    "VennDiagram":       "CLASS-VennDiagram",
    "TwoColumns":        "CLASS-TwoColumns",
    "FourBoxes":         "CLASS-FourBoxes",
    "MatrixGrid":        "CLASS-MatrixGrid",
    "PyramidLevels":     "CLASS-PyramidLevels",
    "FlipCards":         "CLASS-FlipCards",
    "HexGrid":           "CLASS-HexGrid",
    "MosaicReveal":      "CLASS-MosaicReveal",
    # Efectos
    "KineticWords":      "FX-KineticWords",
    "NeonGlow":          "FX-NeonGlow",
    "WaveOrb":           "FX-WaveOrb",
    "RotatingCube":      "FX-RotatingCube",
    "GlitchReveal":      "FX-GlitchReveal",
    "GradientTitle":     "FX-GradientTitle",
    # Portadas / cierres
    "MainCover":         "COVER-MainCover",
    "SectionCover":      "COVER-SectionCover",
    "Credits":           "CLOSE-Credits",
    "ClosingQuote":      "CLOSE-Quote",
    "ClosingKeywords":   "CLOSE-Keywords",
    # Definición
    "CentralDefinition": "DEF-Central",
    "ImpactTerm":        "DEF-ImpactTerm",
    "ProgressiveReveal": "DEF-ProgressiveReveal",
    "RhetoricalQuestion":"DEF-RhetoricalQuestion",
    "VisualAnalogy":     "DEF-VisualAnalogy",
}
# ─────────────────────────────────────────────────────────────────────────────


def parse_duration(duration_str: str) -> int:
    """Convierte 'mm:ss' → cantidad de frames a 30fps."""
    parts = str(duration_str).split(":")
    if len(parts) == 2:
        minutes, seconds = int(parts[0]), int(parts[1])
    elif len(parts) == 1:
        minutes, seconds = 0, int(parts[0])
    else:
        raise ValueError(f"Formato de duración inválido: '{duration_str}'. Usa 'mm:ss'.")
    return (minutes * 60 + seconds) * FPS + 3 * FPS


def resolve_composition_id(template_name: str) -> str:
    """Retorna el ID de composición de Remotion para el template dado."""
    if template_name in TEMPLATE_MAP:
        return TEMPLATE_MAP[template_name]
    # Si el usuario ya puso el ID completo (ej. "FLOW-MindMap"), lo acepta tal cual
    known_ids = set(TEMPLATE_MAP.values())
    if template_name in known_ids:
        return template_name
    console.print(f"[yellow]Advertencia: template '{template_name}' no reconocido. Se usará como ID directo.[/yellow]")
    return template_name


# ─── Comando principal ────────────────────────────────────────────────────────

@app.command()
def main(
    yaml_file: Path = typer.Argument(DEFAULT_YAML, help="Archivo YAML con schema 'videos:'"),
    output_dir: Path = typer.Option(DEFAULT_OUTPUT, help="Directorio donde se guardarán los MP4s"),
    only: str = typer.Option(
        "",
        help="Renderizar solo el video con este nombre de output (ej. 'mindmap_01.mp4')",
    ),
    crf: int = typer.Option(18, help="CRF de calidad para ffmpeg (menor = mejor, 1 = lossless)"),
    scale: float = typer.Option(1.0, help="Factor de escala del render (2.0 = 4K)"),
):
    """Renderiza videos independientes desde un YAML con schema 'videos:'."""

    if not yaml_file.exists():
        console.print(f"[red]Archivo no encontrado: {yaml_file}[/red]")
        raise typer.Exit(1)

    raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
    videos = raw.get("videos", [])

    if not videos:
        console.print("[red]El YAML no tiene entradas en 'videos:'.[/red]")
        raise typer.Exit(1)

    # Filtrar por --only si se indicó
    if only:
        videos = [v for v in videos if v.get("output") == only]
        if not videos:
            console.print(f"[red]No hay ningún video con output='{only}'.[/red]")
            raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Tabla resumen ──────────────────────────────────────────────────────────
    table = Table("output", "template", "duración", "frames", show_header=True)
    for v in videos:
        frames = parse_duration(v["duration"])
        table.add_row(
            v["output"],
            v["template"],
            str(v["duration"]),
            str(frames),
        )
    console.print(table)

    # ── Render individual ──────────────────────────────────────────────────────
    for video in track(videos, description="Renderizando videos..."):
        _render_video(video, output_dir, crf, scale)

    console.print(f"\n[bold green]Listo. Videos en: {output_dir.resolve()}[/bold green]")


def _render_video(video: dict, output_dir: Path, crf: int, scale: float) -> None:
    template    = video["template"]
    output_name = video["output"]
    duration    = video["duration"]
    data        = video.get("data", {})

    composition_id = resolve_composition_id(template)
    frames         = parse_duration(duration)
    output_path    = output_dir / output_name

    console.print(f"\n[cyan]→ {output_name}[/cyan]  [{composition_id}]  {frames} frames")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        props_path = Path(f.name)

    try:
        _run([
            "npx", "remotion", "render",
            "src/index.tsx",
            composition_id,
            "--props",    str(props_path.resolve()),
            "--duration", str(frames),
            "--crf",      str(crf),
            "--scale",    str(scale),
            "--output",   str(output_path.resolve()),
        ], cwd=REMOTION_DIR)
    finally:
        props_path.unlink(missing_ok=True)

    console.print(f"[green]✓ Guardado: {output_path}[/green]")


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=(sys.platform == "win32"),
    )
    if result.returncode != 0:
        console.print(f"[red]Error al renderizar:[/red]")
        console.print(result.stderr.decode(errors="replace")[-3000:])
        sys.exit(1)


if __name__ == "__main__":
    app()
