# StaggeredFadeUp

## Description

Words slide up and fade in sequentially with a wave-like cascade. A typography primitive that splits text into words and animates each one with a small delay, sliding up from a configurable distance while fading in. Great for hero titles and intro shots.

## Installation

```
pnpm dlx shadcn@latest add @remocn/staggered-fade-up
```

## Usage

### Basic Usage

Use for punchy hero titles at the start of a video.

```tsx
<StaggeredFadeUp text="Ship videos faster" staggerDelay={4} />
```

### Cinematic Slow Reveal

Use larger staggerDelay and distance for a more dramatic, cinematic feel.

```tsx
<StaggeredFadeUp text="The future of video" staggerDelay={8} distance={40} speed={0.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to animate. Split on spaces into words. |
| staggerDelay | number | 4 | Frames between the start of each word's animation. |
| distance | number | 20 | Vertical distance in pixels each word travels upward. |
| fontSize | number | 72 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| color | string | "#171717" | Text color (any valid CSS color). |
| speed | number | 1 | Playback speed multiplier (1 = normal, 2 = twice as fast). |
| className | string | - | Optional className passed to the underlying span. |

## Notes

- **Tune the stagger** — A smaller staggerDelay (2-3 frames) feels punchy, larger values (6-8) feel cinematic. Pair with speed to fit your composition's pacing.
