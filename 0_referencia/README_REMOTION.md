# 🎬 Guía Completa: Sistema de Pantallas REMOTION

El sistema **REMOTION** ha sido diseñado para integrar animaciones gráficas complejas y dinámicas (Motion Graphics o similares) dentro de nuestro pipeline automatizado de generación de video, delegando la creación de parámetros complicados a un modelo de IA especializado (LLM).

Aquí explicamos cómo funciona de punta a punta.

---

## 🏗️ 1. Uso Básico (El lado humano)

Para introducir una pantalla Remotion en tu video, lo único que necesitas hacer es editar tu archivo `original_speech.md` con la siguiente etiqueta:

```markdown
<!-- type:REMOTION // $NombreDelTemplate -->
==Texto hablado que servirá de contexto para que la IA deduzca qué mostrar...==
```

**Es fundamental que incluyas el símbolo `$` seguido del nombre exacto de la plantilla soportada.** Tú *no* configuras los parámetros manualmente; la IA lo hará por ti leyendo el discurso. Por ahora, las plantillas predefinidas son:
- `$TypeWriter` (Terminal Hacker)
- `$MindMap` (Mapa Mental)
- `$LinearSteps` (Pasos secuenciales)

---

## 🧠 2. Cómo funciona la "Magia" (El flujo interno)

Cuando ejecutas `python 01_preparacion.py --desde-fase 3`, el orquestador (`VisualOrchestrator`) despliega el siguiente flujo:

1. **Intercepción:** Escanea el guion, separa las etiquetas REMOTION y guarda su posición temporal y duración **real calculada a milisegundo**.
2. **Nombramiento Automático:** A cada clip se le asigna secuencialmente un identificador técnico estilo `REM01.mp4`, `REM02.mp4`, etc.
3. **El Cerebro Dedicado (`RemotionAssistant`):** El orquestador envía un JSON compacto estructurado al nuevo cerebro especializado de IA. Este bot utiliza un *system prompt* almacenado en `root/ai_config.yaml` que le enseña las reglas de estructuras esperadas.
4. **La Respuesta:** La IA devuelve el YAML ya estructurado, tomando palabras clave del locutor (`speech`) y colocándolas de la forma ideal en pantalla (por ejemplo, dividiendo pasos en un bucle lógico).

---

## 📂 3. Entregables del Pipeline

Al finalizar la preparación de la fase 3, tu proyecto tendrá dos grandes actualizaciones referidas a Remotion:

### A. Recursos Dummies (`proyectos/X/assets/videos/`)
El `Dummy Builder` genera los archivos `.mp4` con los nombres técnicos exigidos (ej. `REM01.mp4`). El fondo gris de prueba dirá claramente **REMOTION REM01.mp4**.

### B. El YAML Final (`proyectos/X/output/03_guion/recursos_remotion.yaml`)
El archivo definitivo y limpio que otro sistema/software (como Remotion/React) usará para mandar a producir las pantallas finales. Estructura esperada:

```yaml
videos:
  - template: TypeWriter
    output: REM01.mp4
    duration: "0:45"
    data:
      accent: "#00FF41"
      lines:
        - prefix: "$ "
          text: "Hackeando el pipeline"
          delay: 0
        - prefix: "> "
          text: "Terminado"
          delay: 60
```

> **NOTA CRÍTICA SOBRE EL TIEMPO**: El campo `duration` en este yaml NO es un tiempo simulado. El Orquestador captura los minutos y segundos literales del segmento hablado ("MM:SS") para que la animación termine junto con tu locución.

---

## 🖥 4. Integración en el "Visualizador Maestro" UI

¿Qué pasa cuando abres la web (`python visualizador_pantallas.py`) para editar?

- **Color UI:** Visualmente, los Remotion se pintan de un **Cian Verdoso**.
- **Seguridad y Bloqueo:** Remotion es categorizado internamente dentro de `TYPES_FORBIDDING_TEXT`. Por consiguiente, aunque el archivo haya exportado algo o trates de hacer clic, el panel derecho ("Texto en Pantalla") estará **grisáceo e inhabilitado**.
- Esto previene corrupciones cruzadas, recordándote que la "edición" real de su contenido no se hace directamente aquí a nivel de bloques de subtítulo, sino que está respaldada en el YAML particular (`recursos_remotion.yaml`).
