/**
 * RotatingCube3D — Cubo 3D con CSS perspective que gira mostrando conceptos
 * Cada cara del cubo tiene un concepto del guion.
 * CSS transform-style: preserve-3d, rotación basada en frame.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
export type CubeFace = {
  title: string;
  subtitle?: string;
  color: string;
  textColor?: string;
};

export type RotatingCube3DProps = {
  faces: [CubeFace, CubeFace, CubeFace, CubeFace, CubeFace, CubeFace]; // exactamente 6
  label?: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "radial-gradient(ellipse at 50% 45%, #14122a 0%, #060410 80%)",
  fontFamily:  "Inter, system-ui, sans-serif",

  cubeSize:    500,   // px de cada cara del cubo
  perspective: 1100,  // perspectiva CSS 3D

  rotSpeed:    28,    // grados por segundo en Y
  wobbleAmp:   22,    // amplitud del balanceo en X (grados)

  faceTitleSize:   60,
  faceTitleWeight: 900,
  faceSubSize:     32,

  labelSize:   32,
  labelColor:  "rgba(255,255,255,0.4)",
  labelTracking: "0.14em",

  faceRadius:  12,
  faceStagger: 8,    // frames entre aparición de caras
};
// ─────────────────────────────────────────────────────────────────────────────

const SIZE = CONFIG.cubeSize;

const Face: React.FC<{
  transform: string;
  face: CubeFace;
  size: number;
  frame: number;
  fps: number;
  delay: number;
}> = ({ transform, face, size, frame, fps, delay }) => {
  const op = interpolate(frame - delay, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        width: size,
        height: size,
        transform,
        background: `linear-gradient(135deg, ${face.color}dd 0%, ${face.color}88 100%)`,
        border: `2px solid ${face.color}`,
        borderRadius: 12,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: 12,
        backfaceVisibility: "hidden",
        boxShadow: `inset 0 0 60px rgba(0,0,0,0.4), 0 0 30px ${face.color}44`,
        opacity: op,
        backdropFilter: "blur(2px)",
      }}
    >
      <h2
        style={{
          margin: 0,
          fontSize: CONFIG.faceTitleSize,
          fontWeight: CONFIG.faceTitleWeight,
          color: face.textColor ?? "#FFFFFF",
          fontFamily: CONFIG.fontFamily,
          letterSpacing: "0.04em",
          textAlign: "center",
          padding: "0 24px",
          textShadow: `0 2px 20px rgba(0,0,0,0.6)`,
          lineHeight: 1.2,
        }}
      >
        {face.title}
      </h2>
      {face.subtitle && (
        <p
          style={{
            margin: 0,
            fontSize: CONFIG.faceSubSize,
            color: "rgba(255,255,255,0.65)",
            fontFamily: "Inter, system-ui, sans-serif",
            textAlign: "center",
            padding: "0 20px",
          }}
        >
          {face.subtitle}
        </p>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────

export const RotatingCube3D: React.FC<RotatingCube3DProps> = ({
  faces,
  label = "Las 4 propiedades — Wooldridge",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const half = SIZE / 2;

  // Entrada: el cubo arranca pequeño y crece
  const scaleIn = spring({
    frame,
    fps,
    config: { damping: 22, stiffness: 100 },
    from: 0.2,
    to: 1,
  });

  // Rotaciones continuas
  const ry = (frame / fps) * 28;                          // 28°/s en Y
  const rx = Math.sin((frame / fps) * 0.45) * 22 - 10;   // oscilación en X

  const labelOp = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Transforms de cada cara del cubo
  const faceTransforms = [
    `rotateY(0deg)   translateZ(${half}px)`,   // frente
    `rotateY(180deg) translateZ(${half}px)`,   // atrás
    `rotateY(-90deg) translateZ(${half}px)`,   // izquierda
    `rotateY(90deg)  translateZ(${half}px)`,   // derecha
    `rotateX(90deg)  translateZ(${half}px)`,   // arriba
    `rotateX(-90deg) translateZ(${half}px)`,   // abajo
  ];

  return (
    <AbsoluteFill
      style={{
        background: CONFIG.bg,
      }}
    >
      {/* Label */}
      <div
        style={{
          position: "absolute",
          top: 48,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: labelOp,
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: CONFIG.labelSize,
            fontWeight: 400,
            color: CONFIG.labelColor,
            fontFamily: CONFIG.fontFamily,
            letterSpacing: CONFIG.labelTracking,
            textTransform: "uppercase",
          }}
        >
          {label}
        </p>
      </div>

      {/* Perspectiva CSS 3D */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          perspective: 1100,
          perspectiveOrigin: "50% 48%",
        }}
      >
        {/* Contenedor del cubo */}
        <div
          style={{
            width: SIZE,
            height: SIZE,
            position: "relative",
            transformStyle: "preserve-3d",
            transform: `scale3d(${scaleIn}, ${scaleIn}, ${scaleIn}) rotateX(${rx}deg) rotateY(${ry}deg)`,
          }}
        >
          {faceTransforms.map((t, i) => (
            <Face
              key={i}
              transform={t}
              face={faces[i]}
              size={SIZE}
              frame={frame}
              fps={fps}
              delay={i * 8}
            />
          ))}
        </div>
      </div>

      {/* Sombra proyectada en el suelo */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 130,
          width: SIZE * 1.2,
          height: 30,
          transform: "translateX(-50%)",
          background: "radial-gradient(ellipse, rgba(0,0,0,0.5) 0%, transparent 70%)",
          filter: "blur(12px)",
          opacity: scaleIn * 0.6,
        }}
      />

    </AbsoluteFill>
  );
};
