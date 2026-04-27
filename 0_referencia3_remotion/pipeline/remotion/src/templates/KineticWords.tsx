/**
 * KineticWords — Cada palabra vuela desde una dirección distinta
 * Tipografía cinética: las palabras orbitan hacia el centro.
 * Fondo oscuro, colores por palabra.
 */
import React from "react";
import { AbsoluteFill, spring, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type KineticWordsProps = {
  words:     { text: string; color: string }[];
  subtitle?: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#FFFFFF",
  fontFamily:  "Inter, system-ui, sans-serif",

  wordSize:    100,
  wordWeight:  900,
  wordTracking: "-1px",
  wordLineH:   1.1,

  subtitleSize:   36,
  subtitleWeight: 500,
  subtitleColor:  "#64748B",
  subtitleTracking: "0.15em",

  wordGap:     28,   // gap horizontal entre palabras
  wordPadding: 160,  // padding horizontal del contenedor
  wordStagger: 7,    // frames entre aparición de cada palabra

  // Geometría de llegada
  orbitDist:   260,   // distancia mínima de llegada
  orbitExtra:  80,    // distancia extra máxima por nivel
};
// ─────────────────────────────────────────────────────────────────────────────

export const KineticWords: React.FC<KineticWordsProps> = ({ words, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const subtitleOp = interpolate(frame, [words.length * 7 + 10, words.length * 7 + 28], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Palabras */}
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexWrap: "wrap",
        justifyContent: "center", alignItems: "center",
        gap: `0 ${CONFIG.wordGap}px`, padding: `0 ${CONFIG.wordPadding}px`,
        paddingBottom: 100,
      }}>
        {words.map((w, i) => {
          // Dirección de llegada: ángulo de distribución dorada
          const angle = (i * 137.508 * Math.PI) / 180;
          const dist  = CONFIG.orbitDist + (i % 3) * CONFIG.orbitExtra;
          const fromX = Math.cos(angle) * dist;
          const fromY = Math.sin(angle) * dist;
          const delay = i * CONFIG.wordStagger;

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 16, stiffness: 200 }, from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          return (
            <span key={i} style={{
              display: "inline-block",
              fontSize: CONFIG.wordSize,
              fontWeight: CONFIG.wordWeight,
              fontFamily: CONFIG.fontFamily,
              color: w.color,
              lineHeight: CONFIG.wordLineH,
              letterSpacing: CONFIG.wordTracking,
              opacity: op,
              transform: `translate(${fromX * (1 - s)}px, ${fromY * (1 - s)}px)`,
              textShadow: `0 0 40px ${w.color}55`,
            }}>
              {w.text}
            </span>
          );
        })}
      </div>

      {/* Subtítulo */}
      {subtitle && (
        <div style={{
          position: "absolute", bottom: 140,
          left: 0, right: 0, textAlign: "center",
          opacity: subtitleOp,
        }}>
          <p style={{
            margin: 0, fontSize: CONFIG.subtitleSize, fontWeight: CONFIG.subtitleWeight,
            color: CONFIG.subtitleColor,
            fontFamily: CONFIG.fontFamily,
            letterSpacing: CONFIG.subtitleTracking, textTransform: "uppercase",
          }}>
            {subtitle}
          </p>
        </div>
      )}

    </AbsoluteFill>
  );
};
