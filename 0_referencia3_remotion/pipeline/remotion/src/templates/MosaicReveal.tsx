import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Configuración visual ────────────────────────────────────────────────────
const COLS = 3;
const ROWS = 3;

const PAD_X    = 80;
const PAD_TOP  = 160;  // espacio para el título
const PAD_BOT  = 48;
const GAP      = 18;

const CELL_W = (1920 - 2 * PAD_X - (COLS - 1) * GAP) / COLS;   // ≈ 326
const CELL_H = (1080 - PAD_TOP - PAD_BOT - (ROWS - 1) * GAP) / ROWS; // ≈ 206

const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 700,

  cellRadius:   14,
  termSize:     56,
  termWeight:   700,

  // Timing
  waveSpread: 40,   // rango de frames del frente de ola
};

// Paleta de celdas — texto oscuro sobre fondo pastel
const CELL_PALETTE = [
  { bg: "#EEF2FF", text: "#4338CA" },
  { bg: "#F0FDF4", text: "#16A34A" },
  { bg: "#FFF7ED", text: "#C2410C" },
  { bg: "#FDF4FF", text: "#7C3AED" },
  { bg: "#F0F9FF", text: "#0369A1" },
  { bg: "#FFF1F2", text: "#BE123C" },
  { bg: "#ECFDF5", text: "#065F46" },
  { bg: "#FEFCE8", text: "#A16207" },
];

// Pseudo-random determinista
function dval(i: number, seed: number): number {
  return Math.abs(Math.sin(i * 127.1 + seed * 311.7)) % 1;
}
// ─────────────────────────────────────────────────────────────────────────────

export type MosaicRevealProps = {
  title?: string;
  items:  string[];   // hasta 20 términos (5×4)
};

export const MosaicReveal: React.FC<MosaicRevealProps> = ({ title, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-14, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Centro del grid (en índices de celda)
  const centerCol = (COLS - 1) / 2;   // 2
  const centerRow = (ROWS - 1) / 2;   // 1.5
  const maxDist   = Math.sqrt(centerCol ** 2 + centerRow ** 2);

  const cells = [];
  for (let row = 0; row < ROWS; row++) {
    for (let col = 0; col < COLS; col++) {
      const idx   = row * COLS + col;
      const term  = items[idx];
      if (!term) continue;

      // Distancia al centro → retardo de ola
      const dist  = Math.sqrt((col - centerCol) ** 2 + (row - centerRow) ** 2);
      const delay = 8 + (dist / maxDist) * CONFIG.waveSpread + dval(idx, 3) * 5;

      const scale = spring({
        frame: frame - delay,
        fps,
        config: { damping: 18, stiffness: 180 },
        from: 0,
        to: 1,
      });
      const opacity = interpolate(frame - delay, [0, 10], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });

      // Pequeña rotación de entrada para el efecto "estallido"
      const rotation = interpolate(frame - delay, [0, 14], [dval(idx, 7) * 10 - 5, 0], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });

      const palette = CELL_PALETTE[idx % CELL_PALETTE.length];
      const x = PAD_X + col * (CELL_W + GAP);
      const y = PAD_TOP + row * (CELL_H + GAP);

      cells.push(
        <div
          key={idx}
          style={{
            position:     "absolute",
            left:         x,
            top:          y,
            width:        CELL_W,
            height:       CELL_H,
            background:   palette.bg,
            borderRadius: CONFIG.cellRadius,
            display:      "flex",
            alignItems:   "center",
            justifyContent: "center",
            opacity,
            transform:    `scale(${scale}) rotate(${rotation}deg)`,
            padding:      "12px 20px",
            boxSizing:    "border-box",
          }}
        >
          <span
            style={{
              fontSize:   CONFIG.termSize,
              fontWeight: CONFIG.termWeight,
              color:      palette.text,
              fontFamily: CONFIG.fontFamily,
              textAlign:  "center",
              lineHeight: 1.25,
            }}
          >
            {term}
          </span>
        </div>
      );
    }
  }

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>
      {/* Título */}
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

      {/* Celdas del mosaico */}
      <div style={{ position: "absolute", inset: 0 }}>
        {cells}
      </div>
    </AbsoluteFill>
  );
};
