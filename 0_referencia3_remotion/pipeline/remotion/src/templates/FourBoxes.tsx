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

  titleSize:    52,
  titleColor:   "#0F172A",
  titleWeight:  700,

  iconSize:     64,

  cardTitleSize:   32,
  cardTitleWeight: 700,
  cardTitleColor:  "#0F172A",

  cardDescSize:    26,
  cardDescWeight:  400,
  cardDescColor:   "#475569",
  cardDescLine:    1.5,

  cardRadius:   16,
  cardPadding:  44,
  cardGap:      24,

  stagger:      18,
};

// Paleta de fondos de tarjeta — se asigna por índice
const CARD_PALETTE = [
  { bg: "#EEF2FF", border: "#C7D2FE", accent: "#4338CA" },
  { bg: "#F0FDF4", border: "#BBF7D0", accent: "#16A34A" },
  { bg: "#FFF7ED", border: "#FED7AA", accent: "#C2410C" },
  { bg: "#FDF4FF", border: "#E9D5FF", accent: "#7C3AED" },
];
// ─────────────────────────────────────────────────────────────────────────────

export type BoxItem = {
  icon:        string;
  title:       string;
  description: string;
};

export type FourBoxesProps = {
  title?: string;
  items:  BoxItem[];
};

const Card: React.FC<{
  item:  BoxItem;
  index: number;
  delay: number;
  frame: number;
  fps:   number;
}> = ({ item, index, delay, frame, fps }) => {
  const palette = CARD_PALETTE[index % CARD_PALETTE.length];

  const s = spring({
    frame: frame - delay,
    fps,
    config: { damping: 22, stiffness: 160 },
    from: 0,
    to: 1,
  });
  const opacity = interpolate(frame - delay, [0, 12], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex:          1,
        opacity,
        transform:     `scale(${s})`,
        background:    palette.bg,
        border:        `2px solid ${palette.border}`,
        borderRadius:  CONFIG.cardRadius,
        padding:       CONFIG.cardPadding,
        display:       "flex",
        flexDirection: "column",
        gap:           16,
      }}
    >
      {/* Ícono */}
      <span style={{ fontSize: CONFIG.iconSize, lineHeight: 1 }}>
        {item.icon}
      </span>

      {/* Título */}
      <h3
        style={{
          margin:      0,
          fontSize:    CONFIG.cardTitleSize,
          fontWeight:  CONFIG.cardTitleWeight,
          color:       CONFIG.cardTitleColor,
          fontFamily:  CONFIG.fontFamily,
          lineHeight:  1.2,
        }}
      >
        {item.title}
      </h3>

      {/* Descripción */}
      <p
        style={{
          margin:      0,
          fontSize:    CONFIG.cardDescSize,
          fontWeight:  CONFIG.cardDescWeight,
          color:       CONFIG.cardDescColor,
          fontFamily:  CONFIG.fontFamily,
          lineHeight:  CONFIG.cardDescLine,
        }}
      >
        {item.description}
      </p>
    </div>
  );
};

export const FourBoxes: React.FC<FourBoxesProps> = ({ title, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-12, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const row1 = items.slice(0, 2);
  const row2 = items.slice(2, 4);

  return (
    <AbsoluteFill
      style={{
        background:    CONFIG.bg,
        padding:       "72px 100px",
        flexDirection: "column",
        gap:           0,
      }}
    >
      {/* Título */}
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

      {/* Grid 2×2 */}
      <div style={{ display: "flex", flexDirection: "column", gap: CONFIG.cardGap, flex: 1 }}>
        <div style={{ display: "flex", gap: CONFIG.cardGap, flex: 1 }}>
          {row1.map((item, i) => (
            <Card key={i} item={item} index={i} delay={14 + i * CONFIG.stagger} frame={frame} fps={fps} />
          ))}
        </div>
        <div style={{ display: "flex", gap: CONFIG.cardGap, flex: 1 }}>
          {row2.map((item, i) => (
            <Card key={i} item={item} index={i + 2} delay={14 + (i + 2) * CONFIG.stagger} frame={frame} fps={fps} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
