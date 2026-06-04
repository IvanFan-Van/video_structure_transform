# SpatialPush

## Description

A new scene physically presses the old one back into the frame. Scene A shrinks, dims, and rounds its corners as if being pushed into the background, while Scene B drops in via a spring with overshoot, carrying a heavy directional drop shadow. The result feels kinetic — as if the incoming scene has real mass.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/spatial-push
```

## Usage

### Basic Usage

A new scene pushes the old one back. Use for weighty scene transitions.

```tsx
<SpatialPush from={<SceneA />} to={<SceneB />} direction="up" />
```

### Left Push

Custom direction and timing for different spatial effects.

```tsx
<SpatialPush from={<OldScene />} to={<NewScene />} direction="left" transitionStart={50} transitionDuration={35} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | ReactNode | - | Outgoing scene. |
| to | ReactNode | - | Incoming scene. |
| direction | "up" \| "down" \| "left" \| "right" | "up" | Direction incoming scene enters from. |
| transitionStart | number | durationInFrames * 0.4 | Frame push begins. |
| transitionDuration | number | 30 | Easing window for Scene A's retreat. |
| className | string | - | Optional className. |

## Notes

Spring overshoot creates mass — The incoming scene uses a spring with mass: 1.2 and moderate damping so it overshoots slightly before settling.
