import React from "react";
import {
  AbsoluteFill,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";
import { PlaceholderAsset } from "../components/PlaceholderAsset";

export type FullImageSlideProps = {
  asset: string;
  speech?: string;
  word_cues: WordCue[];
};

export const FullImageSlide: React.FC<FullImageSlideProps> = ({
  asset,
  word_cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 60, stiffness: 60 },
    from: 1.06,
    to: 1.0,
  });

  return (
    <AbsoluteFill style={{ background: "#0f0e13", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      >
        <PlaceholderAsset
          label={asset}
          width="100%"
          height="100%"
          style={{ borderRadius: 0 }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 220,
          background: "linear-gradient(to top, rgba(0,0,0,0.80) 0%, transparent 100%)",
          pointerEvents: "none",
        }}
      />
      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
