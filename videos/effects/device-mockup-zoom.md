# DeviceMockupZoom

## Description

Pull back from a UI to reveal it inside a device frame. Starts zoomed into a UI screen and animates `transform: scale()` from 2 down to 1, revealing an inline SVG laptop or phone frame. No external assets — the device chrome is rendered with plain divs.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/device-mockup-zoom
```

## Usage

### Basic Usage

Zoom out to reveal a UI inside a laptop frame. Use for product hero shots.

```tsx
<DeviceMockupZoom>
  <YourAppScreen />
</DeviceMockupZoom>
```

### Phone Mockup

Show a mobile app inside a phone frame.

```tsx
<DeviceMockupZoom device="phone" frameColor="#333" background="#f0f0f0">
  <MobileAppScreen />
</DeviceMockupZoom>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| children | ReactNode | - | Content inside the device screen. |
| device | "laptop" \| "phone" | "laptop" | Which inline mockup to render. |
| frameColor | string | "#1f1f1f" | Device chrome color. |
| screenColor | string | "#0a0a0a" | Background behind screen content. |
| background | string | "#fafafa" | Outer background. |
| className | string | - | Optional className. |

## Notes

- **Replace with real mockups** — The inline SVG/div frame is intentional for zero asset dependencies. For photoreal mockups, swap for an image loaded via `staticFile()`.
