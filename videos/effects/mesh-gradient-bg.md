# mesh-gradient-bg

## Description

Living gradient with amorphous color blobs slowly drifting across the frame. A background primitive that renders several large radial-gradient blobs and animates them via transform: translate() using Math.sin(frame) and Math.cos(frame) for organic, deterministic drift. Heavy CSS blur plus mix-blend-mode creates a soft mesh gradient without shaders.

## Installation

pnpm dlx shadcn@latest add @remocn/mesh-gradient-bg

## Usage

### Basic Usage

A colorful animated gradient background. Use as a backdrop for hero sections.

```
<MeshGradientBg colors={["#ff0080", "#7928ca", "#00d4ff", "#ffb800"]} speed={1} background="#0a0a0a" />
```

### Subtle Drift

A slower, softer gradient with fewer colors for a calm atmosphere.

```
<MeshGradientBg colors={["#3b82f6", "#8b5cf6"]} speed={0.3} blur={120} background="#0f172a" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| colors | string[] | ["#ff0080","#7928ca","#00d4ff","#ffb800"] | Colors used for the radial blobs. Any number of CSS colors. |
| speed | number | 1 | Drift speed multiplier. Higher = faster motion. |
| background | string | #0a0a0a | Base canvas color. Blend mode is auto-picked. |
| blur | number | 80 | CSS blur radius in pixels applied to each blob. |
| className | string | - | Optional className. |

## Notes

Deterministic motion — Motion uses Math.sin(frame) and Math.cos(frame), so every render produces the same output.

Blur performance — Large blur radii on big elements are expensive. If you see slow renders, reduce blur or blob size.
