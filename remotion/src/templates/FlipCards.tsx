import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#FAFAF8",
  fontFamily:  "Inter, system-ui, sans-serif",

  titleSize:   76,
  titleColor:  "#1A1A2E",
  titleWeight: 700,

  cardWidth:   360,
  cardHeight:  440,
  cardGap:     36,
  cardRadius:  24,

  iconSize:         88,
  frontLabelSize:   32,
  frontLabelWeight: 700,
  frontLabelColor:  "#3D3D5C",

  backTitleSize:   38,
  backTitleWeight: 800,
  backTitleColor:  "#FFFFFF",

  backDescSize:    24,
  backDescWeight:  400,
  backDescColor:   "rgba(255,255,255,0.90)",
  backDescLine:    1.55,

  // Timing
  appearStagger: 14,
  flipStart:     80,
  flipStagger:   24,
  flipFrames:    26,
};

const CARD_PALETTE = [
  { front: "#FFF0F5", border: "#FFCCE0", back: "#E8608A" },
  { front: "#F0F7FF", border: "#C0DEFF", back: "#5B9BE8" },
  { front: "#F2FFF0", border: "#C2EDBB", back: "#52B04A" },
  { front: "#FFF8EC", border: "#FFE0A0", back: "#E8A830" },
  { front: "#F5F0FF", border: "#D8C5FF", back: "#8B65E0" },
  { front: "#F0FFFA", border: "#B0EED8", back: "#35B88A" },
];
// ─────────────────────────────────────────────────────────────────────────────

export type FlipCardItem = {
  icon:        string;
  label:       string;
  title:       string;
  description: string;
};

export type FlipCardsProps = {
  title?: string;
  items:  FlipCardItem[];
};

// ─── Carta individual ────────────────────────────────────────────────────────
const Card: React.FC<{
  item:   FlipCardItem;
  index:  number;
  frame:  number;
  fps:    number;
  cardW:  number;
}> = ({ item, index, frame, fps, cardW }) => {
  const palette = CARD_PALETTE[index % CARD_PALETTE.length];

  const appearDelay = index * CONFIG.appearStagger;
  const scale = spring({
    frame: frame - appearDelay,
    fps,
    config: { damping: 22, stiffness: 160 },
    from: 0,
    to: 1,
  });
  const opacity = interpolate(frame - appearDelay, [0, 12], [0, 1], {
    extrapolateLeft:  "clamp",
    extrapolateRight: "clamp",
  });

  const flipDelay = CONFIG.flipStart + index * CONFIG.flipStagger;
  const flipProgress = interpolate(frame - flipDelay, [0, CONFIG.flipFrames], [0, 1], {
    extrapolateLeft:  "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const rotateY  = interpolate(flipProgress, [0, 0.5, 1], [0, 90, 180]);
  const showBack = rotateY > 90;
  const backRot  = rotateY - 180;

  const cardBase: React.CSSProperties = {
    position:      "absolute",
    inset:         0,
    borderRadius:  CONFIG.cardRadius,
    display:       "flex",
    flexDirection: "column",
    alignItems:    "center",
    justifyContent:"center",
    gap:           20,
    padding:       "40px 36px",
    boxSizing:     "border-box",
  };

  return (
    <div
      style={{
        position:  "relative",
        width:     cardW,
        height:    CONFIG.cardHeight,
        opacity,
        transform: `scale(${scale})`,
        flexShrink: 0,
      }}
    >
      {!showBack && (
        <div
          style={{
            ...cardBase,
            background: palette.front,
            border:     `2px solid ${palette.border}`,
            transform:  `rotateY(${rotateY}deg)`,
          }}
        >
          <span style={{ fontSize: CONFIG.iconSize, lineHeight: 1 }}>
            {item.icon}
          </span>
          <span
            style={{
              fontSize:   CONFIG.frontLabelSize,
              fontWeight: CONFIG.frontLabelWeight,
              color:      CONFIG.frontLabelColor,
              fontFamily: CONFIG.fontFamily,
              textAlign:  "center",
              lineHeight: 1.3,
            }}
          >
            {item.label}
          </span>
        </div>
      )}

      {showBack && (
        <div
          style={{
            ...cardBase,
            background: palette.back,
            transform:  `rotateY(${backRot}deg)`,
          }}
        >
          <div
            style={{
              width:        48,
              height:       4,
              background:   "rgba(255,255,255,0.5)",
              borderRadius: 2,
            }}
          />
          <h3
            style={{
              margin:     0,
              fontSize:   CONFIG.backTitleSize,
              fontWeight: CONFIG.backTitleWeight,
              color:      CONFIG.backTitleColor,
              fontFamily: CONFIG.fontFamily,
              textAlign:  "center",
              lineHeight: 1.2,
            }}
          >
            {item.title}
          </h3>
          <p
            style={{
              margin:     0,
              fontSize:   CONFIG.backDescSize,
              fontWeight: CONFIG.backDescWeight,
              color:      CONFIG.backDescColor,
              fontFamily: CONFIG.fontFamily,
              textAlign:  "center",
              lineHeight: CONFIG.backDescLine,
            }}
          >
            {item.description}
          </p>
        </div>
      )}
    </div>
  );
};

// ─── Composición principal ────────────────────────────────────────────────────
export const FlipCards: React.FC<FlipCardsProps> = ({ title, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft:  "clamp",
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-14, 0], {
    extrapolateLeft:  "clamp",
    extrapolateRight: "clamp",
  });

  const N = items.length;
  const MARGIN = 200;
  const cardW = Math.min(
    CONFIG.cardWidth,
    Math.floor((1920 - MARGIN - (N - 1) * CONFIG.cardGap) / N),
  );

  return (
    <AbsoluteFill
      style={{
        background:    CONFIG.bg,
        padding:       "72px 100px",
        flexDirection: "column",
        alignItems:    "center",
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
            marginBottom: 56,
            textAlign:    "center",
          }}
        >
          {title}
        </h2>
      )}

      <div
        style={{
          display:        "flex",
          gap:            CONFIG.cardGap,
          justifyContent: "center",
          alignItems:     "center",
          flex:           1,
        }}
      >
        {items.map((item, i) => (
          <Card key={i} item={item} index={i} frame={frame} fps={fps} cardW={cardW} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
