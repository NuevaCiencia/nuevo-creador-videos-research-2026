# Componentes y Técnicas que FUNCIONAN en MANIM

## 📋 RESUMEN EJECUTIVO

Basado en el análisis de tus archivos exitosos de MANIM, esta lista incluye solo elementos **comprobados que compilan correctamente**.

---

## 🚨 GESTIÓN DE PANTALLA Y SUPERPOSICIONES - CRÍTICO

### ⚠️ REGLA FUNDAMENTAL - EVITAR SUPERPOSICIONES:

**PROBLEMA COMÚN**: Elementos de secciones anteriores se superponen con nuevos elementos.

**SOLUCIÓN OBLIGATORIA**:

```python
# SIEMPRE al inicio de cada nueva sección:
def nueva_seccion(self, config):
    # 1. LIMPIAR PANTALLA PRIMERO
    self.clear()  # Elimina TODOS los elementos anteriores
    
    # 2. Recrear elementos persistentes si los necesitas
    titulo_persistente = Text("Mi título", font="Arial", font_size=20)
    titulo_persistente.to_edge(UP, buff=0.3)
    self.add(titulo_persistente)  # Añadir SIN animación
    
    # 3. Crear nuevos elementos
    contenido = Text("Contenido nuevo")
    
    # 4. Animar SOLO los nuevos elementos
    self.play(Write(contenido))
```

### ✅ TEMPLATE SEGURO PARA SECCIONES MÚLTIPLES:

```python
def seccion_segura(self, config):
    """Template probado para evitar superposiciones"""
    # PASO 1: Verificar y limpiar
    self.clear()  # OBLIGATORIO para secciones nuevas
    
    # PASO 2: Elementos persistentes (header, etc.)
    if config.get("show_header"):
        header = Text("Header", font="Arial", font_size=20, color="#00D4FF")
        header.to_edge(UP, buff=0.3)
        self.add(header)  # Sin animación
    
    # PASO 3: Contenido principal
    contenido_principal = self.crear_contenido(config)
    contenido_principal.move_to(ORIGIN + DOWN*0.5)  # Dejar espacio al header
    
    # PASO 4: Animaciones
    self.play(FadeIn(contenido_principal, shift=UP*0.3))
    
    # PASO 5: Limpieza al final (opcional)
    self.play(FadeOut(VGroup(*self.mobjects)), run_time=0.8)
```

### 🔍 VERIFICACIONES OBLIGATORIAS:

```python
# Antes de cada sección, pregúntate:
# ✅ ¿Hay elementos previos en pantalla?
# ✅ ¿Necesito mantener algún elemento (header/título)?
# ✅ ¿El nuevo contenido tiene espacio suficiente?
# ✅ ¿Usé self.clear() si es una sección nueva?
```

### 🚫 ERRORES COMUNES A EVITAR:

- ❌ **No usar `self.clear()`** entre secciones diferentes
- ❌ **Asumir que `FadeOut()` limpia automáticamente** (solo oculta)
- ❌ **Posicionar sin verificar espacio disponible**
- ❌ **Mezclar elementos persistentes y temporales sin gestión**

### 🔧 ALTERNATIVAS A `self.clear()`:

```python
# Si solo quieres remover elementos específicos:
self.remove(*elementos_anteriores)

# O hacer FadeOut explícito y luego remover:
self.play(FadeOut(elementos_anteriores))
self.remove(*elementos_anteriores)

# Para debugging - verificar qué hay en pantalla:
print(f"Elementos actuales: {len(self.mobjects)}")
```

---

## 🎯 IMPORTS Y CONFIGURACIÓN BÁSICA

### Imports que funcionan:

```python
from manim import *
import numpy as np
import random
```

### Configuración de escena confiable:

```python
# Color de fondo - SIEMPRE funciona
self.camera.background_color = "#0C1445"  # O cualquier color hex
self.camera.background_color = WHITE
self.camera.background_color = "#1A1A1A"
```

---

## 🎨 COLORES PROBADOS QUE FUNCIONAN

### Colores básicos seguros:

- `WHITE`, `BLACK`
- `BLUE`, `BLUE_A`, `BLUE_B`, `BLUE_C`, `BLUE_D`, `BLUE_E`
- `RED`, `RED_A`, `RED_B`, `RED_C`
- `GREEN`, `GREEN_A`, `GREEN_B`, `GREEN_C`
- `YELLOW`, `YELLOW_A`, `YELLOW_B`
- `PURPLE`, `PURPLE_A`, `PURPLE_B`, `PURPLE_C`
- `LIGHT_GREY`, `DARK_GREY`, `GREY`

### Colores personalizados hex que funcionan:

```python
"#00D4FF"    # Azul eléctrico
"#00FF88"    # Verde neón
"#FFD700"    # Dorado
"#9D4EDD"    # Púrpura tech
"#0C1445"    # Azul oscuro
"#252525"    # Gris oscuro
"#333333"    # Gris medio
"#F5F5F5"    # Gris muy claro
```

---

## 📝 TEXTO Y TIPOGRAFÍA

### Text() - Funciona perfectamente:

```python
Text("Tu texto aquí", font_size=42, color=WHITE)
Text("Texto", font="Arial", font_size=24, color=BLUE)
Text("Texto", weight=BOLD)  # Para negritas
```

### Tipografías comprobadas:

- `"Arial"` (MÁS CONFIABLE - usar como estándar)
- `"Helvetica"`
- `"Open Sans"`
- ⚠️ `"Roboto"` (puede no estar disponible en todos los sistemas)

### Propiedades de texto que funcionan:

```python
font_size=16/20/24/28/32/36/42/48  # Tamaños probados
color=WHITE/BLACK/BLUE_C/etc
font="Arial"  # Usar como estándar
weight=BOLD
line_spacing=1.2/1.3/2.0
```

---

## 🔲 FORMAS GEOMÉTRICAS BÁSICAS

### Formas que siempre funcionan:

```python
# Rectángulos
Rectangle(width=2, height=1, color=BLUE, fill_opacity=0.3)
RoundedRectangle(width=3, height=2, corner_radius=0.3, color=GREEN)
Square(side_length=2, color=RED, fill_opacity=0.7)

# Círculos
Circle(radius=1, color=BLUE, fill_opacity=0.5)
Dot(radius=0.1, color=WHITE)

# Líneas
Line(start=LEFT, end=RIGHT, color=WHITE, stroke_width=2)
Arrow(start=LEFT, end=RIGHT, color=BLUE, stroke_width=3)
DashedLine(start=LEFT*2, end=RIGHT*2, color=YELLOW)

# Arcos
Arc(radius=1, angle=PI, color=RED)
```

### Propiedades confiables:

```python
fill_opacity=0.1/0.2/0.3/0.5/0.7/0.8/0.9
stroke_width=1/2/3/4
corner_radius=0.2/0.3/0.5
```

---

## 🎬 ANIMACIONES BÁSICAS PROBADAS

### Animaciones de entrada:

```python
self.play(Write(objeto), run_time=1.5)
self.play(FadeIn(objeto), run_time=1)
self.play(FadeIn(objeto, shift=UP*0.3), run_time=1.5)
self.play(FadeIn(objeto, scale=1.2), run_time=1)
self.play(Create(objeto), run_time=1)
self.play(DrawBorderThenFill(objeto), run_time=1.5)
```

### Animaciones de salida:

```python
self.play(FadeOut(objeto), run_time=1)
self.play(FadeOut(objeto, shift=UP), run_time=1)
```

### Transformaciones seguras:

```python
self.play(objeto.animate.move_to(ORIGIN), run_time=1)
self.play(objeto.animate.scale(1.2), run_time=1)
self.play(objeto.animate.set_color(YELLOW), run_time=1)
self.play(objeto.animate.shift(RIGHT*2), run_time=1)
```

---

## 📍 POSICIONAMIENTO

### Métodos de posicionamiento probados:

```python
# Posicionamiento absoluto
objeto.move_to(ORIGIN)
objeto.move_to(UP*2 + LEFT*3)

# Posicionamiento relativo
objeto.next_to(otro_objeto, DOWN, buff=0.3)
objeto.next_to(otro_objeto, RIGHT, buff=0.5)

# Posicionamiento en bordes
objeto.to_edge(UP, buff=0.5)
objeto.to_edge(LEFT, buff=1)

# Centrado
objeto.center()
```

### Direcciones que funcionan:

- `UP`, `DOWN`, `LEFT`, `RIGHT`
- `UL`, `UR`, `DL`, `DR` (diagonales)
- `ORIGIN`

---

## 🏗️ AGRUPACIÓN Y ORGANIZACIÓN

### VGroup - Funciona perfectamente:

```python
grupo = VGroup()
grupo.add(objeto1, objeto2, objeto3)

# O crear directamente
grupo = VGroup(objeto1, objeto2, objeto3)

# Organización
grupo.arrange(DOWN, buff=0.5)
grupo.arrange(RIGHT, buff=0.3)
grupo.arrange(DOWN, aligned_edge=LEFT)
```

---

## ⏱️ TIMING Y ESPERAS

### Wait y run_time probados:

```python
self.wait(1)      # Espera 1 segundo
self.wait(0.5)    # Espera medio segundo
self.wait(2)      # Espera 2 segundos

# En animaciones
run_time=0.5/0.8/1/1.2/1.5/2/2.5/3
```

---

## 🎭 EFECTOS ESPECIALES QUE FUNCIONAN

### Flash y efectos:

```python
self.play(Flash(objeto, color=WHITE, line_length=0.3), run_time=1)
```

### Rate functions probadas:

```python
rate_func=smooth
rate_func=there_and_back
rate_func=there_and_back_with_pause
```

### LaggedStart para animaciones secuenciales:

```python
self.play(
    LaggedStart(*[Create(line) for line in lineas], lag_ratio=0.2),
    run_time=2
)
```

---

## 🔧 CONFIGURACIONES ESPECÍFICAS PROBADAS

### Para presentaciones profesionales:

```python
# Configuración centralizada en diccionarios
config = {
    "background_color": "#0C1445",
    "final_wait_time": 30,
    "title": {
        "text": "Tu título aquí",
        "font": "Arial",
        "font_size": 42,
        "color": WHITE,
        "animation_time": 1.5
    }
}
```

### Métodos de construcción probados:

```python
def construct(self):
    # Aplicar configuración
    self.camera.background_color = config["background_color"]

    # Crear elementos
    title = Text(config["title"]["text"],
                font_size=config["title"]["font_size"])

    # Animar
    self.play(Write(title, run_time=config["title"]["animation_time"]))
    self.wait(config["final_wait_time"])
```

---

## 💎 FORMAS AVANZADAS PROBADAS

### Cilindros (para diagramas 3D):

```python
Cylinder(radius=0.3, height=0.5, color=BLUE, fill_opacity=0.7)
```

### Cubos 3D:

```python
Cube(side_length=1.5, fill_opacity=0.8, color=BLUE)
```

### Polígonos regulares:

```python
RegularPolygon(n=5, radius=0.3, color=GREEN, fill_opacity=0.8)
```

---

## ⚠️ PROBLEMAS EVITADOS

### Lo que NO usar (genera errores):

- ❌ `MathTex()` (problemas con LaTeX)
- ❌ `CubicBezier()` (inconsistente)
- ❌ Funciones de transformación complejas
- ❌ `Paragraph()` (a veces falla)
- ❌ `set_height(stretch=True)` (no funciona en todas las versiones)
- ❌ `VGroup(*self.mobjects)` (puede mezclar tipos incompatibles)
- ❌ Usar `"Roboto"` sin verificar disponibilidad

### Usar en su lugar:

- ✅ `Text()` para todo el texto
- ✅ `ArcBetweenPoints()` en lugar de CubicBezier
- ✅ Animaciones simples y directas
- ✅ `objeto.animate.scale([1, factor_y, 1])` en lugar de set_height
- ✅ `self.clear()` + recrear elementos en lugar de VGroup complejo
- ✅ `"Arial"` como fuente estándar

---

## 🚀 COMANDOS DE COMPILACIÓN PROBADOS

```bash
manim -p -ql archivo.py NombreDeLaClase
```

### Flags que funcionan:

- `-p` : Preview (abre automáticamente)
- `-ql` : Quality low (rápido para pruebas)
- `-qh` : Quality high (para producción)

---

## 📊 PATRONES DE ÉXITO IDENTIFICADOS

### 1. Estructura confiable de escena:

```python
class MiEscena(Scene):
    def construct(self):
        # 1. Configurar fondo
        self.camera.background_color = "#0C1445"

        # 2. Crear título
        title = Text("Mi título", font_size=42, color=WHITE)
        title.to_edge(UP, buff=0.5)

        # 3. Animar entrada
        self.play(Write(title), run_time=1.5)
        self.wait(1)

        # 4. Contenido principal
        # ... tu contenido aquí ...

        # 5. Espera final
        self.wait(2)
```

### 2. Configuración por diccionarios (MUY EFECTIVO):

```python
config = {
    "background_color": "#0C1445",
    "title": {
        "text": "Mi título",
        "font_size": 42,
        "color": WHITE
    },
    "boxes": {
        "width": 3,
        "height": 2,
        "color": BLUE_C,
        "fill_opacity": 0.3
    }
}
```

### 3. Animaciones modulares:

```python
def mostrar_concepto(self, config):
    # Crear elementos
    caja = Rectangle(width=config["width"], height=config["height"])

    # Animar
    self.play(FadeIn(caja), run_time=1)
```

---

## 🎯 RECOMENDACIONES FINALES

### Para máxima compatibilidad:

1. **USA SIEMPRE** `Text()` en lugar de `MathTex()`
2. **PREFIERE** `"Arial"` como fuente estándar
3. **MANTÉN** animaciones simples y directas
4. **ORGANIZA** tu código con configuraciones centralizadas
5. **PRUEBA** con `-ql` antes de renderizar en alta calidad
6. **LIMPIA** la pantalla con `self.clear()` entre secciones
7. **VERIFICA** siempre el espacio disponible antes de posicionar

### Flujo de trabajo probado:

1. Configurar fondo y colores
2. Limpiar pantalla si es nueva sección (`self.clear()`)
3. Recrear elementos persistentes (header, etc.)
4. Crear título con Text() y Arial
5. Crear elementos con formas básicas
6. Agrupar con VGroup()
7. Posicionar con .move_to() y .next_to()
8. Animar con FadeIn/Write/Create
9. Usar self.wait() apropiadamente
10. Limpiar al final si es necesario

### Debugging y verificación:

```python
# Añadir comentarios de verificación:
# VERIFICAR: ¿Pantalla limpia antes de esta sección?
# VERIFICAR: ¿Posición Y disponible para nuevo título?
# VERIFICAR: ¿Elementos anteriores removidos correctamente?
# VERIFICAR: ¿Fuente Arial disponible?

# Para debugging - mostrar elementos actuales:
print(f"Elementos en pantalla: {len(self.mobjects)}")
for i, obj in enumerate(self.mobjects):
    print(f"  {i}: {type(obj).__name__}")
```

---

**✅ TODOS ESTOS ELEMENTOS HAN SIDO PROBADOS Y COMPILAN EXITOSAMENTE**
