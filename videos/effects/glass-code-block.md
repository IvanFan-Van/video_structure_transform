# GlassCodeBlock

## Description

A premium frosted-glass code editor window with a regex tokenizer and line-by-line stagger reveal. A code window primitive that uses backdrop-filter: blur() over a slow animated aura; a 1px linear-gradient ring fakes a top-edge highlight; macOS-style traffic lights are dimmed to 60%. Lines fade in one after another with a tiny upward slide via Sequence.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/glass-code-block
```

## Usage

### Basic Usage

Display code with a premium frosted-glass look and line-by-line reveal.

```tsx
<GlassCodeBlock title="hero.tsx" code={`export function Hero() {\n  return <h1>Hello</h1>;\n}`} />
```

### Fast Reveal

Quicker code reveal with smaller stagger.

```tsx
<GlassCodeBlock title="utils.ts" code={`const add = (a: number, b: number) => a + b;`} staggerFrames={2} fontSize={14} width={640} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| code | string | - | Source code to render. Newlines split into lines. |
| title | string | "hero.tsx" | Filename shown in the chrome bar. |
| width | number | 760 | Window width in pixels. |
| height | number | 460 | Window height. |
| fontSize | number | 16 | Code font size. |
| background | string | "#0a0a0a" | Background around the window. |
| glassColor | string | "rgba(10,10,10,0.6)" | Card surface. Keep alpha < 1 for glass. |
| staggerFrames | number | 4 | Frames between each line's reveal. |
| showTrafficLights | boolean | true | Show dimmed macOS-style window controls. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **Tokenizer scope** — The built-in tokenizer covers JS/TS keywords, strings, numbers, and // comments. For richer highlighting, replace `tokenizeLine`.
- **Backdrop filter requires content behind** — The component renders a slow built-in aura for the glass effect.
