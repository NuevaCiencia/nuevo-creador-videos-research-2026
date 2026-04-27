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

  titleSize:      72,
  titleColor:     "#0F172A",
  titleWeight:    700,

  itemSize:       46,
  itemColor:      "#1E293B",
  itemWeight:     400,

  numberSize:     28,
  numberColor:    "#FFFFFF",
  numberBg:       "#6366F1",

  accentColor:    "#6366F1",
  lineColor:      "#E2E8F0",
};
// ─────────────────────────────────────────────────────────────────────────────

export type RevealItem = {
  text:      string;
  t_trigger: number; // segundos desde el inicio de la pantalla
};

export type ProgressiveRevealProps = {
  title: string;
  items: RevealItem[];
};

export const ProgressiveReveal: React.FC<ProgressiveRevealProps> = ({ title, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Título
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 20], [-14, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Línea acento bajo título
  const lineWidth = interpolate(frame, [10, 28], [0, 64], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:  CONFIG.bg,
        padding:     "100px 200px",
        flexDirection: "column",
        justifyContent: "center",
      }}
    >
      {/* Título */}
      <h2
        style={{
          opacity:       titleOpacity,
          transform:     `translateY(${titleY}px)`,
          fontSize:      CONFIG.titleSize,
          fontWeight:    CONFIG.titleWeight,
          color:         CONFIG.titleColor,
          fontFamily:    CONFIG.fontFamily,
          margin:        0,
          marginBottom:  20,
          lineHeight:    1.15,
        }}
      >
        {title}
      </h2>

      {/* Línea acento */}
      <div
        style={{
          width:        lineWidth,
          height:       3,
          borderRadius: 3,
          background:   CONFIG.accentColor,
          marginBottom: 56,
        }}
      />

      {/* Items */}
      <div style={{ display: "flex", flexDirection: "column", gap: 44 }}>
        {items.map((item, i) => {
          const triggerFrame = item.t_trigger * fps;
          const opacity = interpolate(frame, [triggerFrame, triggerFrame + 16], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const x = interpolate(frame, [triggerFrame, triggerFrame + 16], [-24, 0], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const numberScale = spring({
            frame: frame - triggerFrame,
            fps,
            config: { damping: 18, stiffness: 200 },
            from: 0.5,
            to: 1,
          });

          return (
            <div
              key={i}
              style={{
                opacity,
                transform:  `translateX(${x}px)`,
                display:    "flex",
                alignItems: "center",
                gap:        28,
              }}
            >
              {/* Número */}
              <div
                style={{
                  transform:      `scale(${numberScale})`,
                  flexShrink:     0,
                  width:          60,
                  height:         60,
                  borderRadius:   "50%",
                  background:     CONFIG.numberBg,
                  display:        "flex",
                  alignItems:     "center",
                  justifyContent: "center",
                  fontSize:       CONFIG.numberSize,
                  fontWeight:     700,
                  color:          CONFIG.numberColor,
                  fontFamily:     CONFIG.fontFamily,
                }}
              >
                {i + 1}
              </div>

              {/* Texto */}
              <span
                style={{
                  fontSize:   CONFIG.itemSize,
                  fontWeight: CONFIG.itemWeight,
                  color:      CONFIG.itemColor,
                  fontFamily: CONFIG.fontFamily,
                  lineHeight: 1.4,
                }}
              >
                {item.text}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
