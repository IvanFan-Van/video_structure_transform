# DirectionalWipe

## Description

Slide one scene in while pushing the other out. Animates two scenes with `transform: translateX/Y`. The outgoing scene slides off in one direction while the incoming scene slides in from the opposite side. Uses `transform` (not `left`/`top`) so the browser doesn't trigger layout reflow.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/directional-wipe
```

## Usage

### Basic Usage

Slide between two scenes with a left-to-right wipe.

```tsx
<DirectionalWipe from={<SceneA />} to={<SceneB />} direction="left" />
```

### Vertical Wipe

Slide vertically for a different feel.

```tsx
<DirectionalWipe from={<Intro />} to={<Main />} direction="up" transitionStart={45} transitionDuration={25} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | ReactNode | - | Outgoing scene. |
| to | ReactNode | - | Incoming scene. |
| direction | "left" \| "right" \| "up" \| "down" | "left" | Direction outgoing slides toward. |
| transitionStart | number | durationInFrames * 0.4 | Frame wipe begins. |
| transitionDuration | number | 20 | Wipe length in frames. |
| className | string | - | Optional className. |

## Notes

- **Pair with Sequence** — Wrap each scene in `Sequence` and overlap durations for clean blending.
- **Use transform, not left/top** — Animating positional CSS properties triggers layout reflow. Stick to `translateX/Y`.
