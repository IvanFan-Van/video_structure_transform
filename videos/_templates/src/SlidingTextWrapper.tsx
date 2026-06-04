import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

interface SlidingTextWrapperProps {
  children: React.ReactNode;
  startFrame: number;
  endFrame: number;
  fromX: number;
  toX: number;
}

export const SlidingTextWrapper: React.FC<SlidingTextWrapperProps> = ({
  children,
  startFrame,
  endFrame,
  fromX,
  toX,
}) => {
  const frame = useCurrentFrame();
  const translateX = interpolate(
    frame,
    [startFrame, endFrame],
    [fromX, toX],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <div
      style={{
        transform: `translateX(${translateX}px)`,
        display: 'inline-block',
      }}
    >
      {children}
    </div>
  );
};
