# StaggeredBentoGrid

## Description

Cards pop into a bento grid one after another with a spring. Maps an array of items into a CSS grid and wraps each in a Sequence offset by staggerDelay frames. Each card uses spring() for scale and opacity.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/staggered-bento-grid
```

## Usage

### Basic Usage

Cards cascade into a bento layout. Use for feature showcases.

```tsx
<StaggeredBentoGrid staggerDelay={8} columns={3} items={[{ title: "Fast", body: "Built on Remotion", span: 2 }, { title: "Animated", body: "Spring physics" }]} />
```

### Custom Grid

Use with more columns and custom styling.

```tsx
<StaggeredBentoGrid staggerDelay={6} columns={4} items={cards} cardColor="#1e293b" textColor="#e2e8f0" background="#0f172a" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| items | Array<{title:string; body?:string; span?:1\|2}> | 6 sample cards | Cards to render. |
| staggerDelay | number | 8 | Frames between each card's entrance. |
| columns | number | 3 | Number of grid columns. |
| background | string | "#0a0a0a" | Outer background. |
| cardColor | string | "#1a1a1a" | Card background. |
| textColor | string | "white" | Card text color. |
| className | string | - | Optional className. |

## Notes

- **Sequence per card** — Wrapping each card in Sequence resets `useCurrentFrame()` to 0 inside that card, so the spring math stays clean.
