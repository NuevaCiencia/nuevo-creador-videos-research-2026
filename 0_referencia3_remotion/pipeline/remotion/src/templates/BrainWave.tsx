/**
 * BrainWave — Onda SVG animada con etiquetas flotantes
 * Fondo blanco. Una curva sinusoidal que recorre la pantalla
 * con conceptos que "emergen" desde los picos de la ola.
 * Minimalista pero dinámico.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type WavePoint = {
  label: string;
  sub: string;
  color: string;
};

export type BrainWaveProps = {
  title: string;
  accent: string;
  points: WavePoint[];
};

const W = 1920;
const H = 1080;
const WAVE_Y = H * 0.58;
const AMP = 140;
const WAVE_COUNT = 2; // full cycles across screen

// Generate SVG path for the wave (static positions for determinism)
function wavePath(progress: number, offsetX: number): string {
  const pts: string[] = [];
  const steps = 120;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = t * W;
    const phase = t * Math.PI * 2 * WAVE_COUNT + offsetX;
    const y = WAVE_Y + Math.sin(phase) * AMP;
    pts.push(`${x},${y}`);
  }
  // Only draw up to progress
  const visible = Math.floor(progress * (steps + 1));
  const visiblePts = pts.slice(0, Math.max(1, visible));
  return `M ${visiblePts.join(" L ")}`;
}

export const BrainWave: React.FC<BrainWaveProps> = ({ title, accent, points }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Wave draws itself left to right
  const waveProgress = interpolate(frame, [0, 50], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Slow wave drift after drawing
  const drift = (frame / fps) * 0.4;

  // Title
  const titleOp = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY  = interpolate(frame, [0, 20], [-20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Points sit at evenly spaced positions along the wave
  const N = points.length;

  return (
    <AbsoluteFill style={{ background: "#FFFFFF" }}>

      {/* Light grid */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `
          linear-gradient(rgba(0,0,0,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,0,0,0.04) 1px, transparent 1px)
        `,
        backgroundSize: "60px 60px",
        pointerEvents: "none",
      }} />

      {/* Title */}
      <div style={{
        position: "absolute", top: 72, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
        transform: `translateY(${titleY}px)`,
      }}>
        <h1 style={{
          margin: 0, fontSize: 58, fontWeight: 800,
          color: "#111827",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "-0.5px",
        }}>
          {title}
        </h1>
      </div>

      {/* SVG wave + labels */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <defs>
          <filter id="waveglow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Shadow wave — slightly offset for depth */}
        <path
          d={wavePath(waveProgress, drift + 0.12)}
          fill="none"
          stroke={accent}
          strokeWidth={4}
          strokeLinecap="round"
          opacity={0.12}
        />

        {/* Main wave */}
        <path
          d={wavePath(waveProgress, drift)}
          fill="none"
          stroke={accent}
          strokeWidth={4}
          strokeLinecap="round"
          filter="url(#waveglow)"
          opacity={0.85}
        />

        {/* Points along wave */}
        {points.map((pt, i) => {
          const t = (i + 0.5) / N;
          const px = t * W;
          const phase = t * Math.PI * 2 * WAVE_COUNT + drift;
          const py = WAVE_Y + Math.sin(phase) * AMP;

          // Point appears when wave reaches it
          const pointFrame = t * 50;
          const delay = pointFrame + 8;

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 18, stiffness: 180 }, from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          // Label above or below based on sin value
          const above = Math.sin(phase) < 0;
          const labelY = above ? py - 80 - 20 * s : py + 80 + 20 * (1 - s);
          const lineY2 = above ? py - 18 : py + 18;

          return (
            <g key={i} opacity={op}>
              {/* Dot */}
              <circle
                cx={px} cy={py}
                r={10 * s}
                fill={pt.color}
                filter="url(#waveglow)"
              />

              {/* Vertical tick */}
              <line
                x1={px} y1={above ? py - 10 : py + 10}
                x2={px} y2={lineY2}
                stroke={pt.color}
                strokeWidth={2}
                strokeDasharray="4 3"
                opacity={0.5}
              />

              {/* Label box */}
              <g transform={`translate(${px}, ${labelY})`}>
                <rect
                  x={-90} y={-30}
                  width={180} height={56}
                  rx={12}
                  fill={pt.color}
                  fillOpacity={0.1}
                  stroke={pt.color}
                  strokeOpacity={0.3}
                  strokeWidth={1.5}
                />
                <text
                  x={0} y={-6}
                  textAnchor="middle"
                  fontSize={20}
                  fontWeight={700}
                  fontFamily="Inter, system-ui, sans-serif"
                  fill={pt.color}
                >
                  {pt.label}
                </text>
                <text
                  x={0} y={16}
                  textAnchor="middle"
                  fontSize={14}
                  fontFamily="Inter, system-ui, sans-serif"
                  fill="rgba(0,0,0,0.4)"
                >
                  {pt.sub}
                </text>
              </g>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
