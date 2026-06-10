# FrostedGlassWipe

## Description

Elegant scene transition through a sliding pane of frosted glass. Slides a pane of frosted glass across the screen between two scenes. The outgoing scene blurs beneath the glass; once the pane crosses the midpoint, the incoming scene is revealed. Uses backdrop-filter for the glass and transform: translateX for movement.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/frosted-glass-wipe
```

## Usage

### Basic Usage

A frosted glass pane wipes between two scenes. Use for elegant, premium transitions.

```tsx
<FrostedGlassWipe from={<SceneA />} to={<SceneB />} />
```

### Heavy Glass

Increase blur for a more substantial glass feel.

```tsx
<FrostedGlassWipe from={<Intro />} to={<Main />} glassBlur={32} transitionDuration={40} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | ReactNode | - | Outgoing scene. |
| to | ReactNode | - | Incoming scene. |
| transitionStart | number | durationInFrames * 0.4 | Frame wipe begins. |
| transitionDuration | number | 30 | Wipe length in frames. |
| glassBlur | number | 24 | Backdrop blur radius in pixels. |
| className | string | - | Optional className. |

## Notes

Give the glass physical properties — The pane uses thin 1px white borders so light catches as it slides. Keep blur 16-32px for substance.
