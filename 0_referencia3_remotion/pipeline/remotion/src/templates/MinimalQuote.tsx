/**
 * MinimalQuote — Cita editorial, tipografía grande, fondo blanco
 * La comilla gigante entra primero, luego el texto palabra a palabra.
 * Minimalismo editorial. Perfecto para definiciones o frases clave.
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

export type MinimalQuoteProps = {
  quote: string;
  author: string;
  source?: string;
  accent: string;
};

export const MinimalQuote: React.FC<MinimalQuoteProps> = ({
  quote,
  author,
  source,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Giant quote mark drops in
  const quoteScale = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 80 },
    from: 0,
    to: 1,
  });
  const quoteOp = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Words reveal one by one
  const words = quote.split(" ");
  const charsPerFrame = 1.4;
  let charCount = 0;

  // Author line
  const authorOp = interpolate(frame, [55, 75], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const authorX = interpolate(frame, [55, 75], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Accent bar grows
  const barWidth = interpolate(frame, [50, 80], [0, 180], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ background: "#FAFAFA" }}>

      {/* Subtle grid lines */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px)
          `,
          backgroundSize: "80px 80px",
          pointerEvents: "none",
        }}
      />

      {/* Accent corner block */}
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: 280,
          height: 280,
          background: accent,
          opacity: 0.08,
          borderBottomLeftRadius: "100%",
          pointerEvents: "none",
        }}
      />

      {/* Giant quote mark */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 80,
          fontSize: 280,
          fontWeight: 900,
          color: accent,
          fontFamily: "Georgia, serif",
          lineHeight: 1,
          opacity: quoteOp * 0.15,
          transform: `scale(${quoteScale})`,
          transformOrigin: "top left",
          userSelect: "none",
        }}
      >
        "
      </div>

      {/* Quote text — word by word */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: 0,
          right: 0,
          transform: "translateY(-55%)",
          padding: "0 140px",
          textAlign: "center",
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: 72,
            fontWeight: 700,
            color: "#111827",
            fontFamily: "Inter, system-ui, sans-serif",
            lineHeight: 1.25,
            letterSpacing: "-1px",
          }}
        >
          {words.map((word, i) => {
            const wordStart = charCount + 8; // offset after quote mark entrance
            charCount += word.length + 1;
            const wordEnd = wordStart + 8;
            const wOp = interpolate(frame, [wordStart, wordEnd], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const wY = interpolate(frame, [wordStart, wordEnd], [12, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            });
            return (
              <span
                key={i}
                style={{
                  opacity: wOp,
                  display: "inline-block",
                  transform: `translateY(${wY}px)`,
                  marginRight: "0.28em",
                }}
              >
                {word}
              </span>
            );
          })}
        </p>
      </div>

      {/* Author + accent bar */}
      <div
        style={{
          position: "absolute",
          bottom: 100,
          left: 140,
          display: "flex",
          flexDirection: "column",
          gap: 14,
          opacity: authorOp,
          transform: `translateX(${authorX}px)`,
        }}
      >
        <div
          style={{
            width: barWidth,
            height: 4,
            background: accent,
            borderRadius: 2,
          }}
        />
        <div
          style={{
            fontSize: 28,
            fontWeight: 700,
            color: "#111827",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.05em",
          }}
        >
          {author}
        </div>
        {source && (
          <div
            style={{
              fontSize: 20,
              color: "#9CA3AF",
              fontFamily: "Inter, system-ui, sans-serif",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            {source}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
