# ChangelogBite

## Description

Seamlessly looping square card showing a before/after diff with a frosted glass wipe and a pulsing New pill. A square (1080x1080) micro-loop for changelog posts and social. The loop is gapless: the first 10 and last 15 frames mirror each other so you can export straight to GIF/MP4 without a visible seam.

## Installation

```
pnpm dlx shadcn@latest add @remocn/changelog-bite
```

## Usage

### Changelog Post

A looping square card for social media changelog posts.

```tsx
<ChangelogBite label="New" title="Inline diff view" accent="#FFB38E" />
```

### Portrait Format

Use portrait format for vertical social posts.

```tsx
<ChangelogBite label="New" title="Feature update" format="portrait" accent="#7c3aed" background="#0f0f12" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| label | string | "New" | Text in pulsing pill. |
| title | string | "Inline diff view" | Caption above diff. |
| oldContent | ReactNode | — | Custom before content. |
| newContent | ReactNode | — | Custom after content. |
| format | "square"\|"portrait" | "square" | Card aspect ratio. |
| background | string | "#141318" | Stage background. |
| cardBackground | string | "rgba(20,19,24,0.92)" | Card fill. |
| accent | string | "#FFB38E" | Pill, seam, and badge color. |
| speed | number | 1 | Speed multiplier. |
| className | string | — | Optional className. |

## Notes

The loop is already seamless — First 10 and last 15 frames mirror each other. Don't add a separate fade-in/fade-out — you'll double up the envelope.
