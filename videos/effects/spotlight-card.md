# spotlight-card

## Description

A card with a moonlight-cool radial spotlight that follows a synthetic cursor and lights up its microborder. A bento-style card in the dark. A virtual cursor traces a slow Lissajous figure-8 across the card surface; under it, a wide radial gradient softly lights the inside while a brighter, narrower gradient bleeds through a 1px wrapper to pick out the microborder.

## Installation

pnpm dlx shadcn@latest add @remocn/spotlight-card

## Usage

### Basic Usage

A premium dark card with moving spotlight. Use for feature showcases.

```
<SpotlightCard title="Your feature" body="Two-line description goes here." />
```

### Custom Content Card

Override with custom children for flexible card content.

```
<SpotlightCard cardWidth={600} cardHeight={400} glowSize={800} glowOpacity={0.06}>
  <div style={{ padding: 32, color: "#fafafa" }}>
    <h2>Custom Content</h2>
    <p>Any React node can go here.</p>
  </div>
</SpotlightCard>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| title | string | Spotlight Card | Heading when no children. |
| body | string | Soft radial light follows the cursor... | Body copy when no children. |
| cardWidth | number | 520 | Card width in pixels. |
| cardHeight | number | 320 | Card height in pixels. |
| glowSize | number | 600 | Diameter of the radial spotlight. |
| glowOpacity | number | 0.08 | Maximum alpha of the surface glow. |
| background | string | #050505 | Page background color. |
| cardColor | string | #0a0a0a | Card surface color. |
| textColor | string | #fafafa | Heading color. |
| mutedColor | string | #71717a | Body copy color. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className. |
| children | ReactNode | - | Override default title/body with custom content. |

## Notes

Keep the light cold — Use white or near-white glow at very low opacity (0.05-0.1). Brand-colored glow tends to read as cheap when amplified by the radial gradient.
