/**
 * AgentLoop — Diagrama de ciclo animado del agente de IA
 * 4 nodos en diamante: ENTORNO · PERCIBIR · DECIDIR · ACTUAR
 * Flechas que se dibujan solas, badge central pulsante.
 */
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";

export type AgentLoopProps = {
  word_cues: WordCue[];
};

// ── Geometría del diagrama ────────────────────────────────────────────────────
const CX = 960, CY = 500;

const NODES = [
  { label: "ENTORNO",  x: CX,    y: 170, color: "#2d6a9f", delay: 0  },
  { label: "PERCIBIR", x: 1380,  y: CY,  color: "#7c3aed", delay: 18 },
  { label: "DECIDIR",  x: CX,    y: 830, color: "#0e9f6e", delay: 36 },
  { label: "ACTUAR",   x: 540,   y: CY,  color: "#c0522a", delay: 54 },
];

// Control points que curvan los arcos hacia afuera del diamante
const ARROWS = [
  { from: 0, to: 1, cpx: 1380, cpy: 170, label: "señales del entorno",    delay: 24 },
  { from: 1, to: 2, cpx: 1380, cpy: 830, label: "información procesada",  delay: 42 },
  { from: 2, to: 3, cpx: 540,  cpy: 830, label: "acción seleccionada",    delay: 60 },
  { from: 3, to: 0, cpx: 540,  cpy: 170, label: "modifica el entorno",    delay: 78 },
];

const ARC_FRAMES = 22;   // duración de cada arco dibujándose
const CENTER_DELAY = 95; // frame en que aparece el badge central

// ─────────────────────────────────────────────────────────────────────────────

export const AgentLoop: React.FC<AgentLoopProps> = ({ word_cues }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{ background: "linear-gradient(135deg, #0a0912 0%, #12112a 100%)" }}
    >
      {/* ── Título ─────────────────────────────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          top: 40,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: interpolate(frame, [0, 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: 38,
            fontWeight: 600,
            color: "rgba(255,255,255,0.55)",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          ¿Qué es un agente de IA?
        </p>
      </div>

      {/* ── SVG: arcos animados + arrowheads ───────────────────────────────── */}
      <svg
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}
        viewBox="0 0 1920 1080"
      >
        <defs>
          {ARROWS.map((_, i) => (
            <marker
              key={i}
              id={`ah-${i}`}
              markerWidth="9"
              markerHeight="9"
              refX="7"
              refY="3.5"
              orient="auto"
            >
              <path
                d="M 0 0 L 0 7 L 9 3.5 z"
                fill={NODES[ARROWS[i].to].color}
                opacity={0.75}
              />
            </marker>
          ))}
        </defs>

        {ARROWS.map((arrow, i) => {
          const n1 = NODES[arrow.from];
          const n2 = NODES[arrow.to];
          const d = `M ${n1.x} ${n1.y} Q ${arrow.cpx} ${arrow.cpy} ${n2.x} ${n2.y}`;

          const progress = interpolate(
            frame,
            [arrow.delay, arrow.delay + ARC_FRAMES],
            [0, 1],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            }
          );

          // Punto medio del arco cuadrático (t=0.5)
          const t = 0.5;
          const lx = (1 - t) ** 2 * n1.x + 2 * (1 - t) * t * arrow.cpx + t ** 2 * n2.x;
          const ly = (1 - t) ** 2 * n1.y + 2 * (1 - t) * t * arrow.cpy + t ** 2 * n2.y;

          return (
            <g key={i} opacity={progress}>
              <path
                d={d}
                fill="none"
                stroke={`${n1.color}88`}
                strokeWidth={2.5}
                strokeDasharray="1200"
                strokeDashoffset={1200 * (1 - progress)}
                markerEnd={`url(#ah-${i})`}
              />
              {/* Label del arco */}
              <text
                x={lx}
                y={ly - 16}
                textAnchor="middle"
                fill="rgba(255,255,255,0.38)"
                fontSize={20}
                fontFamily="Inter, system-ui, sans-serif"
                fontStyle="italic"
              >
                {arrow.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* ── Nodos ──────────────────────────────────────────────────────────── */}
      {NODES.map((node) => {
        const s = spring({
          frame: frame - node.delay,
          fps,
          config: { damping: 18, stiffness: 220 },
          from: 0,
          to: 1,
        });
        const op = interpolate(frame - node.delay, [0, 8], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={node.label}
            style={{
              position: "absolute",
              left: node.x - 115,
              top: node.y - 48,
              width: 230,
              height: 96,
              background: `${node.color}22`,
              border: `2px solid ${node.color}`,
              borderRadius: 18,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              transform: `scale(${s})`,
              opacity: op,
              boxShadow: `0 0 32px ${node.color}44`,
            }}
          >
            <span
              style={{
                fontSize: 26,
                fontWeight: 800,
                color: "#FFFFFF",
                fontFamily: "Inter, system-ui, sans-serif",
                letterSpacing: "0.1em",
              }}
            >
              {node.label}
            </span>
          </div>
        );
      })}

      {/* ── Badge central pulsante ─────────────────────────────────────────── */}
      {(() => {
        const appear = interpolate(frame, [CENTER_DELAY, CENTER_DELAY + 15], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const pulse = 1 + interpolate(Math.sin((frame / fps) * Math.PI * 1.2), [-1, 1], [-0.03, 0.03]);

        return (
          <div
            style={{
              position: "absolute",
              left: CX - 100,
              top: CY - 44,
              width: 200,
              height: 88,
              background: "rgba(108,99,255,0.22)",
              border: "2px solid rgba(108,99,255,0.85)",
              borderRadius: 44,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              opacity: appear,
              transform: `scale(${pulse})`,
              boxShadow: "0 0 48px rgba(108,99,255,0.45)",
            }}
          >
            <span
              style={{
                fontSize: 22,
                fontWeight: 800,
                color: "#FFFFFF",
                fontFamily: "Inter, system-ui, sans-serif",
                letterSpacing: "0.12em",
              }}
            >
              AGENTE
            </span>
          </div>
        );
      })()}

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
