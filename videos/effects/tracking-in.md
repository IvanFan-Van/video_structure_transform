# TrackingIn

## Description

Letter-spacing collapses and blur clears with a springy entrance. A typography primitive that starts text with a wide letter-spacing and a heavy blur, then springs both back to normal. The result is a tight, premium-feeling title reveal.

## Installation

```
pnpm dlx shadcn@latest add @remocn/tracking-in
```

## Usage

### Basic Usage

Use for a premium brand or product name reveal.

```tsx
<TrackingIn text="REMOCN" startTracking={0.6} startBlur={14} />
```

### Section Title

Use a softer tracking for elegant section dividers.

```tsx
<TrackingIn text="Chapter One" startTracking={0.3} startBlur={8} fontSize={48} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to animate. |
| startTracking | number | 0.5 | Initial letter-spacing in em. Animates down to -0.03em. |
| startBlur | number | 12 | Initial blur radius in pixels. Animates down to 0. |
| fontSize | number | 96 | Font size in pixels. |
| fontWeight | number | 700 | CSS font-weight. |
| color | string | "#171717" | Text color (any valid CSS color). |
| speed | number | 1 | Playback speed multiplier (1 = normal, 2 = twice as fast). |
| className | string | - | Optional className passed to the underlying span. |

## Notes

- **Load fonts before render** — Make sure your font is loaded before the first frame renders. Use @remotion/google-fonts so the blur and tracking effects don't apply to a fallback system font.
- **Overflow** — Wide initial tracking can push text outside the container. Either reduce startTracking, lower fontSize, or wrap the component in a parent with overflow: hidden.
