import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import React from "react";

interface SwingingTagProps {
  text: string;
  textColor: string;
  fontSize: number;
  xPercent: number;
  enterStartFrame: number;
  holdStartFrame: number;
  exitStartFrame: number;
  exitEndFrame: number;
}

export const SwingingTag: React.FC<SwingingTagProps> = ({
  text,
  textColor,
  fontSize,
  xPercent,
  enterStartFrame,
  holdStartFrame,
  exitStartFrame,
  exitEndFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const progressDown = spring({
    frame,
    fps,
    config: { mass: 1, damping: 10 },
    delay: enterStartFrame,
  });

  const translateY = interpolate(progressDown, [0, 1], [-400, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const swingFrame = Math.max(0, frame - holdStartFrame);
  const rotate = interpolate(
    Math.sin(swingFrame * 0.08),
    [-1, 1],
    [-5, 5],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const opacity = interpolate(
    frame,
    [exitStartFrame, exitEndFrame],
    [1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const xPos = (width * xPercent) / 100;

  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      {/* 红绳 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: xPos - 2,
          width: 4,
          height: 180 + translateY,
          backgroundColor: "#ff2222",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 180 + translateY,
          left: xPos,
          transform: `translateX(-50%) translateY(0) rotate(${rotate}deg)`,
          opacity,
        }}
      >
        <span
          style={{
            fontSize,
            color: textColor,
            fontWeight: 700,
            fontFamily: '"Noto Serif SC", serif',
            textShadow: `0 0 16px ${textColor}`,
          }}
        >
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};
