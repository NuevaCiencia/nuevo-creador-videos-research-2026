/**
 * IsometricGrid — Bloques isométricos que se construyen de abajo a arriba
 * Puro SVG con proyección isométrica. Los bloques "crecen" desde el suelo.
 * Cada bloque tiene una etiqueta en la cara frontal. Fondo oscuro.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type IsoBlock = {
  col: number;
  row: number;
  height: number;   // 1–5
  label: string;
  color: string;
};

export type IsometricGridProps = {
  title: string;
  blocks: IsoBlock[];
};

// Isometric projection constants
const ISO_X  = 52;   // tile half-width
const ISO_Y  = 30;   // tile half-height (projected)
const BLOCK_H = 36;  // px per unit of height
const ORIGIN_X = 960;
const ORIGIN_Y = 620;
const STAGGER  = 10;

function isoProject(col: number, row: number) {
  return {
    x: ORIGIN_X + (col - row) * ISO_X,
    y: ORIGIN_Y + (col + row) * ISO_Y,
  };
}

function darken(hex: string, amount: number): string {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.max(0, (n >> 16) - amount);
  const g = Math.max(0, ((n >> 8) & 0xff) - amount);
  const b = Math.max(0, (n & 0xff) - amount);
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

// Parse hex color to components
function hexToRgb(hex: string) {
  const n = parseInt(hex.replace("#", ""), 16);
  return { r: (n >> 16) & 0xff, g: (n >> 8) & 0xff, b: n & 0xff };
}

function darkenColor(hex: string, factor: number): string {
  const { r, g, b } = hexToRgb(hex.replace("#", "").length === 3
    ? hex : hex);
  return `rgb(${Math.round(r * factor)},${Math.round(g * factor)},${Math.round(b * factor)})`;
}

export const IsometricGrid: React.FC<IsometricGridProps> = ({ title, blocks }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Sort blocks: far rows first (painter's algorithm)
  const sorted = [...blocks].sort((a, b) => (a.col + a.row) - (b.col + b.row));

  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #080712 0%, #0e0c24 100%)" }}>

      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {sorted.map((block, idx) => {
          // Find original index for stagger
          const i = blocks.indexOf(block);
          const delay = 10 + i * STAGGER;

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 22, stiffness: 150 }, from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          const h = block.height * BLOCK_H * s;
          const { x, y } = isoProject(block.col, block.row);

          // Top face
          const topFace = [
            [x,           y - h],
            [x + ISO_X,   y - ISO_Y - h],
            [x,           y - ISO_Y * 2 - h],
            [x - ISO_X,   y - ISO_Y - h],
          ].map(([px, py]) => `${px},${py}`).join(" ");

          // Left face (darker)
          const leftFace = [
            [x - ISO_X,   y - ISO_Y],
            [x,           y],
            [x,           y - h],
            [x - ISO_X,   y - ISO_Y - h],
          ].map(([px, py]) => `${px},${py}`).join(" ");

          // Right face (darkest)
          const rightFace = [
            [x,           y],
            [x + ISO_X,   y - ISO_Y],
            [x + ISO_X,   y - ISO_Y - h],
            [x,           y - h],
          ].map(([px, py]) => `${px},${py}`).join(" ");

          const topColor   = block.color;
          const leftColor  = darkenColor(block.color, 0.60);
          const rightColor = darkenColor(block.color, 0.45);

          // Label on front-right face center
          const labelX = x + ISO_X * 0.5;
          const labelY = y - ISO_Y * 0.5 - h / 2;

          return (
            <g key={i} opacity={op}>
              <polygon points={leftFace}  fill={leftColor}  stroke="rgba(0,0,0,0.25)" strokeWidth={0.5} />
              <polygon points={rightFace} fill={rightColor} stroke="rgba(0,0,0,0.25)" strokeWidth={0.5} />
              <polygon points={topFace}   fill={topColor}   stroke="rgba(255,255,255,0.15)" strokeWidth={0.5} />

              {/* Label on right face */}
              <text
                x={labelX} y={labelY}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={15}
                fontWeight={700}
                fill="rgba(255,255,255,0.85)"
                fontFamily="Inter, system-ui, sans-serif"
                transform={`skewY(-30) skewX(0)`}
                style={{ transformOrigin: `${labelX}px ${labelY}px` }}
              >
                {block.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Title */}
      <div style={{
        position: "absolute", top: 56, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
      }}>
        <h1 style={{
          margin: 0, fontSize: 52, fontWeight: 800, color: "#FFFFFF",
          fontFamily: "Inter, system-ui, sans-serif", letterSpacing: "-0.5px",
        }}>{title}</h1>
      </div>
    </AbsoluteFill>
  );
};
