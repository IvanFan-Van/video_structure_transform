# RGBGlitchText

## Description

Three RGB-offset text copies jitter for a few frames to create a chromatic aberration glitch. A typography primitive that stacks red, green, and blue copies of the same text and offsets them on each frame during a short glitch window. Uses random(seed) from Remotion so the jitter is fully deterministic.

## Installation

```
pnpm dlx shadcn@latest add @remocn/rgb-glitch-text
```

## Usage

### Brief Glitch

Glitch text for a few frames at a specific moment. Use for cyberpunk or tech reveals.

```
<RGBGlitchText text="SYSTEM" glitchAt={20} glitchDuration={8} intensity={6} />
```

### Heavy Glitch

A more intense, longer glitch for dramatic effect.

```
<RGBGlitchText text="OVERRIDE" glitchAt={30} glitchDuration={12} intensity={10} color="#ff5e3a" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to display and glitch. |
| fontSize | number | 96 | Font size in pixels. |
| color | string | "#171717" | Base text color (visible at all times). |
| fontWeight | number | 700 | CSS font-weight. |
| glitchAt | number | 20 | Frame at which the glitch starts. |
| glitchDuration | number | 8 | Duration of the glitch window in frames. |
| intensity | number | 6 | Maximum offset (in pixels) for the RGB copies. |
| seed | string | "glitch" | Seed used by random() so the jitter stays deterministic. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className passed to the inline-block wrapper. |

## Notes

- **Determinism** — The RGB offsets use `random(seed)` from remotion, never `Math.random()`. The same seed and frame always produce the same offset.
- **Light backgrounds only** — The RGB copies use `mixBlendMode: multiply` so they read correctly on a light background. On a dark background you'll want to switch to `screen` or stack opaque copies instead.
