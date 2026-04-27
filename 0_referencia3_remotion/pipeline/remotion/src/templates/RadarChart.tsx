/**
 * RadarChart — Gráfico araña / radar que se dibuja desde cero
 * SVG con polygon animado (área se llena gradualmente).
 * Fondo oscuro. Ejes con etiquetas que aparecen con stagger.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type RadarAxis = {
  label: string;
  value: number;   // 0–100
  color: string;
};

export type RadarChartProps = {
  title: string;
  subtitle?: string;
  axes: RadarAxis[];
  fillColor: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  titleSize:    72,
  titleColor:   "#0F172A",
  titleWeight:  800,

  subtitleSize:  24,
  subtitleColor: "#64748B",

  cx:     960,   // centro X del radar
  cy:     560,   // centro Y del radar
  maxR:   300,   // radio máximo
  levels: 4,     // líneas de cuadrícula

  axisLabelSize:   30,
  axisLabelWeight: 700,

  valueSize:    22,
  valueColor:   "#1E293B",
  valueWeight:  700,

  strokeW:     3,
  fillOpacity: 0.18,
};
// ─────────────────────────────────────────────────────────────────────────────

function axisPoint(i: number, n: number, r: number): [number, number] {
  const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
  return [CONFIG.cx + Math.cos(angle) * r, CONFIG.cy + Math.sin(angle) * r];
}

export const RadarChart: React.FC<RadarChartProps> = ({
  title,
  subtitle,
  axes,
  fillColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const N = axes.length;

  // Overall draw progress
  const drawProgress = interpolate(frame, [10, 70], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Labels stagger in
  const labelOp = (i: number) =>
    interpolate(frame - 40 - i * 8, [0, 16], [0, 1], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Grid web points
  const webLevels = Array.from({ length: CONFIG.levels }, (_, l) => {
    const r = (CONFIG.maxR * (l + 1)) / CONFIG.levels;
    return Array.from({ length: N }, (_, i) => axisPoint(i, N, r));
  });

  // Data polygon points (animated)
  const dataPoints = axes.map((ax, i) => {
    const r = (ax.value / 100) * CONFIG.maxR * drawProgress;
    return axisPoint(i, N, r);
  });
  const dataPoly = dataPoints.map(([x, y]) => `${x},${y}`).join(" ");

  // Pulse glow on data polygon
  const glow = 6 + Math.sin((frame / fps) * Math.PI * 1.5) * 4;

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Title */}
      <div style={{
        position: "absolute", top: 56, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
      }}>
        <h1 style={{
          margin: 0, fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight, color: CONFIG.titleColor,
          fontFamily: CONFIG.fontFamily, letterSpacing: "-0.5px",
        }}>{title}</h1>
        {subtitle && (
          <p style={{
            margin: "8px 0 0", fontSize: CONFIG.subtitleSize, color: CONFIG.subtitleColor,
            fontFamily: CONFIG.fontFamily, fontWeight: 300,
            letterSpacing: "0.1em",
          }}>{subtitle}</p>
        )}
      </div>

      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="rglow">
            <feGaussianBlur stdDeviation={glow} result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Grid web */}
        {webLevels.map((pts, l) => (
          <polygon
            key={l}
            points={pts.map(([x, y]) => `${x},${y}`).join(" ")}
            fill="none"
            stroke="rgba(0,0,0,0.08)"
            strokeWidth={1.5}
          />
        ))}

        {/* Axis lines */}
        {axes.map((_, i) => {
          const [ex, ey] = axisPoint(i, N, CONFIG.maxR);
          return (
            <line key={i}
              x1={CONFIG.cx} y1={CONFIG.cy} x2={ex} y2={ey}
              stroke="rgba(0,0,0,0.1)" strokeWidth={1.5}
            />
          );
        })}

        {/* Data polygon fill */}
        <polygon
          points={dataPoly}
          fill={fillColor}
          fillOpacity={CONFIG.fillOpacity}
          stroke="none"
        />

        {/* Data polygon stroke with glow */}
        <polygon
          points={dataPoly}
          fill="none"
          stroke={fillColor}
          strokeWidth={CONFIG.strokeW}
          filter="url(#rglow)"
          opacity={0.9}
        />

        {/* Data dots */}
        {dataPoints.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={7} fill={axes[i].color} filter="url(#rglow)" />
        ))}

        {/* Axis labels */}
        {axes.map((ax, i) => {
          const [ex, ey] = axisPoint(i, N, CONFIG.maxR + 52);
          const anchor = ex < CONFIG.cx - 10 ? "end" : ex > CONFIG.cx + 10 ? "start" : "middle";

          // Value badge position
          const [bx, by] = axisPoint(i, N, (ax.value / 100) * CONFIG.maxR * drawProgress + 28);

          return (
            <g key={i} opacity={labelOp(i)}>
              {/* Axis label */}
              <text
                x={ex} y={ey}
                textAnchor={anchor}
                dominantBaseline="middle"
                fontSize={CONFIG.axisLabelSize}
                fontWeight={CONFIG.axisLabelWeight}
                fill={ax.color}
                fontFamily={CONFIG.fontFamily}
              >
                {ax.label}
              </text>
              {/* Value badge */}
              {drawProgress > 0.4 && (
                <text
                  x={bx} y={by}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={CONFIG.valueSize}
                  fontWeight={CONFIG.valueWeight}
                  fill={CONFIG.valueColor}
                  fontFamily={CONFIG.fontFamily}
                >
                  {ax.value}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
