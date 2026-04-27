# Verificación de Estilo — Documentación Técnica

El verificador de estilo (`agents/style_agent.py`) analiza cada sección escrita de un capítulo en tres capas independientes: estructura matemática, semántica con embeddings, y síntesis editorial vía LLM. El resultado es feedback accionable y la capacidad de auto-corregir cada parte.

---

## Arquitectura general

```
Texto de la parte
       │
       ├──► analyze_structure()   → métricas de ritmo (solo matemáticas, sin IA)
       │
       ├──► analyze_semantics()   → embeddings OpenAI → cosine similarity
       │         ├── drift desde párrafo ancla
       │         ├── estilo más cercano en corpus de referencia
       │         └── embedding de apertura (para detección de clones)
       │
       └──► synthesize_feedback() → LLM con métricas como input → feedback editorial
```

Al terminar todas las partes del capítulo, se corre `detect_clone_openings()` que compara las aperturas de todas las partes entre sí.

---

## Capa 1: Análisis Estructural (matemáticas puras)

**Función:** `analyze_structure(content)`

El texto se divide en frases usando regex: `(?<=[.!?])\s+`. Se calcula el número de palabras por frase y se obtienen las siguientes métricas:

### Promedio de palabras por frase

```
avg = Σ(longitud_i) / n
```

Referencia:
- `avg < 8` → estilo demasiado staccato (fragmentado sin intención)
- `avg > 28` → frases sin respiro (bloque denso, difícil de leer)
- Rango sano: entre 12 y 22 palabras por frase en promedio

### Desviación estándar (varianza de ritmo)

```
variance = Σ(longitud_i - avg)² / n
std_dev = √variance
```

Esto mide si el autor alterna entre frases cortas y largas (ritmo vivo) o si todas las frases tienen la misma longitud (ritmo muerto).

- `std_dev < 3.5` → alerta de ritmo monótono
- `std_dev > 6` → buen ritmo variado

### Rhythm Score (0–100)

```
rhythm_score = min(100, int(std_dev × 6))
```

Penalizaciones:
- Si `avg < 8` → `-25 puntos` (staccato sin propósito)
- Si `avg > 30` → `-20 puntos` (frases interminables)

El factor `×6` convierte una desviación estándar de ~16 en score perfecto de 100. Una std_dev de 5 da score 30, de 10 da 60, de 16+ da 100.

### Ratios de alerta adicionales

| Métrica | Cálculo | Alerta |
|---|---|---|
| `short_ratio` | frases ≤7 palabras / total | — |
| `long_ratio` | frases ≥28 palabras / total | — |
| `question_ratio` | frases que terminan en `?` / total | > 0.30 → alerta |
| `warning_monotonous` | std_dev < 3.5 | |
| `warning_no_breathing` | avg > 28 | |
| `warning_too_staccato` | avg < 8 AND n > 3 | |
| `warning_question_overuse` | question_ratio > 0.30 | |

---

## Capa 2: Embeddings y Similitud Semántica

**Función:** `analyze_semantics(content, anchor_emb, ref_embeddings)`

Usa el modelo `text-embedding-3-small` de OpenAI. Este modelo convierte cualquier texto en un vector de **1536 dimensiones** donde la cercanía geométrica entre vectores refleja similitud de significado, tono y estilo.

### Similitud coseno

La similitud entre dos vectores `a` y `b` se calcula como:

```
cosine(a, b) = (a · b) / (‖a‖ × ‖b‖)
```

Donde:
- `a · b = Σ(aᵢ × bᵢ)` → producto punto
- `‖a‖ = √Σ(aᵢ²)` → magnitud del vector

El resultado es un escalar entre **-1 y 1**:
- `1.0` → textos idénticos en tono y estilo
- `0.0` → textos sin relación
- El rango típico entre textos en español del mismo género es `0.55 – 0.85`

### Drift Score (deriva de tono)

Mide cuánto se aleja el texto escrito del párrafo ancla aprobado por el autor.

```
anchor_similarity = cosine(embedding_parte, embedding_ancla)
drift_score = round((1 - anchor_similarity) × 100)
```

Interpretación:
- `drift_score < 25` → la parte está tonalmente muy cerca del ancla (verde)
- `drift_score 25–40` → ligera deriva aceptable (amarillo)
- `drift_score > 40` → alerta: la parte se alejó del tono del libro (rojo)
- `anchor_similarity < 0.65` → warning explícito en el feedback

### Nearest Reference (estilo más cercano)

El corpus de referencia contiene **15 párrafos curados** en 6 categorías de estilo. El sistema compara el embedding de la parte contra cada referencia y reporta la más cercana:

```
para cada ref en corpus:
    sim = cosine(embedding_parte, ref.embedding)
    si sim > nearest_sim: guardar ref
```

Categorías del corpus:
1. **apertura_escena** — arranca con una escena concreta de acción o decisión
2. **apertura_tension** — paradoja conceptual o afirmación incómoda
3. **ritmo_variado** — alterna frase corta de impacto con desarrollo largo
4. **ritmo_staccato** — frases muy cortas para golpe emocional
5. **registro_periodistico** — dato primero, contexto después
6. **registro_conversacional** — directo al lector, sin filtro académico
7. **cierre_movimiento** — cierra con acción, no con resumen

Esta comparación no juzga si la parte es "buena o mala" — identifica a qué familia de estilo pertenece para que el feedback sea más específico.

### Embedding de apertura (para detección de clones)

Adicionalmente, se embede solo las **dos primeras frases** de cada parte:

```python
opening = ' '.join(sentences[:2])
opening_emb = embed_text([opening])
```

Este vector se usa exclusivamente para `detect_clone_openings()`.

---

## Capa 3: Detección de Aperturas Clonadas

**Función:** `detect_clone_openings(parts_semantic)`

Compara los embeddings de apertura de todas las partes del capítulo entre sí (comparación O(n²) por pares):

```
para cada par (parte_A, parte_B):
    sim = cosine(opening_emb_A, opening_emb_B)
    si sim > 0.88 → reportar como clon
```

**Umbral 0.88:** Por encima de este valor las aperturas son sospechosamente similares en tono y estructura de inicio. Se reportan como pares `{part_a, part_b, similarity}`.

Este fue el problema más frecuente detectado en pruebas: partes 2, 3 y 5 iniciando con la misma estructura aunque el contenido fuera diferente.

---

## Capa 4: Síntesis Editorial (LLM)

**Función:** `synthesize_feedback(part, structural, semantic)`

Las métricas de las dos capas anteriores se pasan como input a un LLM (`gpt-5.4-nano`, temperatura 0.4). El sistema no le pide al LLM que "analice el texto" — le da los números calculados y le pide que produzca feedback editorial concreto.

Input al LLM:
```
- Título y tipo de la parte
- Propósito declarado
- Frases totales, promedio palabras/frase, std_dev
- Rhythm score
- Ratios de frases cortas/largas
- Primera oración completa
- Estilo más cercano en corpus
- Lista de alertas activadas
```

Output del LLM (JSON forzado):
```json
{
  "feedback": "2-3 oraciones concretas de diagnóstico editorial",
  "priority_fix": "La corrección más urgente en una sola oración accionable",
  "warnings": ["alerta 1", "alerta 2", ...]
}
```

La temperatura baja (0.4) hace que el LLM sea más determinista y menos florido — se busca precisión editorial, no creatividad.

---

## Corpus de Referencia: Embeddings Cacheados

Los 15 párrafos del corpus se embeden **una sola vez** y se guardan en SQLite como JSON:

```sql
CREATE TABLE style_references (
    id INTEGER PRIMARY KEY,
    label TEXT,
    category TEXT,
    text TEXT,
    embedding TEXT,   -- JSON array de 1536 floats
    created_at TEXT
)
```

En cada sesión, `_ensure_ref_embeddings()` revisa si hay referencias sin embedding y solo llama a la API si es necesario. El costo de embedding del corpus es ~$0.001 y se paga una sola vez.

---

## Resultado completo de `review_chapter()`

```python
{
  'chapter_id': int,
  'chapter_titulo': str,
  'parts': [
    {
      'part_id': int,
      'part_num': int,
      'part_titulo': str,
      'part_tipo': str,         # apertura, historia, ciencia, etc.
      'structural': {
        'sentence_count': int,
        'avg_words': float,
        'std_dev': float,
        'rhythm_score': int,    # 0–100
        'short_ratio': float,
        'long_ratio': float,
        'question_ratio': float,
        'paragraph_count': int,
        'opening_sentence': str,
        'warning_monotonous': bool,
        'warning_no_breathing': bool,
        'warning_too_staccato': bool,
        'warning_question_overuse': bool,
      },
      'semantic': {
        'drift_score': int,           # 0–100, mayor = más lejos del ancla
        'anchor_similarity': float,   # 0–1
        'nearest_ref_label': str,
        'nearest_ref_similarity': float,
      },
      'feedback': {
        'feedback': str,
        'priority_fix': str,
        'warnings': [str, ...],
      }
    },
    ...
  ],
  'clone_openings': [
    {'part_a': int, 'part_b': int, 'similarity': float},
    ...
  ],
  'avg_rhythm_score': int,    # promedio del capítulo
  'avg_drift_score': int,     # promedio de deriva del capítulo
}
```

---

## Flujo UX en la app

1. **Analizar** → corre `review_chapter()`, guarda resultado en `style_reviews` (SQLite) y en `session_state`
2. **Corregir** → por parte individual o todo el capítulo: llama a `rewrite_part()` pasando `priority_fix` como instrucción, guarda nueva versión en `written_parts`
3. **Comparar** → panel before/after con código de colores (naranja = original, verde = corregido)
4. **Aceptar o Revertir** → aceptar elimina la comparación; revertir guarda el texto original como nueva versión activa

Los resultados del análisis se cachean en la tabla `style_reviews` para no re-analizar en cada recarga.
