import React from "react";
import { Composition, registerRoot } from "remotion";
import { MainCover, MainCoverProps } from "./templates/MainCover";
import { SectionCover } from "./templates/SectionCover";
import { ClosingKeywords } from "./templates/ClosingKeywords";
import { ClosingQuote } from "./templates/ClosingQuote";
import { Credits } from "./templates/Credits";
import { CentralDefinition } from "./templates/CentralDefinition";
import { ProgressiveReveal } from "./templates/ProgressiveReveal";
import { ImpactTerm } from "./templates/ImpactTerm";
import { RhetoricalQuestion } from "./templates/RhetoricalQuestion";
import { VisualAnalogy } from "./templates/VisualAnalogy";
import { FourBoxes } from "./templates/FourBoxes";
import { TwoColumns } from "./templates/TwoColumns";
import { PyramidLevels } from "./templates/PyramidLevels";
import { MatrixGrid } from "./templates/MatrixGrid";
import { FlipCards } from "./templates/FlipCards";
import { HexGrid } from "./templates/HexGrid";
import { VennDiagram } from "./templates/VennDiagram";
import { MosaicReveal } from "./templates/MosaicReveal";
import { LinearSteps } from "./templates/LinearSteps";
import { CycleLoop } from "./templates/CycleLoop";
import { FunnelDiagram } from "./templates/FunnelDiagram";
import { OrgChart } from "./templates/OrgChart";
import { MindMap } from "./templates/MindMap";
import { SketchDiagram } from "./templates/SketchDiagram";
import { HorizontalBars } from "./templates/HorizontalBars";
import { PieDonut } from "./templates/PieDonut";
import { RadarChart } from "./templates/RadarChart";
import { CircleStats } from "./templates/CircleStats";
import { WaveTrend } from "./templates/WaveTrend";
import { Spotlight } from "./templates/Spotlight";
import { TypeWriter } from "./templates/TypeWriter";
import { KineticWords } from "./templates/KineticWords";
import { TitleCard, TitleCardProps } from "./templates/TitleCard";
import { AgentLoop, AgentLoopProps } from "./templates/AgentLoop";
import { ComparisonSlide, ComparisonSlideProps } from "./templates/ComparisonSlide";
import { FourPillars, FourPillarsProps } from "./templates/FourPillars";
import { BulletReveal, BulletRevealProps } from "./templates/BulletReveal";
import { ParticleNetwork, ParticleNetworkProps } from "./templates/ParticleNetwork";
import { NeonGlow, NeonGlowProps } from "./templates/NeonGlow";
import { WaveOrb, WaveOrbProps } from "./templates/WaveOrb";
import { RotatingCube3D, RotatingCube3DProps } from "./templates/RotatingCube3D";
import { TimelineSlide, TimelineSlideProps } from "./templates/TimelineSlide";
import { StatCounter, StatCounterProps } from "./templates/StatCounter";
import { ProcessFlow, ProcessFlowProps } from "./templates/ProcessFlow";
import { GlitchReveal, GlitchRevealProps } from "./templates/GlitchReveal";
import { GradientTitle, GradientTitleProps } from "./templates/GradientTitle";

export const RemotionRoot = () => (
  <>
    <Composition<MainCoverProps>
      id="COVER-MainCover"
      component={MainCover}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        tag:      "Clase 01 — Fundamentos",
        title:    "Agentes de Inteligencia Artificial",
        subtitle: "Qué son, cómo funcionan y por qué importan",
      }}
    />

    <Composition
      id="COVER-SectionCover"
      component={SectionCover}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title:    "Tipos de agentes",
        subtitle: "Reactivos, deliberativos e híbridos",
      }}
    />

    <Composition
      id="FX-KineticWords"
      component={KineticWords}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        subtitle: "propiedades de un agente inteligente",
        words: [
          { text: "Autonomía",     color: "#6366F1" },
          { text: "Percepción",    color: "#0EA5E9" },
          { text: "Decisión",      color: "#10B981" },
          { text: "Acción",        color: "#F59E0B" },
          { text: "Aprendizaje",   color: "#EC4899" },
          { text: "Memoria",       color: "#8B5CF6" },
          { text: "Reactividad",   color: "#6366F1" },
          { text: "Proactividad",  color: "#0EA5E9" },
        ],
      }}
    />

    <Composition
      id="NAR-TypeWriter-Hacker"
      component={TypeWriter}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        accent: "#6366F1",
        lines: [
          { prefix: "$ ", text: "agent.perceive(environment)",          color: "#00FF41", delay: 10,  speed: 2.5 },
          { prefix: "→ ", text: "state = { temp: 22, motion: true }",   color: "#7DD3FC", delay: 60,  speed: 2.5 },
          { prefix: "$ ", text: "agent.reason(state)",                  color: "#00FF41", delay: 110, speed: 2.5 },
          { prefix: "→ ", text: "action = 'turn_on_cooling'",           color: "#FCD34D", delay: 160, speed: 2.5 },
          { prefix: "$ ", text: "agent.act(action)",                    color: "#00FF41", delay: 210, speed: 2.5 },
          { prefix: "✓ ", text: "Environment updated successfully.",     color: "#86EFAC", delay: 260, speed: 2.5 },
        ],
      }}
    />

    <Composition
      id="NAR-Spotlight"
      component={Spotlight}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        spotRadius: 320,
        points: [
          { x: 960,  y: 400, text: "PERCIBIR",   sub: "captura el entorno",     color: "#6366F1", holdFrames: 50 },
          { x: 500,  y: 700, text: "DECIDIR",    sub: "evalúa opciones",        color: "#0EA5E9", holdFrames: 50 },
          { x: 1420, y: 700, text: "ACTUAR",     sub: "modifica el entorno",    color: "#10B981", holdFrames: 50 },
          { x: 960,  y: 600, text: "AGENTE",     sub: "autónomo · inteligente", color: "#F59E0B", holdFrames: 60 },
        ],
      }}
    />

    <Composition
      id="DATA-WaveTrend"
      component={WaveTrend}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title:  "Evolución de la autonomía en agentes de IA",
        yLabel: "Autonomía (%)",
        points: [
          { label: "1950", value: 5,  note: "Turing" },
          { label: "1970", value: 12 },
          { label: "1986", value: 28, note: "BDI" },
          { label: "1995", value: 40, note: "Wooldridge" },
          { label: "2012", value: 58 },
          { label: "2017", value: 72, note: "Deep RL" },
          { label: "2024", value: 92, note: "LLM Agents" },
        ],
      }}
    />

    <Composition
      id="DATA-CircleStats"
      component={CircleStats}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Capacidades del agente autónomo",
        stats: [
          { label: "Autonomía",    value: 92, color: "#6366F1", icon: "🧠" },
          { label: "Reactividad",  value: 85, color: "#0EA5E9", icon: "⚡" },
          { label: "Aprendizaje",  value: 74, color: "#10B981", icon: "🎓" },
          { label: "Planificación",value: 80, color: "#F59E0B", icon: "🎯" },
        ],
      }}
    />

    <Composition
      id="DATA-RadarChart"
      component={RadarChart}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Perfil de un agente autónomo",
        fillColor: "#6366F1",
        axes: [
          { label: "Autonomía",       value: 90, color: "#6366F1" },
          { label: "Razonamiento",    value: 80, color: "#0EA5E9" },
          { label: "Aprendizaje",     value: 70, color: "#10B981" },
          { label: "Comunicación",    value: 65, color: "#F59E0B" },
          { label: "Reactividad",     value: 85, color: "#EC4899" },
          { label: "Planificación",   value: 75, color: "#8B5CF6" },
        ],
      }}
    />

    <Composition
      id="DATA-PieDonut"
      component={PieDonut}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Tipos de agentes en producción",
        unit: "",
        slices: [
          { label: "Reactivos",     value: 38, color: "#6366F1" },
          { label: "Deliberativos", value: 24, color: "#0EA5E9" },
          { label: "Híbridos",      value: 28, color: "#10B981" },
          { label: "Aprendizaje",   value: 10, color: "#F59E0B" },
        ],
      }}
    />

    <Composition
      id="DATA-HorizontalBars"
      component={HorizontalBars}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Capacidades de los agentes de IA",
        bars: [
          { label: "Razonamiento",   value: 94, suffix: "%", color: "#6366F1" },
          { label: "Planificación",  value: 81, suffix: "%", color: "#0EA5E9" },
          { label: "Aprendizaje",    value: 76, suffix: "%", color: "#10B981" },
          { label: "Percepción",     value: 88, suffix: "%", color: "#F59E0B" },
          { label: "Comunicación",   value: 72, suffix: "%", color: "#EC4899" },
        ],
      }}
    />

    <Composition
      id="FLOW-SketchDiagram"
      component={SketchDiagram}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Ciclo percepción → acción",
        boxes: [
          { x: 110,  y: 380, w: 340, h: 200, label: "ENTORNO",    sub: "estado actual",      color: "#6366F1" },
          { x: 550,  y: 380, w: 340, h: 200, label: "PERCIBIR",   sub: "sensores",            color: "#0EA5E9" },
          { x: 990,  y: 380, w: 340, h: 200, label: "DECIDIR",    sub: "razonamiento",        color: "#10B981" },
          { x: 1430, y: 380, w: 340, h: 200, label: "ACTUAR",     sub: "actuadores",          color: "#F59E0B" },
          { x: 660,  y: 680, w: 600, h: 160, label: "MEMORIA",    sub: "estado interno",      color: "#8B5CF6" },
        ],
        arrows: [
          { x1: 450,  y1: 480, x2: 550,  y2: 480, color: "#6366F1" },
          { x1: 890,  y1: 480, x2: 990,  y2: 480, color: "#0EA5E9" },
          { x1: 1330, y1: 480, x2: 1430, y2: 480, color: "#10B981" },
          { x1: 770,  y1: 580, x2: 770,  y2: 680, color: "#0EA5E9" },
          { x1: 1110, y1: 580, x2: 1110, y2: 680, color: "#10B981" },
        ],
      }}
    />

    <Composition
      id="FLOW-MindMap"
      component={MindMap}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        center: "Agente\nInteligente",
        nodes: [
          { text: "Autonomía",        sub: "se gobierna a sí mismo" },
          { text: "Reactividad",      sub: "responde al entorno" },
          { text: "Proactividad",     sub: "toma la iniciativa" },
          { text: "Habilidad Social", sub: "colabora con otros" },
          { text: "Memoria",          sub: "mantiene estado interno" },
          { text: "Aprendizaje",      sub: "mejora con experiencia" },
        ],
      }}
    />

    <Composition
      id="FLOW-OrgChart"
      component={OrgChart}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Tipos de agentes inteligentes",
        nodes: [
          { id: "root",        label: "Agente inteligente", sub: "raíz",              color: "#6366F1" },
          { id: "reactivo",    label: "Reactivo",           sub: "sin memoria",        color: "#0EA5E9", parentId: "root" },
          { id: "deliberativo",label: "Deliberativo",       sub: "con planificación",  color: "#10B981", parentId: "root" },
          { id: "hibrido",     label: "Híbrido",            sub: "reactivo + deliberativo", color: "#F59E0B", parentId: "root" },
          { id: "r1",          label: "Termostato",         sub: "ejemplo",            color: "#0EA5E9", parentId: "reactivo" },
          { id: "d1",          label: "Planificador",       sub: "ejemplo",            color: "#10B981", parentId: "deliberativo" },
          { id: "d2",          label: "BDI",                sub: "creencias-deseos",   color: "#10B981", parentId: "deliberativo" },
          { id: "h1",          label: "Robot autónomo",     sub: "ejemplo",            color: "#F59E0B", parentId: "hibrido" },
        ],
      }}
    />

    <Composition
      id="FLOW-Funnel"
      component={FunnelDiagram}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Embudo de adopción de agentes de IA",
        stages: [
          { label: "Conciencia",   value: 10000, unit: " personas", color: "#6366F1" },
          { label: "Interés",      value: 4200,  unit: " personas", color: "#8B5CF6" },
          { label: "Evaluación",   value: 1800,  unit: " personas", color: "#0EA5E9" },
          { label: "Adopción",     value: 540,   unit: " personas", color: "#10B981" },
        ],
      }}
    />

    <Composition
      id="FLOW-CycleLoop"
      component={CycleLoop}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "El ciclo de un agente inteligente",
        center: { icon: "🤖", label: "Agente" },
        items: [
          { icon: "👁️", title: "Percibir",   description: "Capta el estado del entorno" },
          { icon: "🧠", title: "Razonar",    description: "Procesa y actualiza su modelo" },
          { icon: "🎯", title: "Decidir",    description: "Elige la mejor acción posible" },
          { icon: "⚙️", title: "Actuar",     description: "Ejecuta y modifica el entorno" },
        ],
      }}
    />

    <Composition
      id="FLOW-LinearSteps"
      component={LinearSteps}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "¿Cómo actúa un agente inteligente?",
        steps: [
          { title: "Percibir",   description: "Los sensores capturan el estado actual del entorno." },
          { title: "Procesar",   description: "Interpreta la información y actualiza su modelo interno." },
          { title: "Decidir",    description: "Evalúa opciones y selecciona la mejor acción posible." },
          { title: "Actuar",     description: "Ejecuta la acción y modifica el entorno." },
        ],
      }}
    />

    <Composition
      id="CLASS-MosaicReveal"
      component={MosaicReveal}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Conceptos clave de agentes de IA",
        items: [
          "Autonomía",   "Percepción",  "Razonamiento",
          "Memoria",     "Objetivos",   "Aprendizaje",
          "Reactividad", "Planificación","Acción",
        ],
      }}
    />

    <Composition
      id="CLASS-VennDiagram"
      component={VennDiagram}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Agente reactivo vs Agente deliberativo",
        left: {
          label: "Solo reactivo",
          color: "#0EA5E9",
          items: ["Sin memoria interna", "Respuesta inmediata", "Reglas fijas"],
        },
        right: {
          label: "Solo deliberativo",
          color: "#8B5CF6",
          items: ["Planificación compleja", "Modelo del mundo", "Alta autonomía"],
        },
        overlap: {
          items: ["Percibe el entorno", "Actúa sobre él", "Tiene objetivos"],
        },
      }}
    />

    <Composition
      id="CLASS-HexGrid"
      component={HexGrid}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Componentes de un agente inteligente",
        center: { icon: "🤖", label: "Agente" },
        items: [
          { icon: "👁️",  label: "Sensores"     },
          { icon: "🧠",  label: "Razonamiento" },
          { icon: "💾",  label: "Memoria"       },
          { icon: "⚙️",  label: "Actuadores"   },
          { icon: "🎯",  label: "Objetivos"     },
          { icon: "🌍",  label: "Entorno"       },
        ],
      }}
    />

    <Composition
      id="CLASS-FlipCards"
      component={FlipCards}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Tipos de agentes inteligentes",
        items: [
          { icon: "⚡", label: "Reactivo",     title: "Agente Reactivo",     description: "Responde directamente a percepciones sin memoria interna." },
          { icon: "🧠", label: "Deliberativo", title: "Agente Deliberativo", description: "Razona sobre un modelo interno del mundo antes de actuar." },
          { icon: "🔄", label: "Híbrido",      title: "Agente Híbrido",      description: "Combina reactividad rápida con planificación deliberada." },
          { icon: "🎓", label: "Aprendiz",     title: "Agente Aprendiz",     description: "Mejora su comportamiento a partir de la experiencia acumulada." },
        ],
      }}
    />

    <Composition
      id="CLASS-MatrixGrid"
      component={MatrixGrid}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title:       "Tipos de agentes por dimensión",
        xAxisLeft:   "Baja autonomía",
        xAxisRight:  "Alta autonomía",
        yAxisTop:    "Entorno complejo",
        yAxisBottom: "Entorno simple",
        quadrants: [
          { icon: "🤖", title: "Agente reactivo",      description: "Responde sin planificar en entornos complejos" },
          { icon: "🧠", title: "Agente autónomo",      description: "Planifica y decide en entornos complejos" },
          { icon: "⚙️", title: "Programa tradicional", description: "Reglas fijas en entornos simples" },
          { icon: "🎯", title: "Agente deliberativo",  description: "Alta autonomía en tareas predecibles" },
        ],
      }}
    />

    <Composition
      id="CLASS-PyramidLevels"
      component={PyramidLevels}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Niveles de autonomía en agentes de IA",
        levels: [
          { label: "Reactivo",      description: "Solo responde a estímulos del entorno",         color: "#94A3B8" },
          { label: "Deliberativo",  description: "Planifica antes de actuar",                     color: "#6366F1" },
          { label: "Aprendizaje",   description: "Mejora con la experiencia acumulada",            color: "#0EA5E9" },
          { label: "Autónomo",      description: "Define sus propios objetivos y estrategias",     color: "#10B981" },
        ],
      }}
    />

    <Composition
      id="CLASS-TwoColumns"
      component={TwoColumns}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Programa tradicional vs Agente inteligente",
        left: {
          label: "Programa tradicional",
          color: "#64748B",
          items: [
            { text: "Sigue instrucciones fijas",          positive: false },
            { text: "No percibe el entorno",               positive: false },
            { text: "Sin memoria entre ejecuciones",       positive: false },
            { text: "No se adapta a cambios",              positive: false },
          ],
        },
        right: {
          label: "Agente inteligente",
          color: "#6366F1",
          items: [
            { text: "Toma decisiones autónomas",           positive: true },
            { text: "Percibe y reacciona al entorno",      positive: true },
            { text: "Mantiene estado interno",             positive: true },
            { text: "Se adapta y aprende",                 positive: true },
          ],
        },
      }}
    />

    <Composition
      id="CLASS-FourBoxes"
      component={FourBoxes}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Las 4 propiedades de un agente inteligente",
        items: [
          { icon: "🧠", title: "Autonomía",        description: "Opera sin intervención humana directa." },
          { icon: "⚡", title: "Reactividad",      description: "Percibe su entorno y responde a los cambios." },
          { icon: "🎯", title: "Proactividad",     description: "Toma la iniciativa orientado a objetivos." },
          { icon: "🤝", title: "Habilidad Social", description: "Interactúa con otros agentes y humanos." },
        ],
      }}
    />

    <Composition
      id="DEF-VisualAnalogy"
      component={VisualAnalogy}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Termostato básico vs Termostato inteligente",
        left: {
          label: "Lo que ya conoces",
          items: [
            "Regla fija: si T < X, encender",
            "Sin memoria ni aprendizaje",
            "Reacciona solo al estado actual",
          ],
        },
        right: {
          label: "El concepto nuevo",
          items: [
            "Aprende tus patrones de uso",
            "Recuerda preferencias pasadas",
            "Se adapta continuamente al entorno",
          ],
        },
      }}
    />

    <Composition
      id="DEF-RhetoricalQuestion"
      component={RhetoricalQuestion}
      durationInFrames={270}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        question: "¿Qué hace diferente a un agente de IA de un programa normal?",
        hint:     "Lo descubrirás en los próximos minutos",
      }}
    />

    <Composition
      id="DEF-ImpactTerm"
      component={ImpactTerm}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        category:   "Inteligencia Artificial",
        term:       "AGENTE",
        definition: "Sistema computacional situado en un entorno que percibe ese entorno y actúa sobre él de manera autónoma para alcanzar sus objetivos.",
      }}
    />

    <Composition
      id="DEF-ProgressiveReveal"
      component={ProgressiveReveal}
      durationInFrames={420}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "¿Qué hace un agente inteligente?",
        items: [
          { text: "Percibe su entorno a través de sensores",          t_trigger: 1.0 },
          { text: "Procesa la información y actualiza su estado",     t_trigger: 4.0 },
          { text: "Evalúa opciones y selecciona la mejor acción",     t_trigger: 7.5 },
          { text: "Actúa sobre el entorno mediante actuadores",       t_trigger: 11.0 },
          { text: "Repite el ciclo de forma continua y autónoma",     t_trigger: 14.5 },
        ],
      }}
    />

    <Composition
      id="DEF-Central"
      component={CentralDefinition}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        term:       "Agente inteligente",
        definition: "Sistema que percibe su entorno a través de sensores y actúa sobre él mediante actuadores para alcanzar sus objetivos.",
      }}
    />

    <Composition
      id="CLOSE-Credits"
      component={Credits}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Fuentes y referencias",
        items: [
          { label: "Libro",    text: "Russell & Norvig — Artificial Intelligence: A Modern Approach" },
          { label: "Paper",    text: "Wooldridge & Jennings — Intelligent Agents (1995)" },
          { label: "Curso",    text: "CS221 Stanford — Artificial Intelligence Principles" },
          { label: "Web",      text: "arxiv.org/abs/2309.07864 — Survey on LLM Agents" },
          { label: "Créditos", text: "Producción: NuevaCiencia · Música: Epidemic Sound" },
        ],
      }}
    />

    <Composition
      id="CLOSE-Quote"
      component={ClosingQuote}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        quote:  "Un agente inteligente no solo reacciona al mundo, lo transforma.",
        author: "Stuart Russell",
      }}
    />

    <Composition
      id="CLOSE-Keywords"
      component={ClosingKeywords}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        words:    ["Autonomía", "Percepción", "Decisión", "Acción", "Agente"],
        subtitle: "Lo que aprendiste hoy",
      }}
    />

    <Composition<TitleCardProps>
      id="S01-Intro"
      component={TitleCard}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Fundamentos de agentes de IA",
        word_cues: [
          { word: "Hola a todos.", t_start: 1.8, t_end: 2.6 },
          { word: "Hoy comenzamos una serie", t_start: 3.5, t_end: 5.0 },
          { word: "sobre agentes de IA.", t_start: 5.1, t_end: 7.2 },
        ],
      }}
    />

    <Composition<AgentLoopProps>
      id="S03-AgentLoop"
      component={AgentLoop}
      durationInFrames={420}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        word_cues: [
          { word: "Un agente percibe su entorno", t_start: 11.3, t_end: 13.0 },
          { word: "y actúa sobre él", t_start: 13.1, t_end: 14.5 },
        ],
      }}
    />

    <Composition<ComparisonSlideProps>
      id="S04-Comparison"
      component={ComparisonSlide}
      durationInFrames={540}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Termostato básico vs inteligente",
        left: {
          label: "BÁSICO",
          color: "#6b7280",
          items: [
            { text: "Regla fija: si T < X encender", positive: false },
            { text: "Sin memoria ni aprendizaje",    positive: false },
          ],
        },
        right: {
          label: "INTELIGENTE (AGENTE)",
          color: "#6C63FF",
          items: [
            { text: "Aprende tus patrones de uso",   positive: true },
            { text: "Se adapta continuamente",        positive: true },
          ],
        },
        word_cues: [],
      }}
    />

    <Composition<FourPillarsProps>
      id="S07-FourPillars"
      component={FourPillars}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Las 4 propiedades de Wooldridge",
        pillars: [
          { title: "Autonomía",       description: "Opera sin intervención humana directa.",           color: "#6C63FF", icon: "autonomy"   },
          { title: "Reactividad",     description: "Percibe su entorno y responde a los cambios.",     color: "#00D9FF", icon: "reactivity" },
          { title: "Proactividad",    description: "Toma la iniciativa orientado a objetivos.",        color: "#10b981", icon: "proactivity"},
          { title: "Habilidad Social",description: "Interactúa con otros agentes y humanos.",         color: "#f59e0b", icon: "social"     },
        ],
        word_cues: [],
      }}
    />

    <Composition<BulletRevealProps>
      id="S08-Autonomia"
      component={BulletReveal}
      durationInFrames={480}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Autonomía",
        subtitle: "Se gobierna a sí mismo",
        accent: "#6C63FF",
        items: [
          { text: "Opera sin intervención humana directa",          t_trigger: 2.0  },
          { text: "Controla sus propias acciones y estado interno", t_trigger: 8.0  },
          { text: "No necesita instrucciones paso a paso",          t_trigger: 14.5 },
        ],
        word_cues: [],
      }}
    />

    <Composition
      id="NAR-ParticleNetwork"
      component={ParticleNetwork}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Red de agentes de IA",
        subtitle: "sistemas multiagente",
      }}
    />

    <Composition<NeonGlowProps>
      id="FX-NeonGlow"
      component={NeonGlow}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        line1: "AGENTE DE IA",
        line2: "percibe · decide · actúa",
        accent: "#00D9FF",
        word_cues: [],
      }}
    />

    <Composition<WaveOrbProps>
      id="FX-WaveOrb"
      component={WaveOrb}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        concept: "PERCIBIR",
        label: "El agente monitorea su entorno",
        color: "#6C63FF",
      }}
    />

    <Composition<RotatingCube3DProps>
      id="FX-RotatingCube"
      component={RotatingCube3D}
      durationInFrames={600}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        label: "Las propiedades de Wooldridge",
        faces: [
          { title: "AUTONOMÍA",        subtitle: "se gobierna a sí mismo",    color: "#6C63FF" },
          { title: "REACTIVIDAD",      subtitle: "responde al entorno",        color: "#00D9FF" },
          { title: "PROACTIVIDAD",     subtitle: "toma la iniciativa",         color: "#10b981" },
          { title: "HABILIDAD SOCIAL", subtitle: "colabora con otros agentes", color: "#f59e0b" },
          { title: "AGENTE DE IA",     subtitle: "wooldridge · 1995",          color: "#6C63FF" },
          { title: "ENTORNO",          subtitle: "percibe · decide · actúa",   color: "#ec4899" },
        ],
      }}
    />

    <Composition<TimelineSlideProps>
      id="NAR-Timeline"
      component={TimelineSlide}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Evolución de los agentes de IA",
        accent: "#6C63FF",
        events: [
          { year: "1950", title: "Turing Test", description: "¿Pueden las máquinas pensar?"   },
          { year: "1986", title: "Agentes BDI",  description: "Creencias, Deseos, Intenciones" },
          { year: "1995", title: "Wooldridge",   description: "Las 4 propiedades formales"     },
          { year: "2017", title: "Deep RL",      description: "Agentes que aprenden jugando"   },
          { year: "2024", title: "LLM Agents",   description: "Razonamiento + herramientas"    },
        ],
      }}
    />

    <Composition<StatCounterProps>
      id="DATA-StatCounter"
      component={StatCounter}
      durationInFrames={270}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "¿Por qué importan los agentes?",
        stats: [
          { value: 4,   suffix: "",   label: "Propiedades esenciales", sublabel: "según Wooldridge",       color: "#6C63FF" },
          { value: 95,  suffix: "%",  label: "Autonomía posible",      sublabel: "sin intervención humana", color: "#10b981" },
          { value: 360, suffix: "°",  label: "Percepción del entorno", sublabel: "monitoreo continuo",      color: "#00D9FF" },
        ],
      }}
    />

    <Composition<ProcessFlowProps>
      id="NEW-ProcessFlow"
      component={ProcessFlow}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "¿Cómo decide un agente?",
        subtitle: "El ciclo percepción → decisión → acción",
        steps: [
          { number: "1", title: "PERCIBIR",  description: "Sensores capturan el estado del entorno",          color: "#6C63FF" },
          { number: "2", title: "PROCESAR",  description: "Interpreta y actualiza su modelo interno",          color: "#00D9FF" },
          { number: "3", title: "DECIDIR",   description: "Evalúa opciones y selecciona la mejor acción",      color: "#10b981" },
          { number: "4", title: "ACTUAR",    description: "Ejecuta la acción y modifica el entorno",           color: "#f59e0b" },
        ],
      }}
    />

    <Composition<GlitchRevealProps>
      id="FX-GlitchReveal"
      component={GlitchReveal}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        line1: "AUTÓNOMO",
        line2: "sistema · agente · inteligencia",
      }}
    />

    <Composition<GradientTitleProps>
      id="FX-GradientTitle"
      component={GradientTitle}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        tag: "Clase 01 — Fundamentos",
        line1: "Agentes de IA",
        line2: "Autonomía · Reactividad · Proactividad",
        gradient: "linear-gradient(135deg, #1a1260 0%, #6C63FF 50%, #00D9FF 100%)",
      }}
    />

    <Composition<GradientTitleProps>
      id="FX-GradientTitle-Coral"
      component={GradientTitle}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        tag: "Wooldridge · 1995",
        line1: "4 Propiedades",
        line2: "que definen un verdadero agente",
        gradient: "linear-gradient(135deg, #FC466B 0%, #3F5EFB 100%)",
      }}
    />
  </>
);

registerRoot(RemotionRoot);
