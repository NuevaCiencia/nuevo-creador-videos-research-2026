import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

type Props = {
  label?: string;
  width?: string | number;
  height?: string | number;
  style?: React.CSSProperties;
};

const PALETTE = [
  ["#1e3a5f", "#2d6a9f"],
  ["#3b1f5e", "#7c3aed"],
  ["#1f3b2e", "#2d9e6a"],
  ["#5e2a1f", "#c0522a"],
  ["#1f3b5e", "#2a7fc0"],
  ["#3b2a1f", "#9e6a2d"],
];

function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

/**
 * Placeholder visual para imágenes/videos aún no disponibles.
 * Muestra un gradiente con el nombre del asset.
 */
export const PlaceholderAsset: React.FC<Props> = ({
  label = "asset",
  width = "100%",
  height = "100%",
  style,
}) => {
  const frame = useCurrentFrame();
  const [from, to] = PALETTE[hashStr(label) % PALETTE.length];

  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const filename = label.split("/").pop() ?? label;

  return (
    <div
      style={{
        width,
        height,
        background: `linear-gradient(135deg, ${from} 0%, ${to} 100%)`,
        borderRadius: 16,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        opacity,
        gap: 12,
        border: "1.5px solid rgba(255,255,255,0.1)",
        ...style,
      }}
    >
      {/* Ícono de imagen */}
      <svg width="56" height="56" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="3" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5"/>
        <circle cx="8.5" cy="8.5" r="1.5" fill="rgba(255,255,255,0.4)"/>
        <path d="M3 15l5-5 4 4 3-3 6 6" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <span
        style={{
          fontSize: 20,
          color: "rgba(255,255,255,0.5)",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "0.04em",
        }}
      >
        {filename}
      </span>
    </div>
  );
};
