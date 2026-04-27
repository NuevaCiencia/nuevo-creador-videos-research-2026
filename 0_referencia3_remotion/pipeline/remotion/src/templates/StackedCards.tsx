/**
 * StackedCards — Cartas apiladas en 3D que se abren en abanico
 * CSS perspective + rotateY. Las cartas salen volando hacia su posición.
 * Fondo oscuro con degradado. Impactante para comparar conceptos.
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

export type StackCard = {
  title: string;
  body: string;
  color: string;
  icon: string;
};

export type StackedCardsProps = {
  label: string;
  cards: StackCard[];
};

const CARD_W = 380;
const CARD_H = 480;
const SPREAD = 420;   // px between cards when open
const STAGGER = 10;

export const StackedCards: React.FC<StackedCardsProps> = ({ label, cards }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const N = cards.length;

  // Label entrance
  const labelOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelY  = interpolate(frame, [0, 18], [-20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{
      background: "linear-gradient(160deg, #0a0918 0%, #131130 100%)",
      perspective: "1200px",
    }}>

      {/* Background glow */}
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        width: 900, height: 500,
        transform: "translate(-50%, -50%)",
        background: "radial-gradient(ellipse, rgba(108,99,255,0.10) 0%, transparent 70%)",
        filter: "blur(40px)",
        pointerEvents: "none",
      }} />

      {/* Label top */}
      <div style={{
        position: "absolute", top: 72, left: 0, right: 0,
        textAlign: "center", opacity: labelOp,
        transform: `translateY(${labelY}px)`,
      }}>
        <p style={{
          margin: 0, fontSize: 28, fontWeight: 400,
          color: "rgba(255,255,255,0.4)",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "0.25em",
          textTransform: "uppercase",
        }}>
          {label}
        </p>
      </div>

      {/* Cards container — centered */}
      <div style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        perspective: "1200px",
      }}>
        {cards.map((card, i) => {
          const delay = 8 + i * STAGGER;

          // Final X position: spread evenly around center
          const targetX = (i - (N - 1) / 2) * SPREAD;

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 20, stiffness: 100 }, from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          // Cards start stacked (x=0, rotated) and fan out
          const currentX = targetX * s;
          const rotY = interpolate(s, [0, 1], [i % 2 === 0 ? -35 : 35, 0]);
          const scale = interpolate(s, [0, 1], [0.6, 1]);

          // Floating idle animation per card
          const floatY = Math.sin((frame / fps) * Math.PI * 0.8 + i * 1.2) * 8;

          // Hover tilt
          const idleTilt = Math.sin((frame / fps) * Math.PI * 0.5 + i * 0.7) * 3;

          return (
            <div
              key={i}
              style={{
                position: "absolute",
                width: CARD_W,
                height: CARD_H,
                transform: `translateX(${currentX}px) translateY(${floatY}px) rotateY(${rotY + idleTilt}deg) scale(${scale})`,
                opacity: op,
                transformStyle: "preserve-3d",
              }}
            >
              <div style={{
                width: "100%",
                height: "100%",
                borderRadius: 24,
                background: `linear-gradient(160deg, ${card.color}22 0%, ${card.color}08 100%)`,
                border: `1.5px solid ${card.color}44`,
                boxShadow: `0 24px 80px ${card.color}22, 0 4px 16px rgba(0,0,0,0.4)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 20,
                padding: "40px 32px",
                backdropFilter: "blur(10px)",
              }}>
                {/* Icon */}
                <div style={{
                  fontSize: 64,
                  lineHeight: 1,
                  filter: `drop-shadow(0 0 20px ${card.color}88)`,
                }}>
                  {card.icon}
                </div>

                {/* Title */}
                <h3 style={{
                  margin: 0,
                  fontSize: 36,
                  fontWeight: 800,
                  color: "#FFFFFF",
                  fontFamily: "Inter, system-ui, sans-serif",
                  textAlign: "center",
                  lineHeight: 1.2,
                  letterSpacing: "-0.5px",
                }}>
                  {card.title}
                </h3>

                {/* Divider */}
                <div style={{
                  width: 60, height: 3,
                  background: card.color,
                  borderRadius: 2,
                  boxShadow: `0 0 12px ${card.color}`,
                }} />

                {/* Body */}
                <p style={{
                  margin: 0,
                  fontSize: 20,
                  color: "rgba(255,255,255,0.55)",
                  fontFamily: "Inter, system-ui, sans-serif",
                  textAlign: "center",
                  lineHeight: 1.6,
                }}>
                  {card.body}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
