/**
 * TypeWriter — Terminal con texto que se escribe letra a letra
 * Fondo negro, monospace verde, cursor parpadeante.
 * Varias líneas que aparecen secuencialmente.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type TWLine = {
  prefix: string;   // "$ " comando | "→ " output | "✓ " éxito | "! " error | "// " comentario | "> " resultado
  text: string;
  delay: number;    // frames hasta que empieza
  speed?: number;   // chars per frame (default 1.8)
};

// Color automático según el prefijo — no hace falta ponerlo en el YAML
const PREFIX_COLORS: Record<string, string> = {
  "$ ":  "#00FF41",  // verde   — comando
  "→ ":  "#7DD3FC",  // celeste — output
  "> ":  "#FCD34D",  // amarillo — resultado
  "✓ ":  "#86EFAC",  // verde suave — éxito
  "! ":  "#F87171",  // rojo   — error / advertencia
  "// ": "#9CA3AF",  // gris   — comentario
};

export type TypeWriterProps = {
  lines: TWLine[];
  accent: string;
};

// ─── Configuración visual ────────────────────────────────────────────────────
const CONFIG = {
  bg:          "#000000",
  fontFamily:  "'Courier New', 'Lucida Console', monospace",

  defaultColor: "#00FF41",
  defaultSpeed: 1.8,    // chars per frame

  textSize:    52,      // tamaño de cada línea de código
  prefixWeight: 700,
  prefixOpacity: 0.7,

  headerHeight: 44,
  headerBg:     "#111",
  headerLabel:  "agent_terminal — bash",
  headerLabelSize: 16,

  cursorBlinkFreq: 1.8, // Hz
  cursorW:    30,
  cursorH:    52,
};
// ─────────────────────────────────────────────────────────────────────────────

export const TypeWriter: React.FC<TypeWriterProps> = ({ lines, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scanline movement
  const scanY = (frame * 3.2) % 1080;

  // Cursor blink
  const cursorOn = Math.sin((frame / fps) * Math.PI * 2 * CONFIG.cursorBlinkFreq) > 0;

  // Find which line is actively typing
  let activeLine = -1;
  const renderedLines: { prefix: string; visible: string; full: string; color: string; done: boolean }[] = [];

  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i];
    const speed = ln.speed ?? CONFIG.defaultSpeed;
    const localFrame = frame - ln.delay;
    const charsVisible = Math.floor(Math.max(0, localFrame * speed));
    const done = charsVisible >= ln.text.length;
    const visible = ln.text.slice(0, charsVisible);

    if (localFrame >= 0 && !done) activeLine = i;
    if (localFrame >= 0) {
      renderedLines.push({
        prefix: ln.prefix,
        visible,
        full: ln.text,
        color: PREFIX_COLORS[ln.prefix] ?? CONFIG.defaultColor,
        done,
      });
    }
  }

  return (
    <AbsoluteFill style={{ background: CONFIG.bg, fontFamily: CONFIG.fontFamily }}>

      {/* CRT scanlines overlay */}
      <div style={{
        position: "absolute", inset: 0,
        background: "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,255,65,0.02) 3px, rgba(0,255,65,0.02) 4px)",
        pointerEvents: "none", zIndex: 10,
      }} />

      {/* Moving scan line */}
      <div style={{
        position: "absolute", left: 0, right: 0,
        top: scanY, height: 2,
        background: "rgba(0,255,65,0.04)",
        pointerEvents: "none", zIndex: 11,
      }} />

      {/* Vignette */}
      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.7) 100%)",
        pointerEvents: "none", zIndex: 9,
      }} />

      {/* Terminal window header bar */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        height: CONFIG.headerHeight,
        background: CONFIG.headerBg,
        borderBottom: `1px solid ${accent}22`,
        display: "flex",
        alignItems: "center",
        padding: "0 24px",
        gap: 10,
      }}>
        {["#ff5f57","#ffbd2e","#28c840"].map((c, i) => (
          <div key={i} style={{ width: 14, height: 14, borderRadius: "50%", background: c, opacity: 0.8 }} />
        ))}
        <span style={{
          marginLeft: 20,
          fontSize: CONFIG.headerLabelSize,
          color: "rgba(255,255,255,0.3)",
          letterSpacing: "0.1em",
        }}>{CONFIG.headerLabel}</span>
      </div>

      {/* Code content */}
      <div style={{
        position: "absolute",
        top: 60,
        left: 80,
        right: 80,
        bottom: 60,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 10,
      }}>
        {renderedLines.map((ln, i) => (
          <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 0 }}>
            {/* Prefix */}
            <span style={{
              color: accent,
              fontSize: CONFIG.textSize,
              fontWeight: CONFIG.prefixWeight,
              whiteSpace: "pre",
              lineHeight: 1.5,
              opacity: CONFIG.prefixOpacity,
            }}>
              {ln.prefix}
            </span>
            {/* Typed text */}
            <span style={{
              color: ln.color,
              fontSize: CONFIG.textSize,
              fontWeight: 400,
              whiteSpace: "pre-wrap",
              lineHeight: 1.5,
              letterSpacing: "0.02em",
            }}>
              {ln.visible}
            </span>
            {/* Cursor — only on active line */}
            {i === activeLine && cursorOn && (
              <span style={{
                display: "inline-block",
                width: CONFIG.cursorW,
                height: CONFIG.cursorH,
                background: accent,
                marginLeft: 2,
                verticalAlign: "middle",
                opacity: 0.9,
              }} />
            )}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
