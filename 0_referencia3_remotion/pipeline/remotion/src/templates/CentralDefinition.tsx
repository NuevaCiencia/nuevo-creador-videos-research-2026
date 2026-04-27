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
  bg:             "#FFFFFF",
  fontFamily:     "Inter, system-ui, sans-serif",

  termSize:       26,
  termColor:      "#6366F1",
  termWeight:     600,
  termTracking:   "0.1em",

  textSize:       56,
  textColor:      "#0F172A",
  textWeight:     500,
  lineHeight:     1.4,

  quoteColor:     "#6366F1",
  quoteOpacity:   0.1,
  quoteSize:      500,

  accentColor:    "#6366F1",
};
// ─────────────────────────────────────────────────────────────────────────────

export type CentralDefinitionProps = {
  term:       string;
  definition: string;
};

export const CentralDefinition: React.FC<CentralDefinitionProps> = ({ term, definition }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Comilla decorativa
  const quoteOpacity = interpolate(frame, [0, 30], [0, CONFIG.quoteOpacity], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Término (label pequeño arriba)
  const termOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const termY = interpolate(frame, [0, 18], [-10, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Línea acento
  const lineWidth = interpolate(frame, [10, 28], [0, 56], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Texto de definición
  const textOpacity = interpolate(frame, [20, 42], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const textScale = spring({
    frame: frame - 20,
    fps,
    config: { damping: 26, stiffness: 120 },
    from: 0.97,
    to: 1,
  });

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "center",
        padding:        "0 200px",
      }}
    >
      {/* Comilla gigante decorativa */}
      <div
        style={{
          position:   "absolute",
          top:        -60,
          left:       140,
          fontSize:   CONFIG.quoteSize,
          fontFamily: CONFIG.fontFamily,
          fontWeight: 900,
          color:      CONFIG.quoteColor,
          opacity:    quoteOpacity,
          lineHeight: 1,
          userSelect: "none",
        }}
      >
        "
      </div>

      <div
        style={{
          display:       "flex",
          flexDirection: "column",
          alignItems:    "center",
          textAlign:     "center",
          gap:           0,
        }}
      >
        {/* Término */}
        <span
          style={{
            opacity:       termOpacity,
            transform:     `translateY(${termY}px)`,
            fontSize:      CONFIG.termSize,
            fontWeight:    CONFIG.termWeight,
            color:         CONFIG.termColor,
            fontFamily:    CONFIG.fontFamily,
            letterSpacing: CONFIG.termTracking,
            textTransform: "uppercase",
            marginBottom:  24,
          }}
        >
          {term}
        </span>

        {/* Línea acento */}
        <div
          style={{
            width:        lineWidth,
            height:       3,
            borderRadius: 3,
            background:   CONFIG.accentColor,
            marginBottom: 40,
          }}
        />

        {/* Definición */}
        <p
          style={{
            opacity:    textOpacity,
            transform:  `scale(${textScale})`,
            fontSize:   CONFIG.textSize,
            fontWeight: CONFIG.textWeight,
            color:      CONFIG.textColor,
            fontFamily: CONFIG.fontFamily,
            lineHeight: CONFIG.lineHeight,
            margin:     0,
          }}
        >
          {definition}
        </p>
      </div>
    </AbsoluteFill>
  );
};
