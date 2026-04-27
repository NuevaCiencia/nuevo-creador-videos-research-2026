import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  wordSize:     96,
  wordWeight:   800,
  letterSpacing:"-2px",

  subtitleSize:   28,
  subtitleColor:  "#94A3B8",
  subtitleWeight: 400,

  // Paleta de acentos — se asigna por índice ciclando
  palette: ["#6366F1", "#0EA5E9", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6"],

  // Distancia desde la que vuela cada palabra (px)
  flyDistance: 300,
};
// ─────────────────────────────────────────────────────────────────────────────

// Ángulos de llegada distribuidos para que cada palabra venga de una dirección distinta
const ANGLES = [225, 45, 180, 0, 270, 135];

export type ClosingKeywordsProps = {
  words:     string[];
  subtitle?: string;
};

export const ClosingKeywords: React.FC<ClosingKeywordsProps> = ({ words, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const subtitleOpacity = interpolate(
    frame,
    [words.length * 8 + 10, words.length * 8 + 28],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "center",
        flexDirection:  "column",
        gap:            0,
      }}
    >
      {/* Palabras */}
      <div
        style={{
          display:        "flex",
          flexWrap:       "wrap",
          justifyContent: "center",
          alignItems:     "center",
          gap:            "12px 32px",
          padding:        "0 160px",
        }}
      >
        {words.map((word, i) => {
          const delay      = i * 8;
          const angleDeg   = ANGLES[i % ANGLES.length];
          const angleRad   = (angleDeg * Math.PI) / 180;
          const fromX      = Math.cos(angleRad) * CONFIG.flyDistance;
          const fromY      = Math.sin(angleRad) * CONFIG.flyDistance;

          const s = spring({
            frame: frame - delay,
            fps,
            config: { damping: 18, stiffness: 180 },
            from: 0,
            to: 1,
          });

          const opacity = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          const color = CONFIG.palette[i % CONFIG.palette.length];

          return (
            <span
              key={i}
              style={{
                display:       "inline-block",
                fontSize:      CONFIG.wordSize,
                fontWeight:    CONFIG.wordWeight,
                fontFamily:    CONFIG.fontFamily,
                letterSpacing: CONFIG.letterSpacing,
                color,
                lineHeight:    1.1,
                opacity,
                transform:     `translate(${fromX * (1 - s)}px, ${fromY * (1 - s)}px)`,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>

      {/* Subtítulo */}
      {subtitle && (
        <p
          style={{
            opacity:       subtitleOpacity,
            marginTop:     48,
            fontSize:      CONFIG.subtitleSize,
            fontWeight:    CONFIG.subtitleWeight,
            color:         CONFIG.subtitleColor,
            fontFamily:    CONFIG.fontFamily,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            textAlign:     "center",
          }}
        >
          {subtitle}
        </p>
      )}
    </AbsoluteFill>
  );
};
