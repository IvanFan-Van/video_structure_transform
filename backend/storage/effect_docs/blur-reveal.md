# BlurReveal

## Description

Text fades in from a heavy blur into sharp focus. A typography primitive that animates opacity from 0 to 1 and filter: blur() from a configurable amount down to 0. Useful for title cards and intro shots.

## Installation

```
pnpm dlx shadcn@latest add @remocn/blur-reveal
```

## Usage

### Basic Usage

Shows text fading in from blur. Use for intro title cards.

```tsx
<BlurReveal text="Hello, world" blur={12} fontSize={72} />
```

### Multi-line Hero Title

Combine multiple BlurReveal instances for a cinema-style title sequence.

```tsx
<>
  <BlurReveal text="Build" blur={16} fontSize={96} />
  <BlurReveal text="Faster" blur={16} fontSize={96} />
</>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to reveal |
| blur | number | 10 | Initial blur radius in pixels. Animates down to 0. |
| fontSize | number | 48 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| color | string | "#171717" | Text color (any valid CSS color). |
| className | string | - | Optional className passed to the underlying span. |

## Notes

- **Load fonts before render** — Make sure your font is loaded before the first frame renders. Use @remotion/google-fonts or @remotion/fonts so the blur effect doesn't apply to a fallback system font.
- **Performance** — Heavy blur on large text blocks is expensive. If you stack multiple BlurReveals, consider rendering them in their own Sequence to keep render time predictable.
