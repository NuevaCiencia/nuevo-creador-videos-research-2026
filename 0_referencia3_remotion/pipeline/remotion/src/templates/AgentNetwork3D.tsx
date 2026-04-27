/**
 * AgentNetwork3D — Red de agentes en 3D real (Three.js via @remotion/three)
 * Esferas flotando en espacio 3D conectadas por líneas.
 * La cámara orbita lentamente alrededor.
 */
import React, { useRef } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Subtitles, WordCue } from "../components/Subtitles";

export type AgentNetwork3DProps = {
  word_cues: WordCue[];
};

// ── Nodos de la red (posiciones fijas en 3D) ──────────────────────────────────
const NODES = [
  { pos: [ 0,    0,    0  ], color: "#6C63FF", size: 0.5, label: "AGENTE" },
  { pos: [ 3,    1.5,  1  ], color: "#00D9FF", size: 0.3 },
  { pos: [-2.5,  1,   -1  ], color: "#00D9FF", size: 0.3 },
  { pos: [ 1,   -2,    2  ], color: "#10b981", size: 0.28 },
  { pos: [-1.5, -1.5, -2  ], color: "#10b981", size: 0.28 },
  { pos: [ 2.5, -1,    -1.5], color: "#f59e0b", size: 0.25 },
  { pos: [-3,    0.5,  1.5 ], color: "#f59e0b", size: 0.25 },
  { pos: [ 0.5,  3,   -0.5 ], color: "#ec4899", size: 0.22 },
  { pos: [-2,   -2.5,  0.5 ], color: "#ec4899", size: 0.22 },
];

// Aristas entre nodos (índices)
const EDGES = [
  [0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[0,8],
  [1,2],[2,6],[3,5],[4,8],[5,7],[6,7],
];

// ── Escena Three.js ───────────────────────────────────────────────────────────

const Scene: React.FC<{ frame: number; fps: number }> = ({ frame, fps }) => {
  const t = frame / fps;

  // Posición de la cámara en órbita
  const camAngle = t * 0.35; // rad/s
  const camR = 8;
  const camX = Math.sin(camAngle) * camR;
  const camZ = Math.cos(camAngle) * camR;
  const camY = Math.sin(t * 0.18) * 1.5;

  // Pulsación de los nodos
  const pulse = 1 + Math.sin(t * Math.PI * 1.2) * 0.07;

  return (
    <>
      {/* Cámara en órbita */}
      <perspectiveCamera
        position={[camX, camY, camZ]}
        fov={55}
        near={0.1}
        far={100}
      />

      {/* Iluminación */}
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={1.2} color="#6C63FF" />
      <pointLight position={[-5, -3, -3]} intensity={0.8} color="#00D9FF" />

      {/* Fondo estrellado */}
      {Array.from({ length: 120 }, (_, i) => {
        const theta = (i / 120) * Math.PI * 2;
        const phi   = Math.acos(1 - 2 * ((i * 0.618033) % 1));
        const r     = 18;
        return (
          <mesh
            key={i}
            position={[
              r * Math.sin(phi) * Math.cos(theta),
              r * Math.sin(phi) * Math.sin(theta),
              r * Math.cos(phi),
            ]}
          >
            <sphereGeometry args={[0.04, 4, 4]} />
            <meshBasicMaterial color="white" opacity={0.4} transparent />
          </mesh>
        );
      })}

      {/* Aristas */}
      {EDGES.map(([i, j], idx) => {
        const a = NODES[i].pos as [number, number, number];
        const b = NODES[j].pos as [number, number, number];
        const mid: [number,number,number] = [
          (a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2,
        ];
        const dx = b[0]-a[0], dy = b[1]-a[1], dz = b[2]-a[2];
        const len = Math.sqrt(dx*dx + dy*dy + dz*dz);

        return (
          <mesh key={idx} position={mid}>
            <cylinderGeometry args={[0.012, 0.012, len, 6]} />
            <meshBasicMaterial color="#6C63FF" opacity={0.35} transparent />
          </mesh>
        );
      })}

      {/* Nodos */}
      {NODES.map((node, i) => {
        const isCenter = i === 0;
        const size = node.size * (isCenter ? pulse : 1);
        return (
          <mesh key={i} position={node.pos as [number, number, number]}>
            <sphereGeometry args={[size, 32, 32]} />
            <meshStandardMaterial
              color={node.color}
              emissive={node.color}
              emissiveIntensity={isCenter ? 0.6 : 0.3}
              roughness={0.2}
              metalness={0.5}
            />
          </mesh>
        );
      })}
    </>
  );
};

// ── Componente principal ──────────────────────────────────────────────────────

export const AgentNetwork3D: React.FC<AgentNetwork3DProps> = ({ word_cues }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const titleOp = interpolate(frame, [20, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "#06040f", opacity: fadeIn }}>
      {/* Canvas Three.js */}
      <ThreeCanvas
        width={width}
        height={height}
        frameLoop="always"
        camera={{ position: [0, 0, 8], fov: 55 }}
      >
        <Scene frame={frame} fps={fps} />
      </ThreeCanvas>

      {/* Overlay de texto */}
      <div
        style={{
          position: "absolute",
          bottom: 160,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: titleOp,
          pointerEvents: "none",
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: 38,
            fontWeight: 700,
            color: "rgba(255,255,255,0.75)",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            textShadow: "0 0 40px rgba(108,99,255,0.5)",
          }}
        >
          Habilidad Social — Red de Agentes
        </p>
      </div>

      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
