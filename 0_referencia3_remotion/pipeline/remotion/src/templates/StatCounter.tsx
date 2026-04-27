/**
 * StatCounter — Estadísticas grandes que cuentan desde 0, fondo BLANCO
 * Números enormes con easing, cada tarjeta entra con spring.
 * Ideal para cifras impactantes de una clase.
 */
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type Stat = {
  value: number;
  suffix?: string;   // ej. "%", "x", "+"
  label: string;
  sublabel?: string;
};

const PALETTE = ["#6366F1","#0EA5E9","#10B981","#F59E0B","#EC4899","#8B5CF6"];

export type StatCounterProps = {
  title: string;
  stats: Stat[];
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  titleSize:    72,
  titleColor:   "#111827",
  titleWeight:  700,

  numberSize:   110,
  numberWeight: 900,

  labelSize:    28,
  labelColor:   "#111827",
  labelWeight:  700,

  sublabelSize:  20,
  sublabelColor: "#9CA3AF",

  cardRadius:   24,
  cardGap:      40,
  cardStagger:  18,
};
// ─────────────────────────────────────────────────────────────────────────────

export const StatCounter: React.FC<StatCounterProps> = ({ title, stats }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Franja de color en la parte superior */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 8,
        background: `linear-gradient(90deg, ${PALETTE[0]}, ${PALETTE[Math.min(stats.length - 1, PALETTE.length - 1)]})`,
      }} />

      {/* Título */}
      <div style={{
        position: "absolute", top: 80, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
      }}>
        <h2 style={{
          margin: 0, fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight,
          color: CONFIG.titleColor,
          fontFamily: CONFIG.fontFamily,
        }}>
          {title}
        </h2>
      </div>

      {/* Tarjetas de estadísticas */}
      <div style={{
        position: "absolute",
        top: 180, left: 80, right: 80, bottom: 80,
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "center",
        gap: CONFIG.cardGap,
      }}>
        {stats.map((stat, i) => {
          const delay = 12 + i * CONFIG.cardStagger;

          const cardS = spring({
            frame: frame - delay, fps,
            config: { damping: 20, stiffness: 160 },
            from: 0, to: 1,
          });
          const cardOp = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          // Número contando hacia arriba
          const countProgress = interpolate(
            frame - delay,
            [0, 60],
            [0, 1],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            }
          );
          const displayValue = Math.round(stat.value * countProgress);

          return (
            <div
              key={i}
              style={{
                flex: 1,
                background: "#FFFFFF",
                borderRadius: CONFIG.cardRadius,
                padding: "48px 32px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 16,
                transform: `scale(${cardS})`,
                opacity: cardOp,
                boxShadow: "0 4px 32px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)",
                borderTop: `5px solid ${PALETTE[i % PALETTE.length]}`,
              }}
            >
              {/* Número grande */}
              <div style={{
                fontSize: CONFIG.numberSize,
                fontWeight: CONFIG.numberWeight,
                color: PALETTE[i % PALETTE.length],
                fontFamily: CONFIG.fontFamily,
                lineHeight: 1,
                letterSpacing: "-4px",
              }}>
                {displayValue}{stat.suffix ?? ""}
              </div>

              {/* Separador */}
              <div style={{
                width: 48, height: 3, borderRadius: 2,
                background: `${PALETTE[i % PALETTE.length]}44`,
              }} />

              {/* Label */}
              <div style={{
                fontSize: CONFIG.labelSize,
                fontWeight: CONFIG.labelWeight,
                color: CONFIG.labelColor,
                fontFamily: CONFIG.fontFamily,
                textAlign: "center",
                lineHeight: 1.3,
              }}>
                {stat.label}
              </div>

              {stat.sublabel && (
                <div style={{
                  fontSize: CONFIG.sublabelSize,
                  color: CONFIG.sublabelColor,
                  fontFamily: CONFIG.fontFamily,
                  textAlign: "center",
                }}>
                  {stat.sublabel}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
