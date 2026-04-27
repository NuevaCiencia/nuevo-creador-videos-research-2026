/**
 * NeonGlow — Cartel de neón con efecto CRT
 * Texto con múltiples capas de glow, scan lines, flicker irregular
 * y vignette circular. 100% CSS + math.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";

export type NeonGlowProps = {
  line1: string;
  line2?: string;
  accent: string;   // color neón principal, ej. "#00D9FF"
  word_cues: WordCue[];
};

export const NeonGlow: React.FC<NeonGlowProps> = ({
  line1,
  line2,
  accent,
  word_cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Flicker irregular (no periódico) ────────────────────────────────────
  const flicker =
    0.88 +
    0.12 *
      Math.abs(
        Math.sin(frame * 2.31) *
        Math.sin(frame * 0.37) *
        Math.sin(frame * 0.11)
      );

  // ── Intensidad del glow (pulso lento) ────────────────────────────────────
  const glowPulse =
    0.85 + 0.15 * Math.sin((frame / fps) * Math.PI * 0.6);

  // ── Fade in ───────────────────────────────────────────────────────────────
  const fadeIn = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Línea horizontal de scaneo que baja ──────────────────────────────────
  const scanY = ((frame * 3) % 1080);

  const glow = (mult: number) => `
    0 0 ${10 * mult}px ${accent},
    0 0 ${25 * mult}px ${accent},
    0 0 ${55 * mult}px ${accent},
    0 0 ${100 * mult}px ${accent},
    0 0 ${160 * mult}px ${accent}
  `;

  return (
    <AbsoluteFill
      style={{
        background: "#030208",
        opacity: fadeIn,
      }}
    >
      {/* ── Scan lines (efecto CRT) ──────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.18) 3px, rgba(0,0,0,0.18) 4px)",
          pointerEvents: "none",
          zIndex: 10,
        }}
      />

      {/* ── Línea de scaneo móvil ────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: scanY,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${accent}44, transparent)`,
          pointerEvents: "none",
          zIndex: 11,
        }}
      />

      {/* ── Vignette ────────────────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,0.85) 100%)",
          pointerEvents: "none",
          zIndex: 9,
        }}
      />

      {/* ── Resplandor de fondo ──────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 800,
          height: 400,
          transform: "translate(-50%, -50%)",
          background: `radial-gradient(ellipse, ${accent}18 0%, transparent 70%)`,
          filter: "blur(40px)",
          opacity: glowPulse,
        }}
      />

      {/* ── Texto principal ──────────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 28,
          zIndex: 5,
          opacity: flicker,
        }}
      >
        {/* Línea 1 — neón principal */}
        <div
          style={{
            fontSize: 120,
            fontWeight: 900,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            textAlign: "center",
            lineHeight: 1,
            textShadow: glow(glowPulse),
          }}
        >
          {line1}
        </div>

        {/* Separador neón */}
        <div
          style={{
            width: 500,
            height: 3,
            background: accent,
            borderRadius: 2,
            boxShadow: `0 0 12px ${accent}, 0 0 30px ${accent}, 0 0 60px ${accent}`,
            opacity: glowPulse * flicker,
          }}
        />

        {/* Línea 2 — subtítulo neón secundario */}
        {line2 && (
          <div
            style={{
              fontSize: 56,
              fontWeight: 300,
              color: accent,
              fontFamily: "Inter, system-ui, sans-serif",
              letterSpacing: "0.22em",
              textTransform: "uppercase",
              textAlign: "center",
              textShadow: `0 0 8px ${accent}, 0 0 20px ${accent}, 0 0 50px ${accent}`,
              opacity: glowPulse,
            }}
          >
            {line2}
          </div>
        )}
      </div>

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
