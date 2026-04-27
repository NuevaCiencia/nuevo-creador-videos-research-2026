/**
 * ParticleNetwork — Red neuronal de partículas animadas
 * 55 nodos que se mueven en órbitas suaves y se conectan con líneas
 * cuando están cerca. Simula una red de agentes comunicándose.
 * 100% SVG + Math, sin assets externos.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type ParticleNetworkProps = {
  title?: string;
  subtitle?: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "radial-gradient(ellipse at 50% 50%, #12112a 0%, #080710 70%)",
  fontFamily:   "Inter, system-ui, sans-serif",

  titleSize:    96,
  titleColor:   "rgba(255,255,255,0.92)",
  titleWeight:  900,
  titleGlow:    "0 0 60px rgba(108,99,255,0.6), 0 0 120px rgba(108,99,255,0.3)",

  subtitleSize:   36,
  subtitleColor:  "rgba(255,255,255,0.45)",
  subtitleWeight: 300,

  nParticles:    55,       // número de partículas
  connectDist:   195,     // distancia máxima para conectar
  colors:        ["#6C63FF", "#6C63FF", "#00D9FF", "#6C63FF", "#10b981", "#00D9FF"],
};
// ─────────────────────────────────────────────────────────────────────────────

const N = CONFIG.nParticles;
const CONNECT_DIST = CONFIG.connectDist;
const COLORS = CONFIG.colors;

function rand(i: number, seed: number): number {
  return Math.abs(Math.sin(i * 127.1 + seed * 311.7 + 43758.5453) % 1);
}

// Partículas generadas de forma determinista (mismo resultado en cada render)
const PARTICLES = Array.from({ length: N }, (_, i) => ({
  bx:     80 + rand(i, 0) * 1760,
  by:     80 + rand(i, 1) * 920,
  rx:     35 + rand(i, 2) * 110,
  ry:     25 + rand(i, 3) * 90,
  period: 5  + rand(i, 4) * 13,
  phase:  rand(i, 5) * Math.PI * 2,
  phase2: rand(i, 6) * Math.PI * 2,
  color:  COLORS[Math.floor(rand(i, 7) * COLORS.length)],
  size:   2  + rand(i, 8) * 4.5,
  bright: 0.5 + rand(i, 9) * 0.5,   // "profundidad"
}));

// ─────────────────────────────────────────────────────────────────────────────

export const ParticleNetwork: React.FC<ParticleNetworkProps> = ({
  title = "Red de agentes de IA",
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const fadeIn = interpolate(frame, [0, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Posición actual de cada partícula
  const pos = PARTICLES.map((p) => ({
    x: p.bx + p.rx * Math.cos((t / p.period) * Math.PI * 2 + p.phase),
    y: p.by + p.ry * Math.sin((t / p.period) * Math.PI * 2 + p.phase2),
    color: p.color,
    size: p.size,
    bright: p.bright,
  }));

  // Conexiones entre partículas cercanas
  const lines: { x1: number; y1: number; x2: number; y2: number; op: number; color: string }[] = [];
  for (let i = 0; i < N; i++) {
    for (let j = i + 1; j < N; j++) {
      const dx = pos[i].x - pos[j].x;
      const dy = pos[i].y - pos[j].y;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < CONNECT_DIST) {
        lines.push({
          x1: pos[i].x, y1: pos[i].y,
          x2: pos[j].x, y2: pos[j].y,
          op: (1 - d / CONNECT_DIST) * 0.45,
          color: pos[i].color,
        });
      }
    }
  }

  // Pulso global suave
  const pulse = 1 + Math.sin(t * Math.PI * 0.8) * 0.06;

  return (
    <AbsoluteFill
      style={{
        background: CONFIG.bg,
        opacity: fadeIn,
      }}
    >
      <svg
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "hidden" }}
        viewBox="0 0 1920 1080"
      >
        <defs>
          {/* Glow filter para los nodos */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-strong" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Vignette */}
          <radialGradient id="vignette" cx="50%" cy="50%" r="70%">
            <stop offset="60%" stopColor="transparent" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.7)" />
          </radialGradient>
        </defs>

        {/* Líneas de conexión */}
        {lines.map((l, i) => (
          <line
            key={i}
            x1={l.x1} y1={l.y1}
            x2={l.x2} y2={l.y2}
            stroke={l.color}
            strokeWidth={0.8}
            opacity={l.op}
          />
        ))}

        {/* Nodos */}
        {pos.map((p, i) => (
          <g key={i} filter="url(#glow)">
            {/* Halo exterior */}
            <circle
              cx={p.x} cy={p.y}
              r={p.size * 2.5 * pulse}
              fill={p.color}
              opacity={0.12 * p.bright}
            />
            {/* Núcleo */}
            <circle
              cx={p.x} cy={p.y}
              r={p.size * pulse}
              fill={p.color}
              opacity={0.7 + p.bright * 0.3}
            />
            {/* Punto central brillante */}
            <circle
              cx={p.x} cy={p.y}
              r={p.size * 0.4}
              fill="white"
              opacity={0.6 * p.bright}
            />
          </g>
        ))}

        {/* Vignette overlay */}
        <rect x="0" y="0" width="1920" height="1080" fill="url(#vignette)" />
      </svg>

      {/* Texto central */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 16,
          pointerEvents: "none",
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: CONFIG.titleSize,
            fontWeight: CONFIG.titleWeight,
            color: CONFIG.titleColor,
            fontFamily: CONFIG.fontFamily,
            letterSpacing: "-2px",
            textShadow: CONFIG.titleGlow,
            textAlign: "center",
            padding: "0 120px",
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              margin: 0,
              fontSize: CONFIG.subtitleSize,
              color: CONFIG.subtitleColor,
              fontFamily: CONFIG.fontFamily,
              fontWeight: CONFIG.subtitleWeight,
              letterSpacing: "0.15em",
              textTransform: "uppercase",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

    </AbsoluteFill>
  );
};
