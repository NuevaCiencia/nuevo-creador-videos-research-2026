import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Layout ──────────────────────────────────────────────────────────────────
const CX = 960, CY = 560;
const RX = 560;   // radio horizontal de la corona
const RY = 330;   // radio vertical de la corona

const CARD_W = 320;
const CARD_H = 180;

function getPositions(n: number): { x: number; y: number }[] {
  return Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    return {
      x: CX + RX * Math.cos(angle),
      y: CY + RY * Math.sin(angle),
    };
  });
}

// Inclinación post-it (cicla para cualquier N)
const ROTATIONS = [2, -2, -3, 3, -1, 2, 1, -2];

// Paleta post-it (cicla para cualquier N)
const PALETTE = [
  { bg: "#FEF9C3", line: "#EAB308", text: "#713F12" },
  { bg: "#DBEAFE", line: "#3B82F6", text: "#1E3A8A" },
  { bg: "#FCE7F3", line: "#EC4899", text: "#831843" },
  { bg: "#D1FAE5", line: "#10B981", text: "#065F46" },
  { bg: "#FFEDD5", line: "#F97316", text: "#7C2D12" },
  { bg: "#EDE9FE", line: "#8B5CF6", text: "#4C1D95" },
  { bg: "#F0F9FF", line: "#0EA5E9", text: "#0C4A6E" },
  { bg: "#FFF1F2", line: "#F43F5E", text: "#881337" },
];

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  lineColor:  "#CBD5E1",
  lineW:      3,

  centerW:          380,
  centerH:          180,
  centerRadius:     90,
  centerBg:         "#6366F1",
  centerTextColor:  "#FFFFFF",
  centerTextSize:   38,
  centerTextWeight: 900,

  cardRadius:      10,
  cardTextSize:    38,
  cardTextWeight:  700,
  cardSubSize:     24,
  cardSubWeight:   400,
  cardSubColor:    "#475569",

  stagger: 18,
};
// ─────────────────────────────────────────────────────────────────────────────

export type MindNode = {
  text:  string;
  sub?:  string;
};

export type MindMapProps = {
  center: string;
  nodes:  MindNode[];
};

export const MindMap: React.FC<MindMapProps> = ({ center, nodes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const centerScale = spring({ frame, fps, config: { damping: 18, stiffness: 130 }, from: 0, to: 1 });
  const centerOp    = interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const positions = getPositions(nodes.length);

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* ── Líneas SVG ── */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {nodes.map((_, i) => {
          const pos     = positions[i];
          const palette = PALETTE[i % PALETTE.length];
          const lineDelay = 10 + i * CONFIG.stagger;
          const dist    = Math.sqrt((pos.x - CX) ** 2 + (pos.y - CY) ** 2);

          const progress = interpolate(frame - lineDelay, [0, 22], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          return (
            <line
              key={i}
              x1={CX} y1={CY}
              x2={pos.x} y2={pos.y}
              stroke={palette.line}
              strokeWidth={CONFIG.lineW}
              strokeLinecap="round"
              strokeDasharray={dist}
              strokeDashoffset={dist * (1 - progress)}
              opacity={0.5}
            />
          );
        })}
      </svg>

      {/* ── Post-its ── */}
      {nodes.map((node, i) => {
        const pos     = positions[i];
        const palette = PALETTE[i % PALETTE.length];
        const rot     = ROTATIONS[i % ROTATIONS.length];

        const cardDelay = 10 + i * CONFIG.stagger + 20;
        const scale = spring({ frame: frame - cardDelay, fps, config: { damping: 16, stiffness: 140 }, from: 0, to: 1 });
        const opacity = interpolate(frame - cardDelay, [0, 12], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        return (
          <div
            key={i}
            style={{
              position:      "absolute",
              left:          pos.x - CARD_W / 2,
              top:           pos.y - CARD_H / 2,
              width:         CARD_W,
              height:        CARD_H,
              background:    palette.bg,
              borderRadius:  CONFIG.cardRadius,
              borderTop:     `6px solid ${palette.line}`,
              boxShadow:     "0 6px 24px rgba(0,0,0,0.10)",
              display:       "flex",
              flexDirection: "column",
              alignItems:    "center",
              justifyContent:"center",
              gap:           8,
              padding:       "16px 24px",
              boxSizing:     "border-box",
              opacity,
              transform:     `scale(${scale}) rotate(${rot}deg)`,
            }}
          >
            <span
              style={{
                fontSize:   CONFIG.cardTextSize,
                fontWeight: CONFIG.cardTextWeight,
                color:      palette.text,
                fontFamily: CONFIG.fontFamily,
                textAlign:  "center",
                lineHeight: 1.2,
              }}
            >
              {node.text}
            </span>
            {node.sub && (
              <span
                style={{
                  fontSize:   CONFIG.cardSubSize,
                  fontWeight: CONFIG.cardSubWeight,
                  color:      CONFIG.cardSubColor,
                  fontFamily: CONFIG.fontFamily,
                  textAlign:  "center",
                  lineHeight: 1.3,
                }}
              >
                {node.sub}
              </span>
            )}
          </div>
        );
      })}

      {/* ── Nodo central ── */}
      <div
        style={{
          position:       "absolute",
          left:           CX - CONFIG.centerW / 2,
          top:            CY - CONFIG.centerH / 2,
          width:          CONFIG.centerW,
          height:         CONFIG.centerH,
          background:     CONFIG.centerBg,
          borderRadius:   CONFIG.centerRadius,
          display:        "flex",
          alignItems:     "center",
          justifyContent: "center",
          padding:        "16px 28px",
          boxSizing:      "border-box",
          boxShadow:      "0 8px 32px rgba(99,102,241,0.35)",
          opacity:        centerOp,
          transform:      `scale(${centerScale})`,
        }}
      >
        <span
          style={{
            fontSize:   CONFIG.centerTextSize,
            fontWeight: CONFIG.centerTextWeight,
            color:      CONFIG.centerTextColor,
            fontFamily: CONFIG.fontFamily,
            textAlign:  "center",
          }}
        >
          {center}
        </span>
      </div>

    </AbsoluteFill>
  );
};
