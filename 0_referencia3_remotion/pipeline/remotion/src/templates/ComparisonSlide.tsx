/**
 * ComparisonSlide — Comparación animada: básico vs inteligente
 * Dos columnas que entran desde los costados.
 * Items aparecen uno a uno con stagger.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";

export type ComparisonItem = {
  text: string;
  positive: boolean; // true = check, false = cross
};

export type ComparisonSlideProps = {
  title: string;
  left: {
    label: string;
    color: string;
    items: ComparisonItem[];
  };
  right: {
    label: string;
    color: string;
    items: ComparisonItem[];
  };
  word_cues: WordCue[];
};

// Frames entre cada item de la misma columna
const ITEM_STAGGER = 18;
// La columna derecha empieza después de que la izquierda está lista
const RIGHT_COL_DELAY = 30;

const CheckIcon: React.FC<{ color: string }> = ({ color }) => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="11" fill={`${color}33`} stroke={color} strokeWidth="1.5" />
    <path d="M7 12.5l3.5 3.5 6.5-7" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const CrossIcon: React.FC<{ color: string }> = ({ color }) => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="11" fill="rgba(120,120,120,0.12)" stroke="rgba(150,150,150,0.5)" strokeWidth="1.5" />
    <path d="M8 8l8 8M16 8l-8 8" stroke="rgba(150,150,150,0.6)" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const Column: React.FC<{
  data: ComparisonSlideProps["left"] | ComparisonSlideProps["right"];
  startDelay: number;
  slideFrom: number; // positivo = viene de derecha, negativo = de izquierda
  frame: number;
  fps: number;
}> = ({ data, startDelay, slideFrom, frame, fps }) => {
  const colSpring = spring({
    frame: frame - startDelay,
    fps,
    config: { damping: 22, stiffness: 130 },
    from: slideFrom,
    to: 0,
  });
  const colOpacity = interpolate(frame - startDelay, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        padding: "0 48px",
        transform: `translateX(${colSpring}px)`,
        opacity: colOpacity,
      }}
    >
      {/* Header de columna */}
      <div
        style={{
          background: `${data.color}22`,
          border: `2px solid ${data.color}`,
          borderRadius: 14,
          padding: "18px 28px",
          marginBottom: 32,
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontSize: 32,
            fontWeight: 800,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.04em",
          }}
        >
          {data.label}
        </span>
      </div>

      {/* Items con stagger */}
      {data.items.map((item, idx) => {
        const itemDelay = startDelay + 20 + idx * ITEM_STAGGER;
        const itemSpring = spring({
          frame: frame - itemDelay,
          fps,
          config: { damping: 20, stiffness: 200 },
          from: 0,
          to: 1,
        });
        const itemOp = interpolate(frame - itemDelay, [0, 10], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={idx}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
              marginBottom: 22,
              transform: `scale(${itemSpring})`,
              opacity: itemOp,
              transformOrigin: "left center",
            }}
          >
            {item.positive
              ? <CheckIcon color={data.color} />
              : <CrossIcon color={data.color} />
            }
            <span
              style={{
                fontSize: 28,
                color: item.positive ? "#FFFFFF" : "rgba(255,255,255,0.45)",
                fontFamily: "Inter, system-ui, sans-serif",
                fontWeight: item.positive ? 500 : 400,
                lineHeight: 1.35,
              }}
            >
              {item.text}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────

export const ComparisonSlide: React.FC<ComparisonSlideProps> = ({
  title,
  left,
  right,
  word_cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const dividerH = interpolate(frame, [10, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const rightDelay = 20 + left.items.length * ITEM_STAGGER + RIGHT_COL_DELAY;

  return (
    <AbsoluteFill
      style={{ background: "linear-gradient(135deg, #0a0912 0%, #12112a 100%)" }}
    >
      {/* Título */}
      <div
        style={{
          position: "absolute",
          top: 44,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: titleOp,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 46,
            fontWeight: 700,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
          }}
        >
          {title}
        </h2>
      </div>

      {/* Columnas */}
      <div
        style={{
          position: "absolute",
          top: 130,
          left: 0,
          right: 0,
          bottom: 120,
          display: "flex",
          flexDirection: "row",
          alignItems: "flex-start",
        }}
      >
        <Column
          data={left}
          startDelay={10}
          slideFrom={-120}
          frame={frame}
          fps={fps}
        />

        {/* Línea divisoria */}
        <div
          style={{
            width: 2,
            alignSelf: "stretch",
            background: "rgba(255,255,255,0.1)",
            transform: `scaleY(${dividerH})`,
            transformOrigin: "top center",
          }}
        />

        <Column
          data={right}
          startDelay={rightDelay}
          slideFrom={120}
          frame={frame}
          fps={fps}
        />
      </div>

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
