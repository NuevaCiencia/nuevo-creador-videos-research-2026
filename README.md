# nuevo-creador-videos-research-2026

## Setup

### Mac

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Dependencias Node.js (Remotion)

La app renderiza assets animados con [Remotion](https://www.remotion.dev/), que requiere **Node.js ≥ 18**.

### Instalar Node.js

**Mac (recomendado via nvm):**
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.zshrc   # o ~/.bashrc
nvm install 20
nvm use 20
```

**Windows (recomendado via nvm-windows):**
1. Descarga e instala [nvm-windows](https://github.com/coreybutler/nvm-windows/releases)
2. Abre un terminal nuevo y ejecuta:
```cmd
nvm install 20
nvm use 20
```

**O directamente desde [nodejs.org](https://nodejs.org/) (LTS).**

### Instalar dependencias de Remotion

Después de clonar o hacer `git pull`, una sola vez:

```bash
cd remotion
npm install
cd ..
```

> La carpeta `remotion/node_modules/` está en `.gitignore` — hay que instalar en cada máquina nueva.

---

## Arrancar la app

```bash
python run.py
```

Abre http://127.0.0.1:8080 en el navegador.

## Variables de entorno

Crea un archivo `.env` en la raíz o exporta antes de arrancar:

```bash
export OPENAI_API_KEY=sk-...
export TAVILY_API_KEY=tvly-...
```

En Windows:

```cmd
set OPENAI_API_KEY=sk-...
set TAVILY_API_KEY=tvly-...
```
