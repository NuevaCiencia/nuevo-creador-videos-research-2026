/**
 * FourPillars — Grid 2×2 de las 4 propiedades de Wooldridge
 * Cada tarjeta tiene un ícono SVG propio, título y descripción.
 * Entran con spring staggerado.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";

export type PillarDef = {
  title: string;
  description: string;
  color: string;
  icon: "autonomy" | "reactivity" | "proactivity" | "social";
};

export type FourPillarsProps = {
  title?: string;
  pillars: PillarDef[];
  word_cues: WordCue[];
};

// ── Iconos SVG inline ─────────────────────────────────────────────────────────

const IconAutonomy: React.FC<{ color: string }> = ({ color }) => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
    {/* Agente central */}
    <circle cx="32" cy="32" r="12" fill={`${color}33`} stroke={color} strokeWidth="2.5" />
    <circle cx="32" cy="32" r="5" fill={color} />
    {/* Órbita */}
    <circle cx="32" cy="32" r="22" stroke={`${color}55`} strokeWidth="1.5" strokeDasharray="4 3" />
    {/* Autonomía: escudo propio */}
    <path d="M32 10 L38 14 L38 22 Q38 28 32 31 Q26 28 26 22 L26 14 Z"
      fill={`${color}22`} stroke={color} strokeWidth="1.5" />
  </svg>
);

const IconReactivity: React.FC<{ color: string; frame: number; fps: number }> = ({ color, frame, fps }) => {
  // Onda de señal animada
  const phase = (frame / fps) * Math.PI * 2;
  const r1 = 16 + Math.sin(phase) * 2;
  const r2 = 26 + Math.sin(phase + 0.5) * 2;
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      <circle cx="32" cy="32" r="7" fill={color} />
      <circle cx="32" cy="32" r={r1} stroke={`${color}66`} strokeWidth="2" />
      <circle cx="32" cy="32" r={r2} stroke={`${color}33`} strokeWidth="1.5" />
      {/* Flecha de respuesta */}
      <path d="M44 32 L56 32" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <path d="M52 28 L56 32 L52 36" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

const IconProactivity: React.FC<{ color: string; frame: number; fps: number }> = ({ color, frame, fps }) => {
  // Flecha diagonal apuntando hacia adelante + línea de tiempo
  const offset = interpolate(Math.sin((frame / fps) * Math.PI * 1.5), [-1, 1], [0, 4]);
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      {/* Línea de tiempo */}
      <line x1="8" y1="44" x2="56" y2="44" stroke={`${color}44`} strokeWidth="1.5" />
      {/* Marcadores futuros */}
      <circle cx="36" cy="44" r="3" fill={`${color}55`} />
      <circle cx="48" cy="44" r="3" fill={`${color}33`} />
      {/* Agente anticipando */}
      <circle cx="16" cy="44" r="5" fill={`${color}33`} stroke={color} strokeWidth="2" />
      {/* Flecha de anticipación */}
      <path
        d={`M20 ${44 - offset} L46 ${20 - offset}`}
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray="4 3"
      />
      <path
        d={`M40 ${16 - offset} L46 ${20 - offset} L42 ${26 - offset}`}
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const IconSocial: React.FC<{ color: string; frame: number; fps: number }> = ({ color, frame, fps }) => {
  const nodes = [
    { x: 32, y: 14 },
    { x: 52, y: 40 },
    { x: 32, y: 52 },
    { x: 12, y: 40 },
  ];
  const pulse = interpolate(Math.sin((frame / fps) * Math.PI * 1.8), [-1, 1], [0.8, 1.0]);
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      {/* Conexiones */}
      {nodes.map((n1, i) =>
        nodes.slice(i + 1).map((n2, j) => (
          <line
            key={`${i}-${j}`}
            x1={n1.x} y1={n1.y}
            x2={n2.x} y2={n2.y}
            stroke={`${color}44`}
            strokeWidth="1.5"
          />
        ))
      )}
      {/* Nodos */}
      {nodes.map((n, i) => (
        <circle
          key={i}
          cx={n.x}
          cy={n.y}
          r={i === 0 ? 7 * pulse : 5}
          fill={i === 0 ? color : `${color}88`}
        />
      ))}
    </svg>
  );
};

// ── Tarjeta individual ────────────────────────────────────────────────────────

const Card: React.FC<{
  pillar: PillarDef;
  delay: number;
  frame: number;
  fps: number;
}> = ({ pillar, delay, frame, fps }) => {
  const s = spring({
    frame: frame - delay,
    fps,
    config: { damping: 20, stiffness: 180 },
    from: 0,
    to: 1,
  });
  const op = interpolate(frame - delay, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        background: `${pillar.color}14`,
        border: `1.5px solid ${pillar.color}55`,
        borderRadius: 20,
        padding: "32px 36px",
        display: "flex",
        flexDirection: "column",
        gap: 16,
        transform: `scale(${s})`,
        opacity: op,
        boxShadow: `0 0 40px ${pillar.color}22`,
      }}
    >
      {/* Ícono */}
      <div>
        {pillar.icon === "autonomy"   && <IconAutonomy color={pillar.color} />}
        {pillar.icon === "reactivity" && <IconReactivity color={pillar.color} frame={frame} fps={fps} />}
        {pillar.icon === "proactivity"&& <IconProactivity color={pillar.color} frame={frame} fps={fps} />}
        {pillar.icon === "social"     && <IconSocial color={pillar.color} frame={frame} fps={fps} />}
      </div>

      {/* Título */}
      <h3
        style={{
          margin: 0,
          fontSize: 30,
          fontWeight: 800,
          color: "#FFFFFF",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "0.04em",
        }}
      >
        {pillar.title}
      </h3>

      {/* Descripción */}
      <p
        style={{
          margin: 0,
          fontSize: 22,
          color: "rgba(255,255,255,0.6)",
          fontFamily: "Inter, system-ui, sans-serif",
          lineHeight: 1.5,
        }}
      >
        {pillar.description}
      </p>
    </div>
  );
};

// ── Componente principal ──────────────────────────────────────────────────────

const CARD_STAGGER = 22;

export const FourPillars: React.FC<FourPillarsProps> = ({
  title = "Las 4 propiedades de Wooldridge",
  pillars,
  word_cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const row1 = pillars.slice(0, 2);
  const row2 = pillars.slice(2, 4);

  return (
    <AbsoluteFill
      style={{ background: "linear-gradient(135deg, #0a0912 0%, #12112a 100%)" }}
    >
      {/* Título */}
      <div
        style={{
          position: "absolute",
          top: 40,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: titleOp,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 44,
            fontWeight: 700,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
          }}
        >
          {title}
        </h2>
      </div>

      {/* Grid 2×2 */}
      <div
        style={{
          position: "absolute",
          top: 120,
          left: 72,
          right: 72,
          bottom: 120,
          display: "flex",
          flexDirection: "column",
          gap: 24,
        }}
      >
        {/* Fila 1 */}
        <div style={{ display: "flex", flex: 1, gap: 24 }}>
          {row1.map((p, i) => (
            <Card key={p.title} pillar={p} delay={i * CARD_STAGGER + 14} frame={frame} fps={fps} />
          ))}
        </div>
        {/* Fila 2 */}
        <div style={{ display: "flex", flex: 1, gap: 24 }}>
          {row2.map((p, i) => (
            <Card key={p.title} pillar={p} delay={(i + 2) * CARD_STAGGER + 14} frame={frame} fps={fps} />
          ))}
        </div>
      </div>

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
