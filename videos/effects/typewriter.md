# Typewriter

## Description

Character-by-character text reveal with a deterministic blinking cursor. A typography primitive that reveals text one character at a time using interpolate and substring. The cursor blinks via integer math on the current frame, so it stays consistent across re-renders.

## Installation

```
pnpm dlx shadcn@latest add @remocn/typewriter
```

## Usage

### Basic Typewriter

Type out a message character by character. Use for terminal-style intros or narrated moments.

```
<Typewriter text="Hello, world" speed={20} fontSize={72} />
```

### Code Comment Reveal

Type slowly with a colored cursor for a developer-focused feel.

```
<Typewriter text="// Building the future" speed={10} fontSize={36} cursorColor="#22c55e" color="#a1a1aa" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| text | string | required | The text to type out. |
| cursor | boolean | true | Whether to render the blinking cursor at the end. |
| speed | number | 20 | Typing speed in characters per second. |
| fontSize | number | 48 | Font size in pixels. |
| fontWeight | number | 600 | CSS font-weight. |
| color | string | "#171717" | Text color (any valid CSS color). |
| cursorColor | string | "#171717" | Color of the blinking cursor block. |
| className | string | - | Optional className passed to the underlying span. |

## Notes

- **Deterministic blink** — The cursor uses `Math.floor(frame / 15) % 2 === 0` instead of `setInterval` or `Math.random()`. This is required for Remotion: every frame must be a pure function of frame, otherwise the rendered video will glitch.
- **Composition length** — Make sure your composition's `durationInFrames` is long enough to fit `text.length / speed` seconds of typing plus a hold at the end.
