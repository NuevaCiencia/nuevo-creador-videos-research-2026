import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Easing,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Layout ──────────────────────────────────────────────────────────────────
const PAD_L  = 160;
const PAD_R  = 120;
const PAD_T  = 220;  // espacio para el título
const PAD_B  = 140;
const W_CHART = 1920 - PAD_L - PAD_R;  // 1640
const H_CHART = 1080 - PAD_T - PAD_B;  // 720

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 700,

  lineColor:   "#6366F1",
  lineW:       5,
  areaColor:   "rgba(99,102,241,0.08)",

  gridColor:   "rgba(0,0,0,0.07)",
  gridW:       1,

  axisColor:   "#94A3B8",
  axisSize:    28,

  dotR:        10,
  dotColor:    "#6366F1",
  dotBorder:   "#FFFFFF",
  dotBorderW:  3,

  labelBg:     "#6366F1",
  labelColor:  "#FFFFFF",
  labelSize:   26,
  labelWeight: 700,
  labelPad:    "8px 14px",
  labelRadius: 8,

  drawFrames:  60,
  dotDelay:    10,
};
// ─────────────────────────────────────────────────────────────────────────────

export type TrendPoint = {
  label: string;   // etiqueta del eje X
  value: number;   // 0–100 (se escala al alto del chart)
  note?: string;   // etiqueta flotante sobre el punto
};

export type WaveTrendProps = {
  title?:   string;
  points:   TrendPoint[];
  yLabel?:  string;
};

// Interpolación de curva suave (Catmull-Rom → path SVG)
function smoothPath(pts: [number, number][]): string {
  if (pts.length < 2) return "";
  let d = `M ${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(i + 2, pts.length - 1)];
    const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
    const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
    const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
    const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2[0]},${p2[1]}`;
  }
  return d;
}

// Longitud aproximada del path (suma de distancias entre puntos × factor curva)
function approxLen(pts: [number, number][]): number {
  let len = 0;
  for (let i = 1; i < pts.length; i++) {
    len += Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]);
  }
  return len * 1.05;
}

export const WaveTrend: React.FC<WaveTrendProps> = ({ title, points, yLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY       = interpolate(frame, [0, 18], [-14, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const n = points.length;
  // Coordenadas de cada punto en el sistema SVG
  const coords: [number, number][] = points.map((p, i) => [
    PAD_L + (i / (n - 1)) * W_CHART,
    PAD_T + H_CHART - (p.value / 100) * H_CHART,
  ]);

  const pathD   = smoothPath(coords);
  const totalLen = approxLen(coords);

  // Línea que se dibuja progresivamente
  const drawProg = interpolate(frame, [10, 10 + CONFIG.drawFrames], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const dashOffset = totalLen * (1 - drawProg);

  // Área rellena (aparece con fade tras la línea)
  const areaOp = interpolate(frame, [10 + CONFIG.drawFrames - 10, 10 + CONFIG.drawFrames + 20], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Path cerrado para el área
  const areaD = pathD +
    ` L ${coords[n-1][0]},${PAD_T + H_CHART}` +
    ` L ${coords[0][0]},${PAD_T + H_CHART} Z`;

  // Grid horizontal (5 líneas)
  const gridLines = [0, 25, 50, 75, 100];

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>
      {/* Título */}
      {title && (
        <h2 style={{
          position: "absolute", top: 56, left: 0, right: 0,
          textAlign: "center", margin: 0,
          opacity: titleOpacity, transform: `translateY(${titleY}px)`,
          fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight,
          color: CONFIG.titleColor, fontFamily: CONFIG.fontFamily,
        }}>
          {title}
        </h2>
      )}

      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {/* Grid horizontal */}
        {gridLines.map(v => {
          const y = PAD_T + H_CHART - (v / 100) * H_CHART;
          return (
            <g key={v}>
              <line x1={PAD_L} y1={y} x2={PAD_L + W_CHART} y2={y}
                stroke={CONFIG.gridColor} strokeWidth={CONFIG.gridW} />
              <text x={PAD_L - 16} y={y + 6}
                textAnchor="end" fontSize={CONFIG.axisSize}
                fill={CONFIG.axisColor} fontFamily={CONFIG.fontFamily}>
                {v}
              </text>
            </g>
          );
        })}

        {/* Eje X */}
        <line x1={PAD_L} y1={PAD_T + H_CHART} x2={PAD_L + W_CHART} y2={PAD_T + H_CHART}
          stroke={CONFIG.axisColor} strokeWidth={2} />

        {/* Etiquetas eje X */}
        {coords.map(([x], i) => (
          <text key={i} x={x} y={PAD_T + H_CHART + 44}
            textAnchor="middle" fontSize={CONFIG.axisSize}
            fill={CONFIG.axisColor} fontFamily={CONFIG.fontFamily}>
            {points[i].label}
          </text>
        ))}

        {/* yLabel */}
        {yLabel && (
          <text x={PAD_L - 60} y={PAD_T + H_CHART / 2}
            textAnchor="middle" fontSize={20}
            fill={CONFIG.axisColor} fontFamily={CONFIG.fontFamily}
            transform={`rotate(-90, ${PAD_L - 60}, ${PAD_T + H_CHART / 2})`}>
            {yLabel}
          </text>
        )}

        {/* Área rellena */}
        <path d={areaD} fill={CONFIG.areaColor} opacity={areaOp} />

        {/* Línea de tendencia */}
        <path
          d={pathD}
          fill="none"
          stroke={CONFIG.lineColor}
          strokeWidth={CONFIG.lineW}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={totalLen}
          strokeDashoffset={dashOffset}
        />

        {/* Puntos + etiquetas flotantes */}
        {coords.map(([x, y], i) => {
          const dotDelay = 10 + CONFIG.drawFrames * (i / (n - 1)) + CONFIG.dotDelay;
          const dotOp = interpolate(frame - dotDelay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const dotScale = interpolate(frame - dotDelay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.5)),
          });

          return (
            <g key={i} opacity={dotOp}>
              {/* Punto */}
              <circle cx={x} cy={y} r={CONFIG.dotR * dotScale}
                fill={CONFIG.dotColor}
                stroke={CONFIG.dotBorder} strokeWidth={CONFIG.dotBorderW} />

              {/* Etiqueta flotante */}
              {points[i].note && (
                <foreignObject x={x - 90} y={y - 72} width={180} height={52}>
                  <div
                    style={{
                      background: CONFIG.labelBg,
                      color: CONFIG.labelColor,
                      fontSize: CONFIG.labelSize,
                      fontWeight: CONFIG.labelWeight,
                      fontFamily: CONFIG.fontFamily,
                      borderRadius: CONFIG.labelRadius,
                      padding: CONFIG.labelPad,
                      textAlign: "center",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {points[i].note}
                  </div>
                </foreignObject>
              )}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
