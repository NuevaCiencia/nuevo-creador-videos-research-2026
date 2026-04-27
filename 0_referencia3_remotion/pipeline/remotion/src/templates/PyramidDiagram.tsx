/**
 * PyramidDiagram — Pirámide por capas, cada nivel entra desde abajo
 * Fondo claro. Los niveles se apilan como bloques de pirámide.
 * Etiquetas a la derecha con líneas de conexión.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type PyramidLevel = {
  label: string;
  description: string;
  color: string;
};

export type PyramidDiagramProps = {
  title: string;
  levels: PyramidLevel[];   // bottom to top order
};

const W = 1920;
const H = 1080;
const PYR_H = 700;
const PYR_BASE = 800;
const PYR_X = 480;   // center of pyramid
const PYR_Y_BOTTOM = H / 2 + PYR_H / 2 - 20;
const STAGGER = 16;

export const PyramidDiagram: React.FC<PyramidDiagramProps> = ({ title, levels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const N = levels.length;
  const LEVEL_H = PYR_H / N;

  const titleOp = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #F8F9FF 0%, #EEF2FF 100%)" }}>

      {/* Title */}
      <div style={{
        position: "absolute", top: 60, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
      }}>
        <h1 style={{
          margin: 0, fontSize: 52, fontWeight: 800, color: "#1E1B4B",
          fontFamily: "Inter, system-ui, sans-serif", letterSpacing: "-0.5px",
        }}>{title}</h1>
      </div>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {levels.map((level, idx) => {
          // idx 0 = bottom, idx N-1 = top
          const levelFromTop = N - 1 - idx;
          const delay = STAGGER + idx * STAGGER;  // bottom first

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 24, stiffness: 140 }, from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const labelOp = interpolate(frame - delay - 8, [0, 16], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          // Trapezoid coords for this level
          // y coords
          const yBottom = PYR_Y_BOTTOM - idx * LEVEL_H;
          const yTop    = yBottom - LEVEL_H;

          // x width at each y (linear interpolation of pyramid sides)
          const fBottom = (PYR_Y_BOTTOM - yBottom) / PYR_H;  // 0 at base, 1 at apex
          const fTop    = (PYR_Y_BOTTOM - yTop)    / PYR_H;

          const halfBottom = (PYR_BASE / 2) * (1 - fBottom);
          const halfTop    = (PYR_BASE / 2) * (1 - fTop);

          const x1b = PYR_X - halfBottom;
          const x2b = PYR_X + halfBottom;
          const x1t = PYR_X - halfTop;
          const x2t = PYR_X + halfTop;

          // Animate from bottom
          const slideY = (1 - s) * 30;

          // Midpoint Y of level for label line
          const midY = (yTop + yBottom) / 2;

          // Right-side connector line end
          const lineX1 = x2b + (x2t - x2b) * 0.5; // midpoint of right edge
          const lineX2 = PYR_X + 520;

          return (
            <g key={idx} opacity={op} transform={`translate(0, ${slideY})`}>
              {/* Level trapezoid */}
              <polygon
                points={`${x1b},${yBottom} ${x2b},${yBottom} ${x2t},${yTop} ${x1t},${yTop}`}
                fill={level.color}
                fillOpacity={0.85}
              />
              {/* Divider line */}
              <line
                x1={x1b} y1={yBottom}
                x2={x2b} y2={yBottom}
                stroke="rgba(255,255,255,0.4)"
                strokeWidth={2}
              />

              {/* Level label inside */}
              <text
                x={PYR_X} y={midY + 6}
                textAnchor="middle" dominantBaseline="middle"
                fontSize={Math.max(16, 28 - levelFromTop * 2)}
                fontWeight={800}
                fill="#FFFFFF"
                fontFamily="Inter, system-ui, sans-serif"
                style={{ textShadow: "0 2px 8px rgba(0,0,0,0.3)" }}
              >
                {level.label}
              </text>

              {/* Right connector */}
              <g opacity={labelOp}>
                <line
                  x1={lineX1} y1={midY}
                  x2={lineX2 - 8} y2={midY}
                  stroke={level.color}
                  strokeWidth={1.5}
                  strokeDasharray="5 4"
                />
                <circle cx={lineX2 - 6} cy={midY} r={4} fill={level.color} />

                {/* Description text */}
                <text
                  x={lineX2 + 12} y={midY - 8}
                  fontSize={20} fontWeight={700}
                  fill="#1E1B4B"
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {level.label}
                </text>
                <text
                  x={lineX2 + 12} y={midY + 18}
                  fontSize={16} fontWeight={400}
                  fill="#6366F1"
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {level.description}
                </text>
              </g>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
