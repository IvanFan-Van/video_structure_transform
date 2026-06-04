import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import { HighlightText } from "./HighlightText";

interface GlowHighlightTextProps {
  content: string;
  highlightWord: string;
  highlightColor: string;
  glowIntensity: number;
  fontSize: number;
  textColor: string;
  fontFamily?: string;
  typewriterCharsPerSecond: number;
  highlightDelayFrames: number;
  highlightDurationFrames: number;
}

export const GlowHighlightText: React.FC<GlowHighlightTextProps> = ({
  content,
  highlightWord,
  highlightColor,
  glowIntensity,
  fontSize,
  textColor,
  fontFamily = '"Noto Serif SC", serif',
  typewriterCharsPerSecond,
  highlightDelayFrames,
  highlightDurationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 逐字打字逻辑
  const charCount = Math.floor(frame / (fps / typewriterCharsPerSecond));
  const visible = content.slice(0, charCount);
  const highlightStartIdx = content.indexOf(highlightWord);

  return (
    <div
      style={{
        fontSize,
        color: textColor,
        fontFamily,
        fontWeight: 700,
        textShadow: `0 0 ${glowIntensity}px ${textColor}, 0 0 ${glowIntensity / 2}px ${textColor}`,
        whiteSpace: "nowrap",
      }}
    >
      {visible.slice(0, highlightStartIdx)}
      {highlightStartIdx < charCount ? (
        <HighlightText delay={highlightDelayFrames} duration={highlightDurationFrames} color={highlightColor}>
          {content.slice(highlightStartIdx)}
        </HighlightText>
      ) : (
        content.slice(highlightStartIdx)
      )}
    </div>
  );
};
