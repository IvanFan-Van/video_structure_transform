# AIGenerateOverlay

## Description

A "thinking" overlay for AI-driven UI — source image blurs out under a shimmering dot grid while a glassy pill pulses, then the new image fades in on top. Every layer is driven by the current frame so it renders deterministically.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/ai-generate-overlay
```

## Usage

### Basic Usage

Show an AI generation in progress with blur, shimmer, and reveal.

```tsx
<AIGenerateOverlay maxBlur={20} blurStartFrame={20} blurPeakFrame={40} revealStartFrame={110} pillText="Generating…" accent="#a78bfa" />
```

### Custom Images

Use with real image backgrounds for a real AI flow demo.

```tsx
<AIGenerateOverlay sourceImageBg="url(...)" generatedImageBg="url(...)" blurStartFrame={30} blurPeakFrame={50} revealStartFrame={130} accent="#22c55e" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| maxBlur | number | 20 | Peak blur radius on source image. |
| blurStartFrame | number | 20 | Frame blur ramp begins. |
| blurPeakFrame | number | 40 | Frame blur reaches maxBlur. |
| revealStartFrame | number | 110 | Frame generated-image fade-in fires. |
| pillText | string | "Generating…" | Label in centered glass pill. |
| accent | string | "#a78bfa" | Accent for status dot and glow. |
| background | string | "#050505" | Page background. |
| sourceImageBg | string | warm linear-gradient | CSS background for source image. |
| generatedImageBg | string | cool radial+linear | CSS background for generated image. |
| dotColor | string | "#ffffff" | Dot grid fill. |
| dotSize | number | 1.2 | Dot radius. |
| dotSpacing | number | 20 | Pattern tile spacing. |
| speed | number | 1 | Speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **Deterministic shimmer** — Dot grid jitter is `Math.sin(frame/6)*0.05` — a pure function of frame.
- **Heavy blur is expensive** — `filter: blur(20px)` on a viewport-sized layer is one of the costlier CSS effects.
