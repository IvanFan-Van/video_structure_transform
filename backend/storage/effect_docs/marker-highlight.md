# MarkerHighlight

## Description

A colored marker block draws behind a phrase while the text color shifts. A typography primitive that mimics a physical highlighter sweeping behind a word. The colored block grows from left to right via a spring, and the target text color interpolates to a contrast color.

## Installation

pnpm dlx shadcn@latest add @remocn/marker-highlight

## Usage

### Basic Usage

**Classic Marker**: A bright yellow marker sweeps behind text. Use for emphasize text like a physical highlighter.

```
<MarkerHighlight before="Ship it " highlight="fast" after="." markerColor="#facc15" />
```

### Neon Invert

Use a neon marker on a dark background with inverted text color for a dramatic effect.

```
<MarkerHighlight before="Launch " highlight="now" markerColor="#ff0080" baseColor="#fafafa" highlightedTextColor="#0a0a0a" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| before | string | "" | Text that appears before the highlighted phrase. |
| highlight | string | required | The phrase the marker draws behind. |
| after | string | "" | Text that appears after the highlighted phrase. |
| markerColor | string | "#facc15" | Color of the marker block. |
| baseColor | string | "#171717" | Color of the surrounding text. |
| highlightedTextColor | string | "#171717" | Final color of the highlighted phrase once the marker is drawn. |
| fontSize | number | 72 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| speed | number | 1 | Multiplier for animation speed. |
| className | string | - | Optional className passed to the outer text span. |

## Notes

Pick a contrast color — For the classic marker effect, keep markerColor bright and leave highlightedTextColor dark. Or invert both for a neon look on dark backgrounds.
