# InfiniteBentoPan

## Description

A hypnotic diagonal camera glide over an oversized grid of bento cards. Builds a super-sized bento grid well beyond the canvas and slowly drifts the camera across it on a diagonal trajectory. A radial vignette swallows the edges so cards seem to fade in and out of darkness as the camera moves.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/infinite-bento-pan
```

## Usage

### Basic Usage

A diagonal camera pan over a massive bento grid. Use for ambient hero backgrounds.

```tsx
<InfiniteBentoPan panSpeed={1} accentColor="#7c3aed" />
```

### Slow Pan

A slower, more hypnotic pan speed.

```tsx
<InfiniteBentoPan panSpeed={0.5} accentColor="#3b82f6" speed={0.8} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| panSpeed | `number` | `1` | Multiplier for diagonal camera distance traveled. |
| accentColor | `string` | `"#7c3aed"` | Color for charts, bars, counters, and logos. |
| speed | `number` | `1` | Multiplier for global timing control. |
| className | `string` | — | Optional className. |

## Notes

Vignette is the trick — The grid is absurdly large and the illusion of infinite depth comes entirely from the radial vignette painted on top.
