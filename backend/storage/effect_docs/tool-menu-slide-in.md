# ToolMenuSlideIn

## Description

A horizontal pill of tool icons whips up from below the canvas, then each icon pops in with a staggered spring. A snappy editor-style toolbar reveal. The frosted-glass panel slides up via a stiff, low-mass spring — no overshoot — and each icon pops from scale 0 to 1 with cascaded delay.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/tool-menu-slide-in
```

## Usage

### Basic Usage

A toolbar slides up from below with staggered icon reveals.

```tsx
<ToolMenuSlideIn panelStartFrame={18} iconStagger={4} iconCount={5} accent="#a78bfa" />
```

### Dark Editor

Use with a dark theme and more icons.

```tsx
<ToolMenuSlideIn panelStartFrame={24} iconStagger={3} iconCount={7} accent="#22c55e" panelColor="rgba(10,10,15,0.85)" background="#050508" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| panelStartFrame | number | 18 | Frame panel begins sliding up. |
| iconStagger | number | 4 | Frames delay between each icon. |
| iconCount | number | 5 | Number of tool icons (1-8). |
| accent | string | "#a78bfa" | Accent for active icon glow. |
| panelColor | string | "rgba(18,18,22,0.72)" | Frosted-glass fill. |
| background | string | "#070708" | Editor canvas background. |
| iconBg | string | "rgba(255,255,255,0.06)" | Inactive icon background. |
| speed | number | 1 | Speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **Snappy, not bouncy** — The spring uses `stiffness: 320`, `damping: 20`, `mass: 0.6`. Tool menus that bounce read as toy-like.
- **Sequence resets the icon clock** — Each icon is inside its own Sequence so the spring always sees frame 0 at start.
