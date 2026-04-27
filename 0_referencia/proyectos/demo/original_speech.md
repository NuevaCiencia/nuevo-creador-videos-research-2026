

<# 🔄 REEMPLAZO — Era type:TEXT. Apertura de clase → VIDEO da energía de intro sin texto en pantalla. #>
<!-- type:VIDEO -->

==Hola a todos. Bienvenidos a la segunda parte de nuestra serie sobre Agentes de IA. En la clase anterior establecimos los fundamentos teóricos: qué es un agente, sus propiedades esenciales, los tipos clásicos, y las arquitecturas principales. Hoy vamos a dar un salto hacia el presente. Hablaremos de la revolución que está ocurriendo ahora mismo, impulsada por los LLMs. Exploraremos cómo los LLMs han democratizado la creación de agentes, también qué es el paradigma ReAct que cambió todo, y desentrañaremos la narrativa de Agentic AI que domina el mercado empresarial. Vamos a ello.==

<!-- type:TEXT -->

==La era de los LLMs: El antes y el después==

<!-- type:SPLIT_LEFT -->

==Si los agentes de IA existen desde hace décadas en la investigación académica, ¿por qué de repente todo el mundo habla de ellos en el 2023, 2024, 2025? La respuesta cae por su propio peso: los Large Language Models o Modelos de Lenguaje Grande. La llegada de GPT, Claude, Gemini y otros modelos similares entre el 2022 y 2024 lo cambió todo.==

<!-- type:SPLIT_RIGHT -->

==De pronto, cualquier desarrollador podía acceder a capacidades de inteligencia artificial de nivel mundial simplemente llamando a una API. No necesitas un doctorado en machine learning, no necesitas meses entrenando modelos, no necesitas infraestructura costosa. Pagas por uso, y tienes acceso a sistemas que pueden entender lenguaje natural, razonar sobre problemas complejos, generar código, y mucho más. Repito esta bonita analogía, es como si hubieran inventado el motor de combustión interna, y ahora cualquiera puede construir diferentes tipos de vehículos sin necesidad de reinventar el motor cada vez.==

<# 🔄 REEMPLAZO — Era type:FULL_IMAGE. El locutor enumera seis requisitos en secuencia. #>
<!-- type:LIST // @ Requisitos Pre-LLM // Equipos especializados en IA y ML // Años de investigación y entrenamiento de modelos desde cero // Infraestructura computacional extremadamente costosa // Conocimiento profundo en algoritmos y matemáticas avanzadas // Grandes cantidades de datos etiquetados específicos // Presupuestos de millones de euros -->

==Antes de los LLMs, construir un agente inteligente requería: Equipos especializados en inteligencia artificial y machine learning. Años de investigación, desarrollo y entrenamiento de modelos desde cero. Infraestructura computacional extremadamente costosa: GPUs, TPUs, chips que eran mucho menos eficientes que hoy. Conocimiento profundo en algoritmos complejos y matemáticas avanzadas. Requerían también grandes cantidades de datos etiquetados específicos para tu caso de uso. Y presupuestos de millones de dólares. Y aun así, los resultados eran limitados, frágiles, y difíciles de mantener. Un agente que funcionaba bien en un contexto, fallaba terriblemente en otro ligeramente diferente. Además, antes era muy muy limitado el entendimiento de las máquinas del lenguaje natural.==

<# 🔄 REEMPLAZO — Era type:VIDEO. El locutor enumera cuatro capacidades de los LLMs modernos. #>
<!-- type:LIST // @ Capacidades con LLMs // Comprensión de lenguaje natural a nivel casi humano en múltiples idiomas // Razonamiento complejo sobre problemas diversos sin entrenamiento específico // Capacidad de generar planes y estrategias coherentes // Habilidad para usar herramientas externas de manera inteligente -->

==Con los LLMs modernos, de pronto tienes acceso inmediato a: Comprensión de lenguaje natural a nivel casi humano en múltiples idiomas. Razonamiento complejo sobre problemas diversos sin entrenamiento específico. Capacidad de generar planes y estrategias coherentes. Habilidad para usar herramientas externas de manera inteligente. Todo esto a través de simples llamadas a APIs con costos por uso razonables y accesibles. El cambio de paradigma es muy grande. Lo que antes era territorio exclusivo de grandes corporaciones con recursos masivos, ahora es accesible para startups de tres personas en un garaje.==

<!-- type:REMOTION // $MindMap -->

==Esta democratización ha desatado una explosión de innovación. Miles de aplicaciones nuevas, startups que construyen agentes especializados, y empresas tradicionales integrando capacidades agénticas en sus productos. Estamos viviendo un momento de transformación comparable a cuando surgió internet o los smartphones.==

<!-- type:TEXT -->

==Ahora hablaremos sobre ReAct: un paradigma clave en agentes basados en LLMs==

<!-- type:SPLIT_LEFT -->

==Una de las innovaciones más influyentes en agentes modernos es el paradigma ReAct, que significa Reasoning más Acting, es decir, Razonamiento más Acción. Fue propuesto por investigadores de Princeton y Google Research en 2023. ReAct combinó de forma explícita el razonamiento paso a paso con la capacidad de ejecutar acciones en el entorno, y se convirtió en una referencia central para el diseño de agentes basados en LLMs.==

<# ✂️ PARTIDO — Corte antes de "Thought". Preámbulo queda en SPLIT_LEFT, ciclo ReAct en LIST.
   Audio continuo, sin nueva grabación. #>
<!-- type:SPLIT_LEFT -->

==¿Qué hace a ReAct diferente? El agente trabaja siguiendo un ciclo muy sencillo y repetitivo:==

<!-- type:LIST // @ Ciclo ReAct // Thought: el agente explica qué va a hacer y por qué [Pensamiento] // Action: ejecuta una acción concreta, como usar una herramienta [Acción] // Observation: recibe el resultado y lo analiza [Observación] -->

==Thought (Pensamiento): el agente explica en lenguaje natural qué va a hacer y por qué. Action (Acción): ejecuta una acción concreta, como usar una herramienta o consultar una fuente externa. Observation (Observación): recibe el resultado de esa acción y lo analiza. Luego vuelve al pensamiento, ejecuta otra acción, observa de nuevo, y así sucesivamente hasta completar la tarea. La esencia es ese ciclo continuo de pensamiento, acción y observación. La clave de ReAct es que el agente "piensa en voz alta" antes de cada acción, mostrando su razonamiento paso a paso mientras avanza.==

<!-- type:FULL_IMAGE -->

==Ejemplo concreto: un usuario pregunta: "¿Cuál es el clima actual en Buenos Aires y cómo se compara con el de ayer?" Pensamiento: El agente decide, que, primero necesita el clima de hoy. Acción: Consulta la API de clima. Observación: Hoy: 22 °C, nublado, 78% de humedad. Pensamiento: Ahora necesita el clima de ayer. Acción: Vuelve a consultar la API. Observación: Ayer: 24 °C, soleado, 65% de humedad. Pensamiento: Ya tiene ambos datos y ahora puede compararlos. Acción: Produce la respuesta final con la comparación.==

<!-- type:SPLIT_LEFT -->

==¿Por qué esto es tan poderoso? Primero, porque el razonamiento explícito mejora dramáticamente la calidad de las decisiones. El modelo no solo actúa por impulso, sino que reflexiona sobre qué hacer y por qué. Segundo, porque hace el proceso completamente transparente y auditable. Puedes ver exactamente qué pensó el agente en cada paso. Si comete un error, puedes rastrear dónde falló el razonamiento.==

<!-- type:SPLIT_RIGHT -->

==Tercero, porque permite recuperación de errores. Si una acción no produce el resultado esperado, el agente puede observarlo, reflexionar sobre qué salió mal, y tomar un camino alternativo. Y cuarto, porque es increíblemente flexible. El mismo patrón funciona para tareas muy diferentes: por ejemplo, búsqueda de información, procesamiento de datos, interacción con sistemas externos, resolución de problemas complejos. ReAct se ha convertido en uno de los paradigmas más usados, para construir agentes modernos basados en LLMs, precisamente por esta combinación de poder y simplicidad.==

<!-- type:TEXT -->

==Ahora hablaremos sobre los Function Calling (o llamada a funciones): Los agentes como orquestadores==

<!-- type:SPLIT_LEFT -->

==Otra innovación muy importante que desbloqueó las capacidades agénticas de los LLMs es Function Calling o la capacidad de invocar funciones. Antes, los LLMs solo podían generar texto. Podían describir qué hacer, pero no hacerlo realmente. Era como tener un consultor brillante que te dice exactamente qué pasos a seguir, pero no puede ejecutar nada por sí mismo. Function Calling cambió esto completamente.==

<# ✂️ PARTIDO — Corte antes de "Función recuperar clima". Preámbulo en SPLIT_RIGHT, ejemplos en LIST.
   Audio continuo, sin nueva grabación. #>
<!-- type:SPLIT_RIGHT -->

==¿Cómo funciona? Cuando configuras un LLM con llamadas a funciones (Function Calling), normalmente a nivel de desarrollo con código y APIs, le proporcionas una lista de funciones o herramientas disponibles, cada una con una descripción clara de qué hace y qué parámetros necesita. Por ejemplo, podrías definir cosas como:==

<!-- type:LIST // @ Ejemplos de Herramientas // Función recuperar clima: obtiene información meteorológica para una ubicación y fecha dadas // Función buscar en la web: busca información en internet a partir de una consulta // Función enviar correo: envía un email a un destinatario con asunto y contenido // Función ejecutar consulta SQL: lanza una consulta sobre una base de datos y devuelve el resultado -->

==Función recuperar clima: obtiene información meteorológica para una ubicación y fecha dadas. Función buscar en la web: busca información en internet a partir de una consulta. Función enviar correo: envía un email a un destinatario con un asunto y un contenido. Función ejecutar consulta SQL: lanza una consulta sobre una base de datos y devuelve el resultado. El LLM puede analizar la tarea del usuario, decidir cuál herramienta necesita, generar los parámetros correctos, y solicitar que se ejecute.==

<!-- type:FULL_IMAGE -->

==Ejemplo práctico: Usuario: "Envíale un email a mi equipo con el pronóstico del clima para Madrid, esta semana" El agente razona: Primero necesito obtener el pronóstico. Entonces, llama a la función de clima y recibe los datos meteorológicos. Ahora necesito enviarlo por email. Entonces llama la función para enviar emails. Finalmente confirma que el email fue enviado exitosamente. El LLM actúa como un orquestador inteligente que elige las herramientas correctas, en el orden correcto, para completar tareas complejas.==

<# ✂️ PARTIDO — Corte antes de "Navegar por la web". Preámbulo en SPLIT_LEFT, capacidades en LIST.
   Audio continuo, sin nueva grabación. #>
<!-- type:SPLIT_LEFT -->

==¿Qué representa esta transformación? Ya no sólo hablamos de chatbots que solo responden preguntas en una conversación estática. Los agentes basados en LLMs con Function Calling pueden:==

<!-- type:LIST // @ Capacidades Agénticas // Navegar por la web y extraer información // Interactuar con bases de datos // Escribir y ejecutar código // Enviar emails y mensajes // Actualizar sistemas empresariales // Programar reuniones // Crear, leer y modificar documentos -->

==Navegar por la web y extraer información. Interactuar con bases de datos. Escribir y ejecutar código. Enviar emails y mensajes. Actualizar sistemas empresariales. Programar reuniones. Crear, leer y modificar documentos y muchísimo más.==

<!-- type:SPLIT_RIGHT -->

==Son verdaderos colaboradores digitales capaces de ejecutar trabajo real, no solo generar texto sobre cómo hacerlo. La combinación de ReAct (razonamiento más acción) con Function Calling (capacidad de usar herramientas) ha creado un paradigma completamente nuevo para construir agentes. Y esto es lo que ha impulsado la explosión de aplicaciones agenticas que estamos viendo desde el 2023.==

<!-- type:LIST // La Taxonomia moderna // Workflows ninja // Agentes super agentes -->

==Ahora hablaremos de Workflows (flujos de trabajo) vs Agentes: La taxonomía moderna==
<# 🔄 REMOTION DEMO #>
<!-- type:REMOTION // $TypeWriter -->
==Y recuerda: todo sistema seguro es la suma de sus partes. Entender los protocolos no es opcional, es el cimiento de la arquitectura.==
