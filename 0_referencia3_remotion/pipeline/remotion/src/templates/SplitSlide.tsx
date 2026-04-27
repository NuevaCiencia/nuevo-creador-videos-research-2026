import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Subtitles, WordCue } from "../components/Subtitles";
import { PlaceholderAsset } from "../components/PlaceholderAsset";

export type SplitSlideProps = {
  text: string;
  text_style?: string;
  asset: string;
  side: "left" | "right";
  speech?: string;
  word_cues: WordCue[];
};

export const SplitSlide: React.FC<SplitSlideProps> = ({
  text,
  asset,
  side,
  word_cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const textOffsetFrom = side === "left" ? 80 : -80;
  const textX = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 180 },
    from: textOffsetFrom,
    to: 0,
  });

  const textOpacity = interpolate(frame, [4, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const ImagePanel = (
    <div
      style={{
        flex: 1,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "48px 40px",
      }}
    >
      <PlaceholderAsset label={asset} width="100%" height="100%" />
    </div>
  );

  const TextPanel = (
    <div
      style={{
        flex: 1,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "48px 60px",
        transform: `translateX(${textX}px)`,
        opacity: textOpacity,
      }}
    >
      <p
        style={{
          fontSize: 50,
          fontWeight: 700,
          color: "#FFFFFF",
          fontFamily: "Inter, system-ui, sans-serif",
          lineHeight: 1.45,
          margin: 0,
          background: "rgba(108, 99, 255, 0.14)",
          border: "2px solid rgba(108, 99, 255, 0.45)",
          borderRadius: 16,
          padding: "28px 40px",
        }}
      >
        {text}
      </p>
    </div>
  );

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f0e13 0%, #1a1830 100%)",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 120,
          display: "flex",
          flexDirection: "row",
        }}
      >
        {side === "left"
          ? <>{ImagePanel}{TextPanel}</>
          : <>{TextPanel}{ImagePanel}</>
        }
      </div>
      <Subtitles word_cues={word_cues} />
    </AbsoluteFill>
  );
};
