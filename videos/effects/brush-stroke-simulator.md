# brush-stroke-simulator

## Description

A simulated fingertip drags a blur brush across an image, revealing a pixelated overlay along its trail. A semi-transparent fingertip glides across the frame along a chain of cubic-bezier waypoints, leaving a pixelated overlay in its wake. The reveal is driven by an SVG mask whose stroked path is rebuilt every frame from the cursor's accumulated trail.

## Installation

pnpm dlx shadcn@latest add @remocn/brush-stroke-simulator

## Usage

### Basic Usage

A brush reveals a hidden image underneath a pixelated overlay. Use for "before/after" image reveals.

```
<BrushStrokeSimulator brushSize={70} sweepDuration={150} />
```

### Custom Colors

Use custom base and overlay colors for a branded reveal.

```
<BrushStrokeSimulator brushSize={50} baseColorA="#ff0080" baseColorB="#7928ca" overlayColor="#1a1a2e" sweepDuration={120} startFrame={20} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| brushSize | number | 70 | Diameter of the cursor and width of the reveal stroke in pixels. |
| cursorColor | string | rgba(255,255,255,0.45) | Fill color of the semi-transparent fingertip circle. |
| background | string | #0a0a0a | Page background. |
| baseColorA | string | #f4a261 | Highlight tint of the simulated portrait. |
| baseColorB | string | #e76f51 | Shadow tint of the simulated portrait. |
| overlayColor | string | #1f1f23 | Base color of the pixelated overlay. |
| startFrame | number | 12 | Frame at which the brushing motion begins. |
| sweepDuration | number | 150 | How many frames the brush takes. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className. |

## Notes

Mask, not clip-path — SVG clipPath ignores stroke-width, so a stroked path can't be used as a clip. The reveal is built with an SVG mask instead.

Trail length grows with progress — The mask path is rebuilt from the cursor's accumulated samples every frame.
