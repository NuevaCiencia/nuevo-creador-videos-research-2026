import zipfile
from datetime import datetime
from pathlib import Path

CARPETAS = ["imagenes_iniciales", "imagenes_procesadas"]
BASE_DIR = Path(__file__).parent

def vaciar_carpeta(ruta):
    for item in ruta.iterdir():
        if item.is_dir():
            vaciar_carpeta(item)
        else:
            item.unlink()

def crear_backup():
    respuesta = input("¿Confirmar backup y vaciado de carpetas? (s/n): ").strip().lower()
    if respuesta != "s":
        print("Cancelado.")
        return

    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_zip = BASE_DIR / "deprecated" / f"backup_imagenes_videos_{fecha_hora}.zip"

    with zipfile.ZipFile(nombre_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for carpeta in CARPETAS:
            ruta = BASE_DIR / carpeta
            if not ruta.exists():
                print(f"Advertencia: '{carpeta}' no existe, se omite.")
                continue
            for archivo in ruta.rglob("*"):
                if archivo.is_file():
                    zf.write(archivo, archivo.relative_to(BASE_DIR))
                    print(f"  + {archivo.relative_to(BASE_DIR)}")

    print(f"\nBackup creado: {nombre_zip.name}")

    for carpeta in CARPETAS:
        ruta = BASE_DIR / carpeta
        if ruta.exists():
            vaciar_carpeta(ruta)
            print(f"Vaciada: {carpeta}/")

if __name__ == "__main__":
    crear_backup()
