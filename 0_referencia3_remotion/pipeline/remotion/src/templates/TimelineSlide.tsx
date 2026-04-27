/**
 * TimelineSlide — Línea de tiempo horizontal, fondo BLANCO
 * Eventos que aparecen de izquierda a derecha con stagger.
 * La línea se dibuja primero, luego los nodos "pop" uno a uno.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type TimelineEvent = {
  year: string;
  title: string;
  description: string;
};

export type TimelineSlideProps = {
  title: string;
  events: TimelineEvent[];
  accent: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#FFFFFF",
  fontFamily:  "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#111827",
  titleWeight: 800,

  lineY:      520,    // Y de la línea horizontal
  lineLeft:   140,    // inicio izquierdo de la línea
  lineRight:  1780,   // fin derecho de la línea

  nodeDotR:   12,     // radio del círculo del nodo

  yearSize:   30,
  yearWeight: 700,

  eventTitleSize:   34,
  eventTitleColor:  "#111827",
  eventTitleWeight: 700,

  eventStagger:  20,   // frames entre eventos
  lineDrawEnd:   35,   // frame donde termina de dibujarse la línea
};
// ─────────────────────────────────────────────────────────────────────────────

export const TimelineSlide: React.FC<TimelineSlideProps> = ({
  title,
  events,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleY = interpolate(frame, [0, 20], [-30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleOp = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Línea que se dibuja de izquierda a derecha
  const lineProgress = interpolate(frame, [10, CONFIG.lineDrawEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const N = events.length;
  const lineLeft  = CONFIG.lineLeft;
  const lineRight = CONFIG.lineRight;
  const lineW     = lineRight - lineLeft;
  const lineY     = CONFIG.lineY;

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Fondo sutil — gradiente muy suave */}
      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(180deg, #FFFFFF 0%, #F5F7FF 100%)",
      }} />

      {/* Título */}
      <div style={{
        position: "absolute", top: 80, left: 0, right: 0,
        textAlign: "center",
        opacity: titleOp,
        transform: `translateY(${titleY}px)`,
      }}>
        <h1 style={{
          margin: 0, fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight,
          color: CONFIG.titleColor,
          fontFamily: CONFIG.fontFamily,
          letterSpacing: "-1px",
        }}>
          {title}
        </h1>
        {/* Línea decorativa */}
        <div style={{
          margin: "16px auto 0",
          width: interpolate(frame, [12, 35], [0, 180], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          height: 4, borderRadius: 2,
          background: accent,
        }} />
      </div>

      {/* SVG de la línea de tiempo */}
      <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}
        viewBox="0 0 1920 1080">

        {/* Línea principal */}
        <line
          x1={lineLeft} y1={lineY}
          x2={lineLeft + lineW * lineProgress} y2={lineY}
          stroke={`${accent}33`}
          strokeWidth={3}
        />

        {events.map((evt, i) => {
          const x = lineLeft + (lineW / (N - 1)) * i;
          const delay = CONFIG.lineDrawEnd + i * CONFIG.eventStagger;
          const nodeS = spring({ frame: frame - delay, fps, config: { damping: 16, stiffness: 240 }, from: 0, to: 1 });
          const nodeOp = interpolate(frame - delay, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const above = i % 2 === 0;

          return (
            <g key={i} opacity={nodeOp}>
              {/* Línea vertical hasta el nodo */}
              <line
                x1={x} y1={lineY - (above ? 20 : -20)}
                x2={x} y2={lineY - (above ? 100 : -100)}
                stroke={`${accent}55`} strokeWidth={1.5}
                transform={`scale(1,${nodeS})`}
                style={{ transformOrigin: `${x}px ${lineY}px` }}
              />
              {/* Nodo circular */}
              <circle cx={x} cy={lineY} r={CONFIG.nodeDotR * nodeS}
                fill={accent} />
              <circle cx={x} cy={lineY} r={5 * nodeS}
                fill="white" />

              {/* Año */}
              <text x={x} y={above ? lineY - 115 : lineY + 130}
                textAnchor="middle"
                fontSize={CONFIG.yearSize} fontWeight={CONFIG.yearWeight}
                fill={accent}
                fontFamily={CONFIG.fontFamily}>
                {evt.year}
              </text>

              {/* Título del evento */}
              <text x={x} y={above ? lineY - 145 : lineY + 160}
                textAnchor="middle"
                fontSize={CONFIG.eventTitleSize} fontWeight={CONFIG.eventTitleWeight}
                fill={CONFIG.eventTitleColor}
                fontFamily={CONFIG.fontFamily}>
                {evt.title}
              </text>

            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
