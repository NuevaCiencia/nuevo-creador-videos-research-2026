from utils.llm import call_llm

SYSTEM_SEGMENT = """\
Eres un experto en diseño instruccional y producción de video educativo.

Tu tarea es leer una lista estructurada de fragmentos de guion (párrafos) y asignar a CADA UNO \
el tipo de pantalla más adecuado pedagógicamente para mantener la atención \
y lograr una progresión clara y coherente del contenido.

TIPOS DE PANTALLA DISPONIBLES:
{screen_types_str}

TEMPLATES REMOTION DISPONIBLES (solo para tipo REMOTION):
{remotion_str}

DISTRIBUCIÓN ESPERADA DE TIPOS (orientativa — puede ajustarse por proyecto):
- SPLIT_LEFT / SPLIT_RIGHT / FULL_IMAGE → tipo DOMINANTE. Deben representar el 60-70% de las pantallas. \
Úsalos para la mayoría del contenido explicativo, ejemplos y demostraciones.
- VIDEO → 3-6 pantallas por clase. Para apertura, ejemplos en movimiento o cierre de bloque.
- REMOTION → 2-4 pantallas. Solo cuando hay datos cuantificables, procesos secuenciales, comparaciones o jerarquías.
- LIST → 2-4 pantallas. Solo cuando el narrador enumera 3 o más ítems consecutivos.
- CONCEPT → 1-3 pantallas. Solo para definiciones o términos clave que merecen destacarse.
- TEXT → usar con MODERACIÓN. Máximo 15-20% del total. Solo para apertura de bloque, transición breve y cierre. \
NO uses TEXT como comodín cuando no sabes qué tipo elegir — elige SPLIT_LEFT o SPLIT_RIGHT en su lugar.

REGLAS PEDAGÓGICAS:
1. Mantén coherencia narrativa — cada pantalla debe fluir naturalmente hacia la siguiente.
2. Varía los tipos de pantalla para sostener la atención; no repitas el mismo tipo más de 2 veces seguidas.
3. Usa TEXT para apertura impactante, transiciones breves entre bloques y cierre.
4. Usa LIST cuando el narrador enumera 3 o más ítems consecutivos.
5. Usa CONCEPT para definiciones o términos clave que merecen destacarse visualmente.
6. Usa REMOTION cuando hay datos cuantificables, procesos con pasos secuenciales, \
comparaciones o jerarquías que se benefician de animación.
7. Usa SPLIT_LEFT/SPLIT_RIGHT para ejemplos o demostraciones con imagen de apoyo.
8. Usa FULL_IMAGE para síntesis visuales de alto impacto o cierre con imagen.
9. Respeta los límites de cada tipo (max_items, max_words si se indican).

REGLAS DE PARÁMETROS Y TEMPLATES:
- LIST → params: "@ Título de la Lista // Ítem 1 // Ítem 2 // ..."  (respeta max_items)
- CONCEPT → params: "Nombre del Concepto // Descripción en una sola línea"
- REMOTION → DEBES llenar el campo "remotion_template" con el nombre EXACTO del template elegido (ej. "TypeWriter", "MindMap", etc.). Deja "params" vacío o úsalo solo si el template lo exige.
- TEXT, SPLIT_LEFT, SPLIT_RIGHT, FULL_IMAGE, VIDEO → params: "" y remotion_template: null

REGLA CRÍTICA: El sistema ya ha separado el texto programáticamente en bloques (párrafos). \
Recibirás un JSON con un array de bloques, cada uno con un "id" y un "text". \
Debes devolver EXACTAMENTE el mismo número de elementos que recibes. \
No puedes unir párrafos, ni dividirlos, ni omitir ninguno. Para cada elemento, usa el mismo "id".

Responde ÚNICAMENTE en JSON válido, sin texto adicional:
{{
  "screens": [
    {{
      "id": 0,
      "screen_type": "TEXT",
      "params": "",
      "remotion_template": null, 
      "notes": "Razón breve de la elección de tipo"
    }}
  ]
}}"""


def segment_narration(narration: str, screen_types: list, remotion_templates: list) -> list:
    # Programmatically split by newlines (ignoring empty lines) to guarantee exact 1:1 mapping
    paragraphs = [p.strip() for p in narration.split('\n') if p.strip()]
    if not paragraphs:
        return []

    input_json = [{"id": i, "text": p} for i, p in enumerate(paragraphs)]

    st_lines = []
    for st in screen_types:
        line = f"- {st.name} ({st.category}): {st.description}"
        if st.max_items:
            line += f" [max_items:{st.max_items}]"
        if st.max_words:
            line += f" [max_words:{st.max_words}]"
        if st.has_params:
            line += f" | params: {st.params_syntax}"
        st_lines.append(line)

    rem_lines = [
        f"- {rt.name} ({rt.category}): {rt.description} | {rt.limits}"
        for rt in remotion_templates
    ]

    system = SYSTEM_SEGMENT.format(
        screen_types_str="\n".join(st_lines),
        remotion_str="\n".join(rem_lines) if rem_lines else "No hay templates habilitados.",
    )

    import json
    result = call_llm(
        f"FRAGMENTOS A ANALIZAR:\n\n{json.dumps(input_json, ensure_ascii=False, indent=2)}",
        system,
        temperature=0.3,
        model="gpt-5.4-mini",
    )
    
    # Re-stitch the programmatic text back into the LLM's classification
    llm_screens = result.get("screens", [])
    screens_map = {s.get("id"): s for s in llm_screens if "id" in s}

    final_screens = []
    for i, text in enumerate(paragraphs):
        s_data = screens_map.get(i, {})
        final_screens.append({
            "order": i,
            "screen_type": s_data.get("screen_type", "TEXT"),
            "narration": text,
            "params": s_data.get("params", ""),
            "remotion_template": s_data.get("remotion_template"),
            "notes": s_data.get("notes", "Asignado automáticamente")
        })

    return final_screens
