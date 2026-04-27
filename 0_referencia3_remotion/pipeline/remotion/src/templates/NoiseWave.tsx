/**
 * NoiseWave — Olas orgánicas con ruido Perlin (@remotion/noise)
 * Varias capas de ondas que se mueven de forma natural y distinta.
 * Texto encima. Fondo oscuro.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { noise2D } from "@remotion/noise";

export type NoiseWaveProps = {
  title: string;
  subtitle?: string;
  colors: string[];   // one per wave layer
};

const W = 1920;
const H = 1080;
const COLS = 120;

function buildWavePath(
  frameT: number,
  seed: string,
  baseY: number,
  amp: number,
  freq: number,
): string {
  const pts: [number, number][] = [];
  for (let i = 0; i <= COLS; i++) {
    const x = (i / COLS) * W;
    const nx = (i / COLS) * freq;
    const ny = frameT * 0.18;
    const n  = noise2D(seed, nx, ny); // -1..1
    const y  = baseY + n * amp;
    pts.push([x, y]);
  }
  const top = pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" L ");
  return `M 0,${H} L ${top} L ${W},${H} Z`;
}

export const NoiseWave: React.FC<NoiseWaveProps> = ({ title, subtitle, colors }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const titleOp = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY  = interpolate(frame, [0, 20], [30, 0],  { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const N = colors.length;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #0a0918 0%, #080614 100%)" }}>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {colors.map((color, i) => {
          // Each layer has different base Y, amplitude, frequency and speed
          const baseY  = H * (0.45 + i * (0.12 / N));
          const amp    = 80 - i * 14;
          const freq   = 2.5 + i * 0.7;
          const seed   = `wave${i}`;
          const layerT = t * (1 + i * 0.3);

          const path = buildWavePath(layerT, seed, baseY, amp, freq);

          return (
            <path
              key={i}
              d={path}
              fill={color}
              fillOpacity={0.55 - i * 0.08}
            />
          );
        })}
      </svg>

      {/* Glow bloom on wave surface */}
      <div style={{
        position: "absolute", inset: 0,
        background: `radial-gradient(ellipse at 50% 58%, ${colors[0]}18 0%, transparent 60%)`,
        pointerEvents: "none",
      }} />

      {/* Text */}
      <div style={{
        position: "absolute",
        top: "28%",
        left: 0, right: 0,
        textAlign: "center",
        opacity: titleOp,
        transform: `translateY(${titleY}px)`,
      }}>
        <h1 style={{
          margin: 0, fontSize: 96, fontWeight: 900,
          color: "#FFFFFF",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "-3px",
          lineHeight: 1,
          textShadow: "0 4px 40px rgba(0,0,0,0.5)",
          padding: "0 120px",
        }}>{title}</h1>
        {subtitle && (
          <p style={{
            margin: "20px 0 0",
            fontSize: 30, fontWeight: 300,
            color: "rgba(255,255,255,0.5)",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.18em",
            textTransform: "uppercase",
          }}>{subtitle}</p>
        )}
      </div>
    </AbsoluteFill>
  );
};
