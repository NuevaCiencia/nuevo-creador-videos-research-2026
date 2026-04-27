"""
Resolución de API keys en Windows.
Intenta en orden: os.environ → registro de Windows → .env
"""
import os
import sys
from pathlib import Path

# Cargar .env si existe (para desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


def _read_windows_registry(name: str) -> str:
    """Lee una variable del registro de Windows (HKCU\\Environment)."""
    if sys.platform != "win32":
        return ""
    try:
        import winreg
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = winreg.OpenKey(root, "Environment")
                val, _ = winreg.QueryValueEx(key, name)
                winreg.CloseKey(key)
                if val:
                    return val
            except OSError:
                continue
    except Exception:
        pass
    return ""


def get_key(name: str) -> str:
    """Obtiene un API key probando múltiples fuentes."""
    # 1. Variable de entorno del proceso
    val = os.environ.get(name, "")
    if val:
        return val

    # 2. Registro de Windows
    val = _read_windows_registry(name)
    if val:
        os.environ[name] = val  # inyectar para que los módulos hijos lo vean
        return val

    return ""


# Cargar al importar para que todo el proceso los tenga disponibles
for _key_name in ("OPENAI_API_KEY", "TAVILY_API_KEY", "CLAUDE_API_KEY"):
    _v = get_key(_key_name)
    if _v:
        os.environ[_key_name] = _v
