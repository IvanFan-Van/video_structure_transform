# InfiniteMarquee

## Description

A continuously scrolling horizontal text strip that loops seamlessly. A typography primitive that translates a row of duplicated text spans on the X axis at a fixed pixel-per-frame rate. The offset is taken mod the approximate width of one repetition so the loop is seamless and fully deterministic.

## Installation

```
pnpm dlx shadcn@latest add @remocn/infinite-marquee
```

## Usage

### Scrolling Ticker

A text banner scrolling across the screen. Use for hero sections or footer tickers.

```
<InfiniteMarquee text="ship · build · animate · " pixelsPerFrame={4} stroke />
```

### Filled Text Marquee

A fast-scrolling filled text banner with custom color.

```
<InfiniteMarquee text="BUILD FASTER · " fontSize={80} pixelsPerFrame={6} color="#3b82f6" speed={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | "ship · build · animate · " | Text repeated across the marquee. Include trailing whitespace or punctuation for spacing. |
| fontSize | number | 120 | Font size in pixels. |
| color | string | "#171717" | Text color when stroke is false. |
| fontWeight | number | 900 | CSS font-weight. |
| pixelsPerFrame | number | 4 | Horizontal scroll speed in pixels per frame. |
| stroke | boolean | false | Render outlined text via -webkit-text-stroke instead of filled. |
| strokeColor | string | "#171717" | Stroke color used when stroke is true. |
| background | string | "#fafafa" | Background color of the root container. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className passed to the translating row. |

## Notes

- **Seamless looping** — Width is approximated as `text.length * fontSize * 0.55`. For very wide or very narrow fonts you may see a small jump on loop — tweak the multiplier to match your typeface.
- **No layout reads** — This component intentionally avoids `useRef` / measurement so it stays render-deterministic.
