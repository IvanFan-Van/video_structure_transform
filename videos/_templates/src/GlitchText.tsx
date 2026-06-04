import { useCurrentFrame, interpolate, Easing } from "remotion";
import React from "react";

interface GlitchTextProps {
  children: string;
  fontSize: number;
  color: string;
  scale: number;
}

export const GlitchText: React.FC<GlitchTextProps> = ({
  children,
  fontSize,
  color,
  scale,
}) => {
  const frame = useCurrentFrame();

  const glitchOffsetR = interpolate(
    Math.sin(frame * 0.7),
    [-1, 1],
    [-4, 4],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );
  const glitchOffsetG = interpolate(
    Math.sin(frame * 0.7 + 2),
    [-1, 1],
    [-3, 3],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );
  const glitchOffsetB = interpolate(
    Math.sin(frame * 0.7 + 4),
    [-1, 1],
    [-2, 2],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <div
      style={{
        position: "relative",
        transform: `scale(${scale})`,
      }}
    >
      <span
        style={{
          position: "absolute",
          left: glitchOffsetR,
          top: 0,
          color: "#ff0000",
          fontSize,
          fontWeight: 700,
          fontFamily: '"Noto Serif SC", serif',
          opacity: 0.7,
        }}
      >
        {children}
      </span>
      <span
        style={{
          position: "absolute",
          left: glitchOffsetG,
          top: 0,
          color: "#00ff00",
          fontSize,
          fontWeight: 700,
          fontFamily: '"Noto Serif SC", serif',
          opacity: 0.7,
        }}
      >
        {children}
      </span>
      <span
        style={{
          position: "absolute",
          left: glitchOffsetB,
          top: 0,
          color: "#0000ff",
          fontSize,
          fontWeight: 700,
          fontFamily: '"Noto Serif SC", serif',
          opacity: 0.7,
        }}
      >
        {children}
      </span>
      <span
        style={{
          fontSize,
          color,
          fontWeight: 700,
          fontFamily: '"Noto Serif SC", serif',
          textShadow: `0 0 24px ${color}`,
          position: "relative",
        }}
      >
        {children}
      </span>
    </div>
  );
};
