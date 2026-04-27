import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";

export type TitleCardProps = {
  title: string;
  style?: string;   // ej. "TITLE" — reservado para variantes futuras
  speech?: string;
  word_cues: WordCue[];
};

export const TitleCard: React.FC<TitleCardProps> = ({ title, word_cues }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = spring({
    frame,
    fps,
    config: { damping: 22, stiffness: 140 },
    from: 0.88,
    to: 1,
  });

  // Línea decorativa debajo del título
  const lineWidth = interpolate(frame, [10, 40], [0, 420], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f0e13 0%, #1a1830 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Glow de fondo */}
      <div
        style={{
          position: "absolute",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(108,99,255,0.12) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          textAlign: "center",
          padding: "0 160px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 28,
        }}
      >
        <h1
          style={{
            fontSize: 88,
            fontWeight: 800,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
            lineHeight: 1.15,
            margin: 0,
            letterSpacing: "-1px",
          }}
        >
          {title}
        </h1>

        {/* Línea decorativa */}
        <div
          style={{
            width: lineWidth,
            height: 4,
            borderRadius: 2,
            background: "linear-gradient(90deg, #6C63FF, #00D9FF)",
          }}
        />
      </div>

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
