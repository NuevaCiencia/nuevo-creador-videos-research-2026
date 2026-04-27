/**
 * Spotlight — Foco de luz que viaja por la pantalla revelando conceptos
 * Fondo negro total. Un círculo de luz (radial-gradient) se mueve
 * de punto en punto iluminando texto clave.
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

export type SpotPoint = {
  x: number;          // 0–1920
  y: number;          // 0–1080
  text: string;
  sub?: string;
  color: string;
  holdFrames: number; // frames to stay here
};

export type SpotlightProps = {
  points: SpotPoint[];
  spotRadius?: number;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:           "#FFFFFF",
  fontFamily:   "Inter, system-ui, sans-serif",

  termSize:     88,
  termWeight:   900,
  termTracking: "-2px",

  subSize:      30,
  subWeight:    500,
  subColor:     "#475569",
  subColorOff:  "#CBD5E1",

  termColorOff: "#CBD5E1",

  spotHaloColor:   "rgba(99,102,241,0.10)",
  spotTravelFrames: 18,   // frames para viajar entre puntos
};
// ─────────────────────────────────────────────────────────────────────────────

export const Spotlight: React.FC<SpotlightProps> = ({
  points,
  spotRadius = 320,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Build a schedule: for each point, when does it start?
  const TRAVEL = CONFIG.spotTravelFrames;
  const schedule: { start: number; end: number }[] = [];
  let t = 8;
  for (const pt of points) {
    schedule.push({ start: t, end: t + pt.holdFrames });
    t += pt.holdFrames + TRAVEL;
  }

  // Find current active point and interpolate position
  let currentPt = points[0];
  let nextPt    = points[0];
  let spotX = points[0].x;
  let spotY = points[0].y;

  for (let i = 0; i < points.length; i++) {
    const { start, end } = schedule[i];
    if (frame >= start && frame < end) {
      currentPt = points[i];
      nextPt    = points[i];
      spotX = points[i].x;
      spotY = points[i].y;
      break;
    }
    // Traveling to next
    if (i < points.length - 1) {
      const travelStart = schedule[i].end;
      const travelEnd   = schedule[i + 1].start;
      if (frame >= travelStart && frame < travelEnd) {
        const p = interpolate(frame, [travelStart, travelEnd], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
          easing: Easing.inOut(Easing.cubic),
        });
        spotX = points[i].x + (points[i + 1].x - points[i].x) * p;
        spotY = points[i].y + (points[i + 1].y - points[i].y) * p;
        currentPt = points[i];
        nextPt    = points[i + 1];
        break;
      }
    }
  }

  // Spot radius pulse
  const pulse = spotRadius + Math.sin((frame / fps) * Math.PI * 1.2) * 18;

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Halo de spotlight */}
      <div style={{
        position: "absolute", inset: 0,
        background: `radial-gradient(circle ${pulse}px at ${spotX}px ${spotY}px,
          ${CONFIG.spotHaloColor} 0%,
          transparent 70%
        )`,
        pointerEvents: "none",
        transition: "background 0.1s",
      }} />

      {/* Todos los términos — siempre visibles, el activo se resalta */}
      {points.map((pt, i) => {
        const { start } = schedule[i];

        // A partir de su turno queda permanentemente resaltado
        const activated = interpolate(frame, [start, start + 14], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        // Escala al activarse
        const s = spring({
          frame: frame - start, fps,
          config: { damping: 18, stiffness: 140 }, from: 0, to: 1,
        });
        const scale = 0.85 + s * 0.15;

        const isActive = frame >= start;
        const color    = isActive ? pt.color : CONFIG.termColorOff;
        const subColor = isActive ? CONFIG.subColor : CONFIG.subColorOff;

        return (
          <div key={i} style={{
            position: "absolute",
            left: pt.x,
            top: pt.y,
            transform: `translate(-50%, -50%) scale(${scale})`,
            textAlign: "center",
            opacity: 0.25 + activated * 0.75,
            pointerEvents: "none",
          }}>
            <p style={{
              margin: 0,
              fontSize: CONFIG.termSize,
              fontWeight: CONFIG.termWeight,
              color,
              fontFamily: CONFIG.fontFamily,
              letterSpacing: CONFIG.termTracking,
              lineHeight: 1,
            }}>{pt.text}</p>
            {pt.sub && (
              <p style={{
                margin: "10px 0 0",
                fontSize: CONFIG.subSize,
                fontWeight: CONFIG.subWeight,
                color: subColor,
                fontFamily: CONFIG.fontFamily,
                letterSpacing: "0.05em",
              }}>{pt.sub}</p>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
