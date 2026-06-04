import React from "react";

interface GlowTextProps {
  text: string;
  fontSize: number;
  color: string;
  glowIntensity: number;
  fontWeight?: number;
  style?: React.CSSProperties;
}

export const GlowText: React.FC<GlowTextProps> = ({
  text,
  fontSize,
  color,
  glowIntensity,
  fontWeight = 700,
  style = {},
}) => {
  return (
    <span
      style={{
        fontSize,
        color,
        fontWeight,
        fontFamily: '"Noto Serif SC", serif',
        textShadow: `0 0 ${glowIntensity}px ${color}, 0 0 ${glowIntensity * 2}px ${color}`,
        whiteSpace: "pre-line",
        ...style,
      }}
    >
      {text}
    </span>
  );
};
