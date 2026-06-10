# CursorFlow

## Description

A realistic mouse that arcs along cubic Bezier paths, pauses, and clicks targets that dip in response. Instead of moving on straight lines between waypoints, the cursor follows per-segment cubic Bezier curves whose control points are offset to create a natural arc. An ease-in-out function shapes velocity inside each segment. At click moments, an independent spring drives a press animation. Includes a SimulatedCursor variant for simpler straight-line movement.

## Installation

pnpm dlx shadcn@latest add @remocn/cursor-flow

## Usage

### Basic Usage

Cursor moves between UI elements with clicks. Use for product demos showing user interactions.

```tsx
<CursorFlow
  waypoints={[
    { x: 200, y: 180 },
    { x: 540, y: 240, click: true, label: "Generate" },
    { x: 880, y: 360, hold: 8 },
    { x: 1040, y: 520, click: true, label: "Publish" },
  ]}
/>
```

### Simple Cursor (SimulatedCursor variant)

Linear cursor movement with clicks. Use when Bezier arcs are overkill.

```tsx
<SimulatedCursor
  points={[
    { x: 200, y: 150, hold: 20 },
    { x: 800, y: 360, hold: 25, click: true },
    { x: 1050, y: 560, hold: 20 },
  ]}
  color="#ffffff"
/>
```

Installation for variant: pnpm dlx shadcn@latest add @remocn/simulated-cursor

## Props

### CursorFlow

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| waypoints | CursorWaypoint[] | - | Ordered list of points. Each has x, y, and optional hold, click, and label. |
| cursorColor | string | "#fafafa" | Cursor SVG fill color. |
| cursorSize | number | 28 | Cursor SVG side length in pixels. |
| segmentDuration | number | 36 | Frames spent traversing one segment. |
| background | string | "#0a0a0a" | Page background color. |
| showTargets | boolean | true | Render the click target chips at clickable waypoints. |
| speed | number | 1 | Playback speed multiplier. |
| className | string | - | Optional className passed to the root container. |

### SimulatedCursor

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| points | Array<{x:number; y:number; hold?:number; click?:boolean}> | 3 sample waypoints | Cursor waypoints in pixel coordinates. |
| color | string | "#ffffff" | Cursor fill color. |
| size | number | 32 | Cursor size in pixels. |
| background | string | "#0a0a0a" | Background color. |
| className | string | - | Optional className. |

## Notes

The arc is the point — Per-segment perpendicular control points alternate sign every other segment so the path snakes naturally.

No d3-shape — Curves are computed inline to avoid pulling in d3-shape just for path math.

Inline SVG, no assets — The cursor is drawn as inline SVG, so you don't need to copy anything into public/.
