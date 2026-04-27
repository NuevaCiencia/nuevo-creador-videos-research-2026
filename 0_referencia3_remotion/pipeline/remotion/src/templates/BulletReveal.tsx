/**
 * BulletReveal — Lista de puntos que aparecen uno a uno
 * Cada item slide-in desde la izquierda con spring.
 * El item activo se resalta con barra de color lateral.
 * Útil para: propiedades individuales de Wooldridge.
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

export type BulletItem = {
  text: string;
  t_trigger: number; // segundos desde el inicio de la pantalla
};

export type BulletRevealProps = {
  title: string;
  subtitle?: string;
  accent: string;       // color del tema
  items: BulletItem[];
  word_cues: WordCue[];
};

const ITEM_ENTER_FRAMES = 20;

export const BulletReveal: React.FC<BulletRevealProps> = ({
  title,
  subtitle,
  accent,
  items,
  word_cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 16], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 16], [-20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Línea decorativa bajo el título
  const lineW = interpolate(frame, [12, 40], [0, 280], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const currentTime = frame / fps;

  // Índice del último item cuyo trigger ya pasó
  const activeIdx = items.reduce<number>((acc, item, i) => {
    return item.t_trigger <= currentTime ? i : acc;
  }, -1);

  return (
    <AbsoluteFill
      style={{ background: "linear-gradient(135deg, #0a0912 0%, #12112a 100%)" }}
    >
      {/* Barra lateral de acento */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 6,
          background: `linear-gradient(180deg, ${accent} 0%, ${accent}44 100%)`,
        }}
      />

      {/* Título */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          opacity: titleOp,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 72,
            fontWeight: 800,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
            lineHeight: 1.1,
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              margin: "12px 0 0",
              fontSize: 32,
              color: "rgba(255,255,255,0.5)",
              fontFamily: "Inter, system-ui, sans-serif",
              fontWeight: 400,
            }}
          >
            {subtitle}
          </p>
        )}
        {/* Línea decorativa */}
        <div
          style={{
            marginTop: 18,
            height: 4,
            width: lineW,
            borderRadius: 2,
            background: `linear-gradient(90deg, ${accent}, ${accent}44)`,
          }}
        />
      </div>

      {/* Lista de items */}
      <div
        style={{
          position: "absolute",
          top: 280,
          left: 80,
          right: 80,
          bottom: 130,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 20,
        }}
      >
        {items.map((item, i) => {
          const triggerFrame = item.t_trigger * fps;
          const localFrame = frame - triggerFrame;

          const s = spring({
            frame: localFrame,
            fps,
            config: { damping: 18, stiffness: 160 },
            from: 0,
            to: 1,
          });
          const op = interpolate(localFrame, [0, ITEM_ENTER_FRAMES], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const x = interpolate(localFrame, [0, ITEM_ENTER_FRAMES], [-40, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          const isActive = i === activeIdx;
          const isPast   = i < activeIdx;

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                opacity: op,
                transform: `translateX(${x}px) scale(${s})`,
                transformOrigin: "left center",
              }}
            >
              {/* Barra lateral del item */}
              <div
                style={{
                  width: 5,
                  height: 44,
                  borderRadius: 3,
                  background: isActive
                    ? accent
                    : isPast
                      ? `${accent}44`
                      : "rgba(255,255,255,0.12)",
                  flexShrink: 0,
                  transition: "background 0.2s",
                }}
              />

              {/* Texto */}
              <span
                style={{
                  fontSize: 36,
                  fontWeight: isActive ? 700 : 400,
                  color: isActive
                    ? "#FFFFFF"
                    : isPast
                      ? "rgba(255,255,255,0.5)"
                      : "rgba(255,255,255,0.75)",
                  fontFamily: "Inter, system-ui, sans-serif",
                  lineHeight: 1.35,
                  transition: "color 0.15s",
                }}
              >
                {item.text}
              </span>
            </div>
          );
        })}
      </div>

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
