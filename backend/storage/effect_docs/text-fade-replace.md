# TextFadeReplace

## Description

Cross-fade between two strings on the same line without layout shift. A typography primitive that swaps one string for another in place. Both spans are absolutely positioned in a relative container so they never push each other in the DOM during the fade. Includes a StrikethroughReplace variant.

## Installation

```
pnpm dlx shadcn@latest add @remocn/text-fade-replace
```

## Usage

### Value Swap

Cross-fade between two text values. Use for showing before/after states.

```
<TextFadeReplace from="Before" to="After" fontSize={72} />
```

### Strikethrough Replace

Strike through old text then reveal new text. Use for "old way vs new way" comparisons.

```
<StrikethroughReplace from="Slow setup" to="Instant setup" lineColor="#ff5e3a" fontSize={72} />
```

```
pnpm dlx shadcn@latest add @remocn/strikethrough-replace
```

## Props

### TextFadeReplace

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | string | required | Initial text shown at the start of the composition. |
| to | string | required | Replacement text shown at the end of the composition. |
| fontSize | number | 48 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| color | string | "#171717" | Text color for both strings. |
| className | string | - | Optional className passed to both spans. |

### StrikethroughReplace

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | string | required | Original text that gets struck through. |
| to | string | required | Replacement text that fades in. |
| lineColor | string | "#ff5e3a" | Color of the strikethrough bar. |
| fontSize | number | 48 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| color | string | "#171717" | Text color for both strings. |
| className | string | - | Optional className passed to the underlying spans. |

## Notes

- **Absolute positioning** — Both texts are `position: absolute` inside a zero-size relative anchor. This guarantees there is no layout reflow during the cross-fade.
- **Long strings** — If your strings are very long, make sure your composition is wide enough — neither span will wrap because they use `whiteSpace: nowrap`.
- **Three phases** — The strikethrough animation runs in three phases tied to `durationInFrames`: draw the strike line (0-40%), cross-fade to the new text (40-60%), then hold (60-100%).
