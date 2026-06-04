# BrowserFlow

## Description

A full Safari/Chrome simulation from URL typing to scroll and click. The address bar takes focus, the URL types itself in, the loading bar stalls at 15% before snapping to 100%, the page renders, and a virtual cursor arcs down toward a CTA — clicking it with a scale dip and synchronous press on the button.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/browser-flow
```

## Usage

### Basic Usage

Full browser interaction simulation. Use for product demos showing a web app.

```tsx
<BrowserFlow url="remocn.dev" />
```

### Custom URL

Use with your own URL for a branded demo.

```tsx
<BrowserFlow url="myapp.com" speed={1.2} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| url | `string` | `"remocn.dev"` | URL typed into address bar. |
| speed | `number` | `1` | Multiplier applied to current frame. |
| className | `string` | — | Optional className. |

## Notes

The 15% stall is what sells it — Real browsers fake progress. The loading bar jumps to 15% on Enter, holds for suspense, then races to 100%. Removing that pause makes the flow feel synthetic.
