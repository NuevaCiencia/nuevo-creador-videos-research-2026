from manim import *

class ConceptBoxesMinimal(Scene):
    def construct(self):
        # Configuración centralizada - Editar estos valores para personalizar la animación
        config = {
            # Configuración general
            "background_color": "#0C1445",  # Color de fondo
            "final_wait_time": 30,          # Tiempo de espera final en segundos
            
            # Configuración del título
            "title": {
                "text": "Conceptos Fundamentales de Programación",
                "font": "Arial",
                "font_size": 42,
                "color": WHITE,
                "buff_from_top": 1.5,       # Espacio desde el borde superior
                "animation_time": 1.5,      # Duración de la animación del título
                "wait_after_title": 0.8     # Espera después del título
            },
            
            # Configuración de las cajas
            "boxes": {
                "side_length": 2.7,         # Tamaño del cuadrado (aumentado para dar más espacio al texto)
                "fill_opacity": 0.2,        # Opacidad del relleno
                "stroke_width": 2,          # Grosor del borde
                "spacing": 0.7,             # Espacio entre cajas
                "buff_from_title": 1.2,     # Espacio desde el título
                "animation_time": 1.0,      # Duración de la animación de cada caja
                "wait_between_boxes": 0.3,  # Espera entre cada aparición de caja
                
                # Configuración del título de las cajas
                "title": {
                    "font": "Arial",
                    "font_size": 22,
                    "weight": "BOLD",
                    "position_y": 0.7       # Posición vertical del título en la caja
                },
                
                # Configuración de la línea separadora
                "separator_line": {
                    "y_position": 0.4,      # Posición vertical de la línea
                    "length": 2.0,          # Longitud de la línea (ancho)
                    "stroke_width": 1       # Grosor de la línea
                },
                
                # Configuración de la descripción
                "description": {
                    "font": "Arial",
                    "font_size": 15,        # Tamaño natural de fuente más pequeño
                    "color": WHITE,
                    "line_spacing": 2.0,    # Mayor espaciado entre líneas para mejor legibilidad
                    "y_position": -0.1,     # Posición vertical de la descripción
                    "margin": 1.2,          # Margen interno más amplio desde los bordes
                    "scale_factor": 1.0     # Sin escalado adicional (tamaño natural)
                }
            },
            
            # Contenido de las cajas - Editar para cambiar el contenido
            "concepts": [
                {
                    "título": "Variables",
                    "descripción": "Almacenan datos\ncon tipos específicos",
                    "color": BLUE_C
                },
                {
                    "título": "Condicionales",
                    "descripción": "Controlan el flujo\nbasado en condiciones",
                    "color": GREEN_C
                },
                {
                    "título": "Funciones",
                    "descripción": "Bloques de código\nreutilizables",
                    "color": RED_C
                },
                {
                    "título": "Bucles",
                    "descripción": "Repiten código\nde forma controlada",
                    "color": PURPLE_C
                }
            ]
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
        
        # Animar la entrada del título
        self.play(Write(title, run_time=config["title"]["animation_time"]))
        self.wait(config["title"]["wait_after_title"])
        
        # Crear y mostrar las cajas de conceptos
        self.mostrar_conceptos(title, config)
        
        # Esperar el tiempo especificado al final
        self.wait(config["final_wait_time"])

    def mostrar_conceptos(self, title, config):
        # Crear las cajas de conceptos
        todas_las_cajas = VGroup()
        
        for concepto in config["concepts"]:
            # Crear cuadrado para cada concepto
            cuadrado = Square(
                side_length=config["boxes"]["side_length"], 
                color=concepto["color"], 
                fill_opacity=config["boxes"]["fill_opacity"],
                stroke_width=config["boxes"]["stroke_width"]
            )
            
            # Título de la caja
            titulo = Text(
                concepto["título"], 
                font_size=config["boxes"]["title"]["font_size"],
                color=concepto["color"],
                font=config["boxes"]["title"]["font"],
                weight=config["boxes"]["title"]["weight"]
            )
            titulo.move_to(cuadrado.get_center() + UP*config["boxes"]["title"]["position_y"])
            
            # Línea separadora
            linea = Line(
                start=cuadrado.get_center() + 
                      UP*config["boxes"]["separator_line"]["y_position"] + 
                      LEFT*config["boxes"]["separator_line"]["length"]/2,
                end=cuadrado.get_center() + 
                    UP*config["boxes"]["separator_line"]["y_position"] + 
                    RIGHT*config["boxes"]["separator_line"]["length"]/2,
                stroke_width=config["boxes"]["separator_line"]["stroke_width"],
                color=concepto["color"]
            )
            
            # Descripción 
            descripcion = Text(
                concepto["descripción"], 
                font_size=config["boxes"]["description"]["font_size"],
                color=config["boxes"]["description"]["color"],
                font=config["boxes"]["description"]["font"],
                line_spacing=config["boxes"]["description"]["line_spacing"]
            )
            
            # Posición vertical de la descripción
            descripcion.move_to(cuadrado.get_center() + 
                             DOWN*-config["boxes"]["description"]["y_position"])
            
            # Asegurar que la descripción no toque los bordes del cuadrado
            margin = config["boxes"]["description"]["margin"]
            if descripcion.width > cuadrado.width - margin:
                descripcion.scale_to_fit_width(cuadrado.width - margin)
            
            # Aplicar factor de escala solo si es diferente de 1.0
            if config["boxes"]["description"]["scale_factor"] != 1.0:
                descripcion.scale(config["boxes"]["description"]["scale_factor"])
            
            # Agrupar todos los elementos
            caja_concepto = VGroup(cuadrado, titulo, linea, descripcion)
            todas_las_cajas.add(caja_concepto)
        
        # Organizar todas las cajas en una sola fila horizontal
        fila_horizontal = VGroup(*todas_las_cajas).arrange(
            RIGHT, 
            buff=config["boxes"]["spacing"]
        )
        
        # Posicionar la fila debajo del título con espacio suficiente
        fila_horizontal.next_to(
            title, 
            DOWN, 
            buff=config["boxes"]["buff_from_title"]
        )
        
        # Mostrar cada caja una por una con animación
        for caja in todas_las_cajas:
            self.play(
                FadeIn(caja, shift=UP*0.2), 
                run_time=config["boxes"]["animation_time"]
            )
            self.wait(config["boxes"]["wait_between_boxes"])