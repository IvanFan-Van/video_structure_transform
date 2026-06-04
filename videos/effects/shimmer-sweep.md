# ShimmerSweep

## Description

A bright shine travels across muted text to draw attention. A typography primitive that layers a gradient shine on top of muted base text using background-clip: text. The gradient sweeps horizontally across the text, lighting up letters as it passes. Great for AI and generation moments.

## Installation

pnpm dlx shadcn@latest add @remocn/shimmer-sweep

## Usage

### Basic Usage

**Loading State**: A subtle shimmer across dim text, great for AI generation or loading moments.

```
<ShimmerSweep text="Generating..." fontSize={96} />
```

### Attention Grab

A bright sweep across dark text on a light background. Use for drawing the viewer's eye.

```
<ShimmerSweep text="New Feature" baseColor="#d4d4d8" shineColor="#3b82f6" fontSize={72} speed={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to animate the shine across. |
| baseColor | string | "#3f3f46" | Dim color of the text underneath the shine. |
| shineColor | string | "#fafafa" | Color of the moving highlight gradient. |
| fontSize | number | 96 | Font size in pixels. |
| fontWeight | number | 700 | CSS font-weight. |
| speed | number | 1 | Multiplier for animation speed. |
| className | string | - | Optional className passed to the shine span. |

## Notes

Background-clip support — This effect relies on background-clip: text. It works in all modern browsers and Remotion's Chromium renderer.
