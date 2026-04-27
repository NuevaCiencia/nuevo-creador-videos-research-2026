/**
 * ProcessFlow — Pasos de un proceso con flechas, fondo CLARO
 * Pasos que entran desde abajo con spring, flechas que se dibujan.
 * Perfecto para explicar flujos (ej: cómo toma decisiones un agente).
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type FlowStep = {
  number: string;
  title: string;
  description: string;
  color: string;
};

export type ProcessFlowProps = {
  title: string;
  subtitle?: string;
  steps: FlowStep[];
};

const STEP_STAGGER = 22;

export const ProcessFlow: React.FC<ProcessFlowProps> = ({
  title,
  subtitle,
  steps,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOp = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const headerY = interpolate(frame, [0, 18], [-20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const N = steps.length;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #EEF2FF 0%, #F0FDF4 100%)" }}>

      {/* Header */}
      <div style={{
        position: "absolute", top: 72, left: 0, right: 0,
        textAlign: "center",
        opacity: headerOp,
        transform: `translateY(${headerY}px)`,
      }}>
        <h1 style={{
          margin: 0, fontSize: 58, fontWeight: 800,
          color: "#1E1B4B",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "-0.5px",
        }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{
            margin: "10px 0 0", fontSize: 26,
            color: "#6366F1",
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 500,
          }}>
            {subtitle}
          </p>
        )}
      </div>

      {/* Pasos */}
      <div style={{
        position: "absolute",
        top: 230, left: 60, right: 60, bottom: 60,
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: 0,
      }}>
        {steps.map((step, i) => {
          const delay = 15 + i * STEP_STAGGER;

          const s = spring({
            frame: frame - delay, fps,
            config: { damping: 22, stiffness: 180 },
            from: 0, to: 1,
          });
          const op = interpolate(frame - delay, [0, 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          // Flecha entre pasos
          const arrowDelay = delay + 12;
          const arrowProgress = interpolate(frame - arrowDelay, [0, 14], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <React.Fragment key={i}>
              {/* Tarjeta del paso */}
              <div style={{
                flex: 1,
                background: "#FFFFFF",
                borderRadius: 20,
                padding: "36px 28px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 14,
                transform: `scale(${s}) translateY(${(1 - s) * 40}px)`,
                opacity: op,
                boxShadow: `0 8px 40px ${step.color}22, 0 2px 8px rgba(0,0,0,0.06)`,
                borderBottom: `4px solid ${step.color}`,
                position: "relative",
              }}>
                {/* Número */}
                <div style={{
                  width: 60, height: 60, borderRadius: "50%",
                  background: step.color,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  fontSize: 28, fontWeight: 900,
                  color: "#FFFFFF",
                  fontFamily: "Inter, system-ui, sans-serif",
                  boxShadow: `0 4px 16px ${step.color}55`,
                }}>
                  {step.number}
                </div>

                {/* Título */}
                <h3 style={{
                  margin: 0, fontSize: 28, fontWeight: 800,
                  color: "#111827",
                  fontFamily: "Inter, system-ui, sans-serif",
                  textAlign: "center",
                  lineHeight: 1.2,
                }}>
                  {step.title}
                </h3>

                {/* Descripción */}
                <p style={{
                  margin: 0, fontSize: 20,
                  color: "#6B7280",
                  fontFamily: "Inter, system-ui, sans-serif",
                  textAlign: "center",
                  lineHeight: 1.5,
                }}>
                  {step.description}
                </p>
              </div>

              {/* Flecha entre pasos */}
              {i < N - 1 && (
                <div style={{
                  width: 56,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  flexShrink: 0,
                  opacity: arrowProgress,
                }}>
                  <svg width="48" height="24" viewBox="0 0 48 24">
                    <line
                      x1={0} y1={12}
                      x2={40 * arrowProgress} y2={12}
                      stroke={steps[i].color}
                      strokeWidth={2.5}
                      strokeLinecap="round"
                    />
                    {arrowProgress > 0.8 && (
                      <path
                        d="M36 6 L44 12 L36 18"
                        stroke={steps[i].color}
                        strokeWidth={2.5}
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    )}
                  </svg>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
