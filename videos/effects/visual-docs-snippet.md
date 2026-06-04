# VisualDocsSnippet

## Description

Calm tutorial flow — virtual cursor arcs to a button, clicks, and a bounding box plus tooltip explain what just happened. A virtual cursor traces a soft bezier arc to a CTA button, clicks with a micro-bounce, then a peach bounding box draws around the changed element while a side tooltip stagger-fades in.

## Installation

```
pnpm dlx shadcn@latest add @remocn/visual-docs-snippet
```

## Usage

### Tutorial Snippet

A cursor clicks a button and a tooltip explains the action. Use for documentation videos.

```tsx
<VisualDocsSnippet tooltipTitle="Generate runs" tooltipBody="Click to start a new generation. The job will appear in the sidebar." buttonLabel="Generate" />
```

### Custom Cursor Path

Re-aim the cursor to a different target with custom timing.

```tsx
<VisualDocsSnippet cursorStart={{ x: 900, y: 500 }} cursorTarget={{ x: 500, y: 300 }} clickFrame={90} tooltipTitle="Save changes" tooltipBody="Your work is automatically saved to the cloud." buttonLabel="Save" accent="#22c55e" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| cursorStart | {x:number;y:number} | {x:980,y:560} | Where cursor begins. |
| cursorTarget | {x:number;y:number} | {x:640,y:360} | Where cursor lands and clicks. |
| clickFrame | number | 110 | Frame click fires. All later anchors derive from this. |
| tooltipTitle | string | "Generate runs" | Tooltip heading. |
| tooltipBody | string | "Click to start a new generation..." | Tooltip body. |
| buttonLabel | string | "Generate" | CTA button label. |
| accent | string | "#FFB38E" | Peach accent for bounding box, tooltip, and ripple. |
| background | string | "#141318" | Stage background. |
| speed | number | 1 | Speed multiplier. |
| className | string | — | Optional className. |

## Notes

Retiming — All five timing anchors derive from the single clickFrame prop. Bumping clickFrame shifts the whole flow without breaking sync.

Cursor coordinates are absolute — In 1280x720 frame coordinate space. If you re-aim cursor, also re-aim cursorTarget.
