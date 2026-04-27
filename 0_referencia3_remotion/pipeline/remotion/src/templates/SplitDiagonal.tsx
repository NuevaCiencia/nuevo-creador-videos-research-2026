/**
 * SplitDiagonal — Pantalla dividida en diagonal con clip-path
 * Mitad oscura (izq) con texto grande, mitad clara (der) con datos.
 * La diagonal se "abre" animada desde el centro.
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

export type SplitSide = {
  label: string;
  value: string;
  sub: string;
};

export type SplitDiagonalProps = {
  leftTitle: string;
  leftSub: string;
  accent: string;
  items: SplitSide[];
};

export const SplitDiagonal: React.FC<SplitDiagonalProps> = ({
  leftTitle,
  leftSub,
  accent,
  items,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // The diagonal split opens: clipPath goes from center to full
  const splitProgress = interpolate(frame, [0, 35], [50, 60], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Left side content
  const leftOp = interpolate(frame, [5, 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const leftX = interpolate(frame, [5, 28], [-40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Right side items stagger
  const STAGGER = 18;

  // Decorative line on the diagonal
  const lineOp = interpolate(frame, [30, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>

      {/* LEFT dark panel */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(160deg, #0c0b20 0%, #1a1640 100%)`,
          clipPath: `polygon(0 0, ${splitProgress}% 0, ${splitProgress - 12}% 100%, 0 100%)`,
        }}
      />

      {/* RIGHT light panel */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(160deg, #F0F4FF 0%, #E8EEF8 100%)",
          clipPath: `polygon(${splitProgress}% 0, 100% 0, 100% 100%, ${splitProgress - 12}% 100%)`,
        }}
      />

      {/* Diagonal accent stripe */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: `polygon(${splitProgress - 1}% 0, ${splitProgress + 1}% 0, ${splitProgress - 11}% 100%, ${splitProgress - 13}% 100%)`,
          background: accent,
          opacity: lineOp,
        }}
      />

      {/* LEFT content */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: `${splitProgress - 4}%`,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 80px",
          opacity: leftOp,
          transform: `translateX(${leftX}px)`,
        }}
      >
        <div
          style={{
            width: 60,
            height: 5,
            background: accent,
            borderRadius: 3,
            marginBottom: 28,
          }}
        />
        <h1
          style={{
            margin: 0,
            fontSize: 84,
            fontWeight: 900,
            color: "#FFFFFF",
            fontFamily: "Inter, system-ui, sans-serif",
            lineHeight: 1.0,
            letterSpacing: "-2px",
          }}
        >
          {leftTitle}
        </h1>
        <p
          style={{
            margin: "22px 0 0",
            fontSize: 28,
            fontWeight: 300,
            color: "rgba(255,255,255,0.55)",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.05em",
            lineHeight: 1.5,
          }}
        >
          {leftSub}
        </p>
      </div>

      {/* RIGHT content — items list */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: `${splitProgress + 2}%`,
          right: 0,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 72px 0 48px",
          gap: 32,
        }}
      >
        {items.map((item, i) => {
          const delay = 25 + i * STAGGER;
          const s = spring({
            frame: frame - delay,
            fps,
            config: { damping: 22, stiffness: 160 },
            from: 0,
            to: 1,
          });
          const op = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={i}
              style={{
                opacity: op,
                transform: `translateX(${(1 - s) * 50}px)`,
                background: "#FFFFFF",
                borderRadius: 16,
                padding: "24px 32px",
                borderLeft: `5px solid ${accent}`,
                boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                gap: 28,
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: accent,
                  fontFamily: "Inter, system-ui, sans-serif",
                  minWidth: 80,
                  textAlign: "right",
                  lineHeight: 1,
                }}
              >
                {item.value}
              </div>
              <div>
                <div
                  style={{
                    fontSize: 24,
                    fontWeight: 700,
                    color: "#111827",
                    fontFamily: "Inter, system-ui, sans-serif",
                  }}
                >
                  {item.label}
                </div>
                <div
                  style={{
                    fontSize: 18,
                    color: "#6B7280",
                    fontFamily: "Inter, system-ui, sans-serif",
                    marginTop: 4,
                  }}
                >
                  {item.sub}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
