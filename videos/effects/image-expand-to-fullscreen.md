# ImageExpandToFullscreen

## Description

A thumbnail in a feed post lifts off the card and morphs seamlessly into a fullscreen editor, with toolbars sliding in to meet it. A shared-element transition. The image starts as a thumbnail in a fake feed post — when the morph fires, the post UI fades, the dark editor canvas swells in, and the image rides a single spring to its fullscreen rect.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/image-expand-to-fullscreen
```

## Usage

### Basic Usage

A feed thumbnail expands into a fullscreen editor. Use for photo-editing app demos.

```tsx
<ImageExpandToFullscreen from={{ left: 460, top: 280, width: 360, height: 200 }} to={{ left: 200, top: 120, width: 880, height: 480 }} morphAt={30} />
```

### Custom Feed

Customize the feed post appearance before the expansion.

```tsx
<ImageExpandToFullscreen from={thumbRect} to={editorRect} morphAt={40} postAuthor="Alex Chen" postBody="Check out this design" accent="#ff5e3a" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | {top,left,width,height} | - | Source rect of thumbnail. |
| to | {top,left,width,height} | - | Target rect of editor image. |
| borderRadiusFrom | number | 12 | Thumbnail border radius. |
| borderRadiusTo | number | 16 | Editor image border radius. |
| morphAt | number | 30 | Frame morph fires. |
| imageColorA | string | "#ff6b6b" | First gradient stop. |
| imageColorB | string | "#845ec2" | Second gradient stop. |
| imageColorC | string | "#4d8dff" | Third gradient stop. |
| feedBackground | string | "#f4f4f5" | Feed page background. |
| editorBackground | string | "#0a0a0a" | Editor canvas background. |
| accent | string | "#fafafa" | Toolbar text and active tool accent. |
| postAuthor | string | "Maya Larsson" | Author name on feed post. |
| postBody | string | - | Caption on feed post. |
| speed | number | 1 | Speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **One spring, four properties** — `top`, `left`, `width`, and `height` all from a single `spring()` value.
- **Toolbars arrive last** — Toolbars slide in across `[0.5, 1]` of the morph spring, summoned by the image landing.
