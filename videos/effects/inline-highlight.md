# InlineHighlight

## Description

Animate one word inside a sentence from a base color to a brand color. A typography primitive that splits a sentence into before, highlight, and after parts and animates the color of the middle word using interpolateColors from Remotion.

## Installation

pnpm dlx shadcn@latest add @remocn/inline-highlight

## Usage

### Basic Usage

**Brand Emphasis**: Highlight a brand or product name within a sentence. Use for emphasizing a key term.

```
<InlineHighlight before="Ship faster with " highlight="remocn" highlightColor="#ff5e3a" fontSize={72} />
```

### Feature Callout

Draw attention to a feature keyword in a longer sentence.

```
<InlineHighlight before="Now with " highlight="AI-powered" after=" suggestions" highlightColor="#7c3aed" fontSize={48} baseColor="#52525b" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| before | string | required | Text rendered before the highlighted word. |
| highlight | string | required | The word that animates color. |
| after | string | "" | Text rendered after the highlighted word. |
| baseColor | string | "#171717" | Starting color of the highlighted word and color of the surrounding text. |
| highlightColor | string | "#ff5e3a" | Final color of the highlighted word. |
| fontSize | number | 48 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| className | string | - | Optional className passed to the underlying span. |

## Notes

Smooth color blending — interpolateColors blends in RGB space, so transitions between contrasting hues stay smooth without going through muddy intermediate colors.
