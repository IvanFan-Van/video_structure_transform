# SwipeTransitionWipe

## Description

A mobile-style swipe transition where the outgoing scene flicks off-screen and the new one slides in beside it, with a parallax background and a darkening trail. Two scenes sit side-by-side in a flex slider; one spring drives `translateX`. A parallax background layer moves at a fraction of speed to fake depth, and the outgoing scene darkens.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/swipe-transition-wipe
```

## Usage

### Basic Usage

A snappy mobile-style swipe between scenes.

```tsx
<SwipeTransitionWipe direction="left" swipeAt={30} labelA="Before" labelB="After" />
```

### Custom Scenes

Use custom scene content with parallax and dimming.

```tsx
<SwipeTransitionWipe sceneA={<FirstScene />} sceneB={<SecondScene />} direction="right" swipeAt={50} parallaxFactor={0.5} dimStrength={0.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| sceneA | ReactNode | - | Override first scene. |
| sceneB | ReactNode | - | Override second scene. |
| labelA | string | "First" | Label on default scene A. |
| labelB | string | "Second" | Label on default scene B. |
| colorA1 | string | "#0ea5e9" | Scene A gradient stop 1. |
| colorA2 | string | "#1e3a8a" | Scene A gradient stop 2. |
| colorB1 | string | "#f97316" | Scene B gradient stop 1. |
| colorB2 | string | "#9333ea" | Scene B gradient stop 2. |
| background | string | "#050505" | Stage background. |
| direction | "left" \| "right" | "left" | Swipe direction. |
| swipeAt | number | 30 | Frame swipe spring fires. |
| parallaxFactor | number | 0.6 | Background speed vs foreground. |
| dimStrength | number | 0.4 | Max opacity of darkening overlay. |
| speed | number | 1 | Speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **One spring, two layers** — Same spring value drives foreground and parallax, so they never desync.
- **Keep the flick snappy** — Swipes feel natural when fast. Default spring resolves in ~50 frames.
