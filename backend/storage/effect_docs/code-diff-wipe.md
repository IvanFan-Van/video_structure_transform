# CodeDiffWipe

## Description

Reveal an "after" code snippet by wiping a "before" snippet away. Two code panes stack, and the top layer is masked with clip-path: inset(0 X% 0 0) where X interpolates from 0 to 100, revealing the "after" code beneath.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/code-diff-wipe
```

## Usage

### Basic Usage

Show a before/after code comparison with a wipe transition.

```tsx
<CodeDiffWipe before={"function get() { /* old */ }"} after={"const get = async () => { /* new */ }"} />
```

### Feature Diff

Use custom timing for a specific reveal moment.

```tsx
<CodeDiffWipe before={oldCode} after={newCode} language="typescript" transitionStart={40} transitionDuration={45} accent="#7c3aed" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| before | string | - | Multi-line code on top, wiped away. |
| after | string | - | Multi-line code revealed underneath. |
| language | string | "tsx" | Language label in pane header. |
| background | string | "#0a0a0a" | Editor background. |
| accent | string | "#0ea5e9" | Accent for wipe line, handle, and label. |
| transitionStart | number | 20 | Frame at which the wipe begins. |
| transitionDuration | number | 60 | Frames the wipe takes from 0% to 100%. |
| showHandle | boolean | true | Render a circular handle on the wipe line. |
| className | string | - | Optional className. |

## Notes

- **GPU friendly** — `clip-path` is composited on the GPU in modern browsers.
- **Long lines** — The pane uses `whiteSpace: pre` and `overflow: hidden`, so long lines get clipped rather than wrapped.
