# dynamic-grid

## Description

Subtle moving grid background for tech and dev scenes. A minimal grid background built from two CSS linear gradients, translated each frame via transform. Cheaper than animating background-position because the browser keeps layout untouched.

## Installation

pnpm dlx shadcn@latest add @remocn/dynamic-grid

## Usage

### Basic Usage

A moving grid for developer-focused scenes or dashboards.

```
<DynamicGrid cellSize={40} lineColor="#27272a" background="#0a0a0a" speed={0.5} direction="diagonal" />
```

### Vertical Scan Lines

A vertical-only moving grid for a retro-tech feel.

```
<DynamicGrid cellSize={60} lineColor="#1e293b" background="#0f172a" speed={0.3} direction="vertical" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| cellSize | number | 40 | Grid cell size in pixels. |
| lineColor | string | #27272a | Grid line color. |
| background | string | #0a0a0a | Base background color. |
| speed | number | 0.5 | Pixels moved per frame. Motion wraps at cellSize to loop seamlessly. |
| direction | "diagonal" \| "horizontal" \| "vertical" | diagonal | Direction the grid drifts. |
| className | string | - | Optional className. |

## Notes

Seamless loop — Offset uses modulo cellSize, so the grid loops perfectly — ideal as a base layer under intros and outros.
