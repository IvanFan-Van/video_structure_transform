# ProductLaunchTrailer

## Description

Cinematic Product Hunt teaser with logo pulse, zoom-through, 3D bento fly-over, and a confetti version drop. Built around four pastel tokens — peach, lavender, mint, and obsidian background. Every camera move uses soft cubic-bezier easing for a tactile feel.

## Installation

```
pnpm dlx shadcn@latest add @remocn/product-launch-trailer
```

## Usage

### Product Launch

A full launch trailer with logo, zoom, fly-over, and confetti. Use for product launch announcements.

```tsx
<ProductLaunchTrailer logoLabel="R" productName="Remocn" versionLabel="v1.0 is live" />
```

### Custom Branding

Use custom pastel accent colors for your brand.

```tsx
<ProductLaunchTrailer logoLabel="M" productName="MyApp" versionLabel="v2.0 is here" accentPeach="#FFB38E" accentLavender="#D4B3FF" accentMint="#A1EEBD" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| logoLabel | string | "R" | Single character inside centered logo squircle. |
| productName | string | "Remocn" | Subtitle below pulsing logo. |
| versionLabel | string | "v1.0 is live" | Headline in outro. |
| accentPeach | string | "#FFB38E" | Peach accent for card shadows and confetti. |
| accentLavender | string | "#D4B3FF" | Lavender for logo glow and code border. |
| accentMint | string | "#A1EEBD" | Mint for traffic lights and confetti. |
| background | string | "#141318" | Stage background. |
| speed | number | 1 | Speed multiplier. |
| className | string | — | Optional className. |

## Notes

Audio hooks are stubbed — The composition leaves // TODO(audio) markers at frames 38 and 200 for TransitionWhoosh and SuccessChime.

3D camera — Uses perspective: 2000px and transformStyle: preserve-3d. Render at top level for best results.
