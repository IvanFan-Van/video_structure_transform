# ChromaticAberrationWipe

## Description

An ultra-fast slide transition with an RGB glitch on the peak frames. Two scenes slide past each other in just 5-8 frames, and on the middle of that window the entire container gets a red+cyan drop-shadow filter to fake RGB channel separation. The glitch is intentionally short — restraint is the whole point.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/chromatic-aberration-wipe
```

## Usage

### Basic Usage

A fast slide with a brief RGB glitch. Use for high-energy DevTools or product reels.

```tsx
<ChromaticAberrationWipe from={<SceneC />} to={<SceneD />} direction="left" />
```

### Custom Glitch

Adjust offset and duration for different glitch intensity.

```tsx
<ChromaticAberrationWipe from={<Before />} to={<After />} direction="right" transitionDuration={5} aberrationOffset={12} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | ReactNode | - | Outgoing scene. |
| to | ReactNode | - | Incoming scene. |
| direction | "left" \| "right" | "left" | Slide direction. |
| transitionStart | number | durationInFrames * 0.4 | Frame wipe begins. |
| transitionDuration | number | 7 | Wipe length in frames. Keep 5-8 for glitch to land. |
| aberrationOffset | number | 8 | Horizontal offset in pixels for red/cyan drop shadows. |
| className | string | - | Optional className. |

## Notes

Less is more — The chromatic aberration should only flash for 3-5 frames at peak speed. Any longer and the viewer starts consciously reading the red and cyan fringes.
