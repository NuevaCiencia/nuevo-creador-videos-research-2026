/**
 * FunnelDiagram — Embudo de etapas con porcentajes
 * Fondo claro. Cada capa trapezoidal entra desde arriba con spring.
 * Valores numéricos que cuentan hacia arriba a la derecha.
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

export type FunnelStage = {
  label: string;
  value: number;
  unit?: string;
};

const PALETTE = ["#6366F1","#0EA5E9","#10B981","#F59E0B","#EC4899","#8B5CF6","#EF4444"];

export type FunnelDiagramProps = {
  title: string;
  subtitle?: string;
  stages: FunnelStage[];
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  titleSize:    72,
  titleColor:   "#0F172A",
  titleWeight:  800,

  subtitleSize:  22,
  subtitleColor: "#6366F1",

  funnelTopW:    860,   // ancho del trapecio en la cima
  funnelBottomW: 260,   // ancho del trapecio en la base
  funnelYTop:    190,   // Y donde empieza el embudo
  funnelYBottom: 920,   // Y donde termina el embudo

  labelSize:     26,    // texto dentro de cada capa
  labelColor:    "#FFFFFF",
  labelWeight:   800,

  valueSize:     42,    // cifra animada a la derecha
  valueWeight:   900,

  stagger:       14,    // frames entre capas
};
// ─────────────────────────────────────────────────────────────────────────────

const W = 1920;
const H = 1080;
const FUNNEL_X = W / 2;

export const FunnelDiagram: React.FC<FunnelDiagramProps> = ({ title, subtitle, stages }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const N = stages.length;
  const totalH = CONFIG.funnelYBottom - CONFIG.funnelYTop;
  const levelH = totalH / N;

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Title */}
      <div style={{
        position: "absolute", top: 44, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
      }}>
        <h1 style={{
          margin: 0, fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight, color: CONFIG.titleColor,
          fontFamily: CONFIG.fontFamily, letterSpacing: "-0.5px",
        }}>{title}</h1>
        {subtitle && (
          <p style={{
            margin: "8px 0 0", fontSize: CONFIG.subtitleSize, color: CONFIG.subtitleColor,
            fontFamily: CONFIG.fontFamily, fontWeight: 400,
          }}>{subtitle}</p>
        )}
      </div>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>

        {stages.map((stage, i) => {
          const delay = 16 + i * CONFIG.stagger;

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 22, stiffness: 120 }, from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const labelOp = interpolate(frame - delay - 10, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          // fTop/fBottom: fraction down the funnel for this stage
          const fTop    = i / N;
          const fBottom = (i + 1) / N;

          // Width interpolation: wider at top, narrower at bottom
          const wTop    = CONFIG.funnelTopW + (CONFIG.funnelBottomW - CONFIG.funnelTopW) * fTop;
          const wBottom = CONFIG.funnelTopW + (CONFIG.funnelBottomW - CONFIG.funnelTopW) * fBottom;

          const yTop    = CONFIG.funnelYTop + fTop    * totalH;
          const yBottom = CONFIG.funnelYTop + fBottom * totalH;

          // Slide in from top
          const slideY = (1 - s) * (-40);

          const midY = (yTop + yBottom) / 2;

          // Animated value counter
          const displayVal = Math.round(
            interpolate(frame - delay, [0, 60], [0, stage.value], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            })
          );

          return (
            <g key={i} opacity={op} transform={`translate(0, ${slideY})`}>
              {/* Trapezoid */}
              <polygon
                points={`
                  ${FUNNEL_X - wTop / 2},${yTop}
                  ${FUNNEL_X + wTop / 2},${yTop}
                  ${FUNNEL_X + wBottom / 2},${yBottom}
                  ${FUNNEL_X - wBottom / 2},${yBottom}
                `}
                fill={PALETTE[i % PALETTE.length]}
                fillOpacity={0.88}
              />

              {/* Divider */}
              <line
                x1={FUNNEL_X - wTop / 2} y1={yTop}
                x2={FUNNEL_X + wTop / 2} y2={yTop}
                stroke="rgba(255,255,255,0.4)"
                strokeWidth={2}
              />

              {/* Stage label inside */}
              <text
                x={FUNNEL_X} y={midY}
                textAnchor="middle" dominantBaseline="middle"
                fontSize={CONFIG.labelSize} fontWeight={CONFIG.labelWeight}
                fill={CONFIG.labelColor}
                fontFamily={CONFIG.fontFamily}
              >
                {stage.label}
              </text>

              {/* Right-side value */}
              <g opacity={labelOp}>
                <line
                  x1={FUNNEL_X + wBottom / 2 + 8} y1={midY}
                  x2={FUNNEL_X + 520} y2={midY}
                  stroke={PALETTE[i % PALETTE.length]}
                  strokeWidth={1.5}
                  strokeDasharray="5 4"
                />
                <text
                  x={FUNNEL_X + 535} y={midY - 6}
                  fontSize={CONFIG.valueSize} fontWeight={CONFIG.valueWeight}
                  fill={PALETTE[i % PALETTE.length]}
                  fontFamily={CONFIG.fontFamily}
                >
                  {displayVal}{stage.unit ?? ""}
                </text>
              </g>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
