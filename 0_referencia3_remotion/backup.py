#!/usr/bin/env python3
"""
Backup de pipeline/output/ + las entradas YAML relacionadas con cada MP4.
Crea: backups/YYYY-MM-DD_HH-MM-SS.zip
"""

import io
import zipfile
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "pipeline" / "output"
INPUTS_DIR = ROOT / "pipeline" / "inputs"
BACKUPS_DIR = ROOT / "backups"


def load_videos_from_yamls() -> dict[str, dict]:
    """Devuelve {nombre_mp4: entrada_yaml} para todos los YAMLs de inputs."""
    mapping = {}
    for yaml_file in sorted(INPUTS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or "videos" not in data:
            continue
        for entry in data["videos"]:
            output_name = entry.get("output", "")
            if output_name:
                mapping[output_name] = {"source_yaml": yaml_file.name, "entry": entry}
    return mapping


def main():
    mp4_files = sorted(OUTPUT_DIR.glob("*.mp4"))
    if not mp4_files:
        print("No hay archivos MP4 en pipeline/output/")
        return

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_path = BACKUPS_DIR / f"{timestamp}.zip"

    video_map = load_videos_from_yamls()
    matched_entries: list[dict] = []
    unmatched: list[str] = []

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for mp4 in mp4_files:
            zf.write(mp4, mp4.name)
            print(f"  ✓ {mp4.name}")
            if mp4.name in video_map:
                matched_entries.append(video_map[mp4.name]["entry"])
            else:
                unmatched.append(mp4.name)

        if matched_entries:
            yaml_bytes = yaml.dump(
                {"videos": matched_entries},
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ).encode("utf-8")
            zf.writestr("guion.yaml", yaml_bytes)
            print(f"  ✓ guion.yaml ({len(matched_entries)} entrada(s))")

    if unmatched:
        print(f"\n  Sin YAML encontrado para: {', '.join(unmatched)}")

    size_mb = zip_path.stat().st_size / 1_048_576
    print(f"\nBackup guardado en: backups/{timestamp}.zip ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
