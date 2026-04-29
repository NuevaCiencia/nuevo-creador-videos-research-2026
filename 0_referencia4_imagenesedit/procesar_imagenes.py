from PIL import Image
import os
import numpy as np

CANVAS_SPLIT = (960, 1080)
CANVAS_FULL = (1920, 1080)

WHITE_THRESHOLD = 235  # píxeles con R,G,B > este valor se consideran "blancos"
BORDER_SAMPLE = 20     # píxeles a muestrear por cada lado del borde


def _tiene_borde_blanco(img):
    """Devuelve True si los bordes de la imagen son blancos o cercanos a blanco."""
    rgb = img.convert("RGB")
    arr = np.array(rgb)
    h, w = arr.shape[:2]

    # Muestrea filas/columnas de los 4 bordes
    top    = arr[:BORDER_SAMPLE, :, :]
    bottom = arr[max(0, h - BORDER_SAMPLE):, :, :]
    left   = arr[:, :BORDER_SAMPLE, :]
    right  = arr[:, max(0, w - BORDER_SAMPLE):, :]

    border = np.concatenate([
        top.reshape(-1, 3),
        bottom.reshape(-1, 3),
        left.reshape(-1, 3),
        right.reshape(-1, 3),
    ], axis=0)

    # Un píxel es "blanco" si todos sus canales superan el umbral
    es_blanco = np.all(border > WHITE_THRESHOLD, axis=1)
    return es_blanco.mean() > 0.90  # >90 % de los píxeles de borde son blancos


def centrar_imagen(img, canvas_size):
    """Escala la imagen para que quepa en el canvas (puede dejar barras blancas)."""
    canvas_w, canvas_h = canvas_size
    img_w, img_h = img.size

    scale = min(canvas_w / img_w, canvas_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", canvas_size, (255, 255, 255))
    img_w, img_h = img.size
    offset_x = (canvas_w - img_w) // 2
    offset_y = (canvas_h - img_h) // 2

    if img.mode in ("RGBA", "LA"):
        canvas.paste(img, (offset_x, offset_y), mask=img.split()[-1])
    else:
        canvas.paste(img, (offset_x, offset_y))
    return canvas


def rellenar_imagen(img, canvas_size):
    """Escala la imagen para cubrir todo el canvas (recorta si es necesario, sin barras)."""
    canvas_w, canvas_h = canvas_size
    img_w, img_h = img.size

    scale = max(canvas_w / img_w, canvas_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    offset_x = (new_w - canvas_w) // 2
    offset_y = (new_h - canvas_h) // 2
    img = img.crop((offset_x, offset_y, offset_x + canvas_w, offset_y + canvas_h))

    return img.convert("RGB")


def procesar_imagen(img, canvas_size):
    """Elige fit o fill según si los bordes de la imagen son blancos."""
    if _tiene_borde_blanco(img):
        return centrar_imagen(img, canvas_size), "fit"
    else:
        return rellenar_imagen(img, canvas_size), "fill"

def procesar_split():
    input_dir = os.path.join("imagenes_iniciales", "split")
    output_dir = os.path.join("imagenes_procesadas", "split")

    os.makedirs(output_dir, exist_ok=True)

    extensiones = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
    archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(extensiones)]

    if not archivos:
        print(f"No se encontraron imágenes en '{input_dir}'")
        return

    print(f"\nModo: SPLIT — Canvas: {CANVAS_SPLIT[0]}x{CANVAS_SPLIT[1]}")
    print(f"Procesando {len(archivos)} imagen(es)...\n")

    for nombre in archivos:
        ruta_entrada = os.path.join(input_dir, nombre)
        img = Image.open(ruta_entrada)

        nombre_corto = os.path.splitext(nombre)[0][:4]
        ruta_salida = os.path.join(output_dir, f"{nombre_corto}.png")

        resultado, modo = procesar_imagen(img, CANVAS_SPLIT)
        resultado.save(ruta_salida, "PNG", optimize=True)
        print(f"  OK [{modo:4s}]  {nombre}  ->  {nombre_corto}.png")

    print(f"\nListo. {len(archivos)} imagen(es) guardadas en '{output_dir}/'")

def procesar_full():
    input_dir = os.path.join("imagenes_iniciales", "full")
    output_dir = os.path.join("imagenes_procesadas", "full")

    os.makedirs(output_dir, exist_ok=True)

    extensiones = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
    archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(extensiones)]

    if not archivos:
        print(f"No se encontraron imágenes en '{input_dir}'")
        return

    print(f"\nModo: FULL — Canvas: {CANVAS_FULL[0]}x{CANVAS_FULL[1]}")
    print(f"Procesando {len(archivos)} imagen(es)...\n")

    for nombre in archivos:
        ruta_entrada = os.path.join(input_dir, nombre)
        img = Image.open(ruta_entrada)

        nombre_corto = os.path.splitext(nombre)[0][:4]
        ruta_salida = os.path.join(output_dir, f"{nombre_corto}.png")

        resultado, modo = procesar_imagen(img, CANVAS_FULL)
        resultado.save(ruta_salida, "PNG", optimize=True)
        print(f"  OK [{modo:4s}]  {nombre}  ->  {nombre_corto}.png")

    print(f"\nListo. {len(archivos)} imagen(es) guardadas en '{output_dir}/'")

def main():
    procesar_split()
    procesar_full()

if __name__ == "__main__":
    main()
