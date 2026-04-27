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
  bg:               "#F1F5F9",
  fontFamily:       "Inter, system-ui, sans-serif",

  titleSize:        80,
  titleColor:       "#0F172A",
  titleWeight:      700,

  subtitleSize:     34,
  subtitleColor:    "#64748B",
  subtitleWeight:   400,

  accentColor:      "#6366F1",
  accentLineHeight: 4,
  accentLineWidth:  80,
};
// ─────────────────────────────────────────────────────────────────────────────

export type SectionCoverProps = {
  title:     string;
  subtitle?: string;
};

export const SectionCover: React.FC<SectionCoverProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Línea de acento
  const lineWidth = interpolate(frame, [0, 20], [0, CONFIG.accentLineWidth], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Título
  const titleOpacity = interpolate(frame, [10, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = spring({
    frame: frame - 10,
    fps,
    config: { damping: 24, stiffness: 140 },
    from: 16,
    to: 0,
  });

  // Subtítulo
  const subtitleOpacity = interpolate(frame, [28, 48], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const subtitleY = interpolate(frame, [28, 48], [10, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "flex-start",
        paddingLeft:    160,
        paddingRight:   160,
      }}
    >
      <div
        style={{
          display:       "flex",
          flexDirection: "column",
          alignItems:    "flex-start",
          gap:           0,
        }}
      >
        {/* Línea de acento */}
        <div
          style={{
            width:        lineWidth,
            height:       CONFIG.accentLineHeight,
            borderRadius: CONFIG.accentLineHeight,
            background:   CONFIG.accentColor,
            marginBottom: 32,
          }}
        />

        {/* Título */}
        <h2
          style={{
            opacity:       titleOpacity,
            transform:     `translateY(${titleY}px)`,
            fontSize:      CONFIG.titleSize,
            fontWeight:    CONFIG.titleWeight,
            color:         CONFIG.titleColor,
            fontFamily:    CONFIG.fontFamily,
            lineHeight:    1.15,
            letterSpacing: "-1px",
            margin:        0,
            marginBottom:  subtitle ? 24 : 0,
          }}
        >
          {title}
        </h2>

        {/* Subtítulo */}
        {subtitle && (
          <p
            style={{
              opacity:    subtitleOpacity,
              transform:  `translateY(${subtitleY}px)`,
              fontSize:   CONFIG.subtitleSize,
              fontWeight: CONFIG.subtitleWeight,
              color:      CONFIG.subtitleColor,
              fontFamily: CONFIG.fontFamily,
              lineHeight: 1.5,
              margin:     0,
              textAlign:  "left",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
