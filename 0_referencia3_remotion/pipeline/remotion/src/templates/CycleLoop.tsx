import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Geometría dinámica ──────────────────────────────────────────────────────
const CX = 960, CY = 600;
const RX = 480;
const RY = 250;
const CARD_W = 360;
const CARD_H = 200;
const HW = CARD_W / 2;
const HH = CARD_H / 2;

function getOuterPos(i: number, n: number) {
  const angle = (2 * Math.PI * i) / n - Math.PI / 2;
  return {
    x: CX + RX * Math.cos(angle),
    y: CY + RY * Math.sin(angle),
  };
}

// Punto en el borde de la tarjeta rectangular en dirección del ángulo dado
function cardEdgePoint(cx: number, cy: number, angle: number): { x: number; y: number } {
  const cosA = Math.cos(angle);
  const sinA = Math.sin(angle);
  const tx = cosA !== 0 ? HW / Math.abs(cosA) : Infinity;
  const ty = sinA !== 0 ? HH / Math.abs(sinA) : Infinity;
  const t  = Math.min(tx, ty);
  return { x: cx + cosA * t, y: cy + sinA * t };
}

type ArcData = {
  sx: number; sy: number;
  cx: number; cy: number;
  ex: number; ey: number;
  ha: number;
  len: number;
};

function computeArc(from: { x: number; y: number }, to: { x: number; y: number }): ArcData {
  const angleToNext = Math.atan2(to.y - from.y, to.x - from.x);
  const angleToPrev = angleToNext + Math.PI;

  const start = cardEdgePoint(from.x, from.y, angleToNext);
  const end   = cardEdgePoint(to.x, to.y, angleToPrev);

  // Control point: midpoint empujado hacia afuera del centro
  const mx = (start.x + end.x) / 2;
  const my = (start.y + end.y) / 2;
  const dx = mx - CX;
  const dy = my - CY;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const push = 70;
  const cpx = mx + (dx / dist) * push;
  const cpy = my + (dy / dist) * push;

  // Ángulo de la punta de flecha (tangente al final de la curva)
  const ha = Math.atan2(end.y - cpy, end.x - cpx) * (180 / Math.PI);

  // Longitud aproximada del arco
  const len = Math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2) * 1.3 + 40;

  return { sx: start.x, sy: start.y, cx: cpx, cy: cpy, ex: end.x, ey: end.y, ha, len };
}

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 700,

  cardRadius:  20,

  centerR:           110,
  centerBg:          "#6366F1",
  centerIconSize:    68,
  centerLabelSize:   32,
  centerLabelWeight: 700,
  centerLabelColor:  "#FFFFFF",

  outerIconSize:    46,
  outerTitleSize:   34,
  outerTitleWeight: 700,
  outerDescSize:    24,
  outerDescWeight:  400,
  outerDescLine:    1.35,

  arrowColor: "#6366F1",
  arrowW:     10,
  headSize:   24,

  centerDelay:  8,
  nodeStagger:  20,
  arrowOffset:  22,
};

const OUTER_PALETTE = [
  { bg: "#EEF2FF", border: "#A5B4FC", text: "#4338CA", desc: "#6366F1" },
  { bg: "#F0F9FF", border: "#7DD3FC", text: "#0369A1", desc: "#0EA5E9" },
  { bg: "#F0FDF4", border: "#86EFAC", text: "#16A34A", desc: "#22C55E" },
  { bg: "#FFF7ED", border: "#FDB974", text: "#C2410C", desc: "#F97316" },
  { bg: "#FDF4FF", border: "#E9D5FF", text: "#7C3AED", desc: "#8B5CF6" },
  { bg: "#FFF1F2", border: "#FECDD3", text: "#BE123C", desc: "#F43F5E" },
];
// ─────────────────────────────────────────────────────────────────────────────

export type CycleItem = {
  icon:        string;
  title:       string;
  description: string;
};

export type CycleLoopProps = {
  title?:  string;
  center:  { icon: string; label: string };
  items:   CycleItem[];
};

// ─── Nodo exterior ────────────────────────────────────────────────────────────
const OuterNode: React.FC<{
  item:  CycleItem;
  pos:   { x: number; y: number };
  index: number;
  delay: number;
  frame: number;
  fps:   number;
}> = ({ item, pos, index, delay, frame, fps }) => {
  const palette = OUTER_PALETTE[index % OUTER_PALETTE.length];
  const scale   = spring({ frame: frame - delay, fps, config: { damping: 20, stiffness: 150 }, from: 0, to: 1 });
  const opacity = interpolate(frame - delay, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div
      style={{
        position:       "absolute",
        left:           pos.x - HW,
        top:            pos.y - HH,
        width:          CARD_W,
        height:         CARD_H,
        background:     palette.bg,
        border:         `2px solid ${palette.border}`,
        borderRadius:   CONFIG.cardRadius,
        display:        "flex",
        flexDirection:  "column",
        alignItems:     "center",
        justifyContent: "center",
        gap:            6,
        padding:        "14px 24px",
        boxSizing:      "border-box",
        opacity,
        transform:      `scale(${scale})`,
      }}
    >
      <span style={{ fontSize: CONFIG.outerIconSize, lineHeight: 1 }}>{item.icon}</span>
      <h3
        style={{
          margin:     0,
          fontSize:   CONFIG.outerTitleSize,
          fontWeight: CONFIG.outerTitleWeight,
          color:      palette.text,
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
          fontSize:   CONFIG.outerDescSize,
          fontWeight: CONFIG.outerDescWeight,
          color:      palette.desc,
          fontFamily: CONFIG.fontFamily,
          textAlign:  "center",
          lineHeight: CONFIG.outerDescLine,
        }}
      >
        {item.description}
      </p>
    </div>
  );
};

// ─── Arco animado ─────────────────────────────────────────────────────────────
const Arc: React.FC<{
  arc:   ArcData;
  delay: number;
  frame: number;
}> = ({ arc, delay, frame }) => {
  const progress   = interpolate(frame - delay, [0, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const headOp     = interpolate(frame - delay - 20, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const hs         = CONFIG.headSize;
  const dashOffset = arc.len * (1 - progress);

  return (
    <g>
      <path
        d={`M ${arc.sx},${arc.sy} Q ${arc.cx},${arc.cy} ${arc.ex},${arc.ey}`}
        fill="none"
        stroke={CONFIG.arrowColor}
        strokeWidth={CONFIG.arrowW}
        strokeLinecap="round"
        strokeDasharray={arc.len}
        strokeDashoffset={dashOffset}
      />
      <polygon
        points={`0,0 ${-hs},${-hs / 2} ${-hs},${hs / 2}`}
        fill={CONFIG.arrowColor}
        opacity={headOp}
        transform={`translate(${arc.ex},${arc.ey}) rotate(${arc.ha})`}
      />
    </g>
  );
};

// ─── Composición principal ────────────────────────────────────────────────────
export const CycleLoop: React.FC<CycleLoopProps> = ({ title, center, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY       = interpolate(frame, [0, 18], [-14, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const centerScale = spring({ frame: frame - CONFIG.centerDelay, fps, config: { damping: 20, stiffness: 140 }, from: 0, to: 1 });
  const centerOp    = interpolate(frame - CONFIG.centerDelay, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const N         = items.length;
  const positions = items.map((_, i) => getOuterPos(i, N));
  const arcs      = positions.map((pos, i) => computeArc(pos, positions[(i + 1) % N]));

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>
      {title && (
        <h2
          style={{
            position:   "absolute",
            top:        56,
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
        {arcs.map((arc, i) => (
          <Arc
            key={i}
            arc={arc}
            delay={CONFIG.centerDelay + CONFIG.nodeStagger * (i + 1) + CONFIG.arrowOffset}
            frame={frame}
          />
        ))}
      </svg>

      <div
        style={{
          position:       "absolute",
          left:           CX - CONFIG.centerR,
          top:            CY - CONFIG.centerR,
          width:          CONFIG.centerR * 2,
          height:         CONFIG.centerR * 2,
          borderRadius:   "50%",
          background:     CONFIG.centerBg,
          display:        "flex",
          flexDirection:  "column",
          alignItems:     "center",
          justifyContent: "center",
          gap:            8,
          opacity:        centerOp,
          transform:      `scale(${centerScale})`,
        }}
      >
        <span style={{ fontSize: CONFIG.centerIconSize, lineHeight: 1 }}>{center.icon}</span>
        <span
          style={{
            fontSize:   CONFIG.centerLabelSize,
            fontWeight: CONFIG.centerLabelWeight,
            color:      CONFIG.centerLabelColor,
            fontFamily: CONFIG.fontFamily,
            textAlign:  "center",
            lineHeight: 1.2,
            padding:    "0 16px",
          }}
        >
          {center.label}
        </span>
      </div>

      {items.map((item, i) => (
        <OuterNode
          key={i}
          item={item}
          pos={positions[i]}
          index={i}
          delay={CONFIG.centerDelay + CONFIG.nodeStagger * (i + 1)}
          frame={frame}
          fps={fps}
        />
      ))}
    </AbsoluteFill>
  );
};
