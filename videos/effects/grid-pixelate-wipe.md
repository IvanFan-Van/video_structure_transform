# GridPixelateWipe

## Description

Dissolve from one scene to the next through a deterministic grid of mask cells. The screen is split into a CSS grid of black mask cells covering the outgoing scene. Each cell fades out on its own schedule, computed from a deterministic pattern function (wave, diagonal, or spiral). Per-cell delay is pure math over (x, y) — no Math.random.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/grid-pixelate-wipe
```

## Usage

### Basic Usage

Cells fade in a wave pattern from the center. Use for organic scene transitions.

```tsx
<GridPixelateWipe from={<SceneA />} to={<SceneB />} pattern="wave" cols={12} rows={7} />
```

### Diagonal Sweep

A diagonal sweep for a clean, modern dissolve between product shots.

```tsx
<GridPixelateWipe from={<Before />} to={<After />} pattern="diagonal" cols={16} rows={10} transitionDuration={40} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | ReactNode | - | Outgoing scene. |
| to | ReactNode | - | Incoming scene. |
| cols | number | 12 | Mask grid columns. |
| rows | number | 7 | Mask grid rows. |
| pattern | "wave" \| "diagonal" \| "spiral" | "wave" | Deterministic per-cell delay function. |
| transitionStart | number | durationInFrames * 0.4 | Frame dissolve begins. |
| transitionDuration | number | 30 | Total dissolve length. |
| cellFadeFrames | number | 4 | Frames per cell fade. |
| className | string | - | Optional className. |

## Notes

Pick a pattern — wave radiates from center, diagonal reads as a sweep, spiral is most dramatic for hero reveals.

Never reach for Math.random — Random per-cell delays will resample every render. Always derive from (x,y) coordinates or seeded random.
