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
  bg:               "#FFFFFF",
  fontFamily:       "Inter, system-ui, sans-serif",

  termSize:         160,
  termColor:        "#0F172A",
  termWeight:       900,
  termTracking:     "-4px",

  accentColor:      "#6366F1",
  accentLineWidth:  80,

  postItBg:         "#FEF9C3",
  postItShadow:     "0 8px 40px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)",
  postItRotation:   -1.2,
  postItPadding:    88,

  defSize:          52,
  defColor:         "#1E293B",
  defWeight:        500,
  defLineHeight:    1.5,

  categorySize:     22,
  categoryColor:    "#6366F1",
  categoryWeight:   600,
  categoryTracking: "0.1em",
};
// ─────────────────────────────────────────────────────────────────────────────

export type ImpactTermProps = {
  term:       string;
  definition: string;
  category?:  string;
};

export const ImpactTerm: React.FC<ImpactTermProps> = ({ term, definition, category }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Término
  const termOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const termY = interpolate(frame, [0, 18], [-20, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Línea acento
  const lineWidth = interpolate(frame, [14, 32], [0, CONFIG.accentLineWidth], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Post-it: cae desde arriba con rebote
  const postItY = spring({
    frame: frame - 28,
    fps,
    config: { damping: 14, stiffness: 140 },
    from: -60,
    to: 0,
  });
  const postItOpacity = interpolate(frame, [28, 44], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "center",
        flexDirection:  "column",
        gap:            0,
        padding:        "120px 200px 0 200px",
        justifyContent: "flex-start",
      }}
    >
      {/* Término */}
      <div
        style={{
          opacity:   termOpacity,
          transform: `translateY(${termY}px)`,
          textAlign: "center",
          marginBottom: 24,
        }}
      >
        <h1
          style={{
            fontSize:      CONFIG.termSize,
            fontWeight:    CONFIG.termWeight,
            color:         CONFIG.termColor,
            fontFamily:    CONFIG.fontFamily,
            letterSpacing: CONFIG.termTracking,
            lineHeight:    1,
            margin:        0,
          }}
        >
          {term}
        </h1>
      </div>

      {/* Línea acento */}
      <div
        style={{
          width:        lineWidth,
          height:       4,
          borderRadius: 4,
          background:   CONFIG.accentColor,
          marginBottom: 48,
        }}
      />

      {/* Post-it con definición */}
      <div
        style={{
          opacity:       postItOpacity,
          transform:     `translateY(${postItY}px) rotate(${CONFIG.postItRotation}deg)`,
          background:    CONFIG.postItBg,
          boxShadow:     CONFIG.postItShadow,
          borderRadius:  4,
          padding:       CONFIG.postItPadding,
          maxWidth:      1500,
          width:         "100%",
        }}
      >
        <p
          style={{
            fontSize:   CONFIG.defSize,
            fontWeight: CONFIG.defWeight,
            color:      CONFIG.defColor,
            fontFamily: CONFIG.fontFamily,
            lineHeight: CONFIG.defLineHeight,
            margin:     0,
            textAlign:  "left",
          }}
        >
          {definition}
        </p>
      </div>
    </AbsoluteFill>
  );
};
