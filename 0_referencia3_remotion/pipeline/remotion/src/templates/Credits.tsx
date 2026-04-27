import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
} from "remotion";

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:             "#FFFFFF",
  fontFamily:     "Inter, system-ui, sans-serif",

  titleSize:      40,
  titleColor:     "#0F172A",
  titleWeight:    700,

  itemSize:       28,
  itemColor:      "#334155",
  itemWeight:     400,

  labelSize:      22,
  labelColor:     "#94A3B8",
  labelWeight:    500,

  dotColor:       "#6366F1",
  dotSize:        10,

  accentColor:    "#6366F1",
  itemInterval:   10,
};
// ─────────────────────────────────────────────────────────────────────────────

export type CreditsItem = {
  label?: string;
  text:   string;
};

export type CreditsProps = {
  title?: string;
  items:  CreditsItem[];
};

export const Credits: React.FC<CreditsProps> = ({ title, items }) => {
  const frame = useCurrentFrame();

  // Título
  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-12, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Línea de acento bajo el título
  const lineWidth = interpolate(frame, [10, 30], [0, 60], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "flex-start",
        paddingLeft:    200,
        paddingRight:   200,
      }}
    >
      <div
        style={{
          display:       "flex",
          flexDirection: "column",
          gap:           0,
          width:         "100%",
        }}
      >
        {/* Título */}
        {title && (
          <>
            <h2
              style={{
                opacity:       titleOpacity,
                transform:     `translateY(${titleY}px)`,
                fontSize:      CONFIG.titleSize,
                fontWeight:    CONFIG.titleWeight,
                color:         CONFIG.titleColor,
                fontFamily:    CONFIG.fontFamily,
                margin:        0,
                marginBottom:  16,
              }}
            >
              {title}
            </h2>
            <div
              style={{
                width:        lineWidth,
                height:       3,
                borderRadius: 3,
                background:   CONFIG.accentColor,
                marginBottom: 48,
              }}
            />
          </>
        )}

        {/* Items */}
        {items.map((item, i) => {
          const delay   = (title ? 20 : 0) + i * CONFIG.itemInterval;
          const opacity = interpolate(frame, [delay, delay + 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const x = interpolate(frame, [delay, delay + 14], [-20, 0], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          return (
            <div
              key={i}
              style={{
                opacity,
                transform:     `translateX(${x}px)`,
                display:       "flex",
                alignItems:    "baseline",
                gap:           20,
                marginBottom:  32,
              }}
            >
              {/* Dot */}
              <div
                style={{
                  width:        CONFIG.dotSize,
                  height:       CONFIG.dotSize,
                  borderRadius: "50%",
                  background:   CONFIG.dotColor,
                  flexShrink:   0,
                  marginTop:    6,
                }}
              />

              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {/* Label opcional */}
                {item.label && (
                  <span
                    style={{
                      fontSize:      CONFIG.labelSize,
                      fontWeight:    CONFIG.labelWeight,
                      color:         CONFIG.labelColor,
                      fontFamily:    CONFIG.fontFamily,
                      letterSpacing: "0.04em",
                      textTransform: "uppercase",
                    }}
                  >
                    {item.label}
                  </span>
                )}

                {/* Texto */}
                <span
                  style={{
                    fontSize:   CONFIG.itemSize,
                    fontWeight: CONFIG.itemWeight,
                    color:      CONFIG.itemColor,
                    fontFamily: CONFIG.fontFamily,
                    lineHeight: 1.5,
                  }}
                >
                  {item.text}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
