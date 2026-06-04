import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";
import React from "react";

interface SyncMoveWrapperProps {
  children: React.ReactNode;
  moveDistance: number;
  startFrame: number;
  durationFrames: number;
}

export const SyncMoveWrapper: React.FC<SyncMoveWrapperProps> = ({
  children,
  moveDistance,
  startFrame,
  durationFrames,
}) => {
  const frame = useCurrentFrame();

  const translateX = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, moveDistance],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.linear,
    }
  );

  return (
    <AbsoluteFill
      style={{
        transform: `translateX(${translateX}px)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
