# ZoomThroughTransition

## Description

Aggressively scale into the center of an element to fly through it. A scene transition that interpolates `transform: scale()` with an exponential easing curve, creating the impression of flying through an element. Pair with the next scene rendered behind it for a continuous reveal.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/zoom-through-transition
```

## Usage

### Basic Usage

Zoom through a logo to reveal the next scene. Use for cinematic scene transitions.

```tsx
<ZoomThroughTransition>
  <Logo />
</ZoomThroughTransition>
```

### Targeted Zoom

Zoom through a specific point on an element.

```tsx
<ZoomThroughTransition targetScale={15} transformOrigin="50% 30%">
  <HeroImage />
</ZoomThroughTransition>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| children | ReactNode | - | Element to zoom through. |
| targetScale | number | 20 | Final scale value. |
| transformOrigin | string | "center center" | CSS transform-origin for zoom point. |
| background | string | "white" | Background visible during zoom. |
| className | string | - | Optional className. |

## Notes

- **Aim the camera** — `transformOrigin` controls the focal point of the zoom.
- **Match with the next scene** — Use `Sequence` to overlap timings for a real fly-through.
