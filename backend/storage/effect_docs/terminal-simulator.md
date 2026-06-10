# TerminalSimulator

## Description

A console window that types out commands and rolls older lines off the top. Each line is revealed via Sequence and typed character-by-character. Once the visible line count exceeds the window, the inner container slides up via translateY so the latest line is always in view.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/terminal-simulator
```

## Usage

### Basic Usage

Simulate a CLI build with command, log, success and error lines.

```tsx
<TerminalSimulator
  lines={[
    { text: "npm run build", type: "command" },
    { text: "Compiled successfully", type: "success", delay: 14 },
  ]}
/>
```

### Deploy Log

A longer deploy sequence with error handling.

```tsx
<TerminalSimulator
  lines={[
    { text: "git push origin main", type: "command" },
    { text: "Deploying to Vercel...", type: "log", delay: 10 },
    { text: "Build failed", type: "error", delay: 20 },
    { text: "Check config", type: "log", delay: 8 },
  ]}
  title="~/projects/app"
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| lines | Array<{text:string; type:'command'\|'log'\|'success'\|'error'; delay?:number}> | - | The lines to render. delay is the frame gap before typing starts. |
| prompt | string | "$" | Prompt prefix before command lines. |
| title | string | "~/projects/remocn" | Window chrome bar title. |
| background | string | "#0a0a0a" | Terminal background. |
| chromeColor | string | "#1a1a1a" | Window chrome bar color. |
| fontSize | number | 18 | Monospace font size. |
| charsPerFrame | number | 1 | Characters per frame typing speed. |
| className | string | - | Optional className. |

## Notes

- **Deterministic cursor** — Uses `Math.floor(frame / 15) % 2 === 0`.
- **Auto scroll** — Content layer translates upward in lineHeight increments when lines overflow.
