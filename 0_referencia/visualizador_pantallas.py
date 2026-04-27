#!/usr/bin/env python3
import os
import sys
import signal
import socket
import subprocess
import webbrowser
import time
import threading

PREFERRED_PORT = 8000


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
    # Asegurar dependencias
    check_and_install("fastapi")
    check_and_install("uvicorn")

    print("\n🚀 Iniciando Visualizador de Pantallas...")

    # Ruta al servidor
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "utils", "server.py")

    if not os.path.exists(server_path):
        print(f"❌ No se encontró {server_path}")
        sys.exit(1)

    # 1. Matar proceso anterior en el puerto preferido (resuelve el error "Address already in use")
    kill_port(PREFERRED_PORT)

    # 2. Encontrar un puerto libre (8000 → 8001 → ... si siguen ocupados)
    port = find_free_port(PREFERRED_PORT)
    if port is None:
        print(f"❌ No se encontró ningún puerto disponible desde {PREFERRED_PORT}")
        sys.exit(1)
    if port != PREFERRED_PORT:
        print(f"⚠️  Puerto {PREFERRED_PORT} aún ocupado, usando {port}")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "utils.server:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload"
    ]

    url = f"http://localhost:{port}"
    print(f"🌍 El servidor estará en {url}")

    # Abrir navegador después de un pequeño delay
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
