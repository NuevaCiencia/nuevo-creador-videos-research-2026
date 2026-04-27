from manim import *
import numpy as np
import random

class VideoManim(Scene):
    def construct(self):
        # Configuración centralizada
        config = {
            # Configuración general
            "background_color": "#0C1445",
            "total_duration": 9.746,
            "final_wait_time": 0.5,
            
            # Configuración del título principal
            "title": {
                "text": "REVOLUCIÓN TECNOLÓGICA",
                "font": "Arial",
                "font_size": 42,
                "color": WHITE,
                "animation_time": 1.5,
                "wait_after": 0.8
            },
            
            # Configuración de la línea de tiempo
            "timeline": {
                "start_point": LEFT * 5,
                "end_point": RIGHT * 5,
                "color": "#00D4FF",
                "stroke_width": 4,
                "creation_time": 1.2
            },
            
            # Configuración de la curva exponencial
            "curve": {
                "start_x": -5,
                "end_x": 5,
                "height_factor": 3,
                "color": "#00FF88",
                "stroke_width": 5,
                "glow_color": "#00FF88",
                "transformation_time": 2.0,
                "acceleration_time": 1.5
            },
            
            # Configuración de cajas tecnológicas
            "tech_boxes": {
                "colors": ["#00D4FF", "#00FF88", "#FFD700", "#9D4EDD", "#FF6B6B"],
                "box_width": 2.2,
                "box_height": 0.9,
                "text_size": 18,
                "sizes": [0.8, 0.9, 1.0, 1.1, 1.2],
                "movement_time": 1.8,
                "box_delay": 0.3,
                "final_scale": 1.3,
                "labels": ["PCs", "INTERNET", "SMARTPHONES", "ROBOTS", "IA"]
            },
            
            # Configuración de partículas
            "particles": {
                "count": 50,
                "colors": ["#00D4FF", "#00FF88", "#FFD700"],
                "speed_range": [0.3, 1.2],
                "size_range": [0.02, 0.08],
                "spawn_time": 2.5
            },
            
            # Configuración de brillos
            "glow_effects": {
                "intensity": 0.8,
                "pulse_speed": 2.0,
                "final_brightness": 1.5
            }
        }
        
        # Aplicar color de fondo
        self.camera.background_color = config["background_color"]
        
        # Secuencia principal de animación
        self.crear_secuencia_revolucion_tecnologica(config)
        
        # Espera final
        self.wait(config["final_wait_time"])

    def crear_secuencia_revolucion_tecnologica(self, config):
        # Fase 1: Línea de tiempo inicial (0-1.2s)
        linea_tiempo = self.crear_linea_tiempo_inicial(config)
        self.mostrar_linea_tiempo(linea_tiempo, config)
        
        # Fase 2: Transformación a curva exponencial (1.2-3.2s)
        curva_exponencial = self.crear_curva_exponencial(config)
        self.transformar_a_curva(linea_tiempo, curva_exponencial, config)
        
        # Fase 3: Aparición de cajas tecnológicas (3.2-6.5s)
        cajas_tech = self.crear_cajas_tecnologicas(config)
        self.animar_cajas_por_curva(cajas_tech, curva_exponencial, config)
        
        # Fase 4: Partículas y efectos luminosos (6.5-8.0s)
        particulas = self.crear_particulas_luminosas(config)
        self.mostrar_efectos_luminosos(particulas, curva_exponencial, config)
        
        # Fase 5: Título final y aceleración (8.0-9.246s)
        self.mostrar_titulo_final_y_aceleracion(config, curva_exponencial)

    def crear_linea_tiempo_inicial(self, config):
        timeline_config = config["timeline"]
        
        # Crear línea horizontal simple
        linea = Line(
            start=timeline_config["start_point"],
            end=timeline_config["end_point"],
            color=timeline_config["color"],
            stroke_width=timeline_config["stroke_width"]
        )
        
        # Puntos de marcación en la línea
        puntos = VGroup()
        for i in range(6):
            x_pos = -4 + i * 1.6
            punto = Dot(
                point=[x_pos, 0, 0],
                radius=0.08,
                color=timeline_config["color"]
            )
            puntos.add(punto)
        
        return VGroup(linea, puntos)

    def mostrar_linea_tiempo(self, linea_tiempo, config):
        timeline_config = config["timeline"]
        
        # Animar creación de la línea de tiempo
        self.play(
            Create(linea_tiempo[0]),  # La línea
            run_time=timeline_config["creation_time"] * 0.7
        )
        
        # Animar aparición de puntos
        self.play(
            FadeIn(linea_tiempo[1], lag_ratio=0.2),  # Los puntos
            run_time=timeline_config["creation_time"] * 0.3
        )

    def crear_curva_exponencial(self, config):
        curve_config = config["curve"]
        
        # Crear función exponencial
        def func_exponencial(x):
            # Normalizar x de [-5, 5] a [0, 1] aproximadamente
            norm_x = (x + 5) / 10
            # Función exponencial suave
            return curve_config["height_factor"] * (norm_x ** 2.5) - 1.5
        
        # Crear la curva
        curva = FunctionGraph(
            func_exponencial,
            x_range=[curve_config["start_x"], curve_config["end_x"]],
            color=curve_config["color"],
            stroke_width=curve_config["stroke_width"]
        )
        
        return curva

    def transformar_a_curva(self, linea_tiempo, curva_exponencial, config):
        curve_config = config["curve"]
        
        # Transformar línea en curva exponencial
        self.play(
            Transform(linea_tiempo[0], curva_exponencial),
            linea_tiempo[1].animate.set_opacity(0),  # Desvanecer puntos
            run_time=curve_config["transformation_time"]
        )
        
        # Actualizar referencia para usar en próximas animaciones
        self.curva_actual = curva_exponencial

    def crear_cajas_tecnologicas(self, config):
        tech_config = config["tech_boxes"]
        cajas = VGroup()
        
        for i, (label, color) in enumerate(zip(tech_config["labels"], tech_config["colors"])):
            # Crear la caja
            caja = Rectangle(
                width=tech_config["box_width"],
                height=tech_config["box_height"],
                color=color,
                fill_opacity=0.3,
                stroke_width=3
            )
            caja.set_stroke(color, width=3)
            
            # Crear el texto
            texto = Text(
                label,
                font="Arial",
                font_size=tech_config["text_size"],
                color=WHITE,
                weight=BOLD
            )
            texto.move_to(caja)
            
            # Efecto de brillo en el borde
            brillo = Rectangle(
                width=tech_config["box_width"] + 0.1,
                height=tech_config["box_height"] + 0.1,
                color=color,
                fill_opacity=0,
                stroke_width=1,
                stroke_opacity=0.5
            )
            brillo.move_to(caja)
            
            # Agrupar elementos de la caja
            caja_completa = VGroup(brillo, caja, texto)
            cajas.add(caja_completa)
        
        return cajas

    def animar_cajas_por_curva(self, cajas, curva, config):
        tech_config = config["tech_boxes"]
        
        # Posiciones a lo largo de la curva
        posiciones_t = [0.05, 0.25, 0.45, 0.7, 0.95]
        
        for i, caja in enumerate(cajas):
            # Calcular posición en la curva
            t = posiciones_t[i]
            punto_curva = curva.point_from_proportion(t)
            
            # Ajustar posición vertical para que no se superponga con la curva
            caja.move_to(punto_curva + UP * 0.8)
            
            # Escalar según posición (más grandes hacia el final)
            escala = tech_config["sizes"][i]
            caja.scale(escala)
            
            # Animar aparición con efecto de deslizamiento
            self.play(
                FadeIn(caja, shift=UP*0.5),
                run_time=0.6
            )
            
            # Efecto de brillos en la caja
            self.play(
                Flash(caja, color=WHITE, line_length=0.3),
                run_time=0.2
            )
            
            # Breve pausa entre cajas
            if i < len(cajas) - 1:
                self.wait(tech_config["box_delay"])

    def crear_particulas_luminosas(self, config):
        particles_config = config["particles"]
        particulas = VGroup()
        
        for _ in range(particles_config["count"]):
            # Crear partícula
            size = random.uniform(
                particles_config["size_range"][0],
                particles_config["size_range"][1]
            )
            color = random.choice(particles_config["colors"])
            
            particula = Dot(
                radius=size,
                color=color,
                fill_opacity=random.uniform(0.6, 1.0)
            )
            
            # Posición inicial aleatoria
            x = random.uniform(-6, 6)
            y = random.uniform(-3, 4)
            particula.move_to([x, y, 0])
            
            # Movimiento flotante aleatorio
            velocidad = random.uniform(
                particles_config["speed_range"][0],
                particles_config["speed_range"][1]
            )
            
            particula.add_updater(
                lambda m, dt, v=velocidad: m.shift([
                    v * dt * np.sin(self.time * 2 + m.get_center()[0]),
                    v * dt * np.cos(self.time * 1.5 + m.get_center()[1]),
                    0
                ])
            )
            
            particulas.add(particula)
        
        return particulas

    def mostrar_efectos_luminosos(self, particulas, curva, config):
        particles_config = config["particles"]
        glow_config = config["glow_effects"]
        
        # Mostrar partículas gradualmente
        self.play(
            FadeIn(particulas, lag_ratio=0.05),
            run_time=1.2
        )
        
        # Efectos de brillo en la curva
        self.play(
            curva.animate.set_stroke_width(8).set_opacity(glow_config["intensity"]),
            run_time=0.8
        )

    def mostrar_titulo_final_y_aceleracion(self, config, curva):
        title_config = config["title"]
        glow_config = config["glow_effects"]
        
        # IMPORTANTE: Limpiar pantalla antes de mostrar el título
        self.clear()
        
        # Recrear la curva brillante
        curva_final = curva.copy()
        curva_final.set_stroke_width(10)
        curva_final.set_color("#00FF88")
        curva_final.set_opacity(1.0)
        self.add(curva_final)
        
        # Crear título principal
        titulo = Text(
            title_config["text"],
            font=title_config["font"],
            font_size=title_config["font_size"],
            color=title_config["color"],
            weight=BOLD
        )
        titulo.to_edge(UP, buff=0.8)
        
        # Animar escritura del título
        self.play(
            Write(titulo, run_time=title_config["animation_time"])
        )
        
        # Efecto de aceleración en la curva
        self.play(
            curva_final.animate.set_stroke_width(15).set_opacity(glow_config["final_brightness"]),
            Flash(curva_final, color=WHITE, line_length=0.5),
            run_time=1.0
        )
        
        # Pulso final de energía
        self.play(
            titulo.animate.scale(1.1),
            rate_func=there_and_back,
            run_time=0.5
        )
