# SuccessConfetti

## Description

Deterministic confetti burst from a focal point with optional headline. A workflow finale: a burst of SVG confetti particles fanning out from a configurable origin under gravity. Particle directions, colors, sizes, and rotations are derived from Remotion's seeded random(), so renders are perfectly deterministic.

## Installation

pnpm dlx shadcn@latest add @remocn/success-confetti

## Usage

### Basic Usage

A colorful confetti burst with a centered headline. Use for build completions or success states.

```tsx
<SuccessConfetti text="Merged!" count={60} colors={["#ff5e3a", "#22c55e", "#0ea5e9", "#facc15", "#a855f7"]} />
```

### Corner Burst

Confetti from a specific origin point with fewer particles for a subtle celebration.

```tsx
<SuccessConfetti text="" count={30} originX={0.2} originY={0.8} gravity={0.3} colors={["#22c55e", "#a855f7"]} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| count | number | 60 | Number of confetti particles. |
| colors | string[] | ["#ff5e3a","#22c55e","#0ea5e9","#facc15","#a855f7"] | Pool of colors that particles are randomly drawn from. |
| originX | number | 0.5 | Horizontal burst origin as a fraction of the frame width (0..1). |
| originY | number | 0.5 | Vertical burst origin as a fraction of the frame height (0..1). |
| gravity | number | 0.4 | Downward acceleration applied per frame squared. |
| velocity | number | 12 | Base outward speed for each particle in pixels per frame. |
| text | string | "Merged!" | Optional headline rendered in the middle of the burst. Pass an empty string to hide. |
| textColor | string | "#171717" | Color of the headline. |
| background | string | "#fafafa" | Frame background color. |
| seed | string | "remocn" | Seed used to generate particle randomness. Change to get a different burst. |
| className | string | - | Optional className passed to the outer container. |

## Notes

Deterministic randomness — Particle properties are derived from random('seed:i:property') so the same seed always yields the same burst — critical for chunked video renders.

Avoid Math.random — Never replace random() with Math.random() here. It would produce different results on every frame and tear the burst across rendered chunks.
