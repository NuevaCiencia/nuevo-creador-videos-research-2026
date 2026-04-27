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

  titleSize:    50,
  titleColor:   "#0F172A",
  titleWeight:  700,

  headerSize:   30,
  headerWeight: 700,

  itemSize:     28,
  itemWeight:   400,
  itemColor:    "#334155",
  itemLine:     1.45,

  checkColor:   "#16A34A",
  checkBg:      "#F0FDF4",
  crossColor:   "#DC2626",
  crossBg:      "#FEF2F2",

  stagger:      12,
  cardRadius:   16,
};
// ─────────────────────────────────────────────────────────────────────────────

export type ColItem = {
  text:     string;
  positive: boolean;
};

export type TwoColumnsProps = {
  title?: string;
  left: {
    label:  string;
    color:  string;
    items:  ColItem[];
  };
  right: {
    label:  string;
    color:  string;
    items:  ColItem[];
  };
};

const Check = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <circle cx="14" cy="14" r="13" fill={CONFIG.checkBg} stroke={CONFIG.checkColor} strokeWidth="1.5" />
    <path d="M8 14l4 4 8-8" stroke={CONFIG.checkColor} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Cross = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <circle cx="14" cy="14" r="13" fill={CONFIG.crossBg} stroke={CONFIG.crossColor} strokeWidth="1.5" />
    <path d="M9 9l10 10M19 9L9 19" stroke={CONFIG.crossColor} strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);

const Column: React.FC<{
  label:     string;
  color:     string;
  items:     ColItem[];
  delay:     number;
  slideFrom: number;
  frame:     number;
  fps:       number;
}> = ({ label, color, items, delay, slideFrom, frame, fps }) => {
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
        border:        `2px solid ${color}`,
        borderRadius:  CONFIG.cardRadius,
        overflow:      "hidden",
        display:       "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div
        style={{
          background:     color,
          padding:        "24px 40px",
          textAlign:      "center",
        }}
      >
        <span
          style={{
            fontSize:   CONFIG.headerSize,
            fontWeight: CONFIG.headerWeight,
            color:      "#FFFFFF",
            fontFamily: CONFIG.fontFamily,
            letterSpacing: "0.03em",
          }}
        >
          {label}
        </span>
      </div>

      {/* Items */}
      <div
        style={{
          padding:       "36px 40px",
          display:       "flex",
          flexDirection: "column",
          gap:           20,
          flex:          1,
        }}
      >
        {items.map((item, i) => {
          const itemDelay   = delay + 20 + i * CONFIG.stagger;
          const itemOpacity = interpolate(frame, [itemDelay, itemDelay + 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const itemX = interpolate(frame, [itemDelay, itemDelay + 12], [-16, 0], {
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
                gap:        16,
              }}
            >
              {item.positive ? <Check /> : <Cross />}
              <span
                style={{
                  fontSize:   CONFIG.itemSize,
                  fontWeight: CONFIG.itemWeight,
                  color:      CONFIG.itemColor,
                  fontFamily: CONFIG.fontFamily,
                  lineHeight: CONFIG.itemLine,
                }}
              >
                {item.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const TwoColumns: React.FC<TwoColumnsProps> = ({ title, left, right }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-12, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:    CONFIG.bg,
        padding:       "72px 100px",
        flexDirection: "column",
        gap:           0,
      }}
    >
      {title && (
        <h2
          style={{
            opacity:      titleOpacity,
            transform:    `translateY(${titleY}px)`,
            fontSize:     CONFIG.titleSize,
            fontWeight:   CONFIG.titleWeight,
            color:        CONFIG.titleColor,
            fontFamily:   CONFIG.fontFamily,
            margin:       0,
            marginBottom: 40,
            textAlign:    "center",
          }}
        >
          {title}
        </h2>
      )}

      <div style={{ display: "flex", gap: 32, flex: 1 }}>
        <Column {...left}  delay={10} slideFrom={-100} frame={frame} fps={fps} />
        <Column {...right} delay={30} slideFrom={100}  frame={frame} fps={fps} />
      </div>
    </AbsoluteFill>
  );
};
