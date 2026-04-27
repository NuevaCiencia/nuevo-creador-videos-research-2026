#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FONT RESOLVER
=============
Módulo centralizado para resolución de fuentes tipográficas cross-platform.

Estrategia (en orden de prioridad):
  1. Fuentes embebidas en fonts/ del repo (100% portátil)
  2. Fallback por SO (Helvetica en Mac, Arial en Windows, DejaVu en Linux)

Uso:
  from core.font_resolver import FontResolver
  fr = FontResolver()
  fontfile_arg     = fr.get_fontfile_arg()      # Para drawtext de FFmpeg
  fontsdir_arg     = fr.get_fontsdir_arg()      # Para filtro ass= de FFmpeg
  font_name        = fr.get_font_name()         # Para cabeceras ASS
"""

import os
import platform
import sys

# ---------------------------------------------------------------------------
# Mapeo: variante → nombre de archivo embebido en fonts/
# ---------------------------------------------------------------------------
EMBEDDED_FONTS = {
    "regular":  "Montserrat-Regular.ttf",
    "bold":     "Montserrat-Bold.ttf",
    "italic":   "Inter-Italic.ttf",
    "mono":     "JetBrainsMono-Regular.ttf",
}

# Nombre de familia para cabeceras ASS (libass lo resuelve via fontsdir)
FONT_FAMILY_MAIN = "Montserrat"
FONT_FAMILY_MONO = "JetBrains Mono"

# ---------------------------------------------------------------------------
# Fallbacks por SO si por alguna razón fonts/ no existe
# ---------------------------------------------------------------------------
SYSTEM_FALLBACKS = {
    "Darwin": {        # macOS
        "regular": "/System/Library/Fonts/Helvetica.ttc",
        "bold":    "/System/Library/Fonts/Helvetica.ttc",
        "italic":  "/System/Library/Fonts/Helvetica.ttc",
        "mono":    "/System/Library/Fonts/Menlo.ttc",
        "name":    "Helvetica",
    },
    "Windows": {
        "regular": "C:/Windows/Fonts/arial.ttf",
        "bold":    "C:/Windows/Fonts/arialbd.ttf",
        "italic":  "C:/Windows/Fonts/ariali.ttf",
        "mono":    "C:/Windows/Fonts/cour.ttf",
        "name":    "Arial",
    },
    "Linux": {
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold":    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "italic":  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "mono":    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "name":    "DejaVu Sans",
    },
}


class FontResolver:
    """
    Resuelve rutas y nombres de fuentes de forma portátil.
    Busca primero en fonts/ (repo embebido), luego en el SO.
    """

    def __init__(self, base_dir: str = None):
        """
        Args:
            base_dir: Directorio raíz del proyecto. Si es None, se infiere
                      desde la ubicación de este archivo.
        """
        if base_dir is None:
            # core/font_resolver.py → subir un nivel = raíz del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self._fonts_dir = os.path.join(base_dir, "fonts")
        self._os = platform.system()   # 'Darwin', 'Windows', 'Linux'
        self._embedded_ok = self._check_embedded()

        if self._embedded_ok:
            print(f"✅ FontResolver: fuentes embebidas encontradas en {self._fonts_dir}")
        else:
            fallback_name = SYSTEM_FALLBACKS.get(self._os, {}).get("name", "default")
            print(f"⚠  FontResolver: fonts/ no encontrado. "
                  f"Usando fallback del SO ({self._os}): {fallback_name}")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get_fonts_dir(self) -> str:
        """Devuelve la ruta absoluta al directorio de fuentes embebidas."""
        return self._fonts_dir

    def get_font_path(self, variant: str = "regular") -> str:
        """
        Devuelve la ruta absoluta al archivo TTF para una variante.
        variant: 'regular' | 'bold' | 'italic' | 'mono'
        """
        if self._embedded_ok:
            filename = EMBEDDED_FONTS.get(variant, EMBEDDED_FONTS["regular"])
            path = os.path.join(self._fonts_dir, filename)
            if os.path.exists(path):
                return path

        # Fallback por SO
        fallback = SYSTEM_FALLBACKS.get(self._os, SYSTEM_FALLBACKS["Linux"])
        path = fallback.get(variant, fallback["regular"])
        if os.path.exists(path):
            return path

        # Último recurso: devolver cadena vacía (FFmpeg usará su default)
        print(f"⚠  FontResolver: no se encontró fuente para variante '{variant}'. "
              f"FFmpeg usará su tipografía por defecto.")
        return ""

    def get_font_name(self) -> str:
        """
        Devuelve el nombre de familia para cabeceras ASS.
        Si hay embebidas → 'Inter', si no → nombre del fallback del SO.
        """
        if self._embedded_ok:
            return FONT_FAMILY_MAIN
        return SYSTEM_FALLBACKS.get(self._os, {}).get("name", "Arial")

    def get_fontfile_arg(self, variant: str = "regular") -> str:
        """
        Construye el argumento 'fontfile=/ruta/fuente.ttf:' listo para
        insertar en un filtro drawtext de FFmpeg.
        Devuelve cadena vacía si no se encuentra ninguna fuente.
        """
        path = self.get_font_path(variant)
        if not path:
            return ""
        # En Windows las rutas necesitan barras normales para FFmpeg
        path_ffmpeg = path.replace("\\", "/")
        return f"fontfile='{path_ffmpeg}':"

    def get_fontsdir_arg(self) -> str:
        """
        Construye el argumento ':fontsdir=/ruta' para el filtro ass= de FFmpeg.
        Permite que libass resuelva 'Inter' sin instalarlo en el sistema.
        Ejemplo de uso:  -vf "ass=subs.ass:fontsdir=/abs/path/fonts"
        """
        if self._embedded_ok:
            path_ffmpeg = self._fonts_dir.replace("\\", "/")
            return f":fontsdir={path_ffmpeg}"
        return ""

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _check_embedded(self) -> bool:
        """Verifica que el directorio de fuentes exista y tenga al menos una fuente."""
        if not os.path.isdir(self._fonts_dir):
            return False
        ttf_files = [f for f in os.listdir(self._fonts_dir) if f.endswith(".ttf")]
        return len(ttf_files) > 0


# ---------------------------------------------------------------------------
# Instancia global (singleton ligero) para importación rápida
# ---------------------------------------------------------------------------
_resolver_cache = None

def get_resolver(base_dir: str = None) -> FontResolver:
    """Devuelve una instancia compartida de FontResolver (lazy singleton)."""
    global _resolver_cache
    if _resolver_cache is None:
        _resolver_cache = FontResolver(base_dir)
    return _resolver_cache
