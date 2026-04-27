#!/usr/bin/env python3
"""
prompt_imagenes.py
──────────────────
Visualizador de prompts de imágenes del pipeline.

Carga los archivos imagenes_full.md e imagenes_split.md de cada proyecto
y muestra sus prompts junto con el speech correspondiente del guion_consolidado.txt.

Uso:
    python prompt_imagenes.py
"""
import os
import sys
import signal
import socket
import subprocess
import webbrowser
import time
import threading

PREFERRED_PORT = 8001          # Puerto distinto al del visualizador_pantallas


def check_and_install(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def kill_port(port):
    """Mata cualquier proceso que esté ocupando el puerto (macOS/Linux)."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True, text=True
        )
        pids = [p for p in result.stdout.strip().split("\n") if p]
        for pid in pids:
            os.kill(int(pid), signal.SIGKILL)
            print(f"🔴 Proceso anterior en puerto {port} (PID {pid}) terminado.")
        if pids:
            time.sleep(0.5)
    except Exception:
        pass


def find_free_port(start=PREFERRED_PORT, max_attempts=10):
    """Devuelve el primer puerto libre a partir de start."""
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return None


def main():
    check_and_install("fastapi")
    check_and_install("uvicorn")
    check_and_install("openai")
    check_and_install("python-dotenv")
    check_and_install("pyyaml")

    print("\n🖼️  Iniciando Visualizador de Prompts de Imágenes...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "utils", "server_imagenes.py")

    if not os.path.exists(server_path):
        print(f"❌ No se encontró {server_path}")
        sys.exit(1)

    kill_port(PREFERRED_PORT)

    port = find_free_port(PREFERRED_PORT)
    if port is None:
        print(f"❌ No se encontró ningún puerto disponible desde {PREFERRED_PORT}")
        sys.exit(1)
    if port != PREFERRED_PORT:
        print(f"⚠️  Puerto {PREFERRED_PORT} aún ocupado, usando {port}")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "utils.server_imagenes:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload"
    ]

    url = f"http://localhost:{port}"
    print(f"🌍 El servidor estará en {url}")

    threading.Thread(
        target=lambda: (time.sleep(2), webbrowser.open(url)),
        daemon=True
    ).start()

    proc = None
    try:
        proc = subprocess.Popen(cmd)
        proc.wait()
    except KeyboardInterrupt:
        print("\n👋 Cerrando el servidor...")
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        kill_port(port)
        print("✅ Puerto liberado.")


if __name__ == "__main__":
    main()
