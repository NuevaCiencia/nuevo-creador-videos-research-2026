/**
 * GlitchReveal — Texto con efecto glitch digital, fondo NEGRO
 * RGB split, scan lines, flickering. 100% determinístico.
 * Ideal para transiciones impactantes o términos técnicos.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
export type GlitchRevealProps = {
  line1: string;
  line2?: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#000000",
  fontFamily:  "'Courier New', monospace",

  line1Size:   132,
  line1Weight: 900,
  line1Color:  "#FFFFFF",

  line2Size:   52,
  line2Weight: 400,
  line2Color:  "#00D9FF",
  line2Tracking: "0.25em",

  glitchRedColor:  "#FF0055",
  glitchBlueColor: "#00D9FF",

  footerSize:  18,
  footerColor: "rgba(0,217,255,0.2)",
  footerText:  "> AGENT_INIT :: STATUS: AUTONOMOUS :: PROPS: [react, decide, act]",
};
// ─────────────────────────────────────────────────────────────────────────────

// Genera un valor pseudo-aleatorio determinístico
function drand(frame: number, seed: number): number {
  return Math.abs(Math.sin(frame * 127.1 + seed * 311.7)) % 1;
}

export const GlitchReveal: React.FC<GlitchRevealProps> = ({
  line1,
  line2,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Intensidad del glitch — alta al principio, baja al asentarse
  const glitchIntensity = interpolate(frame, [0, 8, 30, 60], [1, 1, 0.3, 0.08], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Offset del glitch
  const gx = (drand(frame, 1) - 0.5) * 30 * glitchIntensity;
  const gy = (drand(frame, 2) - 0.5) * 8  * glitchIntensity;

  // Frames de glitch fuerte (ocasionales)
  const hardGlitch = drand(frame, 3) < 0.06 * glitchIntensity;

  const rgbOffset = hardGlitch ? 12 : 3 * glitchIntensity;

  // Scan line rota periódicamente
  const scanY = ((frame * 4.5) % 1080);
  const scanH = hardGlitch ? 8 : 2;

  // Fade-in del texto base
  const baseOp = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Texto bloque que se "descifra" al principio
  const decodeProgress = interpolate(frame, [0, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Caracteres visibles de izquierda a derecha
  const visibleChars = Math.floor(line1.length * decodeProgress);
  const decodedLine1 = line1.slice(0, visibleChars) +
    Array.from({ length: line1.length - visibleChars }, (_, i) =>
      "▓░▒█#@&%$!".charAt(Math.floor(drand(frame + i, 9) * 10))
    ).join("");

  const textStyle: React.CSSProperties = {
    fontSize: CONFIG.line1Size,
    fontWeight: CONFIG.line1Weight,
    fontFamily: CONFIG.fontFamily,
    lineHeight: 1,
    letterSpacing: "0.04em",
    position: "absolute",
    whiteSpace: "nowrap",
    userSelect: "none",
  };

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      {/* Scan lines */}
      <div style={{
        position: "absolute", inset: 0,
        background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 3px)",
        pointerEvents: "none", zIndex: 8,
      }} />

      {/* Línea de scaneo móvil */}
      <div style={{
        position: "absolute",
        left: 0, right: 0,
        top: scanY, height: scanH,
        background: "rgba(255,255,255,0.06)",
        pointerEvents: "none", zIndex: 9,
      }} />

      {/* Bloque de glitch horizontal aleatorio */}
      {hardGlitch && (
        <div style={{
          position: "absolute",
          top: drand(frame, 5) * 900,
          left: 0, right: 0,
          height: 3 + drand(frame, 6) * 20,
          background: `rgba(0, 217, 255, ${drand(frame, 7) * 0.3})`,
          transform: `translateX(${(drand(frame, 8) - 0.5) * 40}px)`,
          zIndex: 7,
        }} />
      )}

      {/* Texto — capa ROJA (offset) */}
      <div style={{
        ...textStyle,
        top: "50%", left: "50%",
        transform: `translate(calc(-50% + ${gx + rgbOffset}px), calc(-50% + ${gy}px))`,
        color: CONFIG.glitchRedColor,
        opacity: baseOp * 0.6 * (0.3 + glitchIntensity * 0.7),
        mixBlendMode: "screen",
      }}>
        {line1}
      </div>

      {/* Texto — capa AZUL (offset) */}
      <div style={{
        ...textStyle,
        top: "50%", left: "50%",
        transform: `translate(calc(-50% - ${gx + rgbOffset}px), calc(-50% - ${gy * 0.5}px))`,
        color: CONFIG.glitchBlueColor,
        opacity: baseOp * 0.6 * (0.3 + glitchIntensity * 0.7),
        mixBlendMode: "screen",
      }}>
        {line1}
      </div>

      {/* Texto principal — BLANCO */}
      <div style={{
        ...textStyle,
        top: line2 ? "42%" : "50%",
        left: "50%",
        transform: `translate(calc(-50% + ${gx * 0.2}px), -50%)`,
        color: CONFIG.line1Color,
        opacity: baseOp,
      }}>
        {decodedLine1}
      </div>

      {/* Línea 2 */}
      {line2 && (
        <div style={{
          position: "absolute",
          top: "62%",
          left: "50%",
          transform: `translateX(calc(-50% + ${gx * 0.1}px))`,
          fontSize: CONFIG.line2Size,
          fontWeight: CONFIG.line2Weight,
          fontFamily: CONFIG.fontFamily,
          color: CONFIG.line2Color,
          letterSpacing: CONFIG.line2Tracking,
          textTransform: "uppercase",
          opacity: interpolate(frame, [20, 35], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}>
          {line2}
        </div>
      )}

      {/* Texto decorativo de código */}
      <div style={{
        position: "absolute",
        bottom: 140,
        left: 80,
        fontSize: CONFIG.footerSize,
        color: CONFIG.footerColor,
        fontFamily: CONFIG.fontFamily,
        letterSpacing: "0.1em",
        opacity: interpolate(frame, [30, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      }}>
        {CONFIG.footerText}
      </div>

    </AbsoluteFill>
  );
};
