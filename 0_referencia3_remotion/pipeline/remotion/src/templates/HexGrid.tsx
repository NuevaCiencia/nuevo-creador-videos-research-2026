import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Geometría ───────────────────────────────────────────────────────────────
const S = 138; // radio (centro → vértice), flat-top

const HEX_W = S * 2;                 // 276
const HEX_H = S * Math.sqrt(3);      // ≈ 239

// Posiciones del anillo-1 relativas al centro, sentido horario desde arriba
const RING_OFFSETS = [
  { x: 0,         y: -HEX_H },        // arriba
  { x:  S * 1.5,  y: -HEX_H / 2 },   // arriba-derecha
  { x:  S * 1.5,  y:  HEX_H / 2 },   // abajo-derecha
  { x: 0,         y:  HEX_H },        // abajo
  { x: -S * 1.5,  y:  HEX_H / 2 },   // abajo-izquierda
  { x: -S * 1.5,  y: -HEX_H / 2 },   // arriba-izquierda
];

// Clip-path flat-top hexágono
const HEX_CLIP = "polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)";

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:         "#FFFFFF",
  fontFamily: "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 700,

  // Hexágono central
  centerBg:            "#6366F1",
  centerIconSize:      68,
  centerLabelSize:     30,
  centerLabelWeight:   700,
  centerLabelColor:    "#FFFFFF",

  // Anillo exterior
  ringIconSize:        48,
  ringLabelSize:       24,
  ringLabelWeight:     600,
  ringLabelColor:      "#1E293B",

  // Timing
  centerDelay:  8,
  ringBaseDelay: 38,
  ringStagger:   10,
};

const RING_PALETTE = [
  { bg: "#EEF2FF", border: "#A5B4FC" },
  { bg: "#F0FDF4", border: "#86EFAC" },
  { bg: "#FFF7ED", border: "#FDB974" },
  { bg: "#FDF4FF", border: "#D8B4FE" },
  { bg: "#F0F9FF", border: "#7DD3FC" },
  { bg: "#FFF1F2", border: "#FDA4AF" },
];
// ─────────────────────────────────────────────────────────────────────────────

export type HexItem = {
  icon:  string;
  label: string;
};

export type HexGridProps = {
  title?:  string;
  center:  HexItem;
  items:   HexItem[];  // 6 items para el anillo exterior
};

// ─── Hexágono individual ──────────────────────────────────────────────────────
const Hex: React.FC<{
  item:        HexItem;
  delay:       number;
  frame:       number;
  fps:         number;
  bg:          string;
  iconSize:    number;
  labelSize:   number;
  labelWeight: number;
  labelColor:  string;
  borderColor?: string;
}> = ({ item, delay, frame, fps, bg, iconSize, labelSize, labelWeight, labelColor, borderColor }) => {
  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 18, stiffness: 130 },
    from: 0,
    to: 1,
  });
  const opacity = interpolate(frame - delay, [0, 14], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width:    HEX_W,
        height:   HEX_H,
        clipPath: HEX_CLIP,
        background: bg,
        display:    "flex",
        flexDirection: "column",
        alignItems:    "center",
        justifyContent:"center",
        gap:    8,
        opacity,
        transform: `scale(${scale})`,
        // El borde lo simulamos con un pseudo-wrapper exterior
      }}
    >
      <span style={{ fontSize: iconSize, lineHeight: 1 }}>{item.icon}</span>
      <span
        style={{
          fontSize:   labelSize,
          fontWeight: labelWeight,
          color:      labelColor,
          fontFamily: CONFIG.fontFamily,
          textAlign:  "center",
          lineHeight: 1.25,
          padding:    "0 28px",
        }}
      >
        {item.label}
      </span>
    </div>
  );
};

// Wrapper con borde simulado (un hex levemente más grande detrás)
const HexWithBorder: React.FC<{
  item:        HexItem;
  delay:       number;
  frame:       number;
  fps:         number;
  bg:          string;
  borderColor: string;
  iconSize:    number;
  labelSize:   number;
  labelWeight: number;
  labelColor:  string;
}> = (props) => {
  const scale = spring({
    frame: props.frame - props.delay,
    fps: props.fps,
    config: { damping: 18, stiffness: 130 },
    from: 0,
    to: 1,
  });
  const opacity = interpolate(props.frame - props.delay, [0, 14], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div style={{ position: "relative", width: HEX_W, height: HEX_H, opacity, transform: `scale(${scale})` }}>
      {/* Borde (hex más grande, mismo clip) */}
      <div
        style={{
          position: "absolute",
          inset: -3,
          clipPath: HEX_CLIP,
          background: props.borderColor,
        }}
      />
      {/* Relleno */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: HEX_CLIP,
          background: props.bg,
          display:    "flex",
          flexDirection: "column",
          alignItems:    "center",
          justifyContent:"center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: props.iconSize, lineHeight: 1 }}>{props.item.icon}</span>
        <span
          style={{
            fontSize:   props.labelSize,
            fontWeight: props.labelWeight,
            color:      props.labelColor,
            fontFamily: CONFIG.fontFamily,
            textAlign:  "center",
            lineHeight: 1.25,
            padding:    "0 28px",
          }}
        >
          {props.item.label}
        </span>
      </div>
    </div>
  );
};

// ─── Composición principal ────────────────────────────────────────────────────
export const HexGrid: React.FC<HexGridProps> = ({ title, center, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 18], [-14, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Centro del panal en el canvas
  const cx = 960;
  const cy = title ? 590 : 540;

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

      {/* Panal */}
      <div style={{ position: "absolute", inset: 0 }}>
        {/* Hexágono central */}
        <div
          style={{
            position: "absolute",
            left: cx - HEX_W / 2,
            top:  cy - HEX_H / 2,
          }}
        >
          <Hex
            item={center}
            delay={CONFIG.centerDelay}
            frame={frame}
            fps={fps}
            bg={CONFIG.centerBg}
            iconSize={CONFIG.centerIconSize}
            labelSize={CONFIG.centerLabelSize}
            labelWeight={CONFIG.centerLabelWeight}
            labelColor={CONFIG.centerLabelColor}
          />
        </div>

        {/* Anillo exterior */}
        {RING_OFFSETS.map((off, i) => {
          const palette   = RING_PALETTE[i % RING_PALETTE.length];
          const ringItem  = items[i] ?? { icon: "·", label: "" };
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: cx + off.x - HEX_W / 2,
                top:  cy + off.y - HEX_H / 2,
              }}
            >
              <HexWithBorder
                item={ringItem}
                delay={CONFIG.ringBaseDelay + i * CONFIG.ringStagger}
                frame={frame}
                fps={fps}
                bg={palette.bg}
                borderColor={palette.border}
                iconSize={CONFIG.ringIconSize}
                labelSize={CONFIG.ringLabelSize}
                labelWeight={CONFIG.ringLabelWeight}
                labelColor={CONFIG.ringLabelColor}
              />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
