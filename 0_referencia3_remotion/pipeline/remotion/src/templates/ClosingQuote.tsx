import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:              "linear-gradient(135deg, #1E1B4B 0%, #4338CA 50%, #0EA5E9 100%)",
  fontFamily:      "Inter, system-ui, sans-serif",

  quoteSize:       68,
  quoteColor:      "#FFFFFF",
  quoteWeight:     700,
  lineHeight:      1.3,

  authorSize:      28,
  authorColor:     "rgba(255,255,255,0.6)",
  authorWeight:    400,

  accentColor:     "rgba(255,255,255,0.08)",
  quoteMarkColor:  "rgba(255,255,255,0.12)",
  quoteMarkSize:   320,

  wordInterval:    6,
};
// ─────────────────────────────────────────────────────────────────────────────

export type ClosingQuoteProps = {
  quote:   string;
  author?: string;
};

export const ClosingQuote: React.FC<ClosingQuoteProps> = ({ quote, author }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = quote.split(" ");

  // Comilla decorativa
  const quoteMarkOpacity = interpolate(frame, [0, 25], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Línea decorativa superior
  const lineWidth = interpolate(frame, [0, 22], [0, 80], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Autor
  const authorDelay   = words.length * CONFIG.wordInterval + 12;
  const authorOpacity = interpolate(frame, [authorDelay, authorDelay + 20], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const authorY = spring({
    frame: frame - authorDelay,
    fps,
    config: { damping: 24, stiffness: 120 },
    from: 12,
    to: 0,
  });

  return (
    <AbsoluteFill
      style={{
        background:     CONFIG.bg,
        justifyContent: "center",
        alignItems:     "center",
        padding:        "0 200px",
        flexDirection:  "column",
      }}
    >
      {/* Comilla gigante decorativa — fondo */}
      <div
        style={{
          position:   "absolute",
          top:        -40,
          left:       120,
          fontSize:   CONFIG.quoteMarkSize,
          fontFamily: CONFIG.fontFamily,
          fontWeight: 900,
          color:      CONFIG.quoteMarkColor,
          opacity:    quoteMarkOpacity,
          lineHeight: 1,
          userSelect: "none",
        }}
      >
        "
      </div>

      {/* Línea de acento superior */}
      <div
        style={{
          width:        lineWidth,
          height:       4,
          borderRadius: 4,
          background:   "rgba(255,255,255,0.5)",
          marginBottom: 48,
          alignSelf:    "center",
        }}
      />

      {/* Frase palabra por palabra */}
      <p
        style={{
          fontSize:     CONFIG.quoteSize,
          fontWeight:   CONFIG.quoteWeight,
          fontFamily:   CONFIG.fontFamily,
          color:        CONFIG.quoteColor,
          lineHeight:   CONFIG.lineHeight,
          textAlign:    "center",
          margin:       0,
          marginBottom: author ? 52 : 0,
        }}
      >
        {words.map((word, i) => {
          const delay   = i * CONFIG.wordInterval;
          const opacity = interpolate(frame, [delay, delay + 10], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const y = interpolate(frame, [delay, delay + 10], [10, 0], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          return (
            <span
              key={i}
              style={{
                display:     "inline-block",
                opacity,
                transform:   `translateY(${y}px)`,
                marginRight: "0.25em",
              }}
            >
              {word}
            </span>
          );
        })}
      </p>

      {/* Autor */}
      {author && (
        <p
          style={{
            opacity:       authorOpacity,
            transform:     `translateY(${authorY}px)`,
            fontSize:      CONFIG.authorSize,
            fontWeight:    CONFIG.authorWeight,
            color:         CONFIG.authorColor,
            fontFamily:    CONFIG.fontFamily,
            letterSpacing: "0.08em",
            textAlign:     "center",
            margin:        0,
          }}
        >
          — {author}
        </p>
      )}
    </AbsoluteFill>
  );
};
