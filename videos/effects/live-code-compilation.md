# LiveCodeCompilation

## Description

A split-screen where code is typed on the left and the right-side UI snaps to match in a single frame. A timeline-driven composition pairing a glass code editor with a live preview pane. As each event fires, a new code fragment is appended and the preview instantly applies the matching style — no CSS transitions — mimicking Vite HMR.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/live-code-compilation
```

## Usage

### Basic Usage

Code changes on the left instantly update the preview on the right. Use for developer tool demos.

```tsx
<LiveCodeCompilation accentColor="#3b82f6" />
```

### Custom Accent

Use a brand color for the code highlight and preview accents.

```tsx
<LiveCodeCompilation accentColor="#ff5e3a" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| accentColor | `string` | `"#3b82f6"` | Color for JSX prop highlight, HMR flash, and button background. |
| className | `string` | — | Optional className. |

## Notes

No transitions on the preview — The preview button intentionally sets `transition: none`. Each style change snaps in on a single frame so the right pane reads as a real hot module reload.
