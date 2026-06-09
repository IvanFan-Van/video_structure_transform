"use client";

import {
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface MarkerHighlightProps {
  /** Text before the highlighted word. */
  before?: string;
  /** The word or phrase to highlight. */
  highlight: string;
  /** Text after the highlighted word. */
  after?: string;
  /** Background color of the marker bar swiping behind the highlight text. */
  markerColor?: string;
  /** Color of the surrounding text (before/after). */
  baseColor?: string;
  /** Color of the highlighted text AFTER the marker sweep.
   *  ★ Must visibly differ from baseColor for the effect to be noticeable.
   *  When in doubt, use the accent/contrast color, not the same as baseColor. */
  highlightedTextColor?: string;
  /** Font size in pixels. */
  fontSize?: number;
  /** CSS font-weight. */
  fontWeight?: number;
  /** Playback speed multiplier (1 = normal, 2 = twice as fast). */
  speed?: number;
  /** Spring delay in frames from when the component mounts.
   *  ★ When placed inside a <Sequence from={N}>, set delayFrames={N}
   *  to align the spring start with the Sequence timeline. */
  delayFrames?: number;
  /** Optional CSS class name. */
  className?: string;
}

export function MarkerHighlight({
  before = "",
  highlight,
  after = "",
  markerColor = "#facc15",
  baseColor = "#171717",
  highlightedTextColor = "#171717",
  fontSize = 72,
  fontWeight = 600,
  speed = 1,
  delayFrames = 0,
  className,
}: MarkerHighlightProps) {
  const frame = useCurrentFrame() * speed;
  const { fps } = useVideoConfig();

  const markerScale = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 14 },
  });

  const textColor = interpolateColors(
    interpolate(markerScale, [0.5, 0.8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
    [0, 1],
    [baseColor, highlightedTextColor],
  );

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <span
        className={className}
        style={{
          fontSize,
          fontWeight,
          color: baseColor,
          letterSpacing: "-0.03em",
          fontFamily:
            "var(--font-geist-sans), -apple-system, BlinkMacSystemFont, sans-serif",
        }}
      >
        {before}
        <span style={{ position: "relative", display: "inline-block" }}>
          <span
            aria-hidden
            style={{
              position: "absolute",
              inset: "0 -0.1em",
              background: markerColor,
              transformOrigin: "left center",
              transform: `scaleX(${markerScale})`,
              zIndex: 0,
            }}
          />
          <span style={{ position: "relative", zIndex: 1, color: textColor }}>
            {highlight}
          </span>
        </span>
        {after}
      </span>
    </div>
  );
}
