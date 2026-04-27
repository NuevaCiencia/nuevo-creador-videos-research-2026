/**
 * PieDonut — Gráfico de rosca/donut que se dibuja con strokeDashoffset
 * Cada segmento se anima por separado. Fondo oscuro.
 * Leyenda a la derecha con valores que cuentan.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type DonutSlice = {
  label: string;
  value: number;   // absolute value
};

const PALETTE = ["#6366F1","#0EA5E9","#10B981","#F59E0B","#EC4899","#8B5CF6","#EF4444","#14B8A6"];

export type PieDonutProps = {
  title: string;
  slices: DonutSlice[];
  unit?: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  titleSize:    72,
  titleColor:   "#0F172A",
  titleWeight:  800,

  cx: 680,         // centro X del donut
  cy: 540,         // centro Y del donut
  rOuter: 280,     // radio exterior
  rInner: 160,     // radio interior (hueco)
  gapDeg: 2.5,     // separación entre segmentos en grados

  sliceLabelSize: 28,
  sliceLabelWeight: 700,
  slicePctSize:   22,
  slicePctColor:  "#64748B",

  legendX:       1280,  // X donde empieza la leyenda
  legendStartY:  400,   // Y del primer item de leyenda
  legendGap:     56,    // espacio entre items
  legendLabelSize: 28,
  legendLabelWeight: 600,
  legendValueSize: 28,
  legendValueWeight: 700,

  centerTotalSize:  70,
  centerTotalColor: "#0F172A",
  centerTotalWeight: 900,

  stagger: 12,
};
// ─────────────────────────────────────────────────────────────────────────────

const CIRCUMFERENCE = 2 * Math.PI * ((CONFIG.rOuter + CONFIG.rInner) / 2);
const STROKE_W = CONFIG.rOuter - CONFIG.rInner;
const DRAW_R   = (CONFIG.rOuter + CONFIG.rInner) / 2;

function degToRad(d: number) { return (d * Math.PI) / 180; }

export const PieDonut: React.FC<PieDonutProps> = ({ title, slices, unit = "" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const total = slices.reduce((s, x) => s + x.value, 0);

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const totalOp = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Build segments
  let cumDeg = -90; // start at top

  const segments = slices.map((slice, i) => {
    const sliceDeg = (slice.value / total) * 360 - CONFIG.gapDeg;
    const startDeg = cumDeg + CONFIG.gapDeg / 2;
    cumDeg += (slice.value / total) * 360;

    return { slice, i, sliceDeg, startDeg };
  });

  // Glow pulse
  const glow = 6 + Math.sin((frame / 30) * Math.PI) * 3;

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
      </div>

      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="pglow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation={glow} result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {segments.map(({ slice, i, sliceDeg, startDeg }) => {
          const delay = 14 + i * CONFIG.stagger;
          const arcLen = (sliceDeg / 360) * CIRCUMFERENCE;

          const prog = interpolate(frame - delay, [0, 35], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const op = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          // Midpoint angle for label line
          const midRad = degToRad(startDeg + sliceDeg / 2);
          const labelR  = CONFIG.rOuter + 40;
          const lx = CONFIG.cx + Math.cos(midRad) * labelR;
          const ly = CONFIG.cy + Math.sin(midRad) * labelR;
          const lx2 = CONFIG.cx + Math.cos(midRad) * (labelR + 30);
          const ly2 = CONFIG.cy + Math.sin(midRad) * (labelR + 30);
          const anchor = lx2 > CONFIG.cx ? "start" : "end";

          const displayVal = Math.round(prog * slice.value);
          const pct = Math.round((slice.value / total) * 100);

          return (
            <g key={i} opacity={op}>
              {/* Arc segment */}
              <circle
                cx={CONFIG.cx} cy={CONFIG.cy}
                r={DRAW_R}
                fill="none"
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={STROKE_W}
                strokeLinecap="round"
                strokeDasharray={`${arcLen * prog} ${CIRCUMFERENCE}`}
                strokeDashoffset={0}
                transform={`rotate(${startDeg} ${CONFIG.cx} ${CONFIG.cy})`}
                filter="url(#pglow)"
              />

              {/* Label line */}
              {prog > 0.6 && (
                <g opacity={interpolate(prog, [0.6, 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
                  <line
                    x1={CONFIG.cx + Math.cos(midRad) * CONFIG.rOuter}
                    y1={CONFIG.cy + Math.sin(midRad) * CONFIG.rOuter}
                    x2={lx2} y2={ly2}
                    stroke={PALETTE[i % PALETTE.length]}
                    strokeWidth={1.5}
                    strokeOpacity={0.6}
                  />
                  <text
                    x={lx2 + (anchor === "start" ? 10 : -10)}
                    y={ly2 - 8}
                    textAnchor={anchor}
                    fontSize={CONFIG.sliceLabelSize} fontWeight={CONFIG.sliceLabelWeight}
                    fill={PALETTE[i % PALETTE.length]}
                    fontFamily={CONFIG.fontFamily}
                  >
                    {slice.label}
                  </text>
                  <text
                    x={lx2 + (anchor === "start" ? 10 : -10)}
                    y={ly2 + 24}
                    textAnchor={anchor}
                    fontSize={CONFIG.slicePctSize}
                    fill={CONFIG.slicePctColor}
                    fontFamily={CONFIG.fontFamily}
                  >
                    {pct}%
                  </text>
                </g>
              )}
            </g>
          );
        })}

        {/* Center total */}
        <g opacity={totalOp}>
          <text x={CONFIG.cx} y={CONFIG.cy - 12}
            textAnchor="middle" fontSize={CONFIG.centerTotalSize} fontWeight={CONFIG.centerTotalWeight}
            fill={CONFIG.centerTotalColor} fontFamily={CONFIG.fontFamily}>
            {total}{unit}
          </text>
          <text x={CONFIG.cx} y={CONFIG.cy + 30}
            textAnchor="middle" fontSize={20}
            fill="#94A3B8" fontFamily={CONFIG.fontFamily}
            letterSpacing="0.15em">
            TOTAL
          </text>
        </g>

        {/* Legend right */}
        {slices.map((s, i) => {
          const lop = interpolate(frame - 20 - i * 10, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const lx  = interpolate(frame - 20 - i * 10, [0, 14], [40, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={i} opacity={lop} transform={`translate(${lx}, 0)`}>
              <rect x={CONFIG.legendX} y={CONFIG.legendStartY + i * CONFIG.legendGap} width={16} height={16} rx={4} fill={PALETTE[i % PALETTE.length]} />
              <text x={CONFIG.legendX + 28} y={CONFIG.legendStartY + 14 + i * CONFIG.legendGap}
                fontSize={CONFIG.legendLabelSize} fontWeight={CONFIG.legendLabelWeight}
                fill="#1E293B" fontFamily={CONFIG.fontFamily}>
                {s.label}
              </text>
              <text x={CONFIG.legendX + 270} y={CONFIG.legendStartY + 14 + i * CONFIG.legendGap}
                textAnchor="end" fontSize={CONFIG.legendValueSize} fontWeight={CONFIG.legendValueWeight}
                fill={PALETTE[i % PALETTE.length]} fontFamily={CONFIG.fontFamily}>
                {s.value}{unit}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
