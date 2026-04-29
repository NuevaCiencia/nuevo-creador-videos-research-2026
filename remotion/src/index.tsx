import React from "react";
import { Composition, registerRoot } from "remotion";

import { TypeWriter, TypeWriterProps } from "./templates/TypeWriter";
import { MindMap, MindMapProps } from "./templates/MindMap";
import { LinearSteps, LinearStepsProps } from "./templates/LinearSteps";
import { FlipCards, FlipCardsProps } from "./templates/FlipCards";

const DEFAULT_FPS    = 30;
const DEFAULT_DUR    = 900; // 30 s — overridden per-render via --duration
const DEFAULT_WIDTH  = 1920;
const DEFAULT_HEIGHT = 1080;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="NAR-TypeWriter-Hacker"
      component={TypeWriter}
      durationInFrames={DEFAULT_DUR}
      fps={DEFAULT_FPS}
      width={DEFAULT_WIDTH}
      height={DEFAULT_HEIGHT}
      defaultProps={{
        accent: "#00FF41",
        lines: [
          { prefix: "$ ", text: "Iniciando agente…", delay: 10 },
          { prefix: "→ ", text: "Procesando datos",  delay: 50 },
        ],
      } as TypeWriterProps}
    />

    <Composition
      id="FLOW-MindMap"
      component={MindMap}
      durationInFrames={DEFAULT_DUR}
      fps={DEFAULT_FPS}
      width={DEFAULT_WIDTH}
      height={DEFAULT_HEIGHT}
      defaultProps={{
        center: "Concepto",
        nodes: [
          { text: "Rama 1" },
          { text: "Rama 2" },
          { text: "Rama 3" },
        ],
      } as MindMapProps}
    />

    <Composition
      id="FLOW-LinearSteps"
      component={LinearSteps}
      durationInFrames={DEFAULT_DUR}
      fps={DEFAULT_FPS}
      width={DEFAULT_WIDTH}
      height={DEFAULT_HEIGHT}
      defaultProps={{
        title: "Proceso",
        steps: [
          { title: "Paso 1", description: "Descripción" },
          { title: "Paso 2", description: "Descripción" },
        ],
      } as LinearStepsProps}
    />

    <Composition
      id="CLASS-FlipCards"
      component={FlipCards}
      durationInFrames={DEFAULT_DUR}
      fps={DEFAULT_FPS}
      width={DEFAULT_WIDTH}
      height={DEFAULT_HEIGHT}
      defaultProps={{
        title: "Categorías",
        items: [
          { icon: "🔷", label: "Categoría", title: "Título", description: "Descripción" },
          { icon: "🔶", label: "Categoría", title: "Título", description: "Descripción" },
        ],
      } as FlipCardsProps}
    />
  </>
);

registerRoot(RemotionRoot);
