# Creador de Libros 2026

Sistema de creación de drafts de libros de no-ficción y autoayuda con base científica, construido sobre pipelines de IA con revisión humana en cada paso.

---

## Filosofía

La mayoría de libros generados con IA son detectables a simple vista: solapamiento entre capítulos, tono genérico, frases cliché, historias inventadas y afirmaciones sin respaldo real. Este sistema ataca cada uno de esos problemas de forma estructural, no cosmética.

**El principio central:** la IA recomienda, el humano decide. Ninguna fase avanza sin aprobación explícita. El sistema no genera el libro de un golpe — construye una base sólida capa por capa, y cada capa es revisada antes de continuar.

**El enemigo principal:** el solapamiento. Cuando dos capítulos cubren el mismo territorio conceptual, el lector lo percibe como relleno. Todo el pipeline de estructura está diseñado para eliminarlo antes de escribir una sola palabra.

---

## APIs utilizadas

| API | Uso | Variable de entorno |
|-----|-----|---------------------|
| **OpenAI** (`gpt-5.4-nano`) | Generación de toda la estructura, contenido, análisis y agentes | `OPENAI_API_KEY` |
| **Tavily** | Verificación de fuentes científicas e historias reales con URLs | `TAVILY_API_KEY` |

### Carga de keys en Windows

Las variables de entorno del sistema Windows no siempre llegan a los subprocesos de Python. El módulo `utils/keys.py` resuelve esto leyendo directamente del registro de Windows (`HKEY_CURRENT_USER\Environment`) e inyectándolas en `os.environ` antes de que cualquier cliente de API se inicialice.

---

## Stack técnico

- **Frontend:** Streamlit — interfaz visual completa con navegación por fases
- **Backend:** Python puro, arquitectura de agentes especializados
- **Persistencia:** SQLite — todas las versiones, opciones y decisiones se guardan
- **Modelos:** OpenAI GPT con `response_format: json_object` para salidas estructuradas

---

## Arquitectura del proyecto

```
creador-libros-2026/
├── app.py                    # UI Streamlit completa (todas las fases)
├── agents/
│   ├── base.py               # Cliente OpenAI + función call_llm()
│   ├── title_agent.py        # Generación de títulos
│   ├── structure_agent.py    # Generación de estructuras narrativas
│   ├── chapter_agent.py      # Generación de capítulos con territorios exclusivos
│   ├── parts_agent.py        # Expansión de capítulos en secciones internas
│   ├── overlap_agent.py      # Detección de solapamientos entre capítulos
│   ├── tone_agent.py         # Generación de párrafo ancla y bloque de tono
│   └── research_agent.py     # Investigación científica + verificación Tavily
├── database/
│   └── db.py                 # Todas las operaciones SQLite
├── utils/
│   └── keys.py               # Resolución de API keys (env → registro Windows → .env)
├── data/
│   └── books.db              # Base de datos SQLite (ignorada en git)
└── requirements.txt
```

---

## Lo que está construido

### Bloque 1 — Esqueleto del libro (Fases 0 a 6)

El objetivo de este bloque es construir una estructura de libro absolutamente sólida antes de escribir una sola palabra de contenido.

#### Fase 0 — Idea
El usuario describe la idea del libro. Campos opcionales: lector objetivo y problema principal que resuelve. Todo se guarda en SQLite y es la base de todos los agentes posteriores.

#### Fase 1 — Títulos
La IA genera **6 opciones de título + subtítulo**, cada una explorando un ángulo distinto: emocional, racional, provocador, aspiracional, directo, metafórico. El usuario selecciona una, la edita, o escribe la suya. Opción de regenerar.

#### Fase 2 — Estructura narrativa
La IA genera **3 estructuras narrativas distintas** para el mismo libro, cada una con un arco diferente:
- Problema → Raíz → Solución → Práctica
- Mito → Verdad → Método → Transformación
- Viaje del héroe, Pirámide de comprensión, Contraintuitivo, etc.

Cada estructura incluye: descripción, progresión emocional del lector, fases con capítulos estimados. El usuario elige una.

#### Fase 3 — Capítulos
La IA genera los capítulos que el tema específico demanda (no una cantidad fija). Cada capítulo tiene:
- **Título**
- **Tesis** — qué argumenta o enseña en una oración
- **Territorio exclusivo** — declaración de qué cubre SOLO este capítulo y ningún otro (campo más crítico del sistema)
- **Posición en el arco** — apertura / problema / ciencia / framework / aplicación / transformación / cierre
- **Propósito** — por qué este capítulo es necesario para el lector
- **Promesa al lector** — qué sabrá/podrá al terminar

El usuario puede editar, eliminar o añadir capítulos.

#### Fase 4 — Partes de cada capítulo
Cada capítulo se expande en 4-7 secciones internas con tipos definidos: `apertura`, `ciencia`, `historia`, `teoria`, `ejercicio`, `reflexion`, `sintesis`. Cada parte tiene título evocador, puntos clave accionables, propósito y estimación de palabras. Se pueden generar de una en una o todas de golpe con barra de progreso.

#### Fase 5 — Verificación de coherencia (Anti-solapamiento)
Un agente especializado analiza **todos los pares posibles de capítulos** comparando sus territorios exclusivos. Detecta solapamientos con tres niveles de severidad:

- 🔴 **Alto** — invalida uno de los dos capítulos. Bloquea el avance hasta resolverse.
- 🟡 **Medio** — superposición parcial que requiere delimitación.
- 🟢 **Bajo** — resonancia temática aceptable.

Incluye score de coherencia (0-100) y evaluación general. El usuario marca cada solapamiento como resuelto. Los altos bloquean el avance.

#### Fase 6 — Esqueleto final
Vista completa del libro con todos los capítulos y partes, estimación total de palabras, y exportación a `.txt`.

---

### Bloque 2 — Voz y estilo (Fases 7 y 8)

#### Fase 7 — Bolsa de palabras prohibidas
Sistema de lista negra en dos capas:

**Global (~45 palabras pre-cargadas):** clichés detectables de IA organizados por categoría — clichés de IA, cierres mecánicos, adjetivos vacíos, intensificadores vacíos, jerga corporativa, aperturas cliché. Ejemplos: *"sin lugar a dudas"*, *"fascinante"*, *"en conclusión"*, *"holístico"*, *"paradigma"*, *"en el mundo actual"*.

**Por proyecto:** el usuario añade palabras específicas del tema del libro que tienden a repetirse. Cada palabra tiene toggle ON/OFF individual.

Todas las palabras activas se inyectan automáticamente en los prompts de escritura como restricciones explícitas.

#### Fase 8 — Tono patrón
Configuración del estilo de escritura en 6 dimensiones:

| Dimensión | Opciones |
|-----------|----------|
| Voz narrativa | Segunda persona / Primera persona / Mixta |
| Registro | Conversacional / Periodístico / Académico accesible / Íntimo |
| Longitud de frase | Mixta deliberada / Corta e impactante / Media y fluida |
| Metáforas | Moderadas / Frecuentes / Mínimas |
| Tratamiento de la ciencia | Con analogías / Integrada / Informal |
| Temperatura emocional | Equilibrada / Alta / Racional con calidez |

La IA genera **3 párrafos de ejemplo** sobre el tema real del libro en el tono configurado. El usuario elige uno, lo edita si quiere, y lo aprueba como **párrafo ancla** — el texto de referencia que se inyectará en cada prompt de escritura para mantener coherencia de voz en todo el libro.

---

### Bloque 3 — Investigación (Fase 9)

#### Fase 9 — Investigación por capítulo
Para cada capítulo, la IA construye un dossier de investigación con dos componentes:

**Sustento científico (3-5 ítems por capítulo):**
- Estudios y hallazgos reales de los que el modelo tiene conocimiento
- Autor, año, campo de investigación
- Hallazgo específico relevante al territorio exclusivo del capítulo (no al tema general)
- Query de búsqueda sugerido para verificación

**Historias reales (2-4 por capítulo):**
- Solo protagonistas reales y nombrados — nunca compuestos ni ficticios
- Evento específico y verificable
- Qué ilustra del territorio del capítulo
- Colocación narrativa sugerida: `apertura`, `post_ciencia`, `pre_ejercicio`, `cierre`
- Indicación de en qué parte del capítulo colocarla

**Mapa de colocación narrativa:** análisis de qué partes del capítulo se benefician de una historia y cuáles no. No es mecánico — la IA argumenta por qué cada parte necesita o no necesita anclaje narrativo.

**Verificación con Tavily:** cada ítem propuesto se busca automáticamente en la web. Los verificados muestran ✅ con link real; los no encontrados muestran ⚠️ para verificación manual. El usuario puede reverificar ítems individuales.

---

## Lo que falta construir

### Bloque 4 — Escritura (próximas fases)

El pipeline de escritura tomará todo lo construido en los bloques anteriores y producirá el draft real, sección por sección.

**Escritura por partes:** cada sección del esqueleto se escribe individualmente usando como contexto: tesis del capítulo + puntos clave de la parte + párrafo ancla + palabras prohibidas + investigación del capítulo. No se escribe un capítulo completo de golpe — se mantiene control granular.

**Tres modos por sección:**
1. Aceptar como está
2. Editar manualmente en el editor
3. Reescribir con instrucciones específicas ("más corto", "menos metáforas", "añade la historia de X aquí")

**Contexto acumulado:** conforme se escriben secciones, el sistema trackea qué conceptos ya se explicaron para no repetirlos en capítulos posteriores — la versión dinámica del anti-solapamiento.

**Versiones:** cada reescritura se guarda como versión nueva en SQLite. El usuario puede comparar y volver a versiones anteriores.

### Otras fases pendientes

- **Revisión de draft completo:** agente que lee el draft terminado y señala inconsistencias de tono, repeticiones entre capítulos, y secciones débiles
- **Exportación avanzada:** formatos Word (.docx) y PDF con estilos
- **Gestión de referencias:** formato de citas y bibliografía para las fuentes verificadas

---

## Cómo ejecutar

```bash
# 1. Clonar el repositorio
git clone https://github.com/NuevaCiencia/creador-libros-2026.git
cd creador-libros-2026

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar API keys
# Opción A: variables de entorno del sistema (Windows las lee del registro automáticamente)
# Opción B: crear archivo .env en la raíz del proyecto
echo "OPENAI_API_KEY=sk-..." > .env
echo "TAVILY_API_KEY=tvly-..." >> .env

# 4. Ejecutar
streamlit run app.py
```

El archivo `data/books.db` se crea automáticamente en el primer arranque.

---

## Variables de entorno requeridas

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

---

## Estado actual del proyecto

| Bloque | Estado |
|--------|--------|
| Bloque 1 — Esqueleto (Fases 0-6) | ✅ Completo |
| Bloque 2 — Voz y estilo (Fases 7-8) | ✅ Completo |
| Bloque 3 — Investigación (Fase 9) | ✅ Completo |
| Bloque 4 — Escritura (Fases 10+) | 🔲 Pendiente |
| Revisión de draft completo | 🔲 Pendiente |
| Exportación Word/PDF | 🔲 Pendiente |
