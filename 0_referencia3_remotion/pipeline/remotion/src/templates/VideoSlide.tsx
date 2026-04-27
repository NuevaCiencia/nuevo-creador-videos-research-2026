import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";
import { PlaceholderAsset } from "../components/PlaceholderAsset";

export type VideoSlideProps = {
  asset: string;
  speech?: string;
  word_cues: WordCue[];
};

export const VideoSlide: React.FC<VideoSlideProps> = ({ asset, word_cues }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "#000000", opacity }}>
      <PlaceholderAsset
        label={asset}
        width="100%"
        height="100%"
        style={{ borderRadius: 0 }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 200,
          background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%)",
          pointerEvents: "none",
        }}
      />
      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
