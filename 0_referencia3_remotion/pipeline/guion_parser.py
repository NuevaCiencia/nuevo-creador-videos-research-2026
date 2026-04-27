#!/usr/bin/env python3
"""
guion_parser.py
Convierte guion.txt + transcripcion.txt → un JSON intermedio por pantalla
en pipeline/intermediate/screen_XX.json

Uso:
    python guion_parser.py
    python guion_parser.py --guion ../guion.txt --transcripcion ../transcripcion.txt
"""

import json
import re
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

# Mapeo de TYPE del guion → ID de Composition en Remotion
TEMPLATE_MAP = {
    "TEXT":       "TitleCard",
    "SPLIT_LEFT": "SplitLeft",
    "SPLIT_RIGHT":"SplitRight",
    "VIDEO":      "VideoSlide",
    "FULL_IMAGE": "FullImageSlide",
}


# ─── parsers ─────────────────────────────────────────────────────────────────

def ts_to_seconds(ts: str) -> float:
    """[MM:SS.mmm] → float segundos"""
    ts = ts.strip("[]")
    mm, ss = ts.split(":")
    return int(mm) * 60 + float(ss)


def parse_guion(path: Path) -> list[dict]:
    segments: list[dict] = []
    current: dict | None = None

    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip()

            if line.startswith("#SEGMENT"):
                if current is not None:
                    segments.append(current)
                m = re.search(r"\[([^\]]+)\]", line)
                t_start = ts_to_seconds(m.group(1)) if m else 0.0
                current = {
                    "t_start": t_start,
                    "type": "", "time": 0.0,
                    "text": "", "text_style": "",
                    "asset": "", "speech": "", "notes": "",
                }

            elif "=" in line and current is not None:
                key, _, value = line.partition("=")
                key = key.strip().upper()
                value = value.strip()
                match key:
                    case "TYPE":       current["type"] = value
                    case "TIME":       current["time"] = float(value)
                    case "TEXT":       current["text"] = value
                    case "TEXT_STYLE": current["text_style"] = value
                    case "ASSET":      current["asset"] = value
                    case "SPEECH":     current["speech"] = value
                    case "NOTES":      current["notes"] = value

    if current is not None:
        segments.append(current)

    return segments


def parse_transcription(path: Path) -> list[dict]:
    """[t_start - t_end]: texto → lista de cues"""
    cues: list[dict] = []
    pattern = re.compile(r"\[(\d+\.\d+)\s*-\s*(\d+\.\d+)\]:\s*(.+)")

    with open(path, encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                cues.append({
                    "t_start": float(m.group(1)),
                    "t_end":   float(m.group(2)),
                    "word":    m.group(3).strip(),
                })

    return cues


# ─── helpers ─────────────────────────────────────────────────────────────────

def get_cues_for_segment(
    all_cues: list[dict],
    t_start: float,
    t_end: float,
) -> list[dict]:
    """
    Extrae cues dentro de [t_start, t_end] y convierte a tiempo local
    (relativo al inicio de la pantalla).
    """
    local: list[dict] = []
    for cue in all_cues:
        if cue["t_start"] >= t_start - 0.05 and cue["t_end"] <= t_end + 0.5:
            local.append({
                "word":    cue["word"],
                "t_start": round(cue["t_start"] - t_start, 3),
                "t_end":   round(cue["t_end"]   - t_start, 3),
            })
    return local


def build_content(seg: dict, template: str, word_cues: list[dict]) -> dict:
    base = {"speech": seg["speech"], "word_cues": word_cues}

    match template:
        case "TitleCard":
            return {**base, "title": seg["text"], "style": seg["text_style"]}
        case "SplitLeft":
            return {**base, "text": seg["text"], "text_style": seg["text_style"],
                    "asset": seg["asset"], "side": "left"}
        case "SplitRight":
            return {**base, "text": seg["text"], "text_style": seg["text_style"],
                    "asset": seg["asset"], "side": "right"}
        case "VideoSlide":
            return {**base, "asset": seg["asset"]}
        case "FullImageSlide":
            return {**base, "asset": seg["asset"]}
        case _:
            return base


# ─── comando principal ────────────────────────────────────────────────────────

@app.command()
def main(
    guion: Path = typer.Option(
        Path(__file__).parent.parent / "guion.txt",
        help="Ruta al archivo guion.txt",
    ),
    transcripcion: Path = typer.Option(
        Path(__file__).parent.parent / "transcripcion.txt",
        help="Ruta al archivo transcripcion.txt",
    ),
    out_dir: Path = typer.Option(
        Path(__file__).parent / "intermediate",
        help="Directorio de salida para los JSONs",
    ),
    fps: int = typer.Option(30, help="Frames por segundo del video"),
):
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold cyan]Leyendo guion:[/bold cyan] {guion}")
    segments = parse_guion(guion)

    console.print(f"[bold cyan]Leyendo transcripción:[/bold cyan] {transcripcion}")
    all_cues = parse_transcription(transcripcion)
    console.print(f"  {len(all_cues)} cues encontrados\n")

    table = Table("#", "screen_id", "template", "duración", "cues", show_header=True)

    for i, seg in enumerate(segments, 1):
        t_start  = seg["t_start"]
        t_end    = t_start + seg["time"]
        template = TEMPLATE_MAP.get(seg["type"], "TitleCard")
        screen_id = f"screen_{i:02d}"

        word_cues = get_cues_for_segment(all_cues, t_start, t_end)
        content   = build_content(seg, template, word_cues)

        screen = {
            "screen_id":      screen_id,
            "template":       template,
            "duration_local": round(seg["time"], 3),
            "fps":            fps,
            "t_global": {
                "start": round(t_start, 3),
                "end":   round(t_end,   3),
            },
            "content": content,
        }

        out_path = out_dir / f"{screen_id}.json"
        out_path.write_text(json.dumps(screen, ensure_ascii=False, indent=2), encoding="utf-8")

        table.add_row(
            str(i), screen_id, template,
            f"{seg['time']:.1f}s",
            str(len(word_cues)),
        )

    console.print(table)
    console.print(f"\n[bold green]OK — {len(segments)} JSONs escritos en {out_dir}[/bold green]")


if __name__ == "__main__":
    app()
