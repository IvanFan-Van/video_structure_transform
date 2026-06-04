# TerminalToBrowserDeploy

## Description

A CLI deploy completes and the live site grows out of the URL printed in the console. The terminal types out a deploy sequence, and when the success line lands, the terminal scales down and blurs while a fully formed browser window springs out from exactly the URL that was just printed.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/terminal-to-browser-deploy
```

## Usage

### Basic Usage

A terminal deploy sequence followed by the live site appearing. Use for deployment product demos.

```tsx
<TerminalToBrowserDeploy siteUrl="https://app.example.com" accentColor="#22c55e" />
```

### Custom Speed

Speed up or slow down the entire sequence.

```tsx
<TerminalToBrowserDeploy siteUrl="https://mysaas.com" accentColor="#7c3aed" speed={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| siteUrl | `string` | `"https://app.example.com"` | URL in deploy success line and browser address bar. |
| accentColor | `string` | `"#22c55e"` | Accent for success line, CTA, and browser glow. |
| speed | `number` | `1` | Multiplier for current frame. |
| className | `string` | — | Optional className. |

## Notes

The browser grows from the URL, not the screen center — The browser window's `transform-origin` is computed from the pixel position of the URL line, so the window literally unfurls out of the success line.
