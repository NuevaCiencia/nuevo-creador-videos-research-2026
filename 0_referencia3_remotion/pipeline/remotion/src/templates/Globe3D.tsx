/**
 * Globe3D — Globo 3D wireframe con Three.js + @remotion/three
 * Sin @react-three/drei para compatibilidad con React 18.2
 */
import React, { useRef } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree, useFrame } from "@react-three/fiber";
import * as THREE from "three";

export type Globe3DProps = {
  title: string;
  subtitle?: string;
  accent: string;
};

const GLOBE_R = 2.6;
const POINTS  = 60;

const positions = new Float32Array(POINTS * 3);
for (let i = 0; i < POINTS; i++) {
  const phi   = Math.acos(1 - 2 * (i + 0.5) / POINTS);
  const theta = Math.PI * (1 + Math.sqrt(5)) * i;
  positions[i * 3]     = Math.sin(phi) * Math.cos(theta) * GLOBE_R;
  positions[i * 3 + 1] = Math.sin(phi) * Math.sin(theta) * GLOBE_R;
  positions[i * 3 + 2] = Math.cos(phi) * GLOBE_R;
}
const pointGeo = new THREE.BufferGeometry();
pointGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));

function CameraSetup() {
  const { camera } = useThree();
  camera.position.set(0, 0, 8);
  (camera as THREE.PerspectiveCamera).fov = 45;
  (camera as THREE.PerspectiveCamera).updateProjectionMatrix();
  return null;
}

function GlobeScene({ frame, fps, accent }: { frame: number; fps: number; accent: string }) {
  const t = frame / fps;
  const accentColor = new THREE.Color(accent);
  const wireColor   = accentColor.clone().multiplyScalar(0.4);
  const ringColor   = accentColor.clone().multiplyScalar(0.6);

  return (
    <>
      <CameraSetup />
      <ambientLight intensity={0.4} />
      <pointLight position={[8, 8, 8]} intensity={1.5} color={accent} />

      <group rotation={[Math.sin(t * 0.3) * 0.15, t * 0.5, 0]}>
        <mesh>
          <sphereGeometry args={[GLOBE_R, 24, 16]} />
          <meshBasicMaterial color={wireColor} wireframe transparent opacity={0.35} />
        </mesh>
        <mesh>
          <sphereGeometry args={[GLOBE_R * 0.97, 32, 32]} />
          <meshStandardMaterial color={accentColor} transparent opacity={0.07} roughness={1} />
        </mesh>
        <points geometry={pointGeo}>
          <pointsMaterial color={accentColor} size={0.10} sizeAttenuation />
        </points>
      </group>

      <mesh rotation={[Math.PI / 2 + 0.3, 0, t * 0.8]}>
        <torusGeometry args={[GLOBE_R * 1.5, 0.016, 8, 120]} />
        <meshBasicMaterial color={ringColor} transparent opacity={0.5} />
      </mesh>
    </>
  );
}

export const Globe3D: React.FC<Globe3DProps> = ({ title, subtitle, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleX  = interpolate(frame, [0, 20], [-30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #04030d 0%, #080618 100%)" }}>
      <div style={{ position: "absolute", right: -80, top: 0, width: 1100, height: 1080 }}>
        <ThreeCanvas width={1100} height={1080}>
          <GlobeScene frame={frame} fps={fps} accent={accent} />
        </ThreeCanvas>
      </div>

      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(90deg, #04030d 28%, transparent 55%)",
        pointerEvents: "none",
      }} />

      <div style={{
        position: "absolute", top: "50%", left: 100,
        transform: `translateY(-50%) translateX(${titleX}px)`,
        maxWidth: 680, opacity: titleOp,
      }}>
        <div style={{ width: 56, height: 4, background: accent, borderRadius: 2, marginBottom: 30 }} />
        <h1 style={{
          margin: 0, fontSize: 84, fontWeight: 900, color: "#FFFFFF",
          fontFamily: "Inter, system-ui, sans-serif", lineHeight: 1.05, letterSpacing: "-2px",
        }}>{title}</h1>
        {subtitle && (
          <p style={{
            margin: "24px 0 0", fontSize: 28, fontWeight: 300,
            color: "rgba(255,255,255,0.45)",
            fontFamily: "Inter, system-ui, sans-serif", letterSpacing: "0.05em",
          }}>{subtitle}</p>
        )}
      </div>
    </AbsoluteFill>
  );
};
