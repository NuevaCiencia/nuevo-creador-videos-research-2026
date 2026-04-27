from manim import *

class ElegantConceptPresentation(Scene):
    def construct(self):
        # Configuración centralizada con fondo blanco y estilo elegante
        config = {
            # Configuración general
            "background_color": WHITE,
            "final_wait_time": 40,
            
            # Configuración del título
            "title": {
                "text": "Vibe Coding: Revolución en la Programación",
                "font": "Helvetica",
                "font_size": 38,
                "color": "#333333",
                "buff_from_top": 0.5,
                "animation_time": 1.5,
                "wait_after_title": 0.5
            },
            
            # Configuración de la caja de concepto
            "concept_box": {
                "width": 12,
                "height": 6,
                "corner_radius": 0.5,
                "fill_color": "#F5F5F5",
                "fill_opacity": 1.0,
                "stroke_color": "#DDDDDD",
                "stroke_width": 1.5,
                "buff_from_title": 0.5,
                "animation_time": 1.0,
                "shadow_opacity": 0.1,
            },
            
            # Configuración del título del concepto
            "concept_title": {
                "text": "Cambio de Paradigma en el Desarrollo",
                "font": "Helvetica",
                "font_size": 36,
                "color": "#2C3E50",
                "buff_from_top": 0.5,
                "animation_time": 1.0,
            },
            
            # Configuración del contenido del concepto
            "concept_content": {
                "text": (
                    "El vibe coding transforma la programación:\n"
                    "• El programador actúa como director, usando lenguaje natural.\n"
                    "• Se eliminan barreras de sintaxis (puntos y comas, bloques, tabulaciones).\n"
                    "• Modelos como ChatGPT, Deepseek, Claude y Gemini generan el código.\n"
                    "• Proceso iterativo: expresar intención, revisión, retroalimentación y refinamiento.\n"
                    "• Popularizado en 2025, impulsa la creatividad en el desarrollo de software."
                ),
                "font": "Helvetica",
                "font_size": 28,
                "color": "#555555",
                "line_spacing": 1.2,
                "buff_from_title": 0.6,
                "animation_time": 1.5,
            }
        }

        # Aplicar color de fondo
        self.camera.background_color = config["background_color"]
        
        # Crear y animar el título
        title = Text(
            config["title"]["text"], 
            font_size=config["title"]["font_size"], 
            color=config["title"]["color"], 
            font=config["title"]["font"]
        )
        title.to_edge(UP, buff=config["title"]["buff_from_top"])
        
        # Animación elegante para el título
        self.play(
            FadeIn(title, shift=UP*0.3),
            run_time=config["title"]["animation_time"]
        )
        self.wait(config["title"]["wait_after_title"])
        
        # Mostrar la caja de concepto con sombra y efectos elegantes
        self.mostrar_caja_concepto(title, config)
        
        # Esperar al final
        self.wait(config["final_wait_time"])

    def mostrar_caja_concepto(self, title, config):
        # Crear la caja principal
        caja = RoundedRectangle(
            width=config["concept_box"]["width"],
            height=config["concept_box"]["height"],
            corner_radius=config["concept_box"]["corner_radius"],
            stroke_width=config["concept_box"]["stroke_width"],
            stroke_color=config["concept_box"]["stroke_color"],
            fill_color=config["concept_box"]["fill_color"],
            fill_opacity=config["concept_box"]["fill_opacity"]
        )
        
        # Crear efecto de sombra (una caja ligeramente más grande detrás)
        sombra = RoundedRectangle(
            width=config["concept_box"]["width"] + 0.1,
            height=config["concept_box"]["height"] + 0.1,
            corner_radius=config["concept_box"]["corner_radius"] + 0.05,
            stroke_width=0,
            fill_color=DARK_GRAY,
            fill_opacity=config["concept_box"]["shadow_opacity"]
        )
        sombra.shift(DOWN * 0.1 + RIGHT * 0.1)  # Desplazar para efecto de sombra
        
        # Grupo de la caja con su sombra
        caja_grupo = Group(sombra, caja)
        caja_grupo.next_to(title, DOWN, buff=config["concept_box"]["buff_from_title"])
        
        # Animar la aparición de la caja con su sombra
        self.play(
            FadeIn(sombra, scale=1.02),
            FadeIn(caja, scale=1.01),
            run_time=config["concept_box"]["animation_time"]
        )
        
        # Crear el título del concepto con un estilo elegante
        concepto_titulo = Text(
            config["concept_title"]["text"],
            font_size=config["concept_title"]["font_size"],
            color=config["concept_title"]["color"],
            font=config["concept_title"]["font"],
            weight=BOLD
        )
        
        # Posicionar el título del concepto
        concepto_titulo.next_to(
            caja.get_top(), 
            DOWN, 
            buff=config["concept_title"]["buff_from_top"]
        )
        
        # Animar la aparición del título del concepto
        self.play(
            Write(concepto_titulo),
            run_time=config["concept_title"]["animation_time"]
        )
        
        # Crear una línea elegante debajo del título
        linea = Line(
            start=concepto_titulo.get_corner(DOWN + LEFT) + LEFT * 1.5,
            end=concepto_titulo.get_corner(DOWN + RIGHT) + RIGHT * 1.5,
            stroke_width=1,
            color="#AAAAAA"
        )
        linea.next_to(concepto_titulo, DOWN, buff=0.2)
        
        self.play(
            Create(linea),
            run_time=0.5
        )
        
        # Crear el contenido del concepto
        contenido = Text(
            config["concept_content"]["text"],
            font_size=config["concept_content"]["font_size"],
            color=config["concept_content"]["color"],
            font=config["concept_content"]["font"],
            line_spacing=config["concept_content"]["line_spacing"]
        )
        
        # Asegurar que quepa dentro de la caja
        max_width = caja.width * 0.85
        if contenido.width > max_width:
            contenido.scale_to_fit_width(max_width)
        
        # Posicionar el contenido
        contenido.next_to(
            linea, 
            DOWN, 
            buff=config["concept_content"]["buff_from_title"]
        )
        
        # Animar la aparición del contenido de forma elegante
        self.play(
            FadeIn(contenido, lag_ratio=0.1),
            run_time=config["concept_content"]["animation_time"]
        )