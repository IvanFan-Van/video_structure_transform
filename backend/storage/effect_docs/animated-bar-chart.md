# AnimatedBarChart

## Description

Bars spring up from the baseline with a staggered cascade. A data-viz primitive that renders SVG rect bars and animates each one with a spring() driven scaleY transform. Each bar is offset by staggerFrames, producing a clean cascade.

## Installation

```
pnpm dlx shadcn@latest add @remocn/animated-bar-chart
```

## Usage

### Basic Usage

"Bar Chart": Bars animate up with staggered springs. Use for comparing values.

```tsx
<AnimatedBarChart data={[35, 60, 45, 80, 55, 70, 90, 65]} barColor="#0ea5e9" />
```

### Labeled Chart

Add labels under each bar for categorical data.

```tsx
<AnimatedBarChart
  data={[45, 72, 38, 91, 55]}
  labels={["Mon", "Tue", "Wed", "Thu", "Fri"]}
  barColor="#a855f7"
  staggerFrames={4}
  gap={24}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| data | number[] | [35,60,45,80,55,70,90,65] | Bar values. Auto-scaled. |
| labels | string[] | - | Optional labels under each bar. |
| width | number | 1000 | SVG viewBox width. |
| height | number | 500 | SVG viewBox height. |
| barColor | string | "#0ea5e9" | Bar fill color. |
| background | string | "#0a0a0a" | Outer background. |
| gap | number | 16 | Pixel gap between bars. |
| staggerFrames | number | 6 | Frame delay per successive bar. |
| className | string | - | Optional className. |

## Notes

- **Transform origin** — Each bar uses `transformOrigin: bottom` so the animation grows from the baseline. Uses `transformBox: fill-box` to scope the origin to the rect's box.
