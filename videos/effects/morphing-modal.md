# MorphingModal

## Description

A bento card lifts off the grid and blooms into a full-screen modal driven by a single heavy spring. Five properties — `top`, `left`, `width`, `height`, and `borderRadius` — are all driven by one spring with high mass and low stiffness. Source content fades out in the first third, modal content fades in only in the last third.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/morphing-modal
```

## Usage

### Basic Usage

A card morphs into a full-screen modal. Use for UI expansion demos.

```tsx
<MorphingModal from={{ left: 460, top: 260, width: 360, height: 200 }} to={{ left: 80, top: 60, width: 1120, height: 600 }} morphAt={30} />
```

### Custom Content

Override with custom source card and modal content.

```tsx
<MorphingModal from={cardRect} to={modalRect} morphAt={45} source={<MyCard />} modal={<MyModal />} borderRadiusFrom={16} borderRadiusTo={8} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | {top,left,width,height} | - | Source rect before blooming. |
| to | {top,left,width,height} | - | Target rect of the modal. |
| borderRadiusFrom | number | 24 | Border radius of source card. |
| borderRadiusTo | number | 0 | Border radius of modal. |
| morphAt | number | 30 | Frame morph spring fires. |
| background | string | "#050505" | Page background. |
| cardColor | string | "#0a0a0a" | Card/modal surface. |
| textColor | string | "#fafafa" | Heading color. |
| mutedColor | string | "#71717a" | Body copy color. |
| sourceTitle | string | "Compose video" | Heading on source card. |
| sourceBody | string | "Click to start a new project" | Body on source card. |
| modalTitle | string | "New project" | Heading after morph. |
| modalBody | string | - | Body after morph. |
| source | ReactNode | - | Override source card. |
| modal | ReactNode | - | Override modal content. |
| speed | number | 1 | Speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **One spring, five properties** — All rect properties from a single spring value prevents independent springs drifting out of phase.
- **Asymmetric content fade** — Source fades over `[0, 0.33]`, modal arrives over `[0.66, 1]`. The empty middle third makes the bloom feel intentional.
