from utils.llm import call_llm

SYSTEM_SEGMENT = """\
Eres un experto en diseño instruccional y producción de video educativo.

Tu tarea es leer un guion de locución y dividirlo en PANTALLAS, asignando a cada \
fragmento el tipo de pantalla más adecuado pedagógicamente para mantener la atención \
y lograr una progresión clara y coherente del contenido.

TIPOS DE PANTALLA DISPONIBLES:
{screen_types_str}

TEMPLATES REMOTION DISPONIBLES (solo para tipo REMOTION):
{remotion_str}

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
9. Cada pantalla debe cubrir entre 15 y 60 segundos de locución aproximadamente.
10. Respeta los límites de cada tipo (max_items, max_words si se indican).

REGLAS DE PARÁMETROS:
- LIST → params: "@ Título de la Lista // Ítem 1 // Ítem 2 // ..."  (respeta max_items)
- CONCEPT → params: "Nombre del Concepto // Descripción en una sola línea"
- REMOTION → params: "$NombreTemplate"  (nombre exacto del template elegido)
- TEXT, SPLIT_LEFT, SPLIT_RIGHT, FULL_IMAGE, VIDEO → params: ""

REGLA CRÍTICA: El campo "narration" de cada pantalla es el texto EXACTO que el locutor \
dice mientras esa pantalla es visible. NO inventes texto ni resumas — solo divide y \
asigna fragmentos del guion original tal como aparecen.

Responde ÚNICAMENTE en JSON válido, sin texto adicional:
{{
  "screens": [
    {{
      "order": 1,
      "screen_type": "TEXT",
      "narration": "Fragmento exacto del guion para esta pantalla",
      "params": "",
      "remotion_template": null,
      "notes": "Razón breve de la elección de tipo"
    }}
  ]
}}"""


def segment_narration(narration: str, screen_types: list, remotion_templates: list) -> list:
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

    result = call_llm(
        f"GUION A SEGMENTAR:\n\n{narration}",
        system,
        temperature=0.3,
        model="gpt-5.4-mini",
    )
    return result.get("screens", [])
