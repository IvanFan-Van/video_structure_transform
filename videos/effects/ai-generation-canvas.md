# AIGenerationCanvas

## Description

A prompt input morphs into a dashboard header, then skeletons flip to reveal generated content. A four-phase composition: prompt types into a centered input, the input springs into a header bar, skeletons fade in, then each card flips on its Y axis to reveal rendered dashboard content with a staggered cascade.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/ai-generation-canvas
```

## Usage

### Basic Usage

An AI generation flow from prompt to result. Use for AI product demos.

```tsx
<AIGenerationCanvas prompt="Generate a dashboard" accentColor="#7c3aed" cardCount={4} />
```

### More Cards

Generate more dashboard cards for a richer result.

```tsx
<AIGenerationCanvas prompt="Show me analytics" accentColor="#22c55e" cardCount={6} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| prompt | `string` | `"Generate a dashboard"` | Text typed into input. |
| accentColor | `string` | `"#7c3aed"` | Brand color for input border, shimmer, and chart accents. |
| cardCount | `number` | `4` | Number of skeleton cards rendered. |
| className | `string` | — | Optional className. |

## Notes

Skeletons should not feel like loading spinners — The shimmer is intentionally tinted with the accent color at low alpha. That reframes the wait as anticipation.
