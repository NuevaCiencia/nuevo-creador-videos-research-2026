/**
 * HorizontalBars — Ranking con barras horizontales animadas
 * Las barras crecen de izquierda a derecha con easing.
 * Valores que cuentan. Fondo blanco limpio, estilo infografía.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type BarItem = {
  label: string;
  value: number;
  maxValue?: number;
  suffix?: string;
};

const PALETTE = ["#6366F1","#0EA5E9","#10B981","#F59E0B","#EC4899","#8B5CF6","#EF4444","#14B8A6","#F97316","#06B6D4"];

export type HorizontalBarsProps = {
  title: string;
  subtitle?: string;
  bars: BarItem[];
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  titleSize:    72,
  titleColor:   "#111827",
  titleWeight:  800,

  subtitleSize:  22,
  subtitleColor: "#6B7280",

  barH:       52,     // altura de cada barra
  barGap:     28,     // espacio entre barras
  maxBarW:    860,    // ancho máximo de la barra al 100%
  leftCol:    340,    // ancho de la columna de labels

  labelSize:  30,
  labelColor: "#111827",
  labelWeight: 700,

  valueSize:   28,
  valueWeight: 900,

  stagger: 14,
};
// ─────────────────────────────────────────────────────────────────────────────

export const HorizontalBars: React.FC<HorizontalBarsProps> = ({ title, subtitle, bars }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY  = interpolate(frame, [0, 18], [-20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const globalMax = Math.max(...bars.map(b => b.maxValue ?? b.value));

  const totalH = bars.length * (CONFIG.barH + CONFIG.barGap) - CONFIG.barGap;
  const startY = (1080 - totalH) / 2 + 20;

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Subtle background strip */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
        background: "linear-gradient(180deg, #F9FAFB 0%, #FFFFFF 30%)",
        pointerEvents: "none",
      }} />

      {/* Title */}
      <div style={{
        position: "absolute", top: 56, left: 100, right: 100,
        opacity: titleOp, transform: `translateY(${titleY}px)`,
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

      {/* Bars */}
      <div style={{
        position: "absolute",
        top: startY + 40,
        left: 100,
        right: 100,
      }}>
        {bars.map((bar, i) => {
          const delay = 16 + i * CONFIG.stagger;
          const ratio = bar.value / globalMax;

          const barW = interpolate(frame - delay, [0, 45], [0, CONFIG.maxBarW * ratio], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const op = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const displayVal = Math.round(
            interpolate(frame - delay, [0, 45], [0, bar.value], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            })
          );

          const top = i * (CONFIG.barH + CONFIG.barGap);

          return (
            <div key={i} style={{
              position: "absolute", top, left: 0, right: 0,
              display: "flex", alignItems: "center", gap: 0,
              opacity: op,
            }}>
              {/* Label */}
              <div style={{
                width: CONFIG.leftCol, flexShrink: 0,
                textAlign: "right", paddingRight: 24,
              }}>
                <span style={{
                  fontSize: CONFIG.labelSize, fontWeight: CONFIG.labelWeight, color: CONFIG.labelColor,
                  fontFamily: CONFIG.fontFamily,
                  letterSpacing: "-0.2px",
                }}>{bar.label}</span>
              </div>

              {/* Bar track */}
              <div style={{
                flex: 1,
                position: "relative",
                height: CONFIG.barH,
                background: "#F3F4F6",
                borderRadius: CONFIG.barH / 2,
                overflow: "hidden",
              }}>
                {/* Filled bar */}
                <div style={{
                  position: "absolute",
                  left: 0, top: 0, bottom: 0,
                  width: barW,
                  background: `linear-gradient(90deg, ${PALETTE[i % PALETTE.length]}CC, ${PALETTE[i % PALETTE.length]})`,
                  borderRadius: CONFIG.barH / 2,
                  boxShadow: `0 4px 20px ${PALETTE[i % PALETTE.length]}44`,
                }} />

                {/* Shine */}
                <div style={{
                  position: "absolute",
                  left: 0, top: 0,
                  width: barW,
                  height: "50%",
                  background: "rgba(255,255,255,0.2)",
                  borderRadius: `${CONFIG.barH / 2}px ${CONFIG.barH / 2}px 0 0`,
                }} />
              </div>

              {/* Value */}
              <div style={{
                width: 160, flexShrink: 0,
                paddingLeft: 20,
                fontSize: CONFIG.valueSize, fontWeight: CONFIG.valueWeight,
                color: PALETTE[i % PALETTE.length],
                fontFamily: CONFIG.fontFamily,
                letterSpacing: "-0.5px",
              }}>
                {displayVal}{bar.suffix ?? ""}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
