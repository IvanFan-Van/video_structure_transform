# PricingTierFocus

## Description

Highlight the recommended pricing tier by dimming and blurring its neighbors. Stages a classic three-tier pricing table and then dramatically focuses the camera on the recommended plan. The focused card scales up, lifts off with a heavy drop shadow, while side cards retreat into a soft brightness-dimmed blur. A subtle shimmer sweeps across the CTA button.

## Installation

```
pnpm dlx shadcn@latest add @remocn/pricing-tier-focus
```

## Usage

### Pricing Focus

Highlight the middle (Pro) pricing tier. Use for pricing page demos.

```tsx
<PricingTierFocus focusedTier={1} accentColor="#22c55e" />
```

### Enterprise Focus

Focus on the Enterprise tier instead.

```tsx
<PricingTierFocus focusedTier={2} accentColor="#7c3aed" speed={1.2} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| focusedTier | 0\|1\|2 | 1 | Index of tier to highlight (0=Free, 1=Pro, 2=Enterprise). |
| accentColor | string | "#22c55e" | Brand color for badge, checkmarks, and CTA. |
| speed | number | 1 | Multiplier for global timing. |
| className | string | — | Optional className. |

## Notes

Shimmer is the closer — The focus animation lands the visual hierarchy, but the shimmer sweep on the Pro CTA button makes the moment feel cinematic.
