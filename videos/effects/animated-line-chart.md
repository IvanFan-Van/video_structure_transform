# AnimatedLineChart

## Description

A line chart whose path draws on from left to right. A data-viz primitive built with SVG path. The full path length is computed analytically (sum of segment distances) and animated via strokeDasharray + strokeDashoffset. An optional leading dot rides the head of the line as it draws.

## Installation

```
pnpm dlx shadcn@latest add @remocn/animated-line-chart
```

## Usage

### Basic Usage

"Revenue Chart": An animated line chart drawing a trend line. Use for data visualizations.

```tsx
<AnimatedLineChart data={[12, 19, 8, 15, 22, 18, 28, 25, 32]} strokeColor="#22c55e" />
```

### Compact Chart

A smaller chart without the dot indicator.

```tsx
<AnimatedLineChart
  data={[100, 200, 150, 300, 250, 400]}
  width={600}
  height={300}
  strokeColor="#3b82f6"
  strokeWidth={3}
  showDot={false}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| data | number[] | [12,19,8,15,22,18,28,25,32] | Y-values. Auto-scaled to available height. |
| width | number | 1000 | SVG viewBox width. |
| height | number | 500 | SVG viewBox height. |
| strokeColor | string | "#22c55e" | Line stroke color. |
| strokeWidth | number | 4 | Line stroke width. |
| background | string | "#0a0a0a" | Outer background. |
| gridColor | string | "#27272a" | Grid and axis line color. |
| showDot | boolean | true | Render a dot at the leading edge. |
| className | string | - | Optional className. |

## Notes

- **No getTotalLength()** — Path length is computed analytically to avoid useEffect and DOM measurement.
- **Data range** — Auto-scales to min/max of data. If all values are equal, the line is drawn at the top.
