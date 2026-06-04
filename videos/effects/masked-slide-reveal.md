# MaskedSlideReveal

## Description

Words rise out of an invisible horizontal mask with a springy motion. A strict, architectural typography primitive: each word is wrapped in a fixed-height container with overflow: hidden, and the inner span springs upward from translateY(100%) to 0. The result is text that grows out of an invisible baseline.

## Installation

```
pnpm dlx shadcn@latest add @remocn/masked-slide-reveal
```

## Usage

### Basic Usage

Use for clean, architectural titles that reveal from a baseline.

```tsx
<MaskedSlideReveal text="Built for Remotion" />
```

### Fast Staggered Reveal

Use smaller staggerDelay for a quicker, snappier reveal.

```tsx
<MaskedSlideReveal text="Create. Render. Ship." staggerDelay={2} speed={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to animate. Split on spaces into words. |
| staggerDelay | number | 3 | Frames between the start of each word's spring animation. |
| fontSize | number | 72 | Font size in pixels. |
| fontWeight | number | 700 | CSS font-weight. |
| color | string | "#171717" | Text color (any valid CSS color). |
| speed | number | 1 | Playback speed multiplier (1 = normal, 2 = twice as fast). |
| className | string | - | Optional className passed to the underlying span. |

## Notes

- **Mind descenders** — The mask uses lineHeight: 1, which clips letter descenders (g, y, p) by design. If you need extra room, wrap the component in your own container with padding.
