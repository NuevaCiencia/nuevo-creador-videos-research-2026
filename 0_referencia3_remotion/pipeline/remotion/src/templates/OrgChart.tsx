/**
 * OrgChart — Árbol jerárquico con líneas SVG que se dibujan de arriba a abajo
 * Nodo raíz → hijos → nietos. Líneas con strokeDashoffset, nodos con spring.
 * Fondo claro.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type OrgNode = {
  id: string;
  label: string;
  sub?: string;
  color: string;
  parentId?: string;
};

export type OrgChartProps = {
  title: string;
  nodes: OrgNode[];
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#FFFFFF",
  fontFamily:  "Inter, system-ui, sans-serif",

  titleSize:   72,
  titleColor:  "#0F172A",
  titleWeight: 800,

  nodeW:       340,
  nodeH:       120,
  nodeGap:     60,     // espacio horizontal entre nodos del mismo nivel
  levelH:      240,    // espacio vertical entre niveles
  nodeRadius:  14,
  nodeStroke:  2.5,
  startY:      320,    // Y del nodo raíz

  labelSize:   30,
  labelColor:  "#111827",
  labelWeight: 800,

  subSize:     20,
  subColor:    "#6B7280",
};
// ─────────────────────────────────────────────────────────────────────────────

const W = 1920;
const H = 1080;

function buildLayout(nodes: OrgNode[]) {
  // Group by level (BFS from root)
  const childrenOf: Record<string, string[]> = {};
  const levelOf: Record<string, number> = {};
  nodes.forEach(n => {
    if (!n.parentId) levelOf[n.id] = 0;
    childrenOf[n.parentId ?? "__root"] = childrenOf[n.parentId ?? "__root"] ?? [];
    if (n.parentId) {
      childrenOf[n.parentId] = childrenOf[n.parentId] ?? [];
      childrenOf[n.parentId].push(n.id);
    }
  });

  // Assign levels
  let changed = true;
  while (changed) {
    changed = false;
    nodes.forEach(n => {
      if (n.parentId && levelOf[n.parentId] !== undefined && levelOf[n.id] === undefined) {
        levelOf[n.id] = levelOf[n.parentId] + 1;
        changed = true;
      }
    });
  }

  // Group by level
  const byLevel: Record<number, string[]> = {};
  nodes.forEach(n => {
    const l = levelOf[n.id] ?? 0;
    byLevel[l] = byLevel[l] ?? [];
    byLevel[l].push(n.id);
  });

  // Assign x positions
  const posX: Record<string, number> = {};
  const posY: Record<string, number> = {};
  Object.entries(byLevel).forEach(([lvl, ids]) => {
    const l = Number(lvl);
    const count = ids.length;
    ids.forEach((id, i) => {
      posX[id] = W / 2 + (i - (count - 1) / 2) * (CONFIG.nodeW + CONFIG.nodeGap);
      posY[id] = CONFIG.startY + l * CONFIG.levelH;
    });
  });

  return { posX, posY, childrenOf, levelOf };
}

export const OrgChart: React.FC<OrgChartProps> = ({ title, nodes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const { posX, posY, levelOf } = buildLayout(nodes);

  const titleOp = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: CONFIG.bg }}>

      <div style={{ position: "absolute", top: 44, left: 0, right: 0, textAlign: "center", opacity: titleOp }}>
        <h1 style={{ margin: 0, fontSize: CONFIG.titleSize, fontWeight: CONFIG.titleWeight, color: CONFIG.titleColor, fontFamily: CONFIG.fontFamily }}>
          {title}
        </h1>
      </div>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {/* Lines first (behind nodes) */}
        {nodes.map(node => {
          if (!node.parentId) return null;
          const px = posX[node.parentId];
          const py = posY[node.parentId];
          const cx = posX[node.id];
          const cy = posY[node.id];
          if (px === undefined || cx === undefined) return null;

          const level = levelOf[node.id] ?? 1;
          const lineDelay = (level - 1) * 18 + 12;
          const lineLen = Math.abs(cy - py) + Math.abs(cx - px) * 0.5 + 80;
          const lProg = interpolate(frame - lineDelay, [0, 18], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });

          const mid = (py + cy) / 2;

          return (
            <path
              key={`line-${node.id}`}
              d={`M ${px} ${py + CONFIG.nodeH / 2} C ${px} ${mid}, ${cx} ${mid}, ${cx} ${cy - CONFIG.nodeH / 2}`}
              fill="none"
              stroke={node.color}
              strokeWidth={2}
              strokeOpacity={0.5}
              strokeDasharray={lineLen}
              strokeDashoffset={lineLen * (1 - lProg)}
              strokeLinecap="round"
            />
          );
        })}

        {/* Node boxes */}
        {nodes.map(node => {
          const x = posX[node.id];
          const y = posY[node.id];
          if (x === undefined) return null;

          const level = levelOf[node.id] ?? 0;
          const delay = level * 18 + 6;

          const s = spring({ frame: frame - delay, fps, config: { damping: 22, stiffness: 160 }, from: 0, to: 1 });
          const op = interpolate(frame - delay, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          return (
            <g key={node.id} opacity={op} transform={`scale(${s}) translate(${x * (1 - s)}, ${y * (1 - s)})`}
               style={{ transformOrigin: `${x}px ${y}px` }}>
              <rect
                x={x - CONFIG.nodeW / 2} y={y - CONFIG.nodeH / 2}
                width={CONFIG.nodeW} height={CONFIG.nodeH}
                rx={CONFIG.nodeRadius}
                fill="#FFFFFF"
                stroke={node.color}
                strokeWidth={CONFIG.nodeStroke}
                style={{ filter: `drop-shadow(0 4px 16px ${node.color}33)` }}
              />
              {/* Color top bar */}
              <rect
                x={x - CONFIG.nodeW / 2} y={y - CONFIG.nodeH / 2}
                width={CONFIG.nodeW} height={8}
                rx={CONFIG.nodeRadius}
                fill={node.color}
              />
              <rect
                x={x - CONFIG.nodeW / 2} y={y - CONFIG.nodeH / 2 + 4}
                width={CONFIG.nodeW} height={4}
                fill={node.color}
              />
              <text x={x} y={y - 10}
                textAnchor="middle" fontSize={CONFIG.labelSize} fontWeight={CONFIG.labelWeight}
                fill={CONFIG.labelColor} fontFamily={CONFIG.fontFamily}>
                {node.label}
              </text>
              {node.sub && (
                <text x={x} y={y + 22}
                  textAnchor="middle" fontSize={CONFIG.subSize}
                  fill={CONFIG.subColor} fontFamily={CONFIG.fontFamily}>
                  {node.sub}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
