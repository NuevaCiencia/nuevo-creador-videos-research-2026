#!/usr/bin/env python3
"""
pipeline.py
Orquestador principal: lee JSONs intermedios → renderiza con Remotion → compone con FFmpeg.

Uso:
    python pipeline.py run
    python pipeline.py run --intermediate-dir ./intermediate --audio ./inputs/locucion.wav
    python pipeline.py concat
"""

import json
import os
import subprocess
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

load_dotenv()

app     = typer.Typer(name="pipeline-educativo", add_completion=False)
console = Console()

REMOTION_DIR = Path(os.getenv("REMOTION_DIR", "./remotion"))
FPS          = int(os.getenv("FPS", "30"))


# ─── sub-comandos ─────────────────────────────────────────────────────────────

@app.command()
def run(
    intermediate_dir: Path = typer.Option(
        Path(os.getenv("INTERMEDIATE_DIR", "./intermediate")),
        help="Directorio con los JSON por pantalla",
    ),
    audio: Path = typer.Option(
        Path(os.getenv("AUDIO_FILE", "./inputs/locucion_completa.wav")),
        help="Ruta al audio original",
    ),
    output_dir: Path = typer.Option(
        Path(os.getenv("OUTPUT_DIR", "./output")),
        help="Directorio de salida",
    ),
    only: str = typer.Option(
        "", help="Procesar solo esta pantalla, ej. screen_03"
    ),
):
    """Renderiza y compone todas las pantallas."""
    output_dir.mkdir(parents=True, exist_ok=True)

    screens = sorted(intermediate_dir.glob("*.json"))
    if not screens:
        console.print(f"[red]No hay JSONs en {intermediate_dir}[/red]")
        raise typer.Exit(1)

    if only:
        screens = [s for s in screens if only in s.stem]
        if not screens:
            console.print(f"[red]No se encontró '{only}'[/red]")
            raise typer.Exit(1)

    if not audio.exists():
        console.print(f"[red]Audio no encontrado: {audio}[/red]")
        raise typer.Exit(1)

    console.print(
        f"[bold green]Pipeline iniciado[/bold green] — "
        f"{len(screens)} pantalla(s) | audio: {audio.name}"
    )

    for screen_path in track(screens, description="Procesando..."):
        screen = json.loads(screen_path.read_text(encoding="utf-8"))
        sid = screen["screen_id"]
        tpl = screen["template"]
        console.print(f"  [cyan]{sid}[/cyan] → {tpl} ({screen['duration_local']:.1f}s)")

        _render_remotion(screen, output_dir)
        _compose_final(screen, audio, output_dir)

    console.print("[bold green]✓ Pipeline completo[/bold green]")


@app.command()
def concat(
    output_dir: Path = typer.Option(
        Path(os.getenv("OUTPUT_DIR", "./output")),
        help="Directorio con los videos finales",
    ),
    final_video: Path = typer.Option(
        Path("./output/video_completo.mp4"),
        help="Ruta del video final concatenado",
    ),
):
    """Concatena todos los *_final.mp4 en un único video."""
    finals = sorted(output_dir.glob("*_final.mp4"))
    if not finals:
        console.print("[red]No hay videos _final.mp4 en el directorio[/red]")
        raise typer.Exit(1)

    lista_path = output_dir / "_lista_concat.txt"
    lista_path.write_text(
        "\n".join(f"file '{f.resolve()}'" for f in finals),
        encoding="utf-8",
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(lista_path),
            "-c", "copy",
            str(final_video),
        ],
        check=True,
    )
    console.print(f"[bold green]✓ Video completo: {final_video}[/bold green]")


# ─── funciones internas ───────────────────────────────────────────────────────

def _render_remotion(screen: dict, output_dir: Path) -> None:
    screen_id   = screen["screen_id"]
    template    = screen["template"]
    duration_f  = int(screen["duration_local"] * FPS)

    props_path  = output_dir / f"{screen_id}_props.json"
    output_path = output_dir / f"{screen_id}_video.mp4"

    props_path.write_text(
        json.dumps(screen["content"], ensure_ascii=False),
        encoding="utf-8",
    )

    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.tsx",
            template,
            "--props",  str(props_path.resolve()),
            "--frames", f"0-{duration_f - 1}",
            "--output", str(output_path.resolve()),
        ],
        cwd=str(REMOTION_DIR.resolve()),
        check=True,
    )


def _compose_final(screen: dict, source_audio: Path, output_dir: Path) -> None:
    screen_id  = screen["screen_id"]
    t_start    = screen["t_global"]["start"]
    t_end      = screen["t_global"]["end"]

    audio_clip = output_dir / f"{screen_id}_audio.wav"
    video_mute = output_dir / f"{screen_id}_video.mp4"
    final_out  = output_dir / f"{screen_id}_final.mp4"

    # 1. Extraer segmento de audio
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i",  str(source_audio),
            "-ss", str(t_start),
            "-to", str(t_end),
            "-c",  "copy",
            str(audio_clip),
        ],
        check=True,
    )

    # 2. Mezclar video mudo + audio
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_mute),
            "-i", str(audio_clip),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(final_out),
        ],
        check=True,
    )


if __name__ == "__main__":
    app()
