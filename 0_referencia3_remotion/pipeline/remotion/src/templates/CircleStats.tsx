/**
 * CircleStats — SVG arcos circulares que se dibujan como medidores
 * Fondo oscuro degradado. Cada stat tiene un arco SVG animado
 * con porcentaje que cuenta hacia arriba.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type CircleStat = {
  label: string;
  value: number;   // 0-100
  color: string;
  icon: string;    // emoji or short text
};

export type CircleStatsProps = {
  title: string;
  stats: CircleStat[];
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#FFFFFF",
  fontFamily:  "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 800,

  arcRadius:   140,   // radio de los arcos SVG
  arcStrokeW:  14,    // grosor del trazo del arco

  numberSize:  72,
  numberWeight: 900,
  suffixSize:  36,
  suffixWeight: 600,

  labelSize:   34,
  labelColor:  "#1E293B",
  labelWeight: 600,

  iconSize:    44,    // emoji dentro del círculo

  gap:         80,    // espacio entre arcos
  stagger:     20,    // frames entre apariciones
};
// ─────────────────────────────────────────────────────────────────────────────

const CIRCUMFERENCE = 2 * Math.PI * CONFIG.arcRadius;

function ArcStat({
  stat,
  frame,
  delay,
}: {
  stat: CircleStat;
  frame: number;
  delay: number;
}) {
  const lf = frame - delay;
  const progress = interpolate(lf, [0, 80], [0, stat.value / 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const opacity = interpolate(lf, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(lf, [0, 20], [0.6, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(1.4)),
  });

  const displayValue = Math.round(progress * stat.value);
  const dashoffset = CIRCUMFERENCE * (1 - progress);

  // Glow pulsing on the arc tip
  const glow = 8 + Math.sin((frame / 30) * Math.PI * 1.5) * 4;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 20,
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      {/* SVG arc */}
      <div style={{ position: "relative", width: CONFIG.arcRadius * 2 + 20, height: CONFIG.arcRadius * 2 + 20 }}>
        <svg
          width={CONFIG.arcRadius * 2 + 20}
          height={CONFIG.arcRadius * 2 + 20}
          viewBox={`0 0 ${CONFIG.arcRadius * 2 + 20} ${CONFIG.arcRadius * 2 + 20}`}
        >
          {/* Track */}
          <circle
            cx={CONFIG.arcRadius + 10}
            cy={CONFIG.arcRadius + 10}
            r={CONFIG.arcRadius}
            fill="none"
            stroke="rgba(0,0,0,0.07)"
            strokeWidth={CONFIG.arcStrokeW}
          />
          {/* Progress arc — starts at top (-90deg = -PI/2) */}
          <circle
            cx={CONFIG.arcRadius + 10}
            cy={CONFIG.arcRadius + 10}
            r={CONFIG.arcRadius}
            fill="none"
            stroke={stat.color}
            strokeWidth={CONFIG.arcStrokeW}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashoffset}
            transform={`rotate(-90 ${CONFIG.arcRadius + 10} ${CONFIG.arcRadius + 10})`}
            style={{ filter: `drop-shadow(0 0 ${glow}px ${stat.color})` }}
          />
        </svg>

        {/* Center content */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 4,
          }}
        >
          <span style={{ fontSize: CONFIG.iconSize, lineHeight: 1 }}>{stat.icon}</span>
          <span
            style={{
              fontSize: CONFIG.numberSize,
              fontWeight: CONFIG.numberWeight,
              color: stat.color,
              fontFamily: CONFIG.fontFamily,
              lineHeight: 1,
              letterSpacing: "-1px",
            }}
          >
            {displayValue}
            <span style={{ fontSize: CONFIG.suffixSize, fontWeight: CONFIG.suffixWeight }}>%</span>
          </span>
        </div>
      </div>

      {/* Label */}
      <p
        style={{
          margin: 0,
          fontSize: CONFIG.labelSize,
          fontWeight: CONFIG.labelWeight,
          color: CONFIG.labelColor,
          fontFamily: CONFIG.fontFamily,
          textAlign: "center",
          letterSpacing: "0.02em",
          maxWidth: CONFIG.arcRadius * 2 + 20,
        }}
      >
        {stat.label}
      </p>
    </div>
  );
}

export const CircleStats: React.FC<CircleStatsProps> = ({ title, stats }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 20], [-24, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Ambient rotation of background orb
  const orbAngle = (frame / fps) * 12;

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 72,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: titleOp,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: CONFIG.titleSize,
            fontWeight: CONFIG.titleWeight,
            color: CONFIG.titleColor,
            fontFamily: CONFIG.fontFamily,
            letterSpacing: "-0.5px",
          }}
        >
          {title}
        </h1>
      </div>

      {/* Stats row */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: CONFIG.gap,
          paddingTop: 80,
        }}
      >
        {stats.map((stat, i) => (
          <ArcStat key={i} stat={stat} frame={frame} delay={20 + i * CONFIG.stagger} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
