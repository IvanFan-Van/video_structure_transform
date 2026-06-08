"use client";

import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface FocusZoomProps {
  /** Children to apply the zoom effect to. */
  children: React.ReactNode;
  /** Absolute frame at which the spring zoom animation starts.
   *  ★ When inside <Sequence from={N}>, set zoomStartFrame={N}. */
  zoomStartFrame: number;
  /** Target zoom scale (e.g. 1.5 = 150%). Spring overshoots then settles. */
  zoomScale: number;
  /** X-axis transform origin (0–100% of element width). */
  targetX: number;
  /** Y-axis transform origin (0–100% of element height). */
  targetY: number;
}

export const FocusZoom: React.FC<FocusZoomProps> = ({
  children,
  zoomStartFrame,
  zoomScale,
  targetX,
  targetY,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const zoomSpring = spring({
    frame: frame - zoomStartFrame,
    fps,
    config: { stiffness: 100, damping: 20 },
  });

  const scale = 1 + zoomSpring * (zoomScale - 1);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        transformOrigin: `${targetX}% ${targetY}%`,
        transform: `scale(${scale})`,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {children}
    </div>
  );
};
