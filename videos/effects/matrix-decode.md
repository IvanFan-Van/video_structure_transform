# MatrixDecode

## Description

Random scramble resolves left-to-right into target text. A typography primitive that starts as a stream of random symbols and decodes character by character into the target text. Perfect for DevTools, cybersecurity, and AI reveal moments.

## Installation

```
pnpm dlx shadcn@latest add @remocn/matrix-decode
```

## Usage

### System Access

Decode text like a system access granted message. Use for cybersecurity or developer themes.

```
<MatrixDecode text="ACCESS GRANTED" revealDuration={60} />
```

### Custom Charset

Use a custom character pool for a different visual style.

```
<MatrixDecode text="DECRYPTING..." charset="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" revealDuration={45} color="#0ea5e9" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The final text the scramble resolves into. |
| charset | string | "!@#$%^&*()_+-=<>?/\\|" | Pool of characters used while scrambling. |
| fontSize | number | 72 | Font size in pixels. |
| color | string | "#22c55e" | Text color. |
| fontWeight | number | 600 | CSS font-weight. |
| revealDuration | number | 60 | How many frames it takes for the full text to decode. |
| speed | number | 1 | Multiplier for animation speed. |
| className | string | - | Optional className passed to the text span. |

## Notes

- **Deterministic randomness** — Uses Remotion's `random(seed)` keyed on character index and frame, so scrambled glyphs are stable across renders — no flicker between frames.
