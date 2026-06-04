# PerspectiveMarquee

## Description

A 3D-tilted infinite marquee with depth-of-field blur on items rolling toward the horizon. Takes the seamless modulo-based loop from InfiniteMarquee and tilts it in 3D space using CSS perspective and rotateX/Y. Items further from the viewport center receive progressively heavier filter: blur() and lower opacity, mimicking depth of field.

## Installation

```
pnpm dlx shadcn@latest add @remocn/perspective-marquee
```

## Usage

### Integration Wall

Display partner logos or integration names in a tilted 3D marquee. Use for ecosystem showcases.

```
<PerspectiveMarquee items={["Vercel", "Linear", "Stripe", "Figma"]} rotateY={-28} pixelsPerFrame={2} />
```

### Dark Theme Logo Wall

Use a dark background with light text for a premium cinematic effect.

```
<PerspectiveMarquee items={["React", "Next.js", "Remotion", "Tailwind"]} color="#fafafa" background="#050505" fadeColor="#050505" rotateY={25} pixelsPerFrame={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| items | string[] | ["Vercel","Linear","Stripe","Figma","Notion","Raycast","Arc","Cursor"] | Items rendered in the marquee. Repeated three times for a seamless loop. |
| fontSize | number | 84 | Font size in pixels. |
| color | string | "#fafafa" | Text color of each item. |
| fontWeight | number | 700 | CSS font-weight. |
| pixelsPerFrame | number | 2 | Horizontal scroll speed in pixels per frame. |
| rotateY | number | -28 | Y-axis rotation in degrees. |
| rotateX | number | 8 | X-axis rotation in degrees. |
| perspective | number | 1200 | CSS perspective in pixels on the parent. |
| fadeColor | string | "#050505" | Color used in the edge vignette gradients. |
| background | string | "#050505" | Root container background color. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className passed to the root container. |

## Notes

- **Slow is hypnotic** — Keep `pixelsPerFrame` between 1 and 3. The 3D tilt amplifies perceived speed — anything faster reads as motion sickness.
- **Match fadeColor to background** — The vignette assumes `fadeColor === background`. If they differ you will see hard edges.
