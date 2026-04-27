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
  bg:            "#FFFFFF",
  fontFamily:    "Inter, system-ui, sans-serif",

  titleSize:     52,
  titleColor:    "#0F172A",
  titleWeight:   700,

  labelSize:     26,
  labelColor:    "#FFFFFF",
  labelWeight:   800,

  descSize:      32,
  descColor:     "#475569",
  descWeight:    400,

  connectorColor: "#CBD5E1",

  // Geometría de la pirámide
  pyrCenterX:    560,
  pyrBaseY:      940,
  pyrBaseWidth:  860,
  pyrHeight:     720,

  stagger:       18,
};
// ─────────────────────────────────────────────────────────────────────────────

export type PyramidLevel = {
  label:       string;
  description: string;
};

const PALETTE = ["#6366F1","#818CF8","#A5B4FC","#C7D2FE","#DDD6FE","#EDE9FE","#F5F3FF"];

export type PyramidLevelsProps = {
  title:  string;
  levels: PyramidLevel[]; // de abajo hacia arriba
};

const W = 1920;
const H = 1080;

export const PyramidLevels: React.FC<PyramidLevelsProps> = ({ title, levels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const N = levels.length;
  const levelH = CONFIG.pyrHeight / N;

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>
      {/* Título */}
      <div
        style={{
          position:  "absolute",
          top:       52,
          left:      0,
          right:     0,
          textAlign: "center",
          opacity:   titleOpacity,
        }}
      >
        <h2
          style={{
            margin:        0,
            fontSize:      CONFIG.titleSize,
            fontWeight:    CONFIG.titleWeight,
            color:         CONFIG.titleColor,
            fontFamily:    CONFIG.fontFamily,
            letterSpacing: "-0.5px",
          }}
        >
          {title}
        </h2>
      </div>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {levels.map((level, idx) => {
          // idx 0 = base, idx N-1 = cima
          const delay = CONFIG.stagger + idx * CONFIG.stagger;

          const s = spring({
            frame: frame - delay,
            fps,
            config: { damping: 24, stiffness: 140 },
            from: 0,
            to: 1,
          });
          const opacity = interpolate(frame - delay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const labelOpacity = interpolate(frame - delay - 6, [0, 16], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          const yBottom = CONFIG.pyrBaseY - idx * levelH;
          const yTop    = yBottom - levelH;
          const midY    = (yTop + yBottom) / 2;

          const fBottom = (CONFIG.pyrBaseY - yBottom) / CONFIG.pyrHeight;
          const fTop    = (CONFIG.pyrBaseY - yTop)    / CONFIG.pyrHeight;

          const halfBottom = (CONFIG.pyrBaseWidth / 2) * (1 - fBottom);
          const halfTop    = (CONFIG.pyrBaseWidth / 2) * (1 - fTop);

          const cx = CONFIG.pyrCenterX;
          const x1b = cx - halfBottom;
          const x2b = cx + halfBottom;
          const x1t = cx - halfTop;
          const x2t = cx + halfTop;

          const slideY = (1 - s) * 28;

          // Ancho disponible en el centro del nivel → font size adaptativo
          const fMid       = (CONFIG.pyrBaseY - midY) / CONFIG.pyrHeight;
          const halfMid    = (CONFIG.pyrBaseWidth / 2) * (1 - fMid);
          const availW     = halfMid * 2 - 32;
          const fittedSize = Math.min(CONFIG.labelSize, availW / (level.label.length * 0.58));

          // Punto de conexión al lado derecho del trapezoide
          const connX = x2b + (x2t - x2b) * 0.5;
          const labelX = cx + CONFIG.pyrBaseWidth / 2 + 80;

          return (
            <g key={idx} opacity={opacity} transform={`translate(0, ${slideY})`}>
              {/* Trapezoide */}
              <polygon
                points={`${x1b},${yBottom} ${x2b},${yBottom} ${x2t},${yTop} ${x1t},${yTop}`}
                fill={PALETTE[idx % PALETTE.length]}
              />

              {/* Separador */}
              <line
                x1={x1b} y1={yBottom}
                x2={x2b} y2={yBottom}
                stroke="rgba(255,255,255,0.35)"
                strokeWidth={2}
              />

              {/* Etiqueta dentro */}
              <text
                x={cx} y={midY + 5}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={fittedSize}
                fontWeight={CONFIG.labelWeight}
                fill={CONFIG.labelColor}
                fontFamily={CONFIG.fontFamily}
              >
                {level.label}
              </text>

              {/* Conector + descripción a la derecha */}
              <g opacity={labelOpacity}>
                <line
                  x1={connX} y1={midY}
                  x2={labelX - 10} y2={midY}
                  stroke={CONFIG.connectorColor}
                  strokeWidth={1.5}
                  strokeDasharray="5 4"
                />
                <circle cx={labelX - 8} cy={midY} r={4} fill={PALETTE[idx % PALETTE.length]} />
                <text
                  x={labelX + 8} y={midY + 7}
                  fontSize={CONFIG.descSize}
                  fontWeight={CONFIG.descWeight}
                  fill={CONFIG.descColor}
                  fontFamily={CONFIG.fontFamily}
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
