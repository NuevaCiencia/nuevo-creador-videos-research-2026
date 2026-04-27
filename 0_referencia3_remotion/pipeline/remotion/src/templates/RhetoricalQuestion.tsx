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
  bg:              "linear-gradient(135deg, #1E1B4B 0%, #4338CA 60%, #0EA5E9 100%)",
  fontFamily:      "Inter, system-ui, sans-serif",

  markSize:        220,
  markColor:       "rgba(255,255,255,0.08)",
  markWeight:      900,

  questionSize:    80,
  questionColor:   "#FFFFFF",
  questionWeight:  700,
  lineHeight:      1.3,

  hintSize:        30,
  hintColor:       "rgba(255,255,255,0.45)",
  hintWeight:      400,
  hintTracking:    "0.08em",
};
// ─────────────────────────────────────────────────────────────────────────────

export type RhetoricalQuestionProps = {
  question: string;
  hint?:    string;
};

export const RhetoricalQuestion: React.FC<RhetoricalQuestionProps> = ({ question, hint }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Signo de interrogación decorativo
  const markOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Pregunta: escala desde centro
  const questionOpacity = interpolate(frame, [8, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const questionScale = spring({
    frame: frame - 8,
    fps,
    config: { damping: 20, stiffness: 120 },
    from: 0.92,
    to: 1,
  });

  // Hint: aparece después
  const hintOpacity = interpolate(frame, [45, 65], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const hintY = interpolate(frame, [45, 65], [12, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Pulso sutil en la pregunta una vez aparecida
  const pulse = 1 + Math.sin(Math.max(0, frame - 40) / 30 * Math.PI * 0.4) * 0.008;

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "center",
        flexDirection:  "column",
        padding:        "0 180px",
      }}
    >
      {/* Signo decorativo de fondo */}
      <div
        style={{
          position:   "absolute",
          right:      100,
          top:        "50%",
          transform:  "translateY(-55%)",
          fontSize:   CONFIG.markSize,
          fontFamily: CONFIG.fontFamily,
          fontWeight: CONFIG.markWeight,
          color:      CONFIG.markColor,
          opacity:    markOpacity,
          lineHeight: 1,
          userSelect: "none",
        }}
      >
        ?
      </div>

      {/* Pregunta */}
      <h1
        style={{
          opacity:    questionOpacity,
          transform:  `scale(${questionScale * pulse})`,
          fontSize:   CONFIG.questionSize,
          fontWeight: CONFIG.questionWeight,
          color:      CONFIG.questionColor,
          fontFamily: CONFIG.fontFamily,
          lineHeight: CONFIG.lineHeight,
          textAlign:  "center",
          margin:     0,
          marginBottom: hint ? 48 : 0,
        }}
      >
        {question}
      </h1>

      {/* Hint */}
      {hint && (
        <p
          style={{
            opacity:       hintOpacity,
            transform:     `translateY(${hintY}px)`,
            fontSize:      CONFIG.hintSize,
            fontWeight:    CONFIG.hintWeight,
            color:         CONFIG.hintColor,
            fontFamily:    CONFIG.fontFamily,
            letterSpacing: CONFIG.hintTracking,
            textAlign:     "center",
            margin:        0,
          }}
        >
          {hint}
        </p>
      )}
    </AbsoluteFill>
  );
};
