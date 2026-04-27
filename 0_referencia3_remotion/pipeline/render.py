#!/usr/bin/env python3
"""
render.py — Pipeline simplificado: YAML → MP4

Lee un archivo YAML con la lista de escenas, renderiza cada una con Remotion
y concatena todo en un único MP4.

Uso básico:
    python render.py inputs/ejemplo_45s.yaml

Con audio:
    python render.py inputs/ejemplo_45s.yaml --audio inputs/locucion.wav

Solo una escena (útil para probar):
    python render.py inputs/ejemplo_45s.yaml --only portada

Sin concatenar (deja los clips individuales):
    python render.py inputs/ejemplo_45s.yaml --no-concat
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import track

app     = typer.Typer(add_completion=False)
console = Console()

REMOTION_DIR = Path(__file__).parent / "remotion"
FPS_DEFAULT  = 30


# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def main(
    guion: Path = typer.Argument(..., help="Ruta al archivo YAML del guion"),
    output: Path = typer.Option(
        Path("./output/video_final.mp4"),
        help="Ruta del MP4 final",
    ),
    audio: Path = typer.Option(
        None,
        help="Ruta al audio WAV/MP3 (opcional). Si no se pasa, el video queda mudo.",
    ),
    only: str = typer.Option(
        "",
        help="Renderizar solo la escena con este ID (ej. 'portada').",
    ),
    no_concat: bool = typer.Option(
        False,
        help="No concatenar al final; solo renderizar clips individuales.",
    ),
    keep_tmp: bool = typer.Option(
        False,
        help="Conservar archivos temporales de cada escena.",
    ),
):
    """Renderiza un guion YAML y produce un MP4 final."""

    if not guion.exists():
        console.print(f"[red]No se encontró el archivo: {guion}[/red]")
        raise typer.Exit(1)

    data   = yaml.safe_load(guion.read_text(encoding="utf-8"))
    fps    = data.get("fps", FPS_DEFAULT)
    scenes = data.get("scenes", [])

    if not scenes:
        console.print("[red]El YAML no tiene ninguna escena en 'scenes'.[/red]")
        raise typer.Exit(1)

    # Filtrar por --only si se especificó
    if only:
        scenes = [s for s in scenes if s["id"] == only]
        if not scenes:
            console.print(f"[red]No existe escena con id='{only}'.[/red]")
            raise typer.Exit(1)

    # Validar audio
    if audio and not audio.exists():
        console.print(f"[red]Audio no encontrado: {audio}[/red]")
        raise typer.Exit(1)

    # Crear directorio de salida y tmp
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = output.parent / "_tmp"
    tmp_dir.mkdir(exist_ok=True)

    # ── Resumen ──────────────────────────────────────────────────────────────
    total_sec = sum(s["duration"] for s in scenes)
    table = Table("Escena", "Template", "Duración", "Frames", show_header=True)
    for s in scenes:
        frames = int(s["duration"] * fps)
        table.add_row(s["id"], s["template"], f"{s['duration']}s", str(frames))
    table.add_row("[bold]TOTAL[/bold]", "", f"[bold]{total_sec}s[/bold]", "")
    console.print(table)

    # ── Render ───────────────────────────────────────────────────────────────
    clip_paths: list[Path] = []

    for scene in track(scenes, description="Renderizando..."):
        clip = _render_scene(scene, fps, tmp_dir, audio)
        clip_paths.append(clip)

    if no_concat or len(clip_paths) == 1:
        # Mover el único clip / dejar los clips donde están
        if len(clip_paths) == 1:
            shutil.copy(clip_paths[0], output)
            console.print(f"[bold green]Video guardado: {output}[/bold green]")
        else:
            console.print(f"[bold green]Clips en: {tmp_dir}[/bold green]")
    else:
        _concat(clip_paths, output, tmp_dir)
        console.print(f"[bold green]Video final ({total_sec}s): {output}[/bold green]")

    if not keep_tmp:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ─── render de una escena ──────────────────────────────────────────────────────

def _render_scene(
    scene: dict,
    fps:   int,
    tmp:   Path,
    audio: Path | None,
) -> Path:
    sid       = scene["id"]
    template  = scene["template"]
    duration  = scene["duration"]         # segundos
    frames    = int(duration * fps)
    props     = scene.get("props", {})

    # Archivos temporales de esta escena
    props_file  = tmp / f"{sid}_props.json"
    video_mute  = tmp / f"{sid}_mute.mp4"
    clip_final  = tmp / f"{sid}_clip.mp4"

    # 1. Escribir props en JSON
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    # 2. Remotion render
    _run([
        "npx", "remotion", "render",
        "src/index.tsx",
        template,
        "--props",  str(props_file.resolve()),
        "--frames", f"0-{frames - 1}",
        "--crf",    "1",
        "--scale",  "2",
        "--output", str(video_mute.resolve()),
    ], cwd=REMOTION_DIR)

    # 3. Si hay audio, cortar el segmento y mezclar
    if audio:
        t_start = scene.get("t_start", 0.0)       # offset manual en YAML (opcional)
        t_end   = t_start + duration
        audio_clip = tmp / f"{sid}_audio.wav"

        _run([
            "ffmpeg", "-y",
            "-i",  str(audio),
            "-ss", str(t_start),
            "-to", str(t_end),
            "-c",  "copy",
            str(audio_clip),
        ])

        _run([
            "ffmpeg", "-y",
            "-i", str(video_mute),
            "-i", str(audio_clip),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(clip_final),
        ])
    else:
        # Video mudo
        shutil.copy(video_mute, clip_final)

    return clip_final


# ─── concat ───────────────────────────────────────────────────────────────────

def _concat(clips: list[Path], output: Path, tmp: Path) -> None:
    lista = tmp / "_concat_list.txt"
    lista.write_text(
        "\n".join(f"file '{c.resolve()}'" for c in clips),
        encoding="utf-8",
    )
    _run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(lista),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac",
        str(output),
    ])


# ─── helper ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=(sys.platform == "win32"),
    )
    if result.returncode != 0:
        console.print(f"[red]Error en: {' '.join(cmd[:4])}...[/red]")
        console.print(result.stderr.decode(errors="replace")[-2000:])
        sys.exit(1)


if __name__ == "__main__":
    app()
