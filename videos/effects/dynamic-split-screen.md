# ChatToPreviewLayout

## Description

Cinematic two-column split where one panel shrinks and the other expands into view. Animates the flex-basis of two side-by-side panels — perfect for chat-to-preview handoffs, before/after comparisons, or any moment where one workspace cedes real estate to another.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/chat-to-preview-layout
```

## Usage

### Basic Usage

A chat panel shrinks as a preview panel expands. Use for AI product demos.

```tsx
<ChatToPreviewLayout chat={<MyChat />} preview={<MyPreview />} />
```

### Custom Ratios

Custom split ratios for different layout transitions.

```tsx
<ChatToPreviewLayout chat={<PanelA />} preview={<PanelB />} startChatRatio={0.6} endChatRatio={0.3} background="#050505" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| chat | ReactNode | - | The chat panel. |
| preview | ReactNode | - | The preview panel. |
| startChatRatio | number | 0.5 | Initial fraction of width for chat panel (0..1). |
| endChatRatio | number | 0.25 | Final fraction of width for chat panel. |
| background | string | "#0a0a0a" | Outer background. |
| className | string | - | Optional className. |

## Notes

- **Why flex-basis is OK here** — Most Remotion animations should stick to transform/opacity. This component is an exception because the resizing of two panels IS the effect. Keep both panels' contents inside an `overflow: hidden` wrapper.
