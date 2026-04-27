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

  titleSize:        96,
  titleColor:       "#0F172A",
  titleWeight:      800,

  subtitleSize:     40,
  subtitleColor:    "#64748B",
  subtitleWeight:   400,

  tagSize:          22,
  tagColor:         "#6366F1",
  tagBg:            "#EEF2FF",
  tagWeight:        600,

  accentGradient:   "linear-gradient(90deg, #6366F1 0%, #06B6D4 100%)",
  accentLineHeight: 5,
  accentLineWidth:  480,
};
// ─────────────────────────────────────────────────────────────────────────────

export type MainCoverProps = {
  title:     string;
  subtitle?: string;
  tag?:      string;
};

export const MainCover: React.FC<MainCoverProps> = ({ title, subtitle, tag }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Tag: desliza desde arriba
  const tagOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const tagY = interpolate(frame, [0, 18], [-20, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Título: escala + fade
  const titleOpacity = interpolate(frame, [10, 32], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleScale = spring({
    frame: frame - 10,
    fps,
    config: { damping: 22, stiffness: 130 },
    from: 0.92,
    to: 1,
  });

  // Línea de acento: se extiende de izquierda a derecha
  const lineWidth = interpolate(frame, [30, 55], [0, CONFIG.accentLineWidth], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Subtítulo: fade suave después de la línea
  const subtitleOpacity = interpolate(frame, [50, 72], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const subtitleY = interpolate(frame, [50, 72], [12, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "center",
      }}
    >
      <div
        style={{
          display:        "flex",
          flexDirection:  "column",
          alignItems:     "center",
          textAlign:      "center",
          padding:        "0 180px",
          gap:            0,
        }}
      >
        {/* Tag de episodio/clase */}
        {tag && (
          <div
            style={{
              opacity:         tagOpacity,
              transform:       `translateY(${tagY}px)`,
              display:         "inline-block",
              background:      CONFIG.tagBg,
              color:           CONFIG.tagColor,
              fontFamily:      CONFIG.fontFamily,
              fontSize:        CONFIG.tagSize,
              fontWeight:      CONFIG.tagWeight,
              letterSpacing:   "0.06em",
              textTransform:   "uppercase",
              padding:         "10px 28px",
              borderRadius:    100,
              marginBottom:    48,
            }}
          >
            {tag}
          </div>
        )}

        {/* Título principal */}
        <h1
          style={{
            opacity:       titleOpacity,
            transform:     `scale(${titleScale})`,
            fontSize:      CONFIG.titleSize,
            fontWeight:    CONFIG.titleWeight,
            color:         CONFIG.titleColor,
            fontFamily:    CONFIG.fontFamily,
            lineHeight:    1.1,
            letterSpacing: "-2px",
            margin:        0,
          }}
        >
          {title}
        </h1>

        {/* Línea de acento */}
        <div
          style={{
            width:        lineWidth,
            height:       CONFIG.accentLineHeight,
            borderRadius: CONFIG.accentLineHeight,
            background:   CONFIG.accentGradient,
            marginTop:    40,
            marginBottom: subtitle ? 36 : 0,
          }}
        />

        {/* Subtítulo */}
        {subtitle && (
          <p
            style={{
              opacity:     subtitleOpacity,
              transform:   `translateY(${subtitleY}px)`,
              fontSize:    CONFIG.subtitleSize,
              fontWeight:  CONFIG.subtitleWeight,
              color:       CONFIG.subtitleColor,
              fontFamily:  CONFIG.fontFamily,
              lineHeight:  1.5,
              margin:      0,
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
