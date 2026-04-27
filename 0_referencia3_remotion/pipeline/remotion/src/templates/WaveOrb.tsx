/**
 * WaveOrb — Orbe central con ondas de radar expandiéndose
 * Representa al agente "percibiendo" su entorno.
 * Ondas que se dibujan solas en SVG + texto central animado.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
export type WaveOrbProps = {
  concept: string;      // texto dentro del orbe
  label?: string;       // etiqueta encima
  color?: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "radial-gradient(ellipse at 50% 50%, #0e0c1e 0%, #050409 80%)",
  fontFamily:  "Inter, system-ui, sans-serif",

  conceptSize:   52,
  conceptWeight: 800,
  conceptTracking: "0.08em",

  labelSize:   42,
  labelTracking: "0.2em",

  cx:         960,    // centro X del orbe
  cy:         520,    // centro Y del orbe
  minRadius:  70,
  maxRadius:  480,

  nWaves:      5,
  wavePeriod:  70,    // frames por ciclo

  radarSpeed:  60,    // grados por segundo del barrido
  orbPulseAmp: 0.05,  // amplitud del pulso del orbe
};
// ─────────────────────────────────────────────────────────────────────────────

const WAVE_PERIOD = CONFIG.wavePeriod;
const N_WAVES     = CONFIG.nWaves;
const MAX_RADIUS  = CONFIG.maxRadius;
const MIN_RADIUS  = CONFIG.minRadius;

// Líneas de "sensor" que rotan
const SENSOR_LINES = Array.from({ length: 8 }, (_, i) => ({
  angle: (i / 8) * Math.PI * 2,
  length: 120 + (i % 3) * 40,
  opacity: 0.15 + (i % 2) * 0.12,
}));

export const WaveOrb: React.FC<WaveOrbProps> = ({
  concept,
  label = "PERCIBIENDO EL ENTORNO",
  color = "#6C63FF",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Entrada del texto central
  const textScale = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 160 },
    from: 0.5,
    to: 1,
  });
  const textOp = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Rotación del radar
  const radarAngle = (frame / fps) * 60; // 60°/s

  // Pulso del orbe central
  const orbPulse = 1 + Math.sin((frame / fps) * Math.PI * 1.4) * 0.05;

  const CX = CONFIG.cx, CY = CONFIG.cy;

  return (
    <AbsoluteFill
      style={{
        background: CONFIG.bg,
        opacity: fadeIn,
      }}
    >
      {/* Label superior */}
      <div
        style={{
          position: "absolute",
          top: 50,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: textOp,
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: CONFIG.labelSize,
            fontWeight: 400,
            color: `${color}99`,
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.2em",
            textTransform: "uppercase",
          }}
        >
          {label}
        </p>
      </div>

      {/* SVG principal */}
      <svg
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        viewBox="0 0 1920 1080"
      >
        <defs>
          <filter id="orb-glow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="12" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="wave-blur" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" />
          </filter>
          <radialGradient id="orb-fill" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor={`${color}55`} />
            <stop offset="100%" stopColor={`${color}11`} />
          </radialGradient>
        </defs>

        {/* ── Ondas expandiéndose (radar) ─────────────────────────────── */}
        {Array.from({ length: N_WAVES }, (_, i) => {
          const offset  = i * (WAVE_PERIOD / N_WAVES);
          const local   = ((frame - offset) % WAVE_PERIOD + WAVE_PERIOD) % WAVE_PERIOD;
          const progress = local / WAVE_PERIOD;
          const r = MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * progress;
          const op = (1 - progress) * 0.55;

          return (
            <circle
              key={i}
              cx={CX} cy={CY}
              r={r}
              fill="none"
              stroke={color}
              strokeWidth={1.5}
              opacity={op}
              filter="url(#wave-blur)"
            />
          );
        })}

        {/* ── Líneas de sensor ─────────────────────────────────────────── */}
        {SENSOR_LINES.map((sl, i) => {
          const angle = sl.angle + (radarAngle * Math.PI) / 180;
          const x2 = CX + Math.cos(angle) * (MIN_RADIUS + sl.length);
          const y2 = CY + Math.sin(angle) * (MIN_RADIUS + sl.length);
          const x1 = CX + Math.cos(angle) * MIN_RADIUS;
          const y1 = CY + Math.sin(angle) * MIN_RADIUS;
          return (
            <line
              key={i}
              x1={x1} y1={y1} x2={x2} y2={y2}
              stroke={color}
              strokeWidth={1}
              opacity={sl.opacity}
            />
          );
        })}

        {/* ── Barrido de radar ─────────────────────────────────────────── */}
        <path
          d={`M ${CX} ${CY} L ${CX + MAX_RADIUS * 0.95 * Math.cos((radarAngle * Math.PI) / 180)} ${CY + MAX_RADIUS * 0.95 * Math.sin((radarAngle * Math.PI) / 180)}`}
          stroke={color}
          strokeWidth={2}
          opacity={0.6}
        />

        {/* ── Cruz de crosshair ────────────────────────────────────────── */}
        <line x1={CX - 90} y1={CY} x2={CX - MIN_RADIUS + 10} y2={CY} stroke={`${color}44`} strokeWidth={1} />
        <line x1={CX + MIN_RADIUS - 10} y1={CY} x2={CX + 90} y2={CY} stroke={`${color}44`} strokeWidth={1} />
        <line x1={CX} y1={CY - 90} x2={CX} y2={CY - MIN_RADIUS + 10} stroke={`${color}44`} strokeWidth={1} />
        <line x1={CX} y1={CY + MIN_RADIUS - 10} x2={CX} y2={CY + 90} stroke={`${color}44`} strokeWidth={1} />

        {/* ── Orbe central ─────────────────────────────────────────────── */}
        <g filter="url(#orb-glow)">
          {/* Halo exterior */}
          <circle cx={CX} cy={CY} r={MIN_RADIUS * 1.4 * orbPulse} fill="none" stroke={color} strokeWidth={1} opacity={0.2} />
          {/* Orbe principal */}
          <circle cx={CX} cy={CY} r={MIN_RADIUS * orbPulse} fill="url(#orb-fill)" stroke={color} strokeWidth={2} opacity={0.9} />
          {/* Brillo interior */}
          <circle cx={CX - 18} cy={CY - 20} r={22} fill="white" opacity={0.07} />
        </g>
      </svg>

      {/* ── Texto dentro del orbe ────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          left: CX - 200,
          top: CY - 50,
          width: 400,
          height: 100,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${textScale})`,
          opacity: textOp,
        }}
      >
        <span
          style={{
            fontSize: CONFIG.conceptSize,
            fontWeight: CONFIG.conceptWeight,
            color: "#FFFFFF",
            fontFamily: CONFIG.fontFamily,
            letterSpacing: CONFIG.conceptTracking,
            textAlign: "center",
            textShadow: `0 0 20px ${color}`,
          }}
        >
          {concept}
        </span>
      </div>

    </AbsoluteFill>
  );
};
