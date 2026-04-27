/**
 * TorusKnot3D — Nudo toroidal 3D con Three.js + @remotion/three
 * Sin @react-three/drei — compatible con React 18.2
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";

export type TorusKnot3DProps = {
  title: string;
  subtitle?: string;
  colorA: string;
  colorB: string;
};

function CameraSetup() {
  const { camera } = useThree();
  camera.position.set(0, 0, 9);
  (camera as THREE.PerspectiveCamera).fov = 50;
  (camera as THREE.PerspectiveCamera).updateProjectionMatrix();
  return null;
}

function KnotScene({ frame, fps, colorA, colorB }: {
  frame: number; fps: number; colorA: string; colorB: string;
}) {
  const t = frame / fps;
  const scale = 1 + Math.sin(t * Math.PI * 1.4) * 0.06;
  const cA = new THREE.Color(colorA);
  const cB = new THREE.Color(colorB);
  const lerped  = cA.clone().lerp(cB, (Math.sin(t * 0.8) + 1) / 2);
  const emissive = lerped.clone().multiplyScalar(0.35);

  return (
    <>
      <CameraSetup />
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={2.0} color={colorA} />
      <pointLight position={[-5, -5, 3]} intensity={1.5} color={colorB} />

      <mesh rotation={[t * 0.4, t * 0.7, t * 0.25]} scale={[scale, scale, scale]}>
        <torusKnotGeometry args={[2, 0.55, 200, 32, 2, 3]} />
        <meshStandardMaterial color={lerped} emissive={emissive} roughness={0.25} metalness={0.7} />
      </mesh>

      <mesh rotation={[t * 0.4, t * 0.7, t * 0.25]} scale={[scale * 1.01, scale * 1.01, scale * 1.01]}>
        <torusKnotGeometry args={[2, 0.57, 80, 16, 2, 3]} />
        <meshBasicMaterial color={colorA} wireframe transparent opacity={0.10} />
      </mesh>
    </>
  );
}

export const TorusKnot3D: React.FC<TorusKnot3DProps> = ({ title, subtitle, colorA, colorB }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subOp   = interpolate(frame, [18, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#000000" }}>
      <ThreeCanvas width={1920} height={1080}>
        <KnotScene frame={frame} fps={fps} colorA={colorA} colorB={colorB} />
      </ThreeCanvas>

      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse at center, transparent 35%, rgba(0,0,0,0.75) 100%)",
        pointerEvents: "none",
      }} />

      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "flex-end",
        paddingBottom: 100, gap: 14,
      }}>
        <h1 style={{
          margin: 0, fontSize: 72, fontWeight: 900, color: "#FFFFFF",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "-1.5px", textAlign: "center",
          textShadow: `0 0 60px ${colorA}88`, opacity: titleOp,
        }}>{title}</h1>
        {subtitle && (
          <p style={{
            margin: 0, fontSize: 26, fontWeight: 300,
            color: "rgba(255,255,255,0.45)",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: "0.2em", textTransform: "uppercase", opacity: subOp,
          }}>{subtitle}</p>
        )}
      </div>
    </AbsoluteFill>
  );
};
