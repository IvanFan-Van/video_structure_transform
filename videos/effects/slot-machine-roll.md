# SlotMachineRoll

## Description

Vertical reel scrolls each character from an old value to a new value. A typography primitive that animates changing values (prices, counters, statuses) as a vertical reel. Each character column rolls independently with a staggered spring, giving a slot-machine feel.

## Installation

```
pnpm dlx shadcn@latest add @remocn/slot-machine-roll
```

## Usage

### Price Counter

Roll from an old price to a new price. Use for pricing reveals or metric animations.

```
<SlotMachineRoll from="$99" to="$199" fontSize={120} />
```

### Stat Counter

Animate a numeric stat going up. Use for dashboard counters.

```
<SlotMachineRoll from="1,024" to="12,847" fontSize={96} color="#22c55e" speed={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| from | string | "$99" | Starting value shown before the reel rolls. |
| to | string | "$199" | Target value the reel settles on. |
| fontSize | number | 120 | Font size in pixels. Used to compute reel travel distance. |
| color | string | "#171717" | Text color. |
| fontWeight | number | 700 | CSS font-weight. |
| speed | number | 1 | Multiplier for animation speed. |
| className | string | - | Optional className passed to the outer text span. |

## Notes

- **Right-aligned by design** — `from` and `to` are left-padded with spaces to the same length so digits align on the right. This matches how prices and counters read.
- **Monospaced digits recommended** — Each column is a fixed width (0.7em). If you use a proportional font, wide characters like `W` may get clipped. Use a mono font or characters of similar width.
