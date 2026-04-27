# AGENTES DE IA - PARTE 1: Fundamentos Teóricos

<!-- type:VIDEO -->

==Hola a todos. Hoy comenzamos una serie de clases sobre uno de los temas más revolucionarios en inteligencia artificial: los Agentes de IA. Esta primera parte la dedicaremos a los fundamentos teóricos. Necesitamos entender qué es realmente un agente, cuáles son sus propiedades esenciales, y qué tipos de arquitecturas existen. Puede sonar académico, pero créanme, entender estos conceptos base es sumamente importante para después comprender cómo funcionan los agentes modernos que están revolucionando industrias completas y cambiando nuestra perspectiva sobre la IA. Listo, vamos.==

<!-- type:TEXT -->

==¿Qué es realmente un Agente de IA?==

<!-- type:SPLIT_LEFT -->

==Empecemos con lo esencial: ¿Qué es un agente de IA? Tratando de comprenderlo desde la perspectiva más sencilla, un agente es una entidad de software que PERCIBE su entorno y actúa sobre él para alcanzar objetivos específicos. La palabra clave aquí es "autonomía". NO es un programa que simplemente sigue instrucciones paso a paso como una receta, es un sistema capaz de adaptarse, aprender de situaciones nuevas, y DECIDIR por sí mismo qué hacer en cada momento.==

<!-- type:SPLIT_RIGHT -->

==Por ejemplo, veamos la diferencia entre un termostato, simple y uno inteligente. Digamos, el termostato de una TERMA ELÉCTRICA. El termostato básico solo enciende o apaga la calefacción según una temperatura fija que programaste. Punto. Eso es automatización tradicional, reglas fijas, comportamiento predecible.==
==Pero un termostato inteligente observa tus patrones de comportamiento, aprende cuándo más se usa el aparato, detecta si está encendido sin razón, se conecta a WIFI para recibir instrucciones, y ajusta posibles gastos inútiles de energía sin que se lo pidas. Ese es un agente.==

<!-- type:VIDEO -->

==Otro ejemplo cotidiano: los asistentes de voz como el OK GOOGLE de los televisores con Google TV. Cuando le pides algo como "abre youtube y sigue reproduciendo mis canciones", el asistente no solo ejecuta un comando fijo. Debe interpretar tu lenguaje natural, entender el contexto (¿Qué había en el historial de reproducción?), decidir qué comandos utilizar, verificar conectividad, y ejecutar la acción. Además puede recibir instrucción multimodal o aprender según tus opciones de personalización. Cada paso involucra percepción del entorno, toma de decisiones, y ejecución autónoma. Ese es el comportamiento agentico.==

<!-- type:TEXT -->

==Las cuatro propiedades esenciales de Wooldridge==

<!-- type:SPLIT_LEFT -->

==Para que un sistema sea considerado verdaderamente un agente, debe cumplir con cuatro propiedades fundamentales. Estas fueron establecidas por Michael Wooldridge, uno de los investigadores más importantes en el campo de los agentes inteligentes, en un trabajo pionero que sigue siendo la referencia académica hasta hoy. Son como los pilares que sostienen la definición misma de lo que es un agente.==


<!-- type:LIST // @ Propiedades Esenciales // Autonomía // Reactividad // Pro-actividad // Habilidad social -->

==Las cuatro propiedades son: Autonomía, Reactividad, Pro-actividad, y Habilidad social.==

<!-- type:SPLIT_RIGHT -->

==Primera propiedad: Autonomía. El agente debe poder operar sin intervención humana directa y tener control sobre sus propias acciones y estado interno. No necesita que alguien le esté diciendo en cada momento "ahora haz esto, ahora haz lo otro". Tiene la capacidad de gobernarse a sí mismo dentro de los límites de su diseño. Por ejemplo, un robot aspiradora que decide por sí mismo qué ruta seguir para limpiar toda tu casa, cuándo regresar a cargarse, y cómo evitar obstáculos que van apareciendo.==

<!-- type:SPLIT_LEFT -->

==Segunda propiedad: Reactividad. El agente debe percibir su entorno y responder de manera oportuna a los cambios que ocurren en él. Es como un conductor experimentado que reacciona inmediatamente cuando ve una luz roja, cuando un peatón cruza inesperadamente, o cuando el coche de adelante frena bruscamente. El agente no puede simplemente seguir un plan fijo ignorando lo que sucede a su alrededor. Debe estar constantemente monitoreando y ajustando su comportamiento.==

<!-- type:SPLIT_RIGHT -->

==Tercera propiedad: Pro-actividad. Aquí está lo realmente interesante: el agente no solo reacciona a estímulos externos, sino que también toma la iniciativa. Puede generar comportamientos orientados a objetivos sin que nadie se lo pida explícitamente. Anticipa problemas, identifica oportunidades, actúa preventivamente. Un ejemplo perfecto: un agente personal que detecta que tienes una reunión importante mañana temprano, nota que el pronóstico anuncia tráfico intenso debido a obras en la carretera, y proactivamente te sugiere salir 20 minutos antes, o incluso te ofrece alternativas como hacer la reunión virtual. Nadie le pidió hacer eso. Él tomó la iniciativa basándose en su objetivo de ayudarte a cumplir tus compromisos.==

<!-- type:FULL_IMAGE -->

==Cuarta propiedad: Habilidad social. Los agentes más sofisticados no operan en aislamiento. Pueden interactuar con otros agentes o con humanos para completar sus tareas. Esta capacidad de comunicación y colaboración es fundamental en sistemas complejos donde múltiples agentes trabajan juntos. Por ejemplo, en un sistema de coordinación de entregas: múltiples agentes (cada camión de reparto es un agente) deben comunicarse entre sí para optimizar rutas, evitar duplicaciones, ayudarse mutuamente cuando uno tiene problemas, y todo mientras interactúan con sistemas centrales y humanos.==
      

<!-- type:LIST // @ Las 4 Propiedades // Autonomía // Reactividad // Pro-actividad // Habilidad social -->

==Bien. Estas cuatro propiedades—autonomía, reactividad, pro-actividad y habilidad social—son la base conceptual que distingue a un verdadero agente de IA de un simple programa automatizado con algunas capacidades inteligentes añadidas.==

<!-- type:TEXT -->

==La jerarquía clásica: Tipos de agentes según Russell y Norvig==

<!-- type:SPLIT_LEFT -->

==Stuart Russell y Peter Norvig, autores del libro "Inteligencia Artificial: Un Enfoque Moderno" que es prácticamente la biblia de la IA académica, establecieron una taxonomía —es decir, una clasificación— clásica de agentes que sigue siendo el punto de partida conceptual más claro que existe. Esta clasificación muestra una progresión natural desde sistemas simples hasta agentes verdaderamente inteligentes y adaptativos. Veamos cada nivel.==


<!-- type:LIST // @ Tipos de Agentes // Agentes reactivos simples // Agentes reactivos basados en modelos // Agentes basados en objetivos // Agentes basados en utilidad // Agentes que aprenden -->

==Los cinco niveles son: Agentes reactivos simples, Agentes reactivos basados en modelos, Agentes basados en objetivos, Agentes basados en utilidad, y Agentes que aprenden.==

<!-- type:SPLIT_RIGHT -->

==Nivel 1: Agentes reactivos simples. El tipo más básico. Actúan basándose únicamente en la percepción actual, sin memoria del pasado. Funcionan con reglas del tipo "si-entonces": si detecto obstáculo, entonces giro. Si temperatura > 25°C, entonces enciende ventilador. Son rápidos y eficientes, pero muy limitados. No pueden manejar situaciones que requieran considerar el contexto histórico o planificar a futuro. Un termostato básico de terma eléctrica entra en esta categoría.==

<!-- type:SPLIT_LEFT -->

==Nivel 2: Agentes reactivos basados en modelos. Un paso más sofisticado. Estos agentes mantienen un estado interno que les permite rastrear aspectos del mundo que no son evidentes en la percepción inmediata. Tienen una "memoria de trabajo" que almacena información relevante sobre lo que ha pasado recientemente. Por ejemplo, un agente que controla semáforos en una intersección puede mantener un modelo de cuánto tiempo lleva cada luz en rojo o verde, cuántos coches están esperando en cada dirección, y usar esa información histórica para tomar mejores decisiones. O los ya clásicos robots aspiradora que trazan mapas de la ruta que ya siguieron para no volver a limpiar nuevamente en el mismo lugar.==

<!-- type:SPLIT_RIGHT -->

==Nivel 3: Agentes basados en objetivos. Aquí la cosa se pone más interesante. Estos agentes no solo tienen un modelo del mundo, sino también información sobre estados deseables o metas que quieren alcanzar. Pueden razonar sobre el futuro: "si hago X, llegaré al estado Y, que me acerca a mi objetivo Z". Un GPS aplicativo es un buen ejemplo. Tiene el objetivo de llevarte a tu destino, conoce el estado actual (dónde estás), y puede razonar sobre diferentes rutas para determinar cuál te acerca mejor a tu meta considerando tráfico, distancia, peajes, etc.==

<!-- type:SPLIT_LEFT -->

==Nivel 4: Agentes basados en utilidad. El nivel más sofisticado de la jerarquía llamada clásica. Estos agentes no solo buscan alcanzar objetivos, sino MÁXIMIZAR una función de utilidad que mide "qué tan bien" están haciendo las cosas. Pueden comparar diferentes estados objetivo y elegir el mejor según múltiples criterios. No es solo "llegar al destino", sino "llegar rápido, gastando poco combustible, evitando peajes, y con un viaje confortable". Los sistemas de recomendación avanzados entran aquí: no solo te sugieren contenido relevante, sino que optimizan por múltiples factores como relevancia, novedad, diversidad, y participación. Un ejemplo aquí podría ser el sistema de gestión de batería de un auto eléctrico, que mide cuanta energía falta, que tan bueno es el estado de la batería, la optimización de energía, limites de uso, etc.==

<!-- type:SPLIT_RIGHT -->

==Nivel 5: Agentes que aprenden. La evolución natural de todos los anteriores. Estos agentes pueden mejorar su desempeño con la experiencia, adaptándose a entornos cambiantes sin necesidad de ser reprogramados. Aprenden qué acciones funcionan mejor en qué situaciones, refinan sus modelos del mundo, actualizan sus objetivos basándose en feedback. Los sistemas modernos de IA que usan machine learning entran en esta categoría. Cuantas más interacciones tienen, mejores se vuelven. Aquí podríamos incluir a los chatbots avanzados con aprendizaje continuo que aprenden del usuario y mejoran su experiencia en diversas dimensiones.==

<!-- type:TEXT -->

==Esta jerarquía nos muestra una progresión bien clara: desde sistemas que solo reaccionan al presente inmediato, hasta agentes que mantienen memoria, persiguen objetivos, optimizan múltiples criterios, y aprenden continuamente de la experiencia. Si queremos aprender de agentes, tenemos necesariamente que entender estas bases. Son muy importantes.==
==Luego veremos sobre algo un poco más complejo, que son las arquitecturas internas.==

<!-- type:TEXT -->

==Arquitecturas internas: ¿Cómo están construidos por dentro?==

<!-- type:SPLIT_LEFT -->

==Ahora profundicemos en cómo están construidos internamente estos agentes. La arquitectura interna determina cómo el agente procesa información, toma decisiones, y genera acciones. No todos los agentes funcionan igual por dentro, aunque puedan verse similares desde afuera. Existen cuatro arquitecturas principales que han dominado la investigación y el desarrollo de agentes durante décadas. Entender de la arquitectura nos facilitará a concebir lo que realmente son los agentes con mayor precisión. Y lo más importante, nos permitirá tomar decisiones informadas que maximicen la utilidad en nuestros proyectos.==


<!-- type:LIST // @ Arquitecturas Principales // Reactiva // Deliberativa // Híbrida // BDI -->

==Las cuatro arquitecturas son: Reactiva, Deliberativa, Híbrida, y BDI.==

<!-- type:SPLIT_RIGHT -->

==Arquitectura 1: Reactiva. Basada en el paradigma "estímulo-respuesta" directo. Aquí el agente tiene un conjunto de reglas que mapean directamente percepciones a acciones. No hay razonamiento complejo, no hay planificación, no hay modelo del mundo. Percibo y actúo. Así de simple. Ventajas: Es rápida, eficiente, robusta. Funciona bien en entornos dinámicos donde necesitas reaccionar instantáneamente. Limitaciones: No puede manejar tareas complejas que requieren planificación, memoria, o razonamiento sobre consecuencias futuras.==

<!-- type:FULL_IMAGE -->

==Ejemplo clásico: Los sensores de movimiento y ruido, que activan iluminación en los edificios: Detectan ruido, activa la luz, pasan 15 segundos, apaga la luz. Cada regla es independiente. No hay un plan maestro de "capacidad para identificar si es una persona o un carro o un gato". Solo reacciones que en conjunto, logran el objetivo de iluminar una zona determinada.==

<!-- type:SPLIT_LEFT -->

==Arquitectura 2: Deliberativa. El enfoque opuesto a la arquitectura reactiva. Aquí el agente mantiene un modelo simbólico explícito del mundo y razona sobre él de manera deliberada antes de actuar. Planifica secuencias completas de acciones considerando el estado actual, el estado deseado, y las consecuencias de cada acción posible. Es como jugar ajedrez: piensas varios movimientos hacia adelante, consideras las respuestas del oponente, evalúas diferentes estrategias, y solo entonces ejecutas tu movimiento.==

<!-- type:SPLIT_RIGHT -->

==Ventajas: Mucho más flexible y potente para tareas complejas. Puede manejar objetivos sofisticados que requieren múltiples pasos coordinados. Limitaciones: Computacionalmente costosa. El tiempo que toma planificar puede ser prohibitivo en entornos que cambian rápidamente. Si el mundo cambia mientras estás planificando, tu plan puede volverse obsoleto antes de ejecutarlo. Ejemplo: Sistemas muy clásicos de planificación en IA, como los que se usan en logística para optimizar rutas de flotas completas de vehículos considerando múltiples restricciones.==

<!-- type:SPLIT_LEFT -->

==Arquitectura 3: Híbrida. La solución pragmática que combina lo mejor de ambos mundos. Tiene una capa reactiva para respuestas rápidas a situaciones inmediatas, y una capa deliberativa para planificación compleja y razonamiento estratégico. Las dos capas operan en paralelo pero a diferentes escalas de tiempo. La capa reactiva maneja lo urgente e inmediato. La capa deliberativa trabaja en segundo plano planificando y ajustando estrategias de largo plazo.==

<!-- type:SPLIT_RIGHT -->

==Es como tú conduciendo un auto:==

==Capa reactiva: Frenas inmediatamente cuando ves una luz roja, ajustas el volante constantemente para mantenerte en el carril, reaccionas a peatones. Capa deliberativa: Simultáneamente estás pensando en la ruta óptima, considerando si detenerte a cargar gasolina, evaluando si tomar el atajo o la ruta larga pero más segura.==

==La mayoría de los agentes modernos sofisticados usan alguna variante de arquitectura híbrida porque ofrece el mejor balance entre reactividad y capacidad de planificación.==


<!-- type:CONCEPT // BDI // Arquitectura de agente inspirada en la filosofía de la mente humana: Creencias, Deseos e Intenciones -->

==Arquitectura 4: BDI (Beliefs-Desires-Intentions). O creencias, deseos, intenciones. Esta arquitectura es especialmente interesante porque está inspirada en la filosofía de la mente humana. BDI significa:==


<!-- type:LIST // @ Componentes BDI // Beliefs: Creencias [Lo que el agente cree sobre el mundo] // Desires: Deseos [Los objetivos que quiere alcanzar] // Intentions: Intenciones [Los planes comprometidos que está ejecutando] -->

==Beliefs (Creencias): Lo que el agente cree sobre el mundo. Desires (Deseos): Los objetivos que quiere alcanzar. Intentions (Intenciones): Los planes comprometidos que está ejecutando.==

<!-- type:SPLIT_RIGHT -->

==¿Cómo funciona? El agente mantiene constantemente actualizado su conjunto de creencias sobre el mundo basándose en percepciones. Tiene múltiples deseos u objetivos que puede perseguir. Y en cada momento, selecciona algunos de esos deseos y se compromete a planes específicos (intenciones) para alcanzarlos. Lo interesante es que puede reconsiderar sus intenciones si las circunstancias cambian. No está rígidamente atado a un plan. Ejemplo: Agentes en simulaciones complejas, sistemas multi-agente donde cada agente tiene sus propias metas pero debe coordinarse con otros. Aplicaciones por ejemplo, en robótica autónoma.==

<!-- type:TEXT -->

==Cada arquitectura tiene sus ventajas y se selecciona según los requisitos específicos de la aplicación. No hay una arquitectura universalmente superior, solo la más apropiada para cada contexto y necesidades específicas. Por favor, esto es importante repetir: No hay una arquitectura mejor que otra, sólo la más apropiada para determinado caso de uso.==

<!-- type:TEXT -->

==Perspectivas según el rubro o dominio: Lo que se entiende por agentes en diferentes campos==

<!-- type:SPLIT_LEFT -->

==Aquí pasa algo bien interesante: la noción de "agente" significa cosas sutilmente diferentes según el campo de la IA del que vengas. Cada dominio de investigación ha desarrollado su propia perspectiva sobre qué constituye un agente, qué capacidades son importantes, y cómo deben diseñarse. Probablemente esta sea la razón del porqué existen tantas definiciones de agentes. Veamos pues las perspectivas principales.==

<!-- type:SPLIT_RIGHT -->

==En Machine Learning y Reinforcement Learning. Aquí un agente es una entidad que aprende políticas de comportamiento a través de prueba y error. Interactúa con un entorno, recibe recompensas o penalizaciones según sus acciones, y optimiza su estrategia para maximizar la recompensa acumulada a largo plazo. El enfoque está en el aprendizaje por experiencia. El agente no viene preprogramado con reglas, sino que DESCUBRE POR SÍ MISMO qué funciona mejor. Ejemplos clásicos: Los agentes que juegan videojuegos o los sistemas que controlan robots aprendiendo a caminar o manipular objetos.==

<!-- type:SPLIT_LEFT -->

==En Procesamiento de Lenguaje Natural o NLP por sus siglas en inglés. Tradicionalmente en NLP no se hablaba mucho de "agentes". El foco estaba en entender y generar lenguaje. Pero con la llegada de los Large Language Models o LLM, esto cambió radicalmente. Ahora los modelos de lenguaje pueden ser la piedra angular de agentes que interactúan con herramientas externas o razonan sobre problemas, entienden y toman acciones en el mundo. Así entonces, el procesamiento de lenguaje natural se convierte en la interfaz de control del agente. Puedes darle instrucciones en lenguaje humano y el agente las ejecuta.==

<!-- type:SPLIT_RIGHT -->

==Ahora veamos en Robótica. Aquí los agentes son sistemas físicos que deben navegar y manipular el mundo cien por ciento real. La percepción sensorial es crítica: cámaras, sensores táctiles, motores, etc. La planificación de movimientos debe considerar física real: inercia, fricción, torque, dureza. Un brazo robótico en una fábrica, un dron autónomo haciendo delivery, un coche autoconducido, todos son agentes robóticos que enfrentan desafíos únicos del mundo físico. El entorno es ruidoso, impredecible, y los errores pueden tener consecuencias físicas reales e incluso fatales. No es como un agente de software donde puedes regresar a un punto anterior fácilmente.==

<!-- type:SPLIT_LEFT -->

==En Ingeniería de Software. En desarrollo de software, un agente puede ser un sistema que genera código, ejecuta pruebas, refactoriza, o incluso hace revisión de código. Los agentes de programación son, de hecho, una de las aplicaciones más exitosas actualmente. GitHub Copilot, Cursor, Claude Code, y otros están transformando cómo se escribe software. Estos agentes entienden el contexto de tu código, pueden navegar repositorios completos, buscar documentación, y generar soluciones que se integran con tu base de código existente. Además, están en constante evolución por presión del mercado.==


<!-- type:FULL_IMAGE -->

==Otro de los dominios fuertes, es en la IA Multimodal. Los agentes que pueden ver imágenes, escuchar audio, leer texto, y producir salidas en múltiples modalidades. No solo responden preguntas sobre una imagen== 



<!-- type:LIST // @ IA Multimodal // Analizar una foto // Describir detalladamente qué ven // Buscar información relacionada en internet // Generar un informe completo con gráficos // Crear nuevas imágenes basadas en su análisis -->


==Sino que pueden: Analizar una foto. Describir detalladamente qué ven. Pueden buscar información relacionada en internet. También pueden generar un informe completo con gráficos. Incluso crear nuevas imágenes basadas en su análisis. Esta convergencia de modalidades abre posibilidades enormes para agentes más completos y versátiles.==

<!-- type:TEXT -->

==Desde un punto de vista de rubros, cada dominio aporta conceptos únicos, y los agentes modernos más potentes integran ideas de todos ellos: aprenden por experiencia, entienden lenguaje natural, pueden interactuar con sistemas físicos o digitales, y procesan información multimodal.==


<!-- type:FULL_IMAGE -->

==Esta segmentación nos ayuda a entender claramente, porqué el concepto de agente en el mundo de la inteligencia artificial, es tan difícil de definir con solo una palabra. Como ven, la forma más adecuada es precisar su definición en base a las distintas perspectivas.==

<!-- type:TEXT -->

==Reflexión final de esta primera parte==

<!-- type:VIDEO -->

==Hemos cubierto las bases teóricas fundamentales de los agentes de IA. Ahora entiendes que un agente no es simplemente un programa automatizado, sino sobre todo un sistema con capacidades específicas: autonomía, reactividad, pro-actividad y habilidad social. Conoces la jerarquía clásica que va desde agentes reactivos simples hasta agentes que aprenden continuamente de la experiencia. Has visto las cuatro arquitecturas principales: reactiva, deliberativa, híbrida y BDI (creencias, deseos, intenciones) y entiendes que cada una tiene su lugar dependiendo de los requisitos del problema.==
==En resumen, vimos sobre CARACTERÍSTICAS, JERARQUÍA Y ARQUITECTURA de agentes.==

<!-- type:SPLIT_LEFT -->

==Y también comprendes que diferentes campos de la IA tienen perspectivas ligeramente distintas sobre qué constituye un agente, cada una válida en su contexto. Estos fundamentos teóricos no son solo ejercicio académico, son la base que te permitirá entender las innovaciones modernas que veremos más adelante.==

<!-- type:SPLIT_RIGHT -->

==Lo que está pasando ahora con los Large Language Models —LLMs— está revolucionando completamente el campo de los agentes. Capacidades que antes requerían años de investigación especializada ahora son accesibles a través de APIs. En la siguiente parte exploraremos exactamente esta revolución: cómo los LLMs han transformado el panorama, qué es el paradigma ReAct, por qué todo el mundo habla de "Agentic AI", y cuál es la realidad del mercado más allá del hype.==

<!-- type:TEXT -->

==Eso es todo por esta clase.==