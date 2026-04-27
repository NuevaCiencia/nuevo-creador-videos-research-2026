import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Geometría ───────────────────────────────────────────────────────────────
const R   = 300;   // radio de cada círculo
const CX1 = 790;   // centro círculo izquierdo
const CX2 = 1130;  // centro círculo derecho
const CY  = 590;   // centro vertical compartido

const OVERLAP_LEFT  = CX2 - R;   // 830
const OVERLAP_RIGHT = CX1 + R;   // 1090
const OVERLAP_CX    = (OVERLAP_LEFT + OVERLAP_RIGHT) / 2;  // 960

const LEFT_TEXT_CX  = (CX1 - R + OVERLAP_LEFT) / 2;     // ≈ 650
const RIGHT_TEXT_CX = (OVERLAP_RIGHT + CX2 + R) / 2;    // ≈ 1270

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 700,

  circleLabelSize:   30,
  circleLabelWeight: 800,

  itemSize:    28,
  itemWeight:  600,
  itemColor:   "#1E293B",
  itemLine:    1.5,

  overlapLabelSize:   26,
  overlapLabelWeight: 700,
  overlapLabelColor:  "#0F172A",

  // Timing
  circle1Delay: 8,
  circle2Delay: 22,
  leftItemsDelay:    60,
  overlapItemsDelay: 75,
  rightItemsDelay:   90,
  itemStagger:       12,
};
// ─────────────────────────────────────────────────────────────────────────────

export type VennZone = {
  label: string;
  items: string[];
};

const LEFT_COLOR    = "#6366F1";
const RIGHT_COLOR   = "#0EA5E9";
const OVERLAP_COLOR = "#4338CA";

export type VennDiagramProps = {
  title?:  string;
  left:    VennZone;
  right:   VennZone;
  overlap: { items: string[] };
};

// ─── Lista de ítems con fade escalonado ──────────────────────────────────────
const ItemList: React.FC<{
  items:     string[];
  baseDelay: number;
  stagger:   number;
  frame:     number;
  color?:    string;
  textAlign?: React.CSSProperties["textAlign"];
}> = ({ items, baseDelay, stagger, frame, color, textAlign = "center" }) => (
  <>
    {items.map((item, i) => {
      const opacity = interpolate(
        frame - baseDelay - i * stagger,
        [0, 14],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
      const y = interpolate(
        frame - baseDelay - i * stagger,
        [0, 14],
        [8, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
      return (
        <div
          key={i}
          style={{
            opacity,
            transform:  `translateY(${y}px)`,
            fontSize:   CONFIG.itemSize,
            fontWeight: CONFIG.itemWeight,
            color:      color ?? CONFIG.itemColor,
            fontFamily: CONFIG.fontFamily,
            lineHeight: CONFIG.itemLine,
            textAlign,
          }}
        >
          {item}
        </div>
      );
    })}
  </>
);

// ─── Composición principal ────────────────────────────────────────────────────
export const VennDiagram: React.FC<VennDiagramProps> = ({
  title,
  left,
  right,
  overlap,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-14, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Radio animado por spring
  const r1 = R * spring({ frame: frame - CONFIG.circle1Delay, fps, config: { damping: 22, stiffness: 70 }, from: 0, to: 1 });
  const r2 = R * spring({ frame: frame - CONFIG.circle2Delay, fps, config: { damping: 22, stiffness: 70 }, from: 0, to: 1 });

  // Opacidad de las etiquetas de los círculos
  const labelOp1 = interpolate(frame - 50, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelOp2 = interpolate(frame - 65, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>
      {/* Título */}
      {title && (
        <h2
          style={{
            position:   "absolute",
            top:        64,
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

      {/* ── Círculos SVG ── */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <clipPath id="venn-clip-left">
            <circle cx={CX1} cy={CY} r={R} />
          </clipPath>
        </defs>

        {/* Círculo izquierdo */}
        <circle
          cx={CX1} cy={CY} r={r1}
          fill={LEFT_COLOR}
          fillOpacity={0.12}
          stroke={LEFT_COLOR}
          strokeWidth={3}
        />

        {/* Círculo derecho */}
        <circle
          cx={CX2} cy={CY} r={r2}
          fill={RIGHT_COLOR}
          fillOpacity={0.12}
          stroke={RIGHT_COLOR}
          strokeWidth={3}
        />

        {/* Zona de solapamiento resaltada */}
        <g clipPath="url(#venn-clip-left)">
          <circle
            cx={CX2} cy={CY} r={r2}
            fill="#6366F1"
            fillOpacity={0.08}
            stroke="none"
          />
        </g>
      </svg>

      {/* ── Etiquetas de los círculos ── */}
      {/* Izquierdo */}
      <div
        style={{
          position:   "absolute",
          left:       CX1 - 160,
          top:        CY - R - 60,
          width:      320,
          textAlign:  "center",
          opacity:    labelOp1,
          fontSize:   CONFIG.circleLabelSize,
          fontWeight: CONFIG.circleLabelWeight,
          color:      LEFT_COLOR,
          fontFamily: CONFIG.fontFamily,
        }}
      >
        {left.label}
      </div>

      {/* Derecho */}
      <div
        style={{
          position:   "absolute",
          left:       CX2 - 160,
          top:        CY - R - 60,
          width:      320,
          textAlign:  "center",
          opacity:    labelOp2,
          fontSize:   CONFIG.circleLabelSize,
          fontWeight: CONFIG.circleLabelWeight,
          color:      RIGHT_COLOR,
          fontFamily: CONFIG.fontFamily,
        }}
      >
        {right.label}
      </div>

      {/* ── Ítems zona izquierda ── */}
      <div
        style={{
          position:      "absolute",
          left:          LEFT_TEXT_CX - 140,
          top:           CY - 80,
          width:         280,
          display:       "flex",
          flexDirection: "column",
          gap:           10,
          alignItems:    "center",
        }}
      >
        <ItemList
          items={left.items}
          baseDelay={CONFIG.leftItemsDelay}
          stagger={CONFIG.itemStagger}
          frame={frame}
          color={LEFT_COLOR}
          textAlign="center"
        />
      </div>

      {/* ── Ítems zona de solapamiento ── */}
      <div
        style={{
          position:      "absolute",
          left:          OVERLAP_CX - 110,
          top:           CY - 80,
          width:         220,
          display:       "flex",
          flexDirection: "column",
          gap:           10,
          alignItems:    "center",
        }}
      >
        <ItemList
          items={overlap.items}
          baseDelay={CONFIG.overlapItemsDelay}
          stagger={CONFIG.itemStagger}
          frame={frame}
          color={OVERLAP_COLOR}
          textAlign="center"
        />
      </div>

      {/* ── Ítems zona derecha ── */}
      <div
        style={{
          position:      "absolute",
          left:          RIGHT_TEXT_CX - 140,
          top:           CY - 80,
          width:         280,
          display:       "flex",
          flexDirection: "column",
          gap:           10,
          alignItems:    "center",
        }}
      >
        <ItemList
          items={right.items}
          baseDelay={CONFIG.rightItemsDelay}
          stagger={CONFIG.itemStagger}
          frame={frame}
          color={RIGHT_COLOR}
          textAlign="center"
        />
      </div>
    </AbsoluteFill>
  );
};
