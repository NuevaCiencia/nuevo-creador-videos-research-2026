from manim import *

class SimpleConceptsPresentation(Scene):
    def construct(self):
        # Configuración centralizada - Editar estos valores para personalizar la animación
        config = {
            # Configuración general
            "background_color": "#0C1445",    # Color de fondo
            "final_wait_time": 30,            # Tiempo de espera final en segundos
            "highlight_color": YELLOW,        # Color de resaltado
            
            # Configuración del título
            "title": {
                "text": "Conceptos Fundamentales de Programación",
                "font": "Arial",
                "font_size": 42,
                "color": WHITE,
                "buff_from_top": 1,         # Espacio desde el borde superior
                "animation_time": 1.5,        # Duración de la animación del título
                "wait_after_title": 0.8       # Espera después del título
            },
            
            # Configuración de los conceptos
            "concepts": {
                "vertical_spacing": 0.7,      # Espacio vertical entre conceptos
                "buff_from_title": 1,       # Espacio desde el título
                "animation_time": 1.0,        # Duración de la animación de cada concepto
                "highlight_time": 0.5,        # Duración de la animación de resaltado
                "wait_between_concepts": 1.0, # Espera entre cada concepto
                "wait_before_highlight": 1.5, # Espera antes de resaltar
                
                # Configuración del texto de los conceptos
                "text": {
                    "font": "Arial",
                    "font_size": 30,
                    "color": WHITE,
                },
                # Configuración del bullet
                "bullet": {
                    "radius": 0.08,         # Tamaño del bullet
                    "color": WHITE,          # Color igual al texto
                    "spacing": 0.4           # Espacio entre bullet y texto
                }
            },
            
            # Lista de conceptos a presentar
            "concept_list": [
                "Variables: Almacenan datos con tipos específicos",
                "Condicionales: Controlan el flujo basado en condiciones",
                "Funciones: Bloques de código reutilizables",
                "Bucles: Repiten código de forma controlada"
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
        
        # Crear y mostrar los conceptos
        self.mostrar_conceptos(title, config)
        
        # Esperar el tiempo especificado al final
        self.wait(config["final_wait_time"])

    def mostrar_conceptos(self, title, config):
        # Crear todos los conceptos como textos con bullets
        conceptos = VGroup()
        bullets = VGroup()  # Grupo para los bullets
        
        for texto_concepto in config["concept_list"]:
            # Crear el texto del concepto
            concepto = Text(
                texto_concepto,
                font_size=config["concepts"]["text"]["font_size"],
                color=config["concepts"]["text"]["color"],
                font=config["concepts"]["text"]["font"]
            )
            
            # Crear bullet para el concepto
            bullet = Dot(
                radius=config["concepts"]["bullet"]["radius"],
                color=config["concepts"]["bullet"]["color"]
            )
            
            # Agrupar concepto y su bullet
            item = VGroup(bullet, concepto)
            item.arrange(RIGHT, buff=config["concepts"]["bullet"]["spacing"])  # Espacio entre bullet y texto
            
            conceptos.add(item)
            bullets.add(bullet)  # Añadir bullet al grupo de bullets para resaltarlo después
        
        # Organizar los conceptos uno debajo del otro
        conceptos.arrange(
            DOWN, 
            buff=config["concepts"]["vertical_spacing"],
            aligned_edge=LEFT
        )
        
        # Posicionar los conceptos debajo del título y alineados con el margen izquierdo del título
        conceptos.next_to(
            title, 
            DOWN, 
            buff=config["concepts"]["buff_from_title"]
        )
        
        # Alinear con el margen izquierdo del título
        left_edge = title.get_left()[0]  # Obtener la coordenada X del borde izquierdo del título
        for item in conceptos:
            # Crear un punto de referencia con la coordenada X del título
            punto_referencia = np.array([left_edge, item.get_center()[1], 0])
            item.align_to(punto_referencia, LEFT)
        
        # Primero mostrar todos los conceptos en secuencia
        for i, concepto in enumerate(conceptos):
            # Mostrar el concepto con una animación de escritura
            self.play(
                FadeIn(concepto, shift=RIGHT*0.3),
                run_time=config["concepts"]["animation_time"]
            )
            
            # Esperar entre conceptos
            if i < len(conceptos) - 1:
                self.wait(config["concepts"]["wait_between_concepts"])
        
        # Esperar antes de comenzar a resaltar
        self.wait(config["concepts"]["wait_before_highlight"])
        
        # Luego resaltar cada concepto y su bullet en secuencia
        for i, item in enumerate(conceptos):
            bullet = item[0]  # El primer elemento es el bullet
            concepto = item[1]  # El segundo elemento es el texto
            
            # Resaltar tanto el concepto como su bullet en amarillo
            self.play(
                concepto.animate.set_color(config["highlight_color"]),
                bullet.animate.set_color(config["highlight_color"]),
                run_time=config["concepts"]["highlight_time"]
            )
            self.wait(0.5)  # Breve pausa entre cada resaltado