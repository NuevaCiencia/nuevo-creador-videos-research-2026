# Research Imagenes Educativas

Script para centrar imágenes sobre un canvas de tamaño estándar.

## Setup

### 1. Crear el entorno virtual

```bash
python3 -m venv venv
```

### 2. Activar el entorno virtual

```bash
source venv/bin/activate
```

> Para desactivarlo cuando termines: `deactivate`

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## ⚠️ IMPORTANTE — Crear carpetas necesarias

Antes de usar el script, crea estas carpetas manualmente (están en `.gitignore` y no se incluyen en el repo):

```bash
mkdir imagenes_iniciales
mkdir imagenes_procesadas
```

- **`imagenes_iniciales/`** — aquí van las imágenes de entrada
- **`imagenes_procesadas/`** — aquí se guardarán los resultados

---

## Uso

1. Copia las imágenes a procesar en la carpeta `imagenes_iniciales/`
2. Ejecuta el script:

```bash
python procesar_imagenes.py
```

3. Elige el modo:
   - `1` — SPLIT (960 x 1080)
   - `2` — FULL IMAGE (1920 x 1080)

4. Las imágenes procesadas quedan en `imagenes_procesadas/`

## Estructura

```
.
├── imagenes_iniciales/    # Imágenes de entrada
├── imagenes_procesadas/   # Imágenes de salida (se crea automáticamente)
├── procesar_imagenes.py
├── requirements.txt
└── README.md
```
