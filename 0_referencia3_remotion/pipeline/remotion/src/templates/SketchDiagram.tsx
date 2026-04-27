/**
 * SketchDiagram — Esquema con estética de dibujo a mano
 * Usa SVG feTurbulence + feDisplacementMap para dar aspecto de trazo tembloroso.
 * Fondo papel amarillento, fuente monospace, líneas de cuaderno.
 */
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export type SketchBox = {
  x: number; y: number; w: number; h: number;
  label: string; sub?: string; color: string;
};

export type SketchArrow = {
  x1: number; y1: number; x2: number; y2: number; color: string;
};

export type SketchDiagramProps = {
  title: string;
  boxes: SketchBox[];
  arrows: SketchArrow[];
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#FDF6E3",
  fontFamily:  "'Courier New', monospace",

  titleSize:   68,
  titleColor:  "#2C2C2C",
  titleWeight: 700,

  labelSize:   52,
  labelColor:  "#2C2C2C",
  labelWeight: 700,

  subSize:     30,
  subColor:    "#777",

  stagger:     18,    // frames entre cajas
  lineColor:   "rgba(100,120,200,0.10)",   // rayas de cuaderno
  marginColor: "rgba(220,80,80,0.22)",     // línea roja de margen
};
// ─────────────────────────────────────────────────────────────────────────────

// Jittered rect path (hand-drawn look via math — deterministic)
function jitteredRect(x: number, y: number, w: number, h: number, seed: number): string {
  const j = (n: number, s: number) => Math.sin(n * 127.1 + s * 311.7) * 3.5;
  const pts = [
    [x       + j(0,seed),  y       + j(1,seed)],
    [x+w     + j(2,seed),  y       + j(3,seed)],
    [x+w     + j(4,seed),  y+h     + j(5,seed)],
    [x       + j(6,seed),  y+h     + j(7,seed)],
    [x       + j(8,seed),  y       + j(9,seed)],  // close back to start (slightly off)
  ];
  return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ") + " Z";
}

// Jittered line path
function jitteredLine(x1: number, y1: number, x2: number, y2: number, seed: number): string {
  const j = (n: number) => Math.sin(n * 127.1 + seed * 311.7) * 2.5;
  const mx = (x1 + x2) / 2 + j(1);
  const my = (y1 + y2) / 2 + j(2);
  return `M ${x1+j(3)},${y1+j(4)} Q ${mx},${my} ${x2+j(5)},${y2+j(6)}`;
}

// Arrowhead
function arrowHead(x1: number, y1: number, x2: number, y2: number): string {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const len = 14;
  const spread = 0.4;
  const ax = x2 - Math.cos(angle - spread) * len;
  const ay = y2 - Math.sin(angle - spread) * len;
  const bx = x2 - Math.cos(angle + spread) * len;
  const by = y2 - Math.sin(angle + spread) * len;
  return `M ${ax.toFixed(1)},${ay.toFixed(1)} L ${x2.toFixed(1)},${y2.toFixed(1)} L ${bx.toFixed(1)},${by.toFixed(1)}`;
}

export const SketchDiagram: React.FC<SketchDiagramProps> = ({ title, boxes, arrows }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg, fontFamily: CONFIG.fontFamily }}>

      {/* Notebook horizontal lines */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `repeating-linear-gradient(transparent, transparent 38px, ${CONFIG.lineColor} 38px, ${CONFIG.lineColor} 40px)`,
        pointerEvents: "none",
      }} />

      {/* Red margin line */}
      <div style={{
        position: "absolute", top: 0, bottom: 0, left: 96, width: 2,
        background: CONFIG.marginColor, pointerEvents: "none",
      }} />

      {/* Title */}
      <div style={{ position: "absolute", top: 44, left: 130, right: 100, opacity: titleOp }}>
        <h1 style={{
          margin: 0, fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight, color: CONFIG.titleColor,
          fontFamily: CONFIG.fontFamily,
          borderBottom: "3px solid rgba(44,44,44,0.25)",
          paddingBottom: 6, display: "inline-block",
        }}>{title}</h1>
      </div>

      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <defs>
          {/* Subtle texture turbulence */}
          <filter id="sketch-filter" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" seed="2" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="2.5" xChannelSelector="R" yChannelSelector="G" />
          </filter>
        </defs>

        {/* Arrows (drawn first, behind boxes) */}
        {arrows.map((a, i) => {
          const op = interpolate(frame - 12 - i * 8, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const prog = interpolate(frame - 12 - i * 8, [0, 22], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          // Animate line length via dashoffset
          const len = Math.hypot(a.x2 - a.x1, a.y2 - a.y1) * 1.2;
          return (
            <g key={i} opacity={op} filter="url(#sketch-filter)">
              <path
                d={jitteredLine(a.x1, a.y1, a.x2, a.y2, i * 3)}
                fill="none"
                stroke={a.color}
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeDasharray={len}
                strokeDashoffset={len * (1 - prog)}
              />
              {prog > 0.85 && (
                <path
                  d={arrowHead(a.x1, a.y1, a.x2, a.y2)}
                  fill="none"
                  stroke={a.color}
                  strokeWidth={2.5}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
            </g>
          );
        })}

        {/* Boxes */}
        {boxes.map((box, i) => {
          const delay = 16 + i * CONFIG.stagger;
          const s = spring({ frame: frame - delay, fps, config: { damping: 22, stiffness: 160 }, from: 0, to: 1 });
          const op = interpolate(frame - delay, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          return (
            <g key={i} opacity={op}
               transform={`scale(${s})`}
               style={{ transformOrigin: `${box.x + box.w / 2}px ${box.y + box.h / 2}px` }}>
              {/* Fill hatch lines */}
              {Array.from({ length: Math.ceil(box.h / 10) }, (_, li) => (
                <line key={li}
                  x1={box.x + 4} y1={box.y + li * 10 + 12}
                  x2={box.x + box.w - 4} y2={box.y + li * 10 + 12}
                  stroke={box.color} strokeWidth={0.9} opacity={0.3}
                />
              ))}
              {/* Jittered border */}
              <path
                d={jitteredRect(box.x, box.y, box.w, box.h, i * 11)}
                fill="none"
                stroke={box.color}
                strokeWidth={2.8}
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#sketch-filter)"
              />
            </g>
          );
        })}
      </svg>

      {/* Box labels — HTML layer for readability */}
      {boxes.map((box, i) => {
        const delay = 24 + i * CONFIG.stagger;
        const op = interpolate(frame - delay, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <div key={i} style={{
            position: "absolute",
            left: box.x, top: box.y, width: box.w, height: box.h,
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            gap: 6, opacity: op, pointerEvents: "none",
          }}>
            <span style={{ fontSize: CONFIG.labelSize, fontWeight: CONFIG.labelWeight, color: CONFIG.labelColor, fontFamily: CONFIG.fontFamily, textAlign: "center" }}>
              {box.label}
            </span>
            {box.sub && (
              <span style={{ fontSize: CONFIG.subSize, color: CONFIG.subColor, fontFamily: CONFIG.fontFamily, textAlign: "center" }}>
                {box.sub}
              </span>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
