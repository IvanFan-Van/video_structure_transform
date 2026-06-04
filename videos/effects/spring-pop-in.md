# SpringPopIn

## Description

Elastic scale-in wrapper for any element. A UI primitive that wraps its children in a spring-driven transform: scale(). Based directly on Remotion's spring() so timing and overshoot stay framerate-independent.

## Installation

pnpm dlx shadcn@latest add @remocn/spring-pop-in

## Usage

### Basic Usage

Wrap a card or element to pop it into view with elastic bounce.

```tsx
<SpringPopIn damping={12}>
  <div style={{ padding: 24, background: "#111", color: "white" }}>Hello</div>
</SpringPopIn>
```

### Heavy Bounce

Use lower damping for more exaggerated bounce effect, good for playful UI reveals.

```tsx
<SpringPopIn damping={8} mass={1.5} stiffness={150} delayInFrames={10}>
  <MyComponent />
</SpringPopIn>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| children | ReactNode | required | Element(s) to animate. |
| damping | number | 12 | Spring damping. Lower = more bounce. |
| mass | number | 1 | Spring mass. |
| stiffness | number | 100 | Spring stiffness. |
| delayInFrames | number | 0 | Delay before the spring starts, in frames. |
| className | string | - | Optional className passed to the outer container. |

## Notes

Transform origin — The scale is applied with transform-origin: center. Override it via className if you need corner-anchored growth.
