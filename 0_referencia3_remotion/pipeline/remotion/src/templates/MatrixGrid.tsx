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

  axisLabelSize:   24,
  axisLabelColor:  "#94A3B8",
  axisLabelWeight: 600,
  axisLabelTracking: "0.08em",

  iconSize:     56,

  quadTitleSize:   30,
  quadTitleWeight: 700,
  quadTitleColor:  "#0F172A",

  quadDescSize:    22,
  quadDescWeight:  400,
  quadDescColor:   "#475569",
  quadDescLine:    1.45,

  axisColor:    "#E2E8F0",
  axisWidth:    2,
  cardRadius:   14,
  stagger:      20,
};

const QUAD_PALETTE = [
  { bg: "#FFF7ED", border: "#FED7AA" }, // top-left
  { bg: "#F0FDF4", border: "#BBF7D0" }, // top-right
  { bg: "#EEF2FF", border: "#C7D2FE" }, // bottom-left
  { bg: "#FDF4FF", border: "#E9D5FF" }, // bottom-right
];
// ─────────────────────────────────────────────────────────────────────────────

export type QuadrantItem = {
  icon:        string;
  title:       string;
  description: string;
};

export type MatrixGridProps = {
  title:      string;
  xAxisLeft:  string;
  xAxisRight: string;
  yAxisTop:   string;
  yAxisBottom:string;
  // orden: [top-left, top-right, bottom-left, bottom-right]
  quadrants:  QuadrantItem[];
};

const Quadrant: React.FC<{
  item:    QuadrantItem;
  index:   number;
  delay:   number;
  frame:   number;
  fps:     number;
}> = ({ item, index, delay, frame, fps }) => {
  const palette = QUAD_PALETTE[index % QUAD_PALETTE.length];

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
        padding:       "36px 40px",
        display:       "flex",
        flexDirection: "column",
        gap:           14,
      }}
    >
      <span style={{ fontSize: CONFIG.iconSize, lineHeight: 1 }}>{item.icon}</span>
      <h3
        style={{
          margin:      0,
          fontSize:    CONFIG.quadTitleSize,
          fontWeight:  CONFIG.quadTitleWeight,
          color:       CONFIG.quadTitleColor,
          fontFamily:  CONFIG.fontFamily,
          lineHeight:  1.2,
        }}
      >
        {item.title}
      </h3>
      <p
        style={{
          margin:      0,
          fontSize:    CONFIG.quadDescSize,
          fontWeight:  CONFIG.quadDescWeight,
          color:       CONFIG.quadDescColor,
          fontFamily:  CONFIG.fontFamily,
          lineHeight:  CONFIG.quadDescLine,
        }}
      >
        {item.description}
      </p>
    </div>
  );
};

export const MatrixGrid: React.FC<MatrixGridProps> = ({
  title, xAxisLeft, xAxisRight, yAxisTop, yAxisBottom, quadrants,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const axisOpacity = interpolate(frame, [10, 28], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const axisStyle = {
    fontSize:      CONFIG.axisLabelSize,
    fontWeight:    CONFIG.axisLabelWeight,
    color:         CONFIG.axisLabelColor,
    fontFamily:    CONFIG.fontFamily,
    letterSpacing: CONFIG.axisLabelTracking,
    textTransform: "uppercase" as const,
  };

  return (
    <AbsoluteFill
      style={{
        background:    CONFIG.bg,
        padding:       "64px 100px",
        flexDirection: "column",
        gap:           0,
      }}
    >
      {/* Título */}
      <h2
        style={{
          opacity:      titleOpacity,
          fontSize:     CONFIG.titleSize,
          fontWeight:   CONFIG.titleWeight,
          color:        CONFIG.titleColor,
          fontFamily:   CONFIG.fontFamily,
          margin:       0,
          marginBottom: 32,
          textAlign:    "center",
        }}
      >
        {title}
      </h2>

      {/* Eje X — etiquetas arriba */}
      <div
        style={{
          opacity:        axisOpacity,
          display:        "flex",
          justifyContent: "space-between",
          paddingLeft:    20,
          paddingRight:   20,
          marginBottom:   12,
        }}
      >
        <span style={axisStyle}>← {xAxisLeft}</span>
        <span style={axisStyle}>{xAxisRight} →</span>
      </div>

      {/* Grid principal */}
      <div style={{ display: "flex", flex: 1, gap: 0 }}>

        {/* Eje Y — etiqueta vertical izquierda */}
        <div
          style={{
            opacity:        axisOpacity,
            display:        "flex",
            flexDirection:  "column",
            justifyContent: "space-between",
            alignItems:     "center",
            paddingTop:     20,
            paddingBottom:  20,
            marginRight:    16,
          }}
        >
          <span style={{ ...axisStyle, writingMode: "vertical-rl", transform: "rotate(180deg)" }}>
            {yAxisTop} ↑
          </span>
          <span style={{ ...axisStyle, writingMode: "vertical-rl", transform: "rotate(180deg)" }}>
            ↓ {yAxisBottom}
          </span>
        </div>

        {/* Cuadrantes 2×2 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, flex: 1 }}>
          <div style={{ display: "flex", gap: 16, flex: 1 }}>
            <Quadrant item={quadrants[0]} index={0} delay={20}                   frame={frame} fps={fps} />
            <Quadrant item={quadrants[1]} index={1} delay={20 + CONFIG.stagger}  frame={frame} fps={fps} />
          </div>
          <div style={{ display: "flex", gap: 16, flex: 1 }}>
            <Quadrant item={quadrants[2]} index={2} delay={20 + CONFIG.stagger * 2} frame={frame} fps={fps} />
            <Quadrant item={quadrants[3]} index={3} delay={20 + CONFIG.stagger * 3} frame={frame} fps={fps} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
