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
  bg:              "#FFFFFF",
  fontFamily:      "Inter, system-ui, sans-serif",

  titleSize:       48,
  titleColor:      "#0F172A",
  titleWeight:     700,

  labelSize:       26,
  labelWeight:     700,
  labelTracking:   "0.04em",

  itemSize:        30,
  itemWeight:      400,
  itemLineHeight:  1.5,

  // Columna izquierda — lo conocido
  leftBg:          "#F8FAFC",
  leftBorder:      "#CBD5E1",
  leftLabelColor:  "#475569",
  leftItemColor:   "#475569",
  leftDotColor:    "#94A3B8",

  // Columna derecha — concepto nuevo
  rightBg:         "#EEF2FF",
  rightBorder:     "#6366F1",
  rightLabelColor: "#4338CA",
  rightItemColor:  "#1E293B",
  rightDotColor:   "#6366F1",

  accentColor:     "#6366F1",
  arrowColor:      "#CBD5E1",
};
// ─────────────────────────────────────────────────────────────────────────────

export type AnalogyColumn = {
  label: string;
  items: string[];
};

export type VisualAnalogyProps = {
  title: string;
  left:  AnalogyColumn;
  right: AnalogyColumn;
};

const Column: React.FC<{
  label:      string;
  items:      string[];
  bg:         string;
  border:     string;
  labelColor: string;
  itemColor:  string;
  dotColor:   string;
  delay:      number;
  slideFrom:  number;
  frame:      number;
  fps:        number;
}> = ({ label, items, bg, border, labelColor, itemColor, dotColor, delay, slideFrom, frame, fps }) => {
  const colX = spring({
    frame: frame - delay,
    fps,
    config: { damping: 22, stiffness: 130 },
    from: slideFrom,
    to: 0,
  });
  const colOpacity = interpolate(frame - delay, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex:          1,
        opacity:       colOpacity,
        transform:     `translateX(${colX}px)`,
        background:    bg,
        border:        `2px solid ${border}`,
        borderRadius:  16,
        padding:       "48px 52px",
        display:       "flex",
        flexDirection: "column",
        gap:           0,
      }}
    >
      {/* Label */}
      <p
        style={{
          fontSize:      CONFIG.labelSize,
          fontWeight:    CONFIG.labelWeight,
          color:         labelColor,
          fontFamily:    CONFIG.fontFamily,
          letterSpacing: CONFIG.labelTracking,
          textTransform: "uppercase",
          margin:        0,
          marginBottom:  32,
        }}
      >
        {label}
      </p>

      {/* Items */}
      {items.map((item, i) => {
        const itemDelay   = delay + 20 + i * 12;
        const itemOpacity = interpolate(frame, [itemDelay, itemDelay + 14], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        const itemX = interpolate(frame, [itemDelay, itemDelay + 14], [-16, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        return (
          <div
            key={i}
            style={{
              opacity:    itemOpacity,
              transform:  `translateX(${itemX}px)`,
              display:    "flex",
              alignItems: "flex-start",
              gap:        18,
              marginBottom: 20,
            }}
          >
            <div
              style={{
                width:        10,
                height:       10,
                borderRadius: "50%",
                background:   dotColor,
                flexShrink:   0,
                marginTop:    10,
              }}
            />
            <span
              style={{
                fontSize:   CONFIG.itemSize,
                fontWeight: CONFIG.itemWeight,
                color:      itemColor,
                fontFamily: CONFIG.fontFamily,
                lineHeight: CONFIG.itemLineHeight,
              }}
            >
              {item}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export const VisualAnalogy: React.FC<VisualAnalogyProps> = ({ title, left, right }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-12, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const arrowOpacity = interpolate(frame, [25, 40], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: CONFIG.bg,
        padding:    "80px 120px",
        flexDirection: "column",
        gap:        0,
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
          marginBottom:  48,
          textAlign:     "center",
        }}
      >
        {title}
      </h2>

      {/* Columnas */}
      <div
        style={{
          display:    "flex",
          flexDirection: "row",
          alignItems: "stretch",
          gap:        0,
          flex:       1,
        }}
      >
        <Column
          label={left.label}
          items={left.items}
          bg={CONFIG.leftBg}
          border={CONFIG.leftBorder}
          labelColor={CONFIG.leftLabelColor}
          itemColor={CONFIG.leftItemColor}
          dotColor={CONFIG.leftDotColor}
          delay={10}
          slideFrom={-100}
          frame={frame}
          fps={fps}
        />

        {/* Flecha central */}
        <div
          style={{
            opacity:        arrowOpacity,
            alignSelf:      "center",
            padding:        "0 28px",
            fontSize:       52,
            color:          CONFIG.arrowColor,
            fontFamily:     CONFIG.fontFamily,
            flexShrink:     0,
          }}
        >
          →
        </div>

        <Column
          label={right.label}
          items={right.items}
          bg={CONFIG.rightBg}
          border={CONFIG.rightBorder}
          labelColor={CONFIG.rightLabelColor}
          itemColor={CONFIG.rightItemColor}
          dotColor={CONFIG.rightDotColor}
          delay={30}
          slideFrom={100}
          frame={frame}
          fps={fps}
        />
      </div>
    </AbsoluteFill>
  );
};
