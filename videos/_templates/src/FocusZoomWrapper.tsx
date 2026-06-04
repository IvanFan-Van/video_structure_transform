import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

interface FocusZoomWrapperProps {
  children: React.ReactNode;
  zoomStartFrame: number;
  zoomEndFrame: number;
  scaleFrom: number;
  scaleTo: number;
  targetXPercent: number;
  targetYPercent: number;
}

export const FocusZoomWrapper: React.FC<FocusZoomWrapperProps> = ({
  children,
  zoomStartFrame,
  zoomEndFrame,
  scaleFrom,
  scaleTo,
  targetXPercent,
  targetYPercent,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const scale = interpolate(
    frame,
    [zoomStartFrame, zoomEndFrame],
    [scaleFrom, scaleTo],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const originX = (width * targetXPercent) / 100;
  const originY = (height * targetYPercent) / 100;

  return (
    <AbsoluteFill
      style={{
        transformOrigin: `${originX}px ${originY}px`,
        transform: `scale(${scale})`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
