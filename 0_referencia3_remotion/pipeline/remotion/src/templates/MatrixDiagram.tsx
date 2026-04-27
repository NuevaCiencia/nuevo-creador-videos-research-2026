/**
 * MatrixDiagram — Matriz 2×2 tipo BCG / Eisenhower
 * Los 4 cuadrantes se revelan desde el centro hacia afuera.
 * Los ejes se dibujan primero, luego cada cuadrante aparece.
 * Fondo blanco con cuadrantes de colores suaves.
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

export type Quadrant = {
  title: string;
  description: string;
  icon: string;
  color: string;
};

export type MatrixDiagramProps = {
  title: string;
  xLabel: string;    // horizontal axis label (left→right)
  yLabel: string;    // vertical axis label (bottom→top)
  xLow: string;
  xHigh: string;
  yLow: string;
  yHigh: string;
  quadrants: [Quadrant, Quadrant, Quadrant, Quadrant];
  // order: [top-left, top-right, bottom-left, bottom-right]
};

const W = 1920;
const H = 1080;
const MATRIX_X = W / 2;
const MATRIX_Y = H / 2 + 30;
const HALF_W = 400;
const HALF_H = 360;
const STAGGER = 12;

export const MatrixDiagram: React.FC<MatrixDiagramProps> = ({
  title, xLabel, yLabel, xLow, xHigh, yLow, yHigh, quadrants,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Axes draw in
  const axisH = interpolate(frame, [8, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const axisV = interpolate(frame, [14, 36], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Quadrant positions: [top-left, top-right, bottom-left, bottom-right]
  const qPositions = [
    { dx: -1, dy: -1 },
    { dx:  1, dy: -1 },
    { dx: -1, dy:  1 },
    { dx:  1, dy:  1 },
  ];

  return (
    <AbsoluteFill style={{ background: "#FAFAFA" }}>

      {/* Title */}
      <div style={{
        position: "absolute", top: 44, left: 0, right: 0,
        textAlign: "center", opacity: titleOp,
      }}>
        <h1 style={{
          margin: 0, fontSize: 50, fontWeight: 800, color: "#111827",
          fontFamily: "Inter, system-ui, sans-serif", letterSpacing: "-0.5px",
        }}>{title}</h1>
      </div>

      {/* Quadrant cards */}
      {quadrants.map((q, i) => {
        const { dx, dy } = qPositions[i];
        const delay = 30 + i * STAGGER;

        const s = spring({
          frame: frame - delay, fps,
          config: { damping: 22, stiffness: 140 }, from: 0, to: 1,
        });
        const op = interpolate(frame - delay, [0, 14], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        const left  = dx < 0 ? MATRIX_X - HALF_W      : MATRIX_X + 2;
        const top   = dy < 0 ? MATRIX_Y - HALF_H      : MATRIX_Y + 2;
        const width = HALF_W - 2;
        const height = HALF_H - 2;

        const cx = left + width / 2;
        const cy = top + height / 2;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left, top, width, height,
              background: q.color,
              opacity: op,
              transform: `scale(${0.5 + s * 0.5})`,
              transformOrigin: `${dx < 0 ? "right" : "left"} ${dy < 0 ? "bottom" : "top"}`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 12,
              padding: "20px 32px",
            }}
          >
            <span style={{ fontSize: 52, lineHeight: 1 }}>{q.icon}</span>
            <h3 style={{
              margin: 0, fontSize: 28, fontWeight: 800,
              color: "#111827",
              fontFamily: "Inter, system-ui, sans-serif",
              textAlign: "center", lineHeight: 1.2,
            }}>{q.title}</h3>
            <p style={{
              margin: 0, fontSize: 17,
              color: "rgba(0,0,0,0.5)",
              fontFamily: "Inter, system-ui, sans-serif",
              textAlign: "center", lineHeight: 1.5,
            }}>{q.description}</p>
          </div>
        );
      })}

      {/* SVG axes on top */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        {/* Horizontal axis */}
        <line
          x1={MATRIX_X - HALF_W * axisH} y1={MATRIX_Y}
          x2={MATRIX_X + HALF_W * axisH} y2={MATRIX_Y}
          stroke="#111827" strokeWidth={3} strokeLinecap="round"
        />
        {/* Vertical axis */}
        <line
          x1={MATRIX_X} y1={MATRIX_Y - HALF_H * axisV}
          x2={MATRIX_X} y2={MATRIX_Y + HALF_H * axisV}
          stroke="#111827" strokeWidth={3} strokeLinecap="round"
        />

        {/* Arrowheads */}
        {axisH > 0.9 && (
          <>
            <polygon points={`${MATRIX_X + HALF_W + 12},${MATRIX_Y} ${MATRIX_X + HALF_W - 4},${MATRIX_Y - 8} ${MATRIX_X + HALF_W - 4},${MATRIX_Y + 8}`} fill="#111827" />
            <polygon points={`${MATRIX_X - HALF_W - 12},${MATRIX_Y} ${MATRIX_X - HALF_W + 4},${MATRIX_Y - 8} ${MATRIX_X - HALF_W + 4},${MATRIX_Y + 8}`} fill="#111827" />
          </>
        )}
        {axisV > 0.9 && (
          <>
            <polygon points={`${MATRIX_X},${MATRIX_Y - HALF_H - 12} ${MATRIX_X - 8},${MATRIX_Y - HALF_H + 4} ${MATRIX_X + 8},${MATRIX_Y - HALF_H + 4}`} fill="#111827" />
            <polygon points={`${MATRIX_X},${MATRIX_Y + HALF_H + 12} ${MATRIX_X - 8},${MATRIX_Y + HALF_H - 4} ${MATRIX_X + 8},${MATRIX_Y + HALF_H - 4}`} fill="#111827" />
          </>
        )}

        {/* Axis labels */}
        <text x={MATRIX_X + HALF_W + 24} y={MATRIX_Y + 5}
          fontSize={20} fontWeight={700} fill="#374151"
          fontFamily="Inter, system-ui, sans-serif"
          opacity={axisH}>
          {xHigh}
        </text>
        <text x={MATRIX_X - HALF_W - 24} y={MATRIX_Y + 5}
          textAnchor="end" fontSize={20} fontWeight={700} fill="#374151"
          fontFamily="Inter, system-ui, sans-serif"
          opacity={axisH}>
          {xLow}
        </text>
        <text x={MATRIX_X} y={MATRIX_Y - HALF_H - 22}
          textAnchor="middle" fontSize={20} fontWeight={700} fill="#374151"
          fontFamily="Inter, system-ui, sans-serif"
          opacity={axisV}>
          {yHigh}
        </text>
        <text x={MATRIX_X} y={MATRIX_Y + HALF_H + 30}
          textAnchor="middle" fontSize={20} fontWeight={700} fill="#374151"
          fontFamily="Inter, system-ui, sans-serif"
          opacity={axisV}>
          {yLow}
        </text>

        {/* Center axis labels (rotated) */}
        <text x={MATRIX_X} y={MATRIX_Y + HALF_H + 60}
          textAnchor="middle" fontSize={22} fontWeight={600} fill="#6B7280"
          fontFamily="Inter, system-ui, sans-serif"
          opacity={axisH}>
          {xLabel}
        </text>
        <text
          x={MATRIX_X - HALF_W - 56} y={MATRIX_Y}
          textAnchor="middle" fontSize={22} fontWeight={600} fill="#6B7280"
          fontFamily="Inter, system-ui, sans-serif"
          opacity={axisV}
          transform={`rotate(-90, ${MATRIX_X - HALF_W - 56}, ${MATRIX_Y})`}>
          {yLabel}
        </text>
      </svg>
    </AbsoluteFill>
  );
};
