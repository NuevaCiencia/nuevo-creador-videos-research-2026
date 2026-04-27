#!/usr/bin/env python3
"""studio.py — Abre el Remotion Studio desde la raíz del proyecto."""

import subprocess
import sys
from pathlib import Path

REMOTION_DIR = Path(__file__).parent / "pipeline" / "remotion"

subprocess.run(
    ["npx", "remotion", "preview", "src/index.tsx"],
    cwd=REMOTION_DIR,
    shell=(sys.platform == "win32"),
)
