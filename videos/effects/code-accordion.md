# CodeAccordion

## Description

A code window that springs a range of lines closed and replaces them with a "N lines collapsed" placeholder. A single spring drives the height of a wrapped range from lineCount * lineHeight down to one line, fading the original code out and the placeholder in.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/code-accordion
```

## Usage

### Basic Usage

Collapse a range of irrelevant code lines to focus attention on the important parts.

```tsx
<CodeAccordion lines={fileContents.split("\n")} collapseRange={[3, 14]} collapseAt={30} />
```

### Delayed Collapse

Trigger the collapse later in the timeline.

```tsx
<CodeAccordion lines={codeLines} collapseRange={[5, 20]} collapseAt={60} title="index.ts" fontSize={14} width={800} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| lines | string[] | - | Lines of code. Pre-split into an array. |
| collapseRange | [number, number] | [3, 14] | Inclusive 0-based start and end line indices to collapse. |
| collapseAt | number | 30 | Frame at which the collapse spring fires. |
| title | string | "process-orders.ts" | Filename in chrome bar. |
| fontSize | number | 16 | Code font size. |
| width | number | 720 | Window width. |
| background | string | "#050505" | Page background. |
| cardColor | string | "#0a0a0a" | Editor surface. |
| textColor | string | "#e4e4e7" | Code color. |
| mutedColor | string | "#52525b" | Line numbers and placeholder color. |
| speed | number | 1 | Speed multiplier. |
| className | string | - | Optional className. |

## Notes

- **One spring, many properties** — A single `spring()` with `damping: 10` drives the inner height, opacity, and window height all from one value.
