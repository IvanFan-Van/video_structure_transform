# PulsingIndicator

## Description

Continuous pulsing dot for loading and "live" states. A tiny UI primitive for signalling activity. An inner dot breathes via Math.sin(frame) mapped to scale and opacity, while an outer ring "pings" outward on a separate phase.

## Installation

pnpm dlx shadcn@latest add @remocn/pulsing-indicator

## Usage

### Basic Usage

A green pulsing dot to indicate a live or connected state.

```tsx
<PulsingIndicator color="#22c55e" size={16} speed={8} />
```

### Loading Pulse

A slower, larger pulse in a brand color for loading states.

```tsx
<PulsingIndicator color="#3b82f6" size={24} speed={12} background="#111827" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| color | string | "#22c55e" | Dot and ring color. |
| size | number | 16 | Dot diameter in pixels. The ring expands beyond this. |
| speed | number | 8 | Lower = faster pulse. The value is the frame divisor inside Math.sin. |
| background | string | "white" | Background color of the surrounding container. |
| className | string | - | Optional className passed to the outer container. |

## Notes

Deterministic pulse — Animation is driven by Math.sin(frame / speed) — no setInterval, no randomness, fully frame-accurate on every render.
