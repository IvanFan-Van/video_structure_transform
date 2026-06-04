import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

interface HorizontalSlideWrapperProps {
  children: React.ReactNode;
  slideDistance: number;
  slideStartFrame: number;
  slideDurationFrames: number;
}

export const HorizontalSlideWrapper: React.FC<HorizontalSlideWrapperProps> = ({
  children,
  slideDistance,
  slideStartFrame,
  slideDurationFrames,
}) => {
  const frame = useCurrentFrame();
  const translateX = interpolate(
    frame,
    [slideStartFrame, slideStartFrame + slideDurationFrames],
    [0, slideDistance],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <div style={{ transform: `translateX(${translateX}px)` }}>
      {children}
    </div>
  );
};
