/**
 * GradientTitle — Fondo con gradiente vibrante, formas abstractas
 * Título en blanco sobre colores fuertes. Muy impactante para
 * aperturas o cierres de sección.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
export type GradientTitleProps = {
  line1: string;
  line2?: string;
  tag?: string;          // etiqueta pequeña arriba
  gradient: string;      // CSS gradient, ej. "linear-gradient(135deg, #667eea, #764ba2)"
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  fontFamily:  "Inter, system-ui, sans-serif",

  line1Size:   108,
  line1Weight: 900,
  line1Color:  "#FFFFFF",
  line1Tracking: "-2px",

  line2Size:   48,
  line2Weight: 300,
  line2Color:  "rgba(255,255,255,0.85)",

  tagSize:     22,
  tagWeight:   600,
  tagColor:    "rgba(255,255,255,0.7)",

  separatorW:  280,   // ancho máximo del separador al final de la animación
  separatorH:  3,
  separatorColor: "rgba(255,255,255,0.5)",

  shapeBreatheAmp: 0.04,   // amplitud del "respiro" de las formas de fondo
};
// ─────────────────────────────────────────────────────────────────────────────

export const GradientTitle: React.FC<GradientTitleProps> = ({
  line1,
  line2,
  tag,
  gradient,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Entrada principal con spring
  const titleS = spring({ frame, fps, config: { damping: 20, stiffness: 120 }, from: 0.85, to: 1 });
  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Tag pequeño entra antes
  const tagOp = interpolate(frame, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tagY  = interpolate(frame, [0, 12], [10, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Línea 2 entra después
  const line2Op = interpolate(frame, [14, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const line2Y  = interpolate(frame, [14, 30], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Formas abstractas de fondo (respirando lentamente)
  const breathe = 1 + Math.sin(t * 0.7) * CONFIG.shapeBreatheAmp;
  const breathe2 = 1 + Math.sin(t * 0.5 + 1.2) * (CONFIG.shapeBreatheAmp + 0.01);
  const drift = Math.sin(t * 0.4) * 20;

  return (
    <AbsoluteFill style={{ background: gradient, overflow: "hidden" }}>

      {/* Forma abstracta 1 — círculo grande */}
      <div style={{
        position: "absolute",
        top: -200 + drift,
        right: -150,
        width: 700,
        height: 700,
        borderRadius: "50%",
        background: "rgba(255,255,255,0.08)",
        transform: `scale(${breathe})`,
        pointerEvents: "none",
      }} />

      {/* Forma abstracta 2 — círculo mediano */}
      <div style={{
        position: "absolute",
        bottom: -120,
        left: -100 - drift * 0.5,
        width: 500,
        height: 500,
        borderRadius: "50%",
        background: "rgba(255,255,255,0.06)",
        transform: `scale(${breathe2})`,
        pointerEvents: "none",
      }} />

      {/* Forma abstracta 3 — rectángulo rotado */}
      <div style={{
        position: "absolute",
        top: "30%",
        left: "-5%",
        width: 300,
        height: 300,
        borderRadius: 48,
        background: "rgba(255,255,255,0.05)",
        transform: `rotate(${20 + t * 3}deg)`,
        pointerEvents: "none",
      }} />

      {/* Overlay de ruido sutil */}
      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(0,0,0,0.25) 100%)",
        pointerEvents: "none",
      }} />

      {/* Contenido central */}
      <div style={{
        position: "absolute", inset: 0,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: 20,
        padding: "0 120px",
      }}>

        {/* Tag */}
        {tag && (
          <div style={{
            opacity: tagOp,
            transform: `translateY(${tagY}px)`,
          }}>
            <span style={{
              fontSize: CONFIG.tagSize,
              fontWeight: CONFIG.tagWeight,
              color: CONFIG.tagColor,
              fontFamily: CONFIG.fontFamily,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              background: "rgba(255,255,255,0.15)",
              padding: "8px 24px",
              borderRadius: 50,
              border: "1px solid rgba(255,255,255,0.25)",
            }}>
              {tag}
            </span>
          </div>
        )}

        {/* Línea 1 — título principal */}
        <div style={{
          opacity: titleOp,
          transform: `scale(${titleS})`,
          textAlign: "center",
        }}>
          <h1 style={{
            margin: 0,
            fontSize: CONFIG.line1Size,
            fontWeight: CONFIG.line1Weight,
            color: CONFIG.line1Color,
            fontFamily: CONFIG.fontFamily,
            lineHeight: 1.05,
            letterSpacing: CONFIG.line1Tracking,
            textShadow: "0 4px 40px rgba(0,0,0,0.3)",
          }}>
            {line1}
          </h1>
        </div>

        {/* Separador */}
        <div style={{
          width: interpolate(frame, [16, 45], [0, CONFIG.separatorW], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          height: CONFIG.separatorH,
          background: CONFIG.separatorColor,
          borderRadius: 2,
        }} />

        {/* Línea 2 */}
        {line2 && (
          <div style={{
            opacity: line2Op,
            transform: `translateY(${line2Y}px)`,
            textAlign: "center",
          }}>
            <p style={{
              margin: 0,
              fontSize: CONFIG.line2Size,
              fontWeight: CONFIG.line2Weight,
              color: CONFIG.line2Color,
              fontFamily: CONFIG.fontFamily,
              letterSpacing: "0.02em",
            }}>
              {line2}
            </p>
          </div>
        )}
      </div>

    </AbsoluteFill>
  );
};
