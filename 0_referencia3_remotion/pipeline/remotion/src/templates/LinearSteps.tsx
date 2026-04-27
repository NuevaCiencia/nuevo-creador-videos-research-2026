import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Constantes fijas ─────────────────────────────────────────────────────────
const CARD_H    = 460;
const ARROW_GAP = 80;
const MARGIN    = 120;   // margen lateral total (cada lado)
const CARD_Y    = (1080 - CARD_H) / 2 + 20;

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 700,

  cardRadius:   20,
  cardBg:       "#F8FAFC",
  cardBorder:   "#E2E8F0",

  badgeSize:    52,
  badgeRadius:  999,

  stepTitleSize:   36,
  stepTitleWeight: 700,
  stepTitleColor:  "#0F172A",

  stepDescSize:   27,
  stepDescWeight: 400,
  stepDescColor:  "#475569",
  stepDescLine:   1.5,

  arrowColor:   "#94A3B8",
  arrowWidth:   3,
  arrowHeadSize:12,

  card1Delay:  8,
  stepDelay:   28,
  cardStagger: 32,
};

const CARD_PALETTE = [
  { badge: "#6366F1", badgeText: "#FFFFFF", border: "#C7D2FE" },
  { badge: "#0EA5E9", badgeText: "#FFFFFF", border: "#BAE6FD" },
  { badge: "#10B981", badgeText: "#FFFFFF", border: "#6EE7B7" },
  { badge: "#F59E0B", badgeText: "#FFFFFF", border: "#FCD34D" },
  { badge: "#EC4899", badgeText: "#FFFFFF", border: "#FBCFE8" },
  { badge: "#8B5CF6", badgeText: "#FFFFFF", border: "#DDD6FE" },
];
// ─────────────────────────────────────────────────────────────────────────────

export type StepItem = {
  title:       string;
  description: string;
};

export type LinearStepsProps = {
  title?: string;
  steps:  StepItem[];
};

// ─── Tarjeta individual ──────────────────────────────────────────────────────
const StepCard: React.FC<{
  step:   StepItem;
  index:  number;
  delay:  number;
  frame:  number;
  fps:    number;
  startX: number;
  cardW:  number;
}> = ({ step, index, delay, frame, fps, startX, cardW }) => {
  const palette = CARD_PALETTE[index % CARD_PALETTE.length];

  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 20, stiffness: 150 },
    from: 0,
    to: 1,
  });
  const opacity = interpolate(frame - delay, [0, 14], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame - delay, [0, 20], [30, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const x = startX + index * (cardW + ARROW_GAP);

  return (
    <div
      style={{
        position:      "absolute",
        left:          x,
        top:           CARD_Y,
        width:         cardW,
        height:        CARD_H,
        opacity,
        transform:     `scale(${scale}) translateY(${translateY}px)`,
        background:    CONFIG.cardBg,
        border:        `2px solid ${palette.border}`,
        borderRadius:  CONFIG.cardRadius,
        display:       "flex",
        flexDirection: "column",
        alignItems:    "center",
        padding:       "44px 36px",
        gap:           20,
        boxSizing:     "border-box",
      }}
    >
      <div
        style={{
          width:          CONFIG.badgeSize,
          height:         CONFIG.badgeSize,
          borderRadius:   CONFIG.badgeRadius,
          background:     palette.badge,
          display:        "flex",
          alignItems:     "center",
          justifyContent: "center",
          fontSize:       24,
          fontWeight:     800,
          color:          palette.badgeText,
          fontFamily:     CONFIG.fontFamily,
          flexShrink:     0,
        }}
      >
        {index + 1}
      </div>

      <h3
        style={{
          margin:     0,
          fontSize:   CONFIG.stepTitleSize,
          fontWeight: CONFIG.stepTitleWeight,
          color:      CONFIG.stepTitleColor,
          fontFamily: CONFIG.fontFamily,
          textAlign:  "center",
          lineHeight: 1.2,
        }}
      >
        {step.title}
      </h3>

      <p
        style={{
          margin:     0,
          fontSize:   CONFIG.stepDescSize,
          fontWeight: CONFIG.stepDescWeight,
          color:      CONFIG.stepDescColor,
          fontFamily: CONFIG.fontFamily,
          textAlign:  "center",
          lineHeight: CONFIG.stepDescLine,
        }}
      >
        {step.description}
      </p>
    </div>
  );
};

// ─── Flecha SVG animada ───────────────────────────────────────────────────────
const Arrow: React.FC<{
  index:  number;
  delay:  number;
  frame:  number;
  startX: number;
  cardW:  number;
}> = ({ index, delay, frame, startX, cardW }) => {
  const x1  = startX + (index + 1) * cardW + index * ARROW_GAP + 10;
  const x2  = x1 + ARROW_GAP - 20;
  const y   = CARD_Y + CARD_H / 2;
  const len = x2 - x1;

  const progress = interpolate(frame - delay, [0, 20], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const headOp = interpolate(frame - delay - 18, [0, 8], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const hs = CONFIG.arrowHeadSize;

  return (
    <g>
      <line
        x1={x1} y1={y} x2={x2} y2={y}
        stroke={CONFIG.arrowColor}
        strokeWidth={CONFIG.arrowWidth}
        strokeLinecap="round"
        strokeDasharray={len}
        strokeDashoffset={len * (1 - progress)}
      />
      <polygon
        points={`${x2},${y} ${x2 - hs},${y - hs / 2} ${x2 - hs},${y + hs / 2}`}
        fill={CONFIG.arrowColor}
        opacity={headOp}
      />
    </g>
  );
};

// ─── Composición principal ────────────────────────────────────────────────────
export const LinearSteps: React.FC<LinearStepsProps> = ({ title, steps }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-14, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const N      = steps.length;
  const cardW  = Math.min(360, Math.floor((1920 - MARGIN * 2 - (N - 1) * ARROW_GAP) / N));
  const totalW = N * cardW + (N - 1) * ARROW_GAP;
  const startX = (1920 - totalW) / 2;

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>
      {title && (
        <h2
          style={{
            position:   "absolute",
            top:        60,
            left:       0,
            right:      0,
            textAlign:  "center",
            opacity:    titleOpacity,
            transform:  `translateY(${titleY}px)`,
            margin:     0,
            fontSize:   CONFIG.titleSize,
            fontWeight: CONFIG.titleWeight,
            color:      CONFIG.titleColor,
            fontFamily: CONFIG.fontFamily,
          }}
        >
          {title}
        </h2>
      )}

      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {steps.slice(0, -1).map((_, i) => (
          <Arrow
            key={i}
            index={i}
            delay={CONFIG.card1Delay + i * CONFIG.cardStagger + CONFIG.stepDelay}
            frame={frame}
            startX={startX}
            cardW={cardW}
          />
        ))}
      </svg>

      {steps.map((step, i) => (
        <StepCard
          key={i}
          step={step}
          index={i}
          delay={CONFIG.card1Delay + i * CONFIG.cardStagger}
          frame={frame}
          fps={fps}
          startX={startX}
          cardW={cardW}
        />
      ))}
    </AbsoluteFill>
  );
};
