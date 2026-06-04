# toast-notification

## Description

System-style toast that pops in, holds, then slides out. A micro-interaction primitive that drives a toast through three phases — spring()-based enter (translateY + opacity), a hold, and an interpolate-based exit. Position is anchored to the bottom-right of the frame.

## Installation

pnpm dlx shadcn@latest add @remocn/toast-notification

## Usage

### Basic Usage

A green success toast notification.

```
<ToastNotification title="Deployment successful" message="Your changes are live at remocn.dev" variant="success" />
```

### Error Toast

A red error toast with custom styling.

```
<ToastNotification title="Build failed" message="Check the logs for details" variant="error" cardColor="#1a1a1a" textColor="#fafafa" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| title | string | Deployment successful | Bold headline shown at the top. |
| message | string | Your changes are live at remocn.dev | Secondary message below the title. |
| variant | "success" \| "error" \| "info" \| "warning" | success | Controls the inline icon and accent color. |
| background | string | #fafafa | Frame background color. |
| cardColor | string | white | Toast card background color. |
| textColor | string | #171717 | Color of the toast title. |
| mutedColor | string | #71717a | Color of the toast message. |
| className | string | - | Optional className. |

## Notes

Phase timing is derived from durationInFrames — The toast reserves 15 frames for enter and 15 frames for exit, with the rest as hold phase.

Anchored absolutely — The toast is positioned at right: 32, bottom: 32. Make sure the parent composition fills the frame.
