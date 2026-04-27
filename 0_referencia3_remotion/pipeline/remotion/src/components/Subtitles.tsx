import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

export type WordCue = {
  word: string;
  t_start: number; // segundos locales (relativos al inicio de la pantalla)
  t_end: number;
};

type SubtitlesProps = {
  word_cues: WordCue[];
};

/**
 * Muestra los últimos N fragmentos de audio como subtítulos karaoke.
 * La frase activa aparece en blanco; las anteriores en gris.
 */
export const Subtitles: React.FC<SubtitlesProps> = ({ word_cues }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;

  // Índice del último cue ya iniciado
  const lastIdx = [...word_cues]
    .reverse()
    .findIndex((c) => c.t_start <= now);
  const spokenIdx =
    lastIdx === -1 ? -1 : word_cues.length - 1 - lastIdx;

  if (spokenIdx < 0) return null;

  // Ventana deslizante: hasta 8 fragmentos visibles
  const windowStart = Math.max(0, spokenIdx - 7);
  const visible = word_cues.slice(windowStart, spokenIdx + 1);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 52,
        left: 80,
        right: 80,
        display: "flex",
        flexWrap: "wrap",
        gap: "0 10px",
        justifyContent: "center",
        alignItems: "flex-end",
        pointerEvents: "none",
      }}
    >
      {visible.map((cue, idx) => {
        const isActive = now >= cue.t_start && now < cue.t_end;
        const globalIdx = windowStart + idx;
        return (
          <span
            key={globalIdx}
            style={{
              fontSize: 34,
              lineHeight: 1.4,
              fontWeight: isActive ? 700 : 400,
              color: isActive ? "#FFFFFF" : "rgba(255,255,255,0.38)",
              fontFamily: "Inter, system-ui, sans-serif",
              textShadow: isActive
                ? "0 2px 12px rgba(0,0,0,0.9)"
                : "0 1px 4px rgba(0,0,0,0.6)",
              transition: "color 0.08s ease",
            }}
          >
            {cue.word}
          </span>
        );
      })}
    </div>
  );
};
